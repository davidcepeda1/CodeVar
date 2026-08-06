import logging
from typing import Optional

import requests

from .config import CodevarConfig
from .traceback_utils import ExceptionInfo

logger = logging.getLogger("codevar_client")


class EventReporter:
    def __init__(self, config: CodevarConfig):
        self.config = config

    def send(
        self,
        info: ExceptionInfo,
        request_path: Optional[str] = None,
        request_method: Optional[str] = None,
    ) -> None:
        payload = {
            "project_api_key": self.config.api_key,
            "exception_type": info.exception_type,
            "file_path": info.file_path,
            "line_number": info.line_number,
            "stack_trace": info.stack_trace,
            "request_path": request_path,
            "request_method": request_method,
        }
        try:
            requests.post(
                f"{self.config.server_url}/api/events",
                json=payload,
                timeout=self.config.timeout,
            )
        except requests.RequestException:
            # CodeVAR nunca debe romper la app que instrumenta: si el
            # servidor no responde, se registra el fallo y se sigue.
            logger.warning("codevar: failed to report event to %s", self.config.server_url, exc_info=True)
