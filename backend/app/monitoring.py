from __future__ import annotations

import logging
import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


logger = logging.getLogger("tee_time_app")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        start_time = time.perf_counter()
        response_status = 500
        try:
            response = await call_next(request)
            response_status = response.status_code
            return response
        finally:
            process_time_ms = (time.perf_counter() - start_time) * 1000
            client_host = request.client.host if request.client else "unknown"
            logger.info(
                "request",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response_status,
                    "duration_ms": round(process_time_ms, 2),
                    "client_host": client_host,
                },
            )


def setup_logging() -> None:
    if logger.handlers:
        return
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def setup_monitoring(app: FastAPI) -> None:
    setup_logging()

    app.add_middleware(RequestLoggingMiddleware)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:  # type: ignore[override]
        logger.exception("unhandled_exception", extra={"path": request.url.path})
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

