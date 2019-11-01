# Setup logs
import django
import logging
import os
import threading
logging.basicConfig(level=os.environ['LOG_LEVEL'])
logger = logging.getLogger(__name__)
parallelism = int(os.environ['DUEL_PARALLELISM'])

# Start Django in stand-alone mode
logger.info('Setup django')
django.setup()

if __name__ == "__main__":
    from duel_runner.smoke import SmokeController
    from duel_runner.tournament import TournamentController

    logger.info('Start app')
    smoke = SmokeController()
    tournament = TournamentController()
    for i in range(parallelism):
        # Start one thread for each controller
        threading.Thread(target=smoke.run).start()
        threading.Thread(target=tournament.run).start()
