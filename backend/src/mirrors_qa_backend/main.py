from contextlib import asynccontextmanager

from fastapi import FastAPI

from mirrors_qa_backend import db
from mirrors_qa_backend.routes import auth, tests


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.upgrade_db_schema()
    db.initialize_mirrors()
    yield


def create_app(*, debug: bool = True):
    app = FastAPI(debug=debug, docs_url="/", lifespan=lifespan)

    app.include_router(router=tests.router)
    app.include_router(router=auth.router)

    return app


app = create_app()
