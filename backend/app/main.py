import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .config import settings
from .db import Base, SessionLocal, engine, get_db
from .metrics import ITEMS_OPEN, ITEMS_REPORTED, ITEMS_RESOLVED
from .models import Item, utcnow
from .schemas import Category, ItemCreate, ItemOut, ItemType, ItemUpdate, StatsOut, Status

log = logging.getLogger("foundit")


def db_error(exc: SQLAlchemyError) -> str:
    """The driver's own message, e.g. 'password authentication failed for user "foundit"'."""
    lines = str(getattr(exc, "orig", None) or exc).strip().splitlines()
    return lines[-1] if lines else exc.__class__.__name__


def refresh_open_gauge(db: Session) -> None:
    rows = db.execute(
        select(Item.type, func.count(Item.id)).where(Item.status != "RETURNED").group_by(Item.type)
    ).all()
    counts = dict(rows)
    for item_type in ("LOST", "FOUND"):
        ITEMS_OPEN.labels(type=item_type).set(counts.get(item_type, 0))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Production containers run Alembic before Uvicorn; create_all keeps tests self-contained
    # and is a no-op once the migrations have created the table.
    # A database outage must not stop the process: it starts, /health says UP (no restart loop)
    # and /ready returns 503 until the database is reachable, so Kubernetes simply holds traffic back.
    try:
        Base.metadata.create_all(bind=engine)
        with SessionLocal() as db:
            refresh_open_gauge(db)
    except SQLAlchemyError as exc:
        log.warning("database not reachable at startup, /ready will report 503 until it is: %s", db_error(exc))
    yield


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
# Probe and scrape traffic would drown the real request rate, so they are not measured.
Instrumentator(excluded_handlers=["/metrics", "/health", "/ready"]).instrument(app).expose(app, endpoint="/metrics")


def get_item_or_404(item_id: int, db: Session) -> Item:
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.get("/")
def root():
    return {"service": settings.app_name, "version": settings.app_version, "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "UP"}


@app.get("/ready")
def ready(db: Session = Depends(get_db)):
    # A real query: if Postgres is down or the password is wrong, this raises and the
    # readiness probe takes the pod out of the Service until it recovers.
    try:
        db.execute(select(func.count(Item.id)))
    except SQLAlchemyError as exc:
        log.warning("readiness check failed: %s", db_error(exc))
        raise HTTPException(status_code=503, detail="Database unavailable")
    return {"status": "READY"}


@app.get("/api/items", response_model=list[ItemOut])
def list_items(
    type: ItemType | None = None,
    status: Status | None = None,
    category: Category | None = None,
    q: str | None = Query(default=None, max_length=100),
    db: Session = Depends(get_db),
):
    query = select(Item)
    if type:
        query = query.where(Item.type == type)
    if status:
        query = query.where(Item.status == status)
    if category:
        query = query.where(Item.category == category)
    if q:
        pattern = f"%{q.strip()}%"
        query = query.where(or_(Item.title.ilike(pattern), Item.description.ilike(pattern), Item.location.ilike(pattern)))
    return list(db.scalars(query.order_by(Item.id.desc())))


# Declared before /api/items/{item_id} so "stats" is not parsed as an item id.
@app.get("/api/items/stats", response_model=StatsOut)
def stats(db: Session = Depends(get_db)):
    rows = db.execute(select(Item.type, Item.status, func.count(Item.id)).group_by(Item.type, Item.status)).all()
    by_category = dict(db.execute(select(Item.category, func.count(Item.id)).group_by(Item.category)).all())
    count = lambda t=None, s=None: sum(n for it, st, n in rows if (t is None or it == t) and (s is None or st == s))  # noqa: E731
    refresh_open_gauge(db)
    return StatsOut(
        total=count(),
        open_lost=count("LOST", "OPEN"),
        open_found=count("FOUND", "OPEN"),
        claimed=count(s="CLAIMED"),
        returned=count(s="RETURNED"),
        by_category=by_category,
    )


@app.get("/api/items/{item_id}", response_model=ItemOut)
def get_item(item_id: int, db: Session = Depends(get_db)):
    return get_item_or_404(item_id, db)


@app.post("/api/items", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
def create_item(payload: ItemCreate, db: Session = Depends(get_db)):
    item = Item(**payload.model_dump(), status="OPEN")
    db.add(item)
    db.commit()
    db.refresh(item)
    ITEMS_REPORTED.labels(type=item.type).inc()
    refresh_open_gauge(db)
    return item


@app.put("/api/items/{item_id}", response_model=ItemOut)
def update_item(item_id: int, payload: ItemUpdate, db: Session = Depends(get_db)):
    item = get_item_or_404(item_id, db)
    changes = payload.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(item, key, value)
    # Keep resolved_at consistent with the status whichever endpoint changed it.
    if "status" in changes:
        if item.status == "RETURNED" and item.resolved_at is None:
            item.resolved_at = utcnow()
            ITEMS_RESOLVED.inc()
        elif item.status != "RETURNED":
            item.resolved_at = None
    db.commit()
    db.refresh(item)
    refresh_open_gauge(db)
    return item


@app.post("/api/items/{item_id}/resolve", response_model=ItemOut)
def resolve_item(item_id: int, db: Session = Depends(get_db)):
    item = get_item_or_404(item_id, db)
    if item.status == "RETURNED":
        raise HTTPException(status_code=409, detail="Item is already returned")
    item.status = "RETURNED"
    item.resolved_at = utcnow()
    db.commit()
    db.refresh(item)
    ITEMS_RESOLVED.inc()
    refresh_open_gauge(db)
    return item


@app.delete("/api/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = get_item_or_404(item_id, db)
    db.delete(item)
    db.commit()
    refresh_open_gauge(db)
