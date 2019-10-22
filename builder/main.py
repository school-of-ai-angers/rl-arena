# Setup logs
import django
import logging
logging.basicConfig()
logger = logging.getLogger(__name__)

# Start Django in stand-alone mode
logger.info('Setup django')
django.setup()

if __name__ == "__main__":
    from builder.builder import main

    logger.info('Start app')
    main()
