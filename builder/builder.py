from core.task_controller import TaskController
from core.models import Revision
import os
from django.conf import settings
import subprocess
import tempfile
import shutil
from zipfile import ZipFile
import traceback
import uuid

image_base_name = os.environ['PLAYER_IMAGE_NAME']
push_image = bool(int(os.environ['PLAYER_IMAGE_PUSH']))


class BuilderController(TaskController):
    Model = Revision
    fields_prefix = 'image_'
    scheduled_state = Revision.IMAGE_SCHEDULED
    running_state = Revision.IMAGE_RUNNING
    completed_state = Revision.IMAGE_COMPLETED
    failed_state = Revision.IMAGE_FAILED
    log_dir = 'revision_image_logs'

    def find_next_task(self):
        return Revision.objects.filter(
            image_state=Revision.IMAGE_SCHEDULED).order_by('created_at').first()

    def execute_task(self, task):
        # Create temp folder
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                # Load ZIP file
                submission = ZipFile(task.zip_file.open('rb'))

                # Unzip
                submission.extractall(tmpdir)
            except:
                return self.TaskResult.error('Failed to unzip provided file', traceback.format_exc())

            # Check zip files
            for expected_file in ['environment.yml', 'player.py']:
                if not os.path.exists(os.path.join(tmpdir, expected_file)):
                    return self.TaskResult.error(
                        f'The expected file {expected_file} was not found in the provided ZIP')

            # Copy extra image files
            for image_file in os.scandir('builder/image'):
                shutil.copy2(image_file.path, tmpdir)

            # Build image
            image_tag = str(uuid.uuid4())
            image_name = f'{image_base_name}:{image_tag}'
            image_result, image_log = _run_shell(
                ['docker', 'build', '--tag', image_name, tmpdir])
            if image_result != 0:
                return self.TaskResult.error('Image failed to be built', image_log)

            if push_image:
                # Push image
                push_result, push_log = _run_shell(['docker', 'push', image_name])
                if push_result != 0:
                    image_log += '\n---\n' + push_log
                    return self.TaskResult.error('Image failed to be pushed', image_log)

        task.image_name = image_name
        return self.TaskResult.success(image_log)


def main():
    BuilderController().run()


def _run_shell(cmd):
    result = subprocess.run(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    return result.returncode, result.stdout.decode('utf-8')
