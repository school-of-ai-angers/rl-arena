import subprocess
import time
import requests
import os
import numpy as np

MAX_HEALTH_CHECK_SECONDS = 30
HEALTH_CHECK_INTERVAL_SECONDS = 0.5
CALL_TIMEOUT = 10


def _run_shell(cmd, extra_env):
    env = os.environ.copy()
    env.update(extra_env)
    result = subprocess.run(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, env=env)
    return result.returncode, result.stdout.decode('utf-8')


def _to_jsonable(x):
    if isinstance(x, np.ndarray):
        return x.tolist()
    return x


class RemotePlayer:
    """
    Provide an interface like a Player, but will start a remote Docker image
    """

    def __init__(self, image_name, namespace, cpu_limit, memory_limit, service):
        """
        :param image_name: str
        :param namespace: str
        :param cpu_limit: float
        :param memory_limit: str
        :param service: str
        """
        self.service = service

        # Start docker
        status, docker_log = _run_shell([
            'docker-compose',
            '--project-name', namespace,
            '--file', 'run_duel/docker-compose.yml',
            'up',
            '--detach',
            service,
        ], {
            'PLAYER_IMAGE': image_name,
            'PLAYER_CPU_LIMIT': str(cpu_limit),
            'PLAYER_MEMORY_LIMIT': memory_limit,
        })
        assert status == 0, 'Docker image failed to start:\n'+docker_log

        # Health check
        max_health_time = time.time() + MAX_HEALTH_CHECK_SECONDS
        is_healthy = False
        while time.time() < max_health_time:
            try:
                response = requests.get(
                    f'http://{self.service}:8000/health-check')
                if response.status_code == 200:
                    is_healthy = True
                    break
            except:
                pass
            time.sleep(HEALTH_CHECK_INTERVAL_SECONDS)
        assert is_healthy, 'Docker image failed initial health check'

    def _request(self, action, body):
        response = requests.post(
            f'http://{self.service}:8000/{action}', json=body, timeout=CALL_TIMEOUT)
        assert response.status_code == 200, f'Call to {action} failed'
        return response.json()

    def start(self, state, valid_actions):
        """
        :param state: np.array
        :param valid_actions: np.array 1D
        :returns: float
        """
        output = self._request('start', {
            'state': _to_jsonable(state),
            'valid_actions': _to_jsonable(valid_actions)
        })
        return output['action']

    def step(self, state, valid_actions, prev_reward):
        """
        :param state: np.array
        :param valid_actions: np.array 1D
        :param prev_reward: float
        :returns: float
        """
        output = self._request('step', {
            'state': _to_jsonable(state),
            'valid_actions': _to_jsonable(valid_actions),
            'prev_reward': prev_reward
        })
        return output['action']

    def end(self, state, prev_reward):
        """
        :param state: np.array
        :param prev_reward: float
        """
        self._request('end', {
            'state': _to_jsonable(state),
            'prev_reward': prev_reward
        })
