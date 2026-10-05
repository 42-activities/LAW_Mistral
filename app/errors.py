from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.modules.saas.service import LimitExceeded, TooManyAttempts


class NotFoundError(Exception):
    def __init__(self, detail: str) -> None:
        self.detail = detail


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    async def _not_found(_: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": exc.detail})

    @app.exception_handler(LimitExceeded)
    async def _limit(_: Request, exc: LimitExceeded) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={"detail": exc.detail},
            headers={"Retry-After": str(exc.retry_after)},
        )

    @app.exception_handler(TooManyAttempts)
    async def _attempts(_: Request, exc: TooManyAttempts) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={"detail": "too many failed sign-in attempts; try again later"},
            headers={"Retry-After": str(exc.retry_after)},
        )
