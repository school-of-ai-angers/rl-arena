from django.utils import timezone
from builder.build import build
from core.models import Revision
import time
import uuid
from datetime import timedelta
from django.conf import settings
import os
import logging


IDLE_SLEEP = timedelta(seconds=15)
BUILD_TIMEOUT = timedelta(minutes=10)
logger = logging.getLogger(__name__)


def main():
    # Continously look for images to build
    while True:
        # Timeout previous builds
        timeouts = Revision.objects.filter(
            image_state=Revision.IMAGE_RUNNING,
            image_started_at__lt=timezone.now() - BUILD_TIMEOUT
        ).update(
            image_state=Revision.IMAGE_SCHEDULED
        )
        if timeouts > 0:
            logger.warn(f'Timeouted {timeouts} builds')

        logger.info('Search for submissions')
        submission = Revision.objects.filter(
            image_state=Revision.IMAGE_SCHEDULED).order_by('created_at').first()

        if submission:
            logger.info(f'Will build {submission}')
            build_submission(submission)
        else:
            time.sleep(IDLE_SLEEP.total_seconds())


def build_submission(submission):
    # Change state
    submission.image_state = Revision.IMAGE_RUNNING
    submission.image_started_at = timezone.now()
    submission.save()

    # Call main builder logic
    logger.info(f'Build zip {submission.zip_file.path}')
    image_tag = str(uuid.uuid4())
    result = build(submission.zip_file.path, image_tag)
    logger.warn(f'Build error {result.error_msg}')

    # Save result
    if result.ok:
        submission.image_name = result.name
        submission.image_state = Revision.IMAGE_COMPLETED
    else:
        submission.image_error_msg = result.error_msg
        submission.image_state = Revision.IMAGE_FAILED
    submission.image_logs = create_log_file(result.build_log)
    submission.image_ended_at = timezone.now()
    submission.save()


def create_log_file(log_str):
    """
    :param log_str: str or None
    :returns str or None: the file path
    """
    if log_str is None:
        return None

    log_path = os.path.join(settings.MEDIA_ROOT,
                            'revision_image_logs', str(uuid.uuid4())+'.log')
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, 'w') as fp:
        fp.write(log_str)
    return log_path
