from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
    DateTime,
    JSON,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    api_key = Column(String(64), unique=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class ErrorGroup(Base):
    __tablename__ = "error_groups"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    fingerprint = Column(String(64), nullable=False)
    exception_type = Column(String(200))
    file_path = Column(String(300))
    line_number = Column(Integer)
    first_seen = Column(DateTime, server_default=func.now())
    last_seen = Column(DateTime, server_default=func.now())
    event_count = Column(Integer, default=1)
    status = Column(String(20), default="unresolved")

    __table_args__ = (UniqueConstraint("project_id", "fingerprint"),)


class ErrorEvent(Base):
    __tablename__ = "error_events"

    id = Column(Integer, primary_key=True)
    error_group_id = Column(Integer, ForeignKey("error_groups.id"))
    stack_trace = Column(String)
    request_path = Column(String(300))
    request_method = Column(String(10))
    occurred_at = Column(DateTime, server_default=func.now())
    extra_context = Column(JSON)
