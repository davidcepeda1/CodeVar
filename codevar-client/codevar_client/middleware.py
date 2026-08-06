import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from .config import CodevarConfig
from .traceback_utils import extract_exception_info

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
        info = extract_exception_info(exc)
        logger.warning(
            "codevar captured %s at %s:%s",
            info.exception_type,
            info.file_path,
            info.line_number,
        )
