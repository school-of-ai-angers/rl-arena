from core.task_controller import TaskController
from core.models import Revision
import os
from django.conf import settings
import subprocess
import shutil
import traceback
import uuid
import json
from gzip import GzipFile

result_dir = 'revision_test_results'


class SmokeTesterController(TaskController):
    Model = Revision
    fields_prefix = 'test_'
    scheduled_state = Revision.TEST_SCHEDULED
    running_state = Revision.TEST_RUNNING
    completed_state = Revision.TEST_COMPLETED
    failed_state = Revision.TEST_FAILED
    log_dir = 'revision_test_logs'

    def find_next_task(self):
        return Revision.objects.filter(
            test_state=Revision.TEST_SCHEDULED, image_state=Revision.IMAGE_COMPLETED).order_by('created_at').first()

    def execute_task(self, task):
        # Run duel
        environment = task.competitor.environment
        output_file = f'{result_dir}/{uuid.uuid4()}.json.gz'
        status, duel_logs = _run_shell(
            ['./run_duel.sh', 'smoke_test_duel', task.image_name, task.image_name, environment.slug, output_file])
        if status != 0:
            return self.TaskResult.error('Internal error', duel_logs)

        # Check result
        try:
            with GzipFile(output_file, 'r') as fp:
                result = json.loads(fp.read().decode('utf-8'))
            for match in result['matches']:
                if match['result'] == 'PLAYER_1_ERROR' or match['result'] == 'PLAYER_2_ERROR':
                    return self.TaskResult.error('Player failed with ' + match['error_msg'], duel_logs)
                if match['result'] == 'OTHER_ERROR':
                    return self.TaskResult.error('Environment failed with ' + match['error_msg'], duel_logs)
        except Exception as e:
            return self.TaskResult.error(str(e), duel_logs)
        return self.TaskResult.success(duel_logs)


def main():
    SmokeTesterController().run()


def _run_shell(cmd):
    result = subprocess.run(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    return result.returncode, result.stdout.decode('utf-8')
