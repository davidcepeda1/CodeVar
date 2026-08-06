from typing import Optional

import requests

from .config import CodevarConfig
from .traceback_utils import ExceptionInfo


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
        requests.post(
            f"{self.config.server_url}/api/events",
            json=payload,
            timeout=self.config.timeout,
        )
