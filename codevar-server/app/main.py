import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import engine, get_db
from app.fingerprint import compute_fingerprint
from app.models import Base, ErrorEvent, ErrorGroup, Project
from app.rate_limit import events_rate_limiter
from app.schemas import ErrorGroupDetailOut, ErrorGroupOut, ErrorStatusUpdate, EventIn

APP_DIR = Path(__file__).resolve().parent

app = FastAPI(title="CodeVAR")
app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")
templates = Jinja2Templates(directory=APP_DIR / "templates")


@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)


def get_project_by_api_key(db: Session, api_key: str) -> Project:
    project = db.query(Project).filter(Project.api_key == api_key).first()
    if project is None:
        raise HTTPException(status_code=401, detail="invalid project api key")
    return project


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
    project = get_project_by_api_key(db, event.project_api_key)

    retry_after = events_rate_limiter.check(project.api_key)
    if retry_after > 0:
        raise HTTPException(
            status_code=429,
            detail="rate limit exceeded",
            headers={"Retry-After": str(retry_after)},
        )

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


def get_error_groups(db: Session, project: Project) -> List[ErrorGroup]:
    return (
        db.query(ErrorGroup)
        .filter(ErrorGroup.project_id == project.id)
        .order_by(ErrorGroup.last_seen.desc())
        .all()
    )


DEFAULT_PAGE_SIZE = 20


def query_error_groups(
    db: Session,
    project: Project,
    q: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> tuple[List[ErrorGroup], int]:
    query = db.query(ErrorGroup).filter(ErrorGroup.project_id == project.id)

    if status:
        query = query.filter(ErrorGroup.status == status)

    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(ErrorGroup.exception_type.ilike(like), ErrorGroup.file_path.ilike(like))
        )

    total = query.count()

    error_groups = (
        query.order_by(ErrorGroup.last_seen.desc())
        .offset((max(page, 1) - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return error_groups, total


@app.get("/api/errors", response_model=List[ErrorGroupOut])
def list_errors(
    api_key: str,
    q: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    db: Session = Depends(get_db),
):
    project = get_project_by_api_key(db, api_key)
    error_groups, _ = query_error_groups(db, project, q=q, status=status, page=page, page_size=page_size)
    return error_groups


def get_error_group_or_404(db: Session, project: Project, error_group_id: int) -> ErrorGroup:
    error_group = (
        db.query(ErrorGroup)
        .filter(ErrorGroup.id == error_group_id, ErrorGroup.project_id == project.id)
        .first()
    )
    if error_group is None:
        raise HTTPException(status_code=404, detail="error group not found")
    return error_group


@app.get("/api/errors/{error_group_id}", response_model=ErrorGroupDetailOut)
def get_error_detail(error_group_id: int, api_key: str, db: Session = Depends(get_db)):
    project = get_project_by_api_key(db, api_key)
    return get_error_group_or_404(db, project, error_group_id)


def set_error_status(db: Session, error_group: ErrorGroup, status: str) -> ErrorGroup:
    error_group.status = status
    db.commit()
    db.refresh(error_group)
    return error_group


@app.patch("/api/errors/{error_group_id}", response_model=ErrorGroupOut)
def update_error_status(
    error_group_id: int,
    update: ErrorStatusUpdate,
    api_key: str,
    db: Session = Depends(get_db),
):
    project = get_project_by_api_key(db, api_key)
    error_group = get_error_group_or_404(db, project, error_group_id)
    return set_error_status(db, error_group, update.status)


@app.get("/")
def dashboard_projects_overview(request: Request, error: str = None, db: Session = Depends(get_db)):
    projects = db.query(Project).order_by(Project.name).all()

    overview = []
    for project in projects:
        error_groups = get_error_groups(db, project)
        overview.append(
            {
                "project": project,
                "error_count": len(error_groups),
                "last_seen": error_groups[0].last_seen if error_groups else None,
            }
        )

    return templates.TemplateResponse(
        request=request,
        name="projects_overview.html",
        context={"overview": overview, "error": error},
    )


@app.post("/projects")
def create_project(name: str = Form(...), db: Session = Depends(get_db)):
    project = Project(name=name, api_key=secrets.token_hex(32))
    db.add(project)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return RedirectResponse(url="/?error=duplicate_name", status_code=303)

    return RedirectResponse(url=f"/dashboard?api_key={project.api_key}&new=1", status_code=303)


@app.get("/dashboard")
def dashboard_errors_list(
    request: Request,
    api_key: str,
    q: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    new: bool = False,
    error: str = None,
    db: Session = Depends(get_db),
):
    project = get_project_by_api_key(db, api_key)
    error_groups, total = query_error_groups(db, project, q=q, status=status, page=page)
    total_pages = max((total + DEFAULT_PAGE_SIZE - 1) // DEFAULT_PAGE_SIZE, 1)

    return templates.TemplateResponse(
        request=request,
        name="errors_list.html",
        context={
            "error_groups": error_groups,
            "api_key": api_key,
            "project": project,
            "new_project": new,
            "error": error,
            "server_url": str(request.base_url).rstrip("/"),
            "q": q or "",
            "status_filter": status or "",
            "page": page,
            "total_pages": total_pages,
            "total": total,
        },
    )


@app.post("/dashboard/projects/rename")
def dashboard_rename_project(api_key: str, name: str = Form(...), db: Session = Depends(get_db)):
    project = get_project_by_api_key(db, api_key)
    project.name = name
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return RedirectResponse(
            url=f"/dashboard?api_key={api_key}&error=duplicate_name", status_code=303
        )

    return RedirectResponse(url=f"/dashboard?api_key={api_key}", status_code=303)


@app.post("/dashboard/projects/delete")
def dashboard_delete_project(
    api_key: str, confirm_name: str = Form(...), db: Session = Depends(get_db)
):
    project = get_project_by_api_key(db, api_key)

    if confirm_name != project.name:
        return RedirectResponse(
            url=f"/dashboard?api_key={api_key}&error=confirm_mismatch", status_code=303
        )

    db.delete(project)
    db.commit()

    return RedirectResponse(url="/", status_code=303)


CHART_BAR_WIDTH = 12
CHART_BAR_GAP = 5
CHART_MAX_BAR_HEIGHT = 40
CHART_BASELINE_Y = 44
CHART_MARKER_SPACE = 10  # espacio bajo la línea base para el punto de selección


def build_frequency_chart_bars(daily_counts: List[dict]) -> List[dict]:
    max_count = max((d["count"] for d in daily_counts), default=0)

    bars = []
    for i, day in enumerate(daily_counts):
        if day["count"] == 0:
            height = 2
        else:
            height = max(4, round((day["count"] / max_count) * CHART_MAX_BAR_HEIGHT))

        x = i * (CHART_BAR_WIDTH + CHART_BAR_GAP)
        bars.append(
            {
                "date": day["date"],
                "count": day["count"],
                "x": x,
                "y": CHART_BASELINE_Y - height,
                "height": height,
                "marker_x": x + CHART_BAR_WIDTH / 2,
                "is_today": i == len(daily_counts) - 1,
            }
        )
    return bars


def get_daily_event_counts(db: Session, error_group: ErrorGroup, days: int = 14) -> List[dict]:
    # occurred_at se guarda en UTC (func.now()); usar la fecha UTC aquí también,
    # o los eventos recientes en zonas horarias detrás de UTC (ej. Ecuador)
    # quedarían fechados como "mañana" y caerían fuera del rango.
    start_date = datetime.now(timezone.utc).date() - timedelta(days=days - 1)

    rows = (
        db.query(func.date(ErrorEvent.occurred_at).label("day"), func.count(ErrorEvent.id))
        .filter(ErrorEvent.error_group_id == error_group.id)
        .filter(func.date(ErrorEvent.occurred_at) >= start_date.isoformat())
        .group_by("day")
        .all()
    )
    counts_by_day = {str(day): count for day, count in rows}

    return [
        {
            "date": (start_date + timedelta(days=i)).isoformat(),
            "count": counts_by_day.get((start_date + timedelta(days=i)).isoformat(), 0),
        }
        for i in range(days)
    ]


@app.get("/dashboard/errors/{error_group_id}")
def dashboard_error_detail(
    error_group_id: int, request: Request, api_key: str, db: Session = Depends(get_db)
):
    project = get_project_by_api_key(db, api_key)
    error_group = get_error_group_or_404(db, project, error_group_id)
    daily_counts = get_daily_event_counts(db, error_group)
    chart_bars = build_frequency_chart_bars(daily_counts)

    return templates.TemplateResponse(
        request=request,
        name="error_detail.html",
        context={
            "error_group": error_group,
            "api_key": api_key,
            "chart_bars": chart_bars,
            "chart_total": sum(d["count"] for d in daily_counts),
            "chart_width": len(chart_bars) * (CHART_BAR_WIDTH + CHART_BAR_GAP) - CHART_BAR_GAP,
            "chart_height": CHART_BASELINE_Y,
            "svg_height": CHART_BASELINE_Y + CHART_MARKER_SPACE,
        },
    )


@app.post("/dashboard/errors/{error_group_id}/status")
def dashboard_update_error_status(
    error_group_id: int,
    api_key: str,
    status: str = Form(...),
    db: Session = Depends(get_db),
):
    project = get_project_by_api_key(db, api_key)
    error_group = get_error_group_or_404(db, project, error_group_id)

    try:
        valid_status = ErrorStatusUpdate(status=status).status
    except ValidationError:
        raise HTTPException(status_code=400, detail="invalid status value")

    set_error_status(db, error_group, valid_status)

    return RedirectResponse(
        url=f"/dashboard/errors/{error_group_id}?api_key={api_key}",
        status_code=303,
    )
