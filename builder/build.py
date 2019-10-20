import re
import tempfile
import shutil
from zipfile import ZipFile
import os
import subprocess
import traceback


class BuildResult:
    def __init__(self, ok, error_msg, build_log, name):
        self.ok = ok
        self.error_msg = error_msg
        self.build_log = build_log
        self.name = name

    @staticmethod
    def error(error_msg, build_log=None):
        return BuildResult(False, error_msg, build_log, None)

    @staticmethod
    def success(build_log, name):
        return BuildResult(True, None, build_log, name)


def _run_shell(cmd):
    result = subprocess.run(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    return result.returncode, result.stdout.decode('utf-8')


def build(zip_path, image_tag):
    """
    :param zip_path: str
    :param image_tag: str
    :returns: BuildResult
    """
    try:
        # Create temp folder
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                # Load ZIP file
                submission = ZipFile(zip_path)

                # Unzip
                submission.extractall(tmpdir)
            except:
                traceback.print_exc()
                return BuildResult.error('Failed to unzip provided file')

            # Check zip files
            for expected_file in ['environment.yml', 'player.py']:
                if not os.path.exists(os.path.join(tmpdir, expected_file)):
                    return BuildResult.error(
                        f'The expected file {expected_file} was not found in the provided ZIP')

            # Copy extra image files
            for image_file in os.scandir('builder/image'):
                shutil.copy2(image_file.path, tmpdir)

            # Build image
            image_name = f'rl-arena-player:{image_tag}'
            image_result, image_log = _run_shell(
                ['docker', 'build', '--tag', image_name, tmpdir])
            if image_result != 0:
                return BuildResult.error('Image failed to be built', image_log)

        return BuildResult.success(image_log, image_name)
    except:
        traceback.print_exc()
        return BuildResult.error('Unexpected error')
