from core.task_controller import TaskController
from core.models import Revision
import subprocess
import tempfile
import shutil
from zipfile import ZipFile
import traceback
import logging
import os
from django.conf import settings
from django.urls import reverse
logger = logging.getLogger(__name__)

PUBLISHER_WEB_URL = os.environ['PUBLISHER_WEB_URL']


class PublisherController(TaskController):
    Model = Revision
    fields_prefix = 'publish_'
    scheduled_state = Revision.PUBLISH_SCHEDULED
    running_state = Revision.PUBLISH_RUNNING
    completed_state = Revision.PUBLISH_COMPLETED
    failed_state = Revision.PUBLISH_FAILED
    log_dir = 'revision_publish_logs'

    def find_next_task(self):
        return Revision.objects \
            .filter(publish_state=Revision.PUBLISH_SCHEDULED, image_state=Revision.IMAGE_COMPLETED) \
            .order_by('created_at').first()

    def execute_task(self, task):
        # Note that this task is not thread safe: at most one can be executed at a time

        # Create temp folder
        with tempfile.TemporaryDirectory() as tmpdir:
            # Unzip
            try:
                with task.zip_file.open('rb') as fp:
                    submission = ZipFile(fp)
                    submission.extractall(tmpdir)
            except:
                return self.TaskResult.error('Failed to unzip provided file', traceback.format_exc())

            # Rewrite big files with a warning (GitHub accepts up to 100MiB, but we will use a much lower limit of 1MiB
            # to make sure the full repo won't too big either)
            for root, dirs, files in os.walk(tmpdir):
                for name in files:
                    file_path = os.path.join(root, name)
                    size_MiB = os.path.getsize(file_path) / 1024 / 1024
                    if size_MiB > 1:
                        logger.warning(f'File {file_path} is too big ({size_MiB:.1f}MiB)')
                        with open(file_path, 'w') as fp:
                            fp.write(f'!!! The original file was too large !!!\nPlease find the complete ZIP on the platform')

            # Prepare commands
            competitor = task.competitor
            environment = competitor.environment
            submitter = competitor.submitter
            destination = f'data/publish_repo/{environment.slug}/{competitor.name}'
            commit_message = f'Publish {competitor.name} v{task.version_number} for {environment.name} by {submitter.username}'
            cmds = [
                ['git', '-C', 'data/publish_repo', 'fetch'],
                ['git', '-C', 'data/publish_repo',
                    'reset', '--hard', 'origin/master'],
                ['rm', '-rf', destination],
                ['mkdir', '-p', destination],
                ['cp', '-r', tmpdir + '/.', destination],
                ['git', '-C', 'data/publish_repo', 'add', '-A'],
                ['git', '-C', 'data/publish_repo', 'commit', '--allow-empty', '-m', commit_message],
                ['git', '-C', 'data/publish_repo', 'push'],
            ]

            # Run them sequentially
            logs = ''
            for cmd in cmds:
                status, extra_logs = _run_shell(cmd)
                logs += f'$ {cmd}\n{extra_logs}'
                if status != 0:
                    return self.TaskResult.error(f'Operation failed with status {status}', logs)
            _, commit = _run_shell(
                ['git', '-C', 'data/publish_repo', 'rev-parse', 'HEAD'])
            task.publish_url = f'{PUBLISHER_WEB_URL}/blob/{commit.strip()}/{environment.slug}/{competitor.name}/player.py'
            return self.TaskResult.success(logs)


def main():
    # Prepare GitHub repo
    clone_status, clone_log = _run_shell(
        ['git', 'clone', os.environ['PUBLISHER_REMOTE'], 'data/publish_repo'])
    if clone_status != 0:
        logger.warn(clone_log)
    if not os.path.exists('data/publish_repo/.git'):
        raise Exception('Failed to clone repo')
    _run_shell(['git', 'config', '--global', 'user.name', 'Publisher Bot'])
    _run_shell(['git', 'config', '--global', 'user.email', 'publisher_bot'])

    PublisherController().run()


def _run_shell(cmd):
    result = subprocess.run(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    return result.returncode, result.stdout.decode('utf-8')
