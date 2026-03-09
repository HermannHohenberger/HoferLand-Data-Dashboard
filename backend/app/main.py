from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import Region
from app.routers.data import router as data_router


app = FastAPI(title="HoferLand Data Dashboard API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def migrate_schema() -> None:
    with engine.begin() as connection:
        columns = connection.execute(text("PRAGMA table_info(indicators)")).fetchall()
        column_names = {row[1] for row in columns}
        if "description" not in column_names:
            connection.execute(text("ALTER TABLE indicators ADD COLUMN description VARCHAR(255)"))
        if "theme" not in column_names:
            connection.execute(text("ALTER TABLE indicators ADD COLUMN theme VARCHAR(80)"))
        connection.execute(text("UPDATE indicators SET theme = 'Legacy' WHERE theme IS NULL"))


def seed_regions(db: Session) -> None:
    seeds = [
        {"ags_code": "09", "name": "Bayern", "type": "bundesland"},
        {"ags_code": "094", "name": "Oberfranken, Regierungsbezirk", "type": "regierungsbezirk"},
        {"ags_code": "09462", "name": "Bayreuth, kreisfreie Stadt", "type": "stadt"},
        {"ags_code": "09464", "name": "Hof, kreisfreie Stadt", "type": "stadt"},
        {"ags_code": "09472", "name": "Bayreuth, Landkreis", "type": "landkreis"},
        {"ags_code": "09475", "name": "Hof, Landkreis", "type": "landkreis"},
        {"ags_code": "09476", "name": "Kronach, Landkreis", "type": "landkreis"},
        {"ags_code": "09477", "name": "Kulmbach, Landkreis", "type": "landkreis"},
        {"ags_code": "09479", "name": "Wunsiedel i.Fichtelgebirge, Landkreis", "type": "landkreis"},
        {"ags_code": "14523", "name": "Vogtlandkreis", "type": "landkreis"},
        {"ags_code": "16075", "name": "Saale-Orla-Kreis", "type": "landkreis"},
    ]
    for seed in seeds:
        existing = db.scalar(select(Region).where(Region.ags_code == seed["ags_code"]))
        if not existing:
            db.add(Region(**seed))
            continue

        if existing.name != seed["name"] or existing.type != seed["type"]:
            existing.name = seed["name"]
            existing.type = seed["type"]
    db.commit()


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    migrate_schema()
    with SessionLocal() as db:
        seed_regions(db)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(data_router)
