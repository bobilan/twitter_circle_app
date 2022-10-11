from fastapi import APIRouter, Request
from starlette.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from celery_utils import get_task_info
from circle_app.celery_tasks.tasks import score_accounts_task
from circle_app.factory import app
from models import TaskInfo

router = APIRouter(
    tags="scored_accounts",
    responses={404: {"description": "Not found"}}
)

app.mount("/static", StaticFiles(directory="templates"), name="static")
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def main_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/score/{username}")
async def score_accounts(username: str):
    task = score_accounts_task.apply_async(args=username)
    return JSONResponse({"task_id": task.id})


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    task_info = get_task_info(task_id)
    if task_info.task_result:
        return RedirectResponse(url=app.url_path_for("redirected"))
    return JSONResponse({"await": True})


@router.post("/scored-accounts")
async def get_scored_account(data: TaskInfo, request: Request):
    return templates.TemplateResponse("index.html", {"request": request, **data.task_result})

