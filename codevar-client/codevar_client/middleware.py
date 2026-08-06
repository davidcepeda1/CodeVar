import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from .config import CodevarConfig

logger = logging.getLogger("codevar_client")


class CodevarMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, config: CodevarConfig):
        super().__init__(app)
        self.config = config

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            self._capture(exc, request)
            raise

    def _capture(self, exc: Exception, request: Request) -> None:
        logger.warning("codevar captured %s: %s", type(exc).__name__, exc)
