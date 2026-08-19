import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from .config import CodevarConfig
from .reporter import EventReporter
from .traceback_utils import extract_exception_info

logger = logging.getLogger("codevar_client")


class CodevarMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, config: CodevarConfig):
        super().__init__(app)
        self.config = config
        self.reporter = EventReporter(config)

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
        self.reporter.send(
            info,
            request_path=request.url.path,
            request_method=request.method,
            extra_context=self._build_extra_context(request),
        )

    @staticmethod
    def _build_extra_context(request: Request) -> dict:
        context = {}

        user_agent = request.headers.get("user-agent")
        if user_agent:
            context["user_agent"] = user_agent

        if request.query_params:
            context["query_params"] = dict(request.query_params)

        return context
