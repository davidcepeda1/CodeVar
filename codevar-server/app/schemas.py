from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class EventIn(BaseModel):
    project_api_key: str
    exception_type: str
    file_path: str
    line_number: int
    stack_trace: Optional[str] = None
    request_path: Optional[str] = None
    request_method: Optional[str] = None
    extra_context: Optional[dict] = None


class ErrorGroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    exception_type: Optional[str]
    file_path: Optional[str]
    line_number: Optional[int]
    first_seen: Optional[datetime]
    last_seen: Optional[datetime]
    event_count: int
    status: str
