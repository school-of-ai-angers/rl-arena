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


class BuilderController(TaskController):
    Model = Revision
    fields_prefix = 'image'
    scheduled_state = Revision.IMAGE_SCHEDULED
    running_state = Revision.IMAGE_RUNNING
    completed_state = Revision.IMAGE_COMPLETED
    failed_state = Revision.IMAGE_FAILED
    log_dir = os.path.join(settings.MEDIA_ROOT, 'revision_image_logs')

    def find_next_task(self):
        return Revision.objects.filter(
            image_state=Revision.IMAGE_SCHEDULED).order_by('created_at').first()

    def execute_task(self, task):
        # Create temp folder
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                # Load ZIP file
                submission = ZipFile(task.zip_file.path)

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
            image_name = f'rl-arena-player:{image_tag}'
            image_result, image_log = _run_shell(
                ['docker', 'build', '--tag', image_name, tmpdir])
            if image_result != 0:
                return self.TaskResult.error('Image failed to be built', image_log)

        task.image_name = image_name
        return self.TaskResult.success(image_log)


def main():
    BuilderController().run()


def _run_shell(cmd):
    result = subprocess.run(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    return result.returncode, result.stdout.decode('utf-8')
