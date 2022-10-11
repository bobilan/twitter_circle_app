import os
from functools import lru_cache
from typing import List

from kombu import Queue

SCORE_ACCOUNTS_QUEUE_NAME = "score_accounts"


def route_task(name, args, kwargs, options, task=None, **kw):
    que_dict = dict(queue=SCORE_ACCOUNTS_QUEUE_NAME)
    if ":" in name:
        queue, _ = name.split(":")
        que_dict = dict(queue=queue)
    return que_dict


class CeleryConfig:
    CELERY_BROKER_URL: str = os.environ.get("REDIS_BROKER", "redis://127.0.0.1:6379/0")
    CELERY_RESULT_BACKEND: str = os.environ.get("REDIS_BROKER", "redis://127.0.0.1:6379/0")

    CELERY_TASK_QUEUES: List[str] = [
        Queue("%s" % SCORE_ACCOUNTS_QUEUE_NAME)
    ]
    CELERY_TASK_ROUTES = (route_task,)


@lru_cache()
def get_settings() -> CeleryConfig:
    return CeleryConfig()


settings = get_settings()
