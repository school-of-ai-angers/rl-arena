from core.models import Revision
import logging
from datetime import timedelta
import time
from django.utils import timezone
import os
import uuid
import traceback
from django.core.files.base import ContentFile
from django.db import transaction

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

    # Whether to stop any further task search
    stop = False

    # The TaskWorker instance (if any) that runs this task
    task_worker = None

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
        Use select_for_update(skip_locked=True) to allow for multiple parallel runs
        (https://docs.djangoproject.com/en/2.2/ref/models/querysets/#select-for-update)
        """
        raise NotImplementedError

    def execute_task(self, task):
        """
        Do something with the task and returns a TaskResult.
        Feel free to raise in case of unkown error, it will be handled nicely
        """
        raise NotImplementedError

    def run(self):
        # Continously look for tasks to run
        while not self.stop:
            # Timeout previous tasks
            timeouts = self.Model.objects.filter(**{
                f'{self.fields_prefix}state': self.running_state,
                f'{self.fields_prefix}started_at__lt': timezone.now() - self.task_timeout
            }).update(**{
                f'{self.fields_prefix}state': self.scheduled_state
            })
            if timeouts > 0:
                logger.warn(f'Timeouted {timeouts} tasks')

            # Search task and set it as running
            logger.info('Search for next task')
            task = None
            with transaction.atomic():
                task = self.find_next_task()

                if task:
                    logger.info(f'Will execute task {task}')

                    # Change state
                    setattr(task, f'{self.fields_prefix}state',
                            self.running_state)
                    setattr(
                        task, f'{self.fields_prefix}started_at', timezone.now())
                    if self.task_worker:
                        setattr(task, f'{self.fields_prefix}task_worker', self.task_worker)
                    task.save()

            # Run selected task
            if task:
                # Change state
                setattr(task, f'{self.fields_prefix}state',
                        self.running_state)
                setattr(
                    task, f'{self.fields_prefix}started_at', timezone.now())
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
                    setattr(task, f'{self.fields_prefix}state',
                            self.completed_state)
                else:
                    logger.warn(f'Task failed with {result.error_msg}')
                    setattr(task, f'{self.fields_prefix}state',
                            self.failed_state)
                    setattr(
                        task, f'{self.fields_prefix}error_msg', result.error_msg[:200])
                self.create_log_file(task, result.task_log)
                setattr(task, f'{self.fields_prefix}ended_at', timezone.now())
                task.save()
            else:
                time.sleep(self.idle_sleep.total_seconds())

    def create_log_file(self, task, log_str):
        """
        :param log_str: str or None
        """
        if log_str is None:
            return

        field_file = getattr(task, f'{self.fields_prefix}logs')
        field_file.save(f'{self.log_dir}/{uuid.uuid4()}.log', ContentFile(bytes(log_str, 'utf-8')))
