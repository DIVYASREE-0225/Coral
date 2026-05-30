"""structlog configuration + FastAPI request-ID middleware.

Each incoming request gets a UUID4 request_id. Logs emitted within the
request handler include that ID via structlog's contextvars binding.
"""
from __future__ import annotations

import logging
import sys
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from config import settings


def configure() -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(stream=sys.stdout, level=level, format="%(message)s")

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    if settings.log_json:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        cache_logger_on_first_use=True,
    )


log = structlog.get_logger("gigproof")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Bind a request_id to the structlog context for the lifetime of the request."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )
        log.info("request.start")
        try:
            response = await call_next(request)
        except Exception:
            log.exception("request.error")
            raise
        response.headers["x-request-id"] = request_id
        log.info("request.end", status=response.status_code)
        return response
