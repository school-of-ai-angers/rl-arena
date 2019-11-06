from core.task_controller import TaskController
from django.core.files.storage import default_storage
from core.models import Duel
import os
from django.conf import settings
import traceback
import uuid
import json
from gzip import decompress
from duel_runner.run_duel import run_duel


class TournamentController(TaskController):
    Model = Duel
    fields_prefix = ''
    scheduled_state = Duel.SCHEDULED
    running_state = Duel.RUNNING
    completed_state = Duel.COMPLETED
    failed_state = Duel.FAILED
    log_dir = 'duel_logs'

    def find_next_task(self):
        return Duel.objects.select_for_update(skip_locked=True) \
            .filter(state=Duel.SCHEDULED).order_by('created_at').first()

    def execute_task(self, task):
        # Run duel
        environment = task.tournament.environment
        output_file = f'duel_results/{uuid.uuid4()}.json.gz'
        log_1_file = f'duel_player_logs/{uuid.uuid4()}.log'
        log_2_file = f'duel_player_logs/{uuid.uuid4()}.log'
        status, duel_logs = run_duel(
            task.player_1.image_name,
            task.player_2.image_name,
            environment.slug,
            output_file,
            log_1_file,
            log_2_file)
        if status != 0:
            return self.TaskResult.error('Internal error', duel_logs)

        # Save player logs
        task.player_1_logs = log_1_file
        task.player_2_logs = log_2_file

        # Save result
        try:
            with default_storage.open(output_file) as fp:
                contents = decompress(fp.read())
                task.results = fp
            result = json.loads(contents.decode('utf-8'))
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
