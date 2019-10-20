from django.utils import timezone
from builder.build import build
from core.models import Submission
import time
import uuid
from datetime import timedelta
from django.conf import settings
import os

IDLE_SLEEP = timedelta(seconds=15)
BUILD_TIMEOUT = timedelta(minutes=10)


def main():
    # Continously look for images to build
    while True:
        # Timeout previous builds
        timeouts = Submission.objects.filter(
            state=Submission.BUILDING,
            image_started_at__lt=timezone.now() - BUILD_TIMEOUT
        ).update(
            state=Submission.WAITING_BUILD
        )
        if timeouts > 0:
            print(f'Timeouted {timeouts} builds')

        print('Search for submissions')
        submissions = Submission.objects.filter(
            state=Submission.WAITING_BUILD).all()[0:1]

        if len(submissions) == 1:
            submission = submissions[0]
            print(f'Will build {submission}')
            build_submission(submission)
        else:
            time.sleep(IDLE_SLEEP.total_seconds())


def build_submission(submission):
    # Change state to BUILDING
    submission.state = Submission.BUILDING
    submission.image_started_at = timezone.now()
    submission.save()

    # Call main builder logic
    print(f'Build zip {submission.zip_file.path}')
    result = build(submission.zip_file.path)
    print(f'Error = {result.error_msg}')

    # Save result
    submission.ended_at = timezone.now()
    if result.ok:
        submission.image_name = result.name
        submission.state = Submission.WAITING_SMOKE_TEST
    else:
        submission.image_error_msg = result.error_msg
        submission.state = Submission.BUILD_FAILED
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
                            'submission_image_logs', str(uuid.uuid4())+'.log')
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, 'w') as fp:
        fp.write(log_str)
    return log_path
