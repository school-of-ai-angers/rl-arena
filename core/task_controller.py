from core.models import Revision
import logging
from datetime import timedelta
import time
from django.utils import timezone
import os
import uuid
import traceback

logger = logging.getLogger(__name__)


class TaskController:
    """
    Implement common logic for the execution of background tasks.

    Subclass this, fille the necessary fields and then call run()
    """

    idle_sleep = timedelta(seconds=15)
    task_timeout = timedelta(minutes=10)

    # This class is tighly coupled with how the Revision model works, with fields
    # like FOO_state, FOO_started_at, FOO_ended_at, FOO_error_msg and FOO_test_logs
    # The fields below are parameter for this structure
    Model = None
    fields_prefix = None
    scheduled_state = None
    running_state = None
    completed_state = None
    failed_state = None

    # The dir into which to save the logs
    log_dir = None

    class TaskResult:
        """
        A simple wrapper for representing whether the task failed or completed
        """

        def __init__(self, ok, error_msg, task_log):
            self.ok = ok
            self.error_msg = error_msg
            self.task_log = task_log

        @classmethod
        def error(cls, error_msg, task_log=None):
            return cls(False, error_msg, task_log)

        @classmethod
        def success(cls, task_log):
            return cls(True, None, task_log)

    def find_next_task(self):
        """
        Should return a task or None
        """
        raise NotImplementedError

    def execute_task(self, task):
        """
        Do something with the task and returns a TaskResult.
        Feel free to raise in case of unkown error, it will be handled nicely
        """
        raise NotImplementedError

    def run(self):
        if self.log_dir:
            os.makedirs(self.log_dir, exist_ok=True)

        # Continously look for tasks to run
        while True:
            # Timeout previous tasks
            timeouts = self.Model.objects.filter(**{
                f'{self.fields_prefix}_state': self.running_state,
                f'{self.fields_prefix}_started_at__lt': timezone.now() - self.task_timeout
            }).update(**{
                f'{self.fields_prefix}_state': self.scheduled_state
            })
            if timeouts > 0:
                logger.warn(f'Timeouted {timeouts} tasks')

            logger.info('Search for next task')
            task = self.find_next_task()

            if task:
                logger.info(f'Will execute task {task}')

                # Change state
                setattr(task, f'{self.fields_prefix}_state',
                        self.running_state)
                setattr(
                    task, f'{self.fields_prefix}_started_at', timezone.now())
                task.save()

                # Call main builder logic
                try:
                    result = self.execute_task(task)
                except Exception as e:
                    result = self.TaskResult.error(
                        str(e), traceback.format_exc())

                # Save result
                if result.ok:
                    logger.info('Task completed')
                    setattr(task, f'{self.fields_prefix}_state',
                            self.completed_state)
                else:
                    logger.warn(f'Task failed with {result.error_msg}')
                    setattr(task, f'{self.fields_prefix}_state',
                            self.failed_state)
                    setattr(
                        task, f'{self.fields_prefix}_error_msg', result.error_msg[:200])
                setattr(task, f'{self.fields_prefix}_logs',
                        self.create_log_file(result.task_log))
                setattr(task, f'{self.fields_prefix}_ended_at', timezone.now())
                task.save()
            else:
                time.sleep(self.idle_sleep.total_seconds())

    def create_log_file(self, log_str):
        """
        :param log_str: str or None
        :returns str or None: the file path
        """
        if log_str is None:
            return None

        log_path = os.path.join(self.log_dir, str(uuid.uuid4())+'.log')
        with open(log_path, 'w') as fp:
            fp.write(log_str)
        return log_path
