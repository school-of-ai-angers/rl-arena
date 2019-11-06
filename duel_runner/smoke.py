from core.task_controller import TaskController
from django.core.files.storage import default_storage
from core.models import Revision
import os
from django.conf import settings
import traceback
import uuid
import json
from gzip import decompress
from duel_runner.run_duel import run_duel


class SmokeController(TaskController):
    Model = Revision
    fields_prefix = 'test_'
    scheduled_state = Revision.TEST_SCHEDULED
    running_state = Revision.TEST_RUNNING
    completed_state = Revision.TEST_COMPLETED
    failed_state = Revision.TEST_FAILED
    log_dir = 'revision_test_logs'

    def find_next_task(self):
        return Revision.objects.select_for_update(skip_locked=True) \
            .filter(test_state=Revision.TEST_SCHEDULED, image_state=Revision.IMAGE_COMPLETED).order_by('created_at').first()

    def execute_task(self, task):
        # Run duel
        environment = task.competitor.environment
        output_file = f'revision_test_results/{uuid.uuid4()}.json.gz'
        log_1_file = f'revision_test_player_logs/{uuid.uuid4()}.log'
        log_2_file = f'revision_test_player_logs/{uuid.uuid4()}.log'
        status, duel_logs = run_duel(task.image_name, task.image_name, environment.slug,
                                     output_file, log_1_file, log_2_file)
        if status != 0:
            return self.TaskResult.error('Internal error', duel_logs)

        # Save player logs
        task.test_player_1_logs = log_1_file
        task.test_player_2_logs = log_2_file

        # Check result
        try:
            with default_storage.open(output_file) as fp:
                contents = decompress(fp.read())
            result = json.loads(contents.decode('utf-8'))
            for match in result['matches']:
                if match['result'] == 'PLAYER_1_ERROR' or match['result'] == 'PLAYER_2_ERROR':
                    return self.TaskResult.error('Player failed with ' + match['error_msg'], duel_logs)
                if match['result'] == 'OTHER_ERROR':
                    return self.TaskResult.error('Environment failed with ' + match['error_msg'], duel_logs)
        except Exception as e:
            return self.TaskResult.error(str(e), duel_logs)
        return self.TaskResult.success(duel_logs)
