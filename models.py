from typing import Any, Dict

from pydantic import BaseModel


class TaskInfo(BaseModel):
    task_id: str
    task_result: Dict[str, Any]
    task_status: str
