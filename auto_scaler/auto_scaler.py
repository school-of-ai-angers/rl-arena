from core.models import Revision, Duel, TaskWorker
import os
import digitalocean
import time
from datetime import timedelta
import logging
from django.db import models
import math
from django.utils import timezone
import uuid
import requests

sleep_time = timedelta(seconds=60)
avg_over = 10
min_avg = timedelta(minutes=1)
target_max_time = timedelta(minutes=15)
min_lifetime = timedelta(minutes=10)
max_lifetime = timedelta(minutes=100)
timeout = timedelta(minutes=10)
worker_tag = os.environ['DO_WORKER_TAG']
region = os.environ['DO_REGION']
size = os.environ['DO_SIZE']
image = os.environ['DO_IMAGE']
ssh_keys = os.environ['DO_SSH_KEYS']
private_ip = ''

logger = logging.getLogger(__name__)
duel_parallelism = int(os.environ['DUEL_PARALLELISM'])
max_task_workers = int(os.environ['MAX_TASK_WORKERS'])
token = os.environ['DO_TOKEN']
do_manager = digitalocean.Manager(token=token)


def main():
    # Get my private IP
    global private_ip
    private_ip = requests.get('http://169.254.169.254/metadata/v1/interfaces/private/0/ipv4/address').text
    logger.info(f'My private ip is {private_ip}')

    while True:
        logger.info('Start cycle')

        timeout_operations()

        desired = count_desired()
        current = TaskWorker.objects.filter(
            state__in=[TaskWorker.CREATING, TaskWorker.READY]
        ).count()

        logger.info(f'Current = {current}, desired = {desired}')
        if current > desired:
            stop_n(current - desired)
        elif current < desired:
            create_n(desired - current)

        destroy_stopped()

        time.sleep(sleep_time.total_seconds())


def timeout_operations():
    """ Look for operations that are stuck and mark them as failed """
    # Stuck at creating
    stuck = TaskWorker.objects.filter(
        state=TaskWorker.CREATING,
        creating_at__lt=timezone.now() - timeout)
    for worker in stuck:
        fail_worker(worker)

    # Stuck at stopping
    stuck = TaskWorker.objects.filter(
        state=TaskWorker.STOPPING,
        stopping_at__lt=timezone.now() - timeout)
    for worker in stuck:
        fail_worker(worker)

    # Running for too long
    stuck = TaskWorker.objects.filter(
        state=TaskWorker.READY,
        creating_at__lt=timezone.now() - max_lifetime)
    for worker in stuck:
        stop_worker(worker)


def get_avg_time(queryset, limit, start_field, end_field, min_value):
    result = queryset.order_by(f'-{end_field}')[:limit].aggregate(
        avg_time=models.Avg(models.F(end_field) - models.F(start_field)))
    avg_time = result['avg_time']
    if avg_time is None or avg_time < min_value:
        return min_value
    return avg_time


def fail_worker(worker):
    logger.error(f'Fail worker {worker} (state was {worker.state})')
    worker.state = TaskWorker.FAILED
    worker.failed_at = timezone.now()
    destroy_worker(worker)
    worker.save()


def stop_worker(worker):
    logger.info(f'Stop worker {worker} (state was {worker.state})')
    worker.state = TaskWorker.STOPPING
    worker.stopping_at = timezone.now()
    worker.save()


def count_desired():
    # Count pending
    pending_tests = Revision.objects.filter(
        test_state=Revision.TEST_SCHEDULED,
        image_state=Revision.IMAGE_COMPLETED).count()
    pending_duels = Duel.objects.filter(state=Duel.SCHEDULED).count()

    # Measure average execution time of the previous tasks
    avg_tests = get_avg_time(Revision.objects.filter(
        test_state__in=[Revision.TEST_COMPLETED, Revision.TEST_FAILED]
    ), avg_over, 'test_started_at', 'test_ended_at', min_avg)
    avg_duels = get_avg_time(Duel.objects.filter(
        state__in=[Duel.COMPLETED, Duel.FAILED]
    ), avg_over, 'started_at', 'ended_at', min_avg)

    logger.info(f'Pending {pending_tests}x{avg_tests} tests and {pending_duels}x{avg_duels} duels')

    # Total required resources
    needed_time = pending_tests * avg_tests + pending_duels * avg_duels
    needed_instances = math.ceil(needed_time / target_max_time / duel_parallelism)
    if needed_instances > max_task_workers:
        logger.warning(f'Capping {needed_instances} neeed instances to {max_task_workers}')
        needed_instances = max_task_workers

    return needed_instances


def create_n(n):
    """ Create `n` new workers """
    for i in range(n):
        name = f'{worker_tag}-{uuid.uuid4()}'
        worker = TaskWorker.objects.create(tag=name)
        user_data = f'''#!/bin/bash -e
        cd /root/rl-arena
        git pull
        docker build -t rl-arena .
        DO_TAG="{name}" POSTGRES_HOST="{private_ip}" docker-compose up -d duel_runner
        '''
        droplet = digitalocean.Droplet(
            token=token,
            name=name,
            region=region,
            size=size,
            image=image,
            ssh_keys=ssh_keys.split(','),
            user_data=user_data,
            private_networking=True,
            tags=[worker_tag, name]
        )
        droplet.create()
        logger.info(f'Created droplet {droplet.id}')


def stop_n(n):
    """ Stop up to `n` workers, respecting the minimum lifetime """
    workers = TaskWorker.objects.filter(
        state=TaskWorker.READY,
        creating_at__lt=timezone.now() - min_lifetime
    ).order_by('creating_at')[:n]

    for worker in workers:
        stop_worker(worker)


def destroy_stopped():
    for worker in TaskWorker.objects.filter(state=TaskWorker.STOPPED):
        logger.info(f'Destroy worker {worker} (state was {worker.state})')
        worker.state = TaskWorker.DESTROYED
        worker.destroyed_at = timezone.now()
        destroy_worker(worker)
        worker.save()


def destroy_worker(worker):
    droplets = do_manager.get_all_droplets(tag_name=worker.tag)

    if len(droplets) != 1:
        logger.error(f'Droplet with tag {worker.tag} not found ({len(droplets)} candidates)')
        return

    droplets[0].destroy()
