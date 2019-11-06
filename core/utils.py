import subprocess
import os


def run_shell(cmd, extra_env=None):
    env = os.environ.copy()
    if extra_env is not None:
        env.update(extra_env)
    result = subprocess.run(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, env=env)
    return result.returncode, result.stdout.decode('utf-8')
