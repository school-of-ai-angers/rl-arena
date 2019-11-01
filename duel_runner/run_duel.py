import threading
import os
from queue import LifoQueue
import subprocess
import logging

logger = logging.getLogger(__name__)
parallelism = int(os.environ['DUEL_PARALLELISM'])

# Create namespaces tokens
available_namespaces = LifoQueue(parallelism)
for i in range(parallelism):
    available_namespaces.put_nowait(f'rl_arena_duel_{i}')


def run_duel(image_1, image_2, environment, output_file):
    """
    :param image_1: str
    :param image_2: str
    :param environment: str
    :param output_file: str
    :returns: int, str
    """
    # Grab (or wait for) a namespace
    namespace = available_namespaces.get()
    logger.info(f'Run duel in namespace {namespace}')

    # Run
    try:
        status, duel_logs = _run_shell([
            './run_duel.sh',
            namespace,
            image_1,
            image_2,
            environment,
            output_file])
    finally:
        available_namespaces.put_nowait(namespace)

    return status, duel_logs


def _run_shell(cmd):
    result = subprocess.run(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    return result.returncode, result.stdout.decode('utf-8')
