from celery import current_app as current_celery_app
from celery.app import Celery
from celery.result import AsyncResult

from celery_config import settings
from models import TaskInfo


def create_celery() -> Celery:
    celery_app = current_celery_app
    celery_app.config_from_object(settings, namespace="CELERY")
    celery_app.conf.update(task_track_started=True)
    celery_app.conf.update(task_serializer="pickle")
    celery_app.conf.update(result_serializer="pickle")
    celery_app.conf.update(accept_content=["pickle", "json"])
    celery_app.conf.update(result_expires=200)
    celery_app.conf.update(result_persistent=True)
    celery_app.conf.update(worker_send_task_events=False)
    celery_app.conf.update(worker_prefetch_multiplier=1)

    return celery_app


def get_task_info(task_id) -> TaskInfo:
    """
    :returns task info for a given task
    :param task_id:
    :return:
    """
    task_result = AsyncResult(task_id)
    return TaskInfo(
        task_id=task_id,
        task_result=task_result.result,
        task_status=task_result.status
    )
