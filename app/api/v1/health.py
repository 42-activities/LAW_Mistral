from fastapi import APIRouter, Response

from app.db import check_database

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
def ready(response: Response) -> dict[str, str]:
    if check_database():
        return {"status": "ready"}
    response.status_code = 503
    return {"status": "unavailable"}
