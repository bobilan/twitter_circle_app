import uvicorn
from fastapi import FastAPI


from celery_utils import create_celery

from circle_app.api import scored_accounts_api


def create_circle_app() -> FastAPI:
    current_app = FastAPI()
    current_app.celery_app = create_celery()
    current_app.include_router(scored_accounts_api.router)

    return current_app


app = create_circle_app()
celery = app.celery_app


if __name__ == "__main__":
    uvicorn.run("circle_app/factory:app", port=5700, reload=True)
