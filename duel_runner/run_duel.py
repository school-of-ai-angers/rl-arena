import threading
import os
from queue import LifoQueue
from core.utils import run_shell
import logging

logger = logging.getLogger(__name__)
parallelism = int(os.environ['DUEL_PARALLELISM'])

# Create namespaces tokens
available_namespaces = LifoQueue(parallelism)
for i in range(parallelism):
    available_namespaces.put_nowait(f'rl_arena_duel_{i}')


def run_duel(image_1, image_2, environment, output_file, log_1_file, log_2_file):
    """
    :param image_1: str
    :param image_2: str
    :param environment: str
    :param output_file: str
    :param log_1_file: str
    :param log_2_file: str
    :returns: int, str
    """
    # Grab (or wait for) a namespace
    namespace = available_namespaces.get()
    logger.info(f'Run duel in namespace {namespace}')

    # Run
    try:
        status, duel_logs = run_shell([
            './run_duel.sh',
            namespace,
            image_1,
            image_2,
            environment,
            output_file,
            log_1_file,
            log_2_file])
    finally:
        available_namespaces.put_nowait(namespace)

    return status, duel_logs
