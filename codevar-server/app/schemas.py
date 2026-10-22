from datetime import datetime
from typing import List, Literal, Optional

import json

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Límites alineados con las columnas de la base de datos: un valor mayor
# provocaría un error 500 en PostgreSQL en lugar de un rechazo controlado.
MAX_ENTERO_BD = 2_147_483_647
MAX_TRAZA = 65_536
MAX_CONTEXTO = 16_384


class EventIn(BaseModel):
    project_api_key: str = Field(max_length=64)
    exception_type: str = Field(min_length=1, max_length=200)
    file_path: str = Field(min_length=1, max_length=300)
    line_number: int = Field(ge=0, le=MAX_ENTERO_BD)
    stack_trace: Optional[str] = Field(default=None, max_length=MAX_TRAZA)
    request_path: Optional[str] = Field(default=None, max_length=300)
    request_method: Optional[str] = Field(default=None, max_length=10)
    extra_context: Optional[dict] = None

    @field_validator("extra_context")
    @classmethod
    def limitar_contexto(cls, valor):
        if valor is not None and len(json.dumps(valor, default=str)) > MAX_CONTEXTO:
            raise ValueError("extra_context exceeds the maximum size")
        return valor


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
