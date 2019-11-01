# Setup logs
import django
import logging
import os
import threading
from django.utils import timezone
import time
logging.basicConfig(level=os.environ['LOG_LEVEL'])
logger = logging.getLogger(__name__)
parallelism = int(os.environ['DUEL_PARALLELISM'])
do_tag = os.environ.get('DO_TAG')

# Start Django in stand-alone mode
logger.info('Setup django')
django.setup()

if __name__ == "__main__":
    from duel_runner.smoke import SmokeController
    from duel_runner.tournament import TournamentController
    from core.models import TaskWorker

    logger.info('Start app')
    smoke = SmokeController()
    tournament = TournamentController()
    threads = []
    task_worker = None

    if do_tag:
        # Mark worker as ready
        task_worker = TaskWorker.objects.get(tag=do_tag)
        logger.info(f'Set task worker {task_worker} as ready')
        task_worker.state = TaskWorker.READY
        task_worker.ready_at = timezone.now()
        task_worker.save()
        smoke.task_worker = task_worker
        tournament.task_worker = task_worker

    for i in range(parallelism):
        # Start one thread for each controller
        threads.append(threading.Thread(target=smoke.run))
        threads.append(threading.Thread(target=tournament.run))
    for t in threads:
        t.start()

    if do_tag:
        # Monitor for stop signal
        while True:
            time.sleep(15)
            task_worker.refresh_from_db()
            if task_worker.state != TaskWorker.READY:
                logger.info(f'Handling stop signal')
                smoke.stop = True
                tournament.stop = True
                break
    else:
        logger.info('Standalone mode')

    # Wait for all tasks to end
    for t in threads:
        t.join()

    if do_tag:
        # Mark worker as done
        logger.info(f'Set task worker {task_worker} as stopped')
        task_worker.state = TaskWorker.STOPPED
        task_worker.stopped_at = timezone.now()
        task_worker.save()
