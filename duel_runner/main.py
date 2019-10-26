# Setup logs
import django
import logging
import os
logging.basicConfig(level=os.environ['LOG_LEVEL'])
logger = logging.getLogger(__name__)

# Start Django in stand-alone mode
logger.info('Setup django')
django.setup()

if __name__ == "__main__":
    from duel_runner.duel_runner import main

    logger.info('Start app')
    main()
