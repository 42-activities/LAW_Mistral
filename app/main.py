from fastapi import FastAPI

from app.api.v1 import api_router


def create_app() -> FastAPI:
    app = FastAPI(title="Jurisdiction Recommender", version="0.0.0")
    app.include_router(api_router)
    return app


app = create_app()
