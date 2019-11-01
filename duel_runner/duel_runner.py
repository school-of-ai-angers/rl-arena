from core.task_controller import TaskController
from core.models import Duel
import os
from django.conf import settings
import subprocess
import shutil
import traceback
import uuid
import json
from gzip import GzipFile

result_dir = 'duel_results'


class DuelRunnerController(TaskController):
    Model = Duel
    fields_prefix = ''
    scheduled_state = Duel.SCHEDULED
    running_state = Duel.RUNNING
    completed_state = Duel.COMPLETED
    failed_state = Duel.FAILED
    log_dir = 'duel_logs'

    def find_next_task(self):
        return Duel.objects.filter(state=Duel.SCHEDULED).order_by('created_at').first()

    def execute_task(self, task):
        # Run duel
        environment = task.tournament.environment
        output_file = f'{result_dir}/{uuid.uuid4()}.json.gz'
        status, duel_logs = _run_shell([
            './run_duel.sh',
            'tournament_duel',
            task.player_1.image_name,
            task.player_2.image_name,
            environment.slug,
            output_file])
        if status != 0:
            return self.TaskResult.error('Internal error', duel_logs)

        # Save result
        try:
            with GzipFile(output_file, 'r') as fp:
                result = json.loads(fp.read().decode('utf-8'))
            task.results = output_file
            task.result = result['result']
            task.num_matches = result['num_matches']
            task.player_1_errors = result['player_1_errors']
            task.player_2_errors = result['player_2_errors']
            task.other_errors = result['other_errors']
            task.player_1_wins = result['player_1_wins']
            task.player_2_wins = result['player_2_wins']
            task.draws = result['draws']
            task.player_1_score = result['player_1_score']
            task.player_2_score = result['player_2_score']

            # Translate to task result
            if task.result == 'ERROR':
                return self.TaskResult.error(result['error_msg'], duel_logs)
        except Exception as e:
            return self.TaskResult.error(str(e), duel_logs)
        return self.TaskResult.success(duel_logs)


def main():
    DuelRunnerController().run()


def _run_shell(cmd):
    result = subprocess.run(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    return result.returncode, result.stdout.decode('utf-8')
