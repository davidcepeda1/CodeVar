from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.fingerprint import compute_fingerprint
from app.models import ErrorEvent, ErrorGroup, Project
from app.schemas import EventIn

app = FastAPI(title="CodeVAR")


def get_or_create_error_group(db: Session, project: Project, event: EventIn) -> ErrorGroup:
    fingerprint = compute_fingerprint(event.exception_type, event.file_path, event.line_number)

    error_group = (
        db.query(ErrorGroup)
        .filter(
            ErrorGroup.project_id == project.id,
            ErrorGroup.fingerprint == fingerprint,
        )
        .first()
    )

    if error_group is not None:
        error_group.event_count += 1
        error_group.last_seen = func.now()
        return error_group

    error_group = ErrorGroup(
        project_id=project.id,
        fingerprint=fingerprint,
        exception_type=event.exception_type,
        file_path=event.file_path,
        line_number=event.line_number,
    )
    db.add(error_group)
    try:
        db.flush()
    except IntegrityError:
        # otro evento con el mismo fingerprint se insertó primero (condición de carrera)
        db.rollback()
        error_group = (
            db.query(ErrorGroup)
            .filter(
                ErrorGroup.project_id == project.id,
                ErrorGroup.fingerprint == fingerprint,
            )
            .one()
        )
        error_group.event_count += 1
        error_group.last_seen = func.now()

    return error_group


@app.post("/api/events", status_code=201)
def create_event(event: EventIn, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.api_key == event.project_api_key).first()
    if project is None:
        raise HTTPException(status_code=401, detail="invalid project api key")

    error_group = get_or_create_error_group(db, project, event)

    error_event = ErrorEvent(
        error_group_id=error_group.id,
        stack_trace=event.stack_trace,
        request_path=event.request_path,
        request_method=event.request_method,
        extra_context=event.extra_context,
    )
    db.add(error_event)
    db.commit()

    return {"error_group_id": error_group.id}
