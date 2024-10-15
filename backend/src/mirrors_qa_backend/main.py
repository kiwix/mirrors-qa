from contextlib import asynccontextmanager

from fastapi import FastAPI

from mirrors_qa_backend.db import initialize_mirrors, upgrade_db_schema
from mirrors_qa_backend.routes import auth, health, tests, worker


@asynccontextmanager
async def lifespan(_: FastAPI):
    upgrade_db_schema()
    initialize_mirrors()
    yield


def create_app(*, debug: bool = True):
    app = FastAPI(debug=debug, docs_url="/", lifespan=lifespan)

    app.include_router(router=tests.router)
    app.include_router(router=auth.router)
    app.include_router(router=worker.router)
    app.include_router(router=health.router)

    return app


app = create_app()
