import time
import argparse
from build import build
from mongo import db

if __name__ == "__main__":
    while True:
        print('Will look for a new build job')
        next_job = db.build_jobs.find_one({'status': 'PENDING'})

        if next_job is not None:
            print(f'Found job {next_job["_id"]}')

        time.sleep(30)
