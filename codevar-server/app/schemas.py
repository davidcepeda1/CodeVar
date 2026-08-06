from datetime import datetime
from typing import List, Literal, Optional

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


class ErrorEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    stack_trace: Optional[str]
    request_path: Optional[str]
    request_method: Optional[str]
    occurred_at: Optional[datetime]
    extra_context: Optional[dict]


class ErrorGroupDetailOut(ErrorGroupOut):
    events: List[ErrorEventOut]


class ErrorStatusUpdate(BaseModel):
    status: Literal["unresolved", "resolved", "ignored"]
