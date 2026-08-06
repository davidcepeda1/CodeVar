from typing import Optional

from pydantic import BaseModel


class EventIn(BaseModel):
    project_api_key: str
    exception_type: str
    file_path: str
    line_number: int
    stack_trace: Optional[str] = None
    request_path: Optional[str] = None
    request_method: Optional[str] = None
    extra_context: Optional[dict] = None
