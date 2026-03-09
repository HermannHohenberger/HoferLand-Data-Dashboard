from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.etl.population import (
    ETL_AREA_ORDER,
    run_population_etl,
    run_population_etl_aggregates,
    run_population_etl_by_areas_with_status,
)
from app.database import get_db
from app.genesis.client import GenesisClientError
from app.models import DataPoint, Indicator, Region
from app.schemas import DataPointRead, ETLAreaResult, ETLBatchResult, ETLResult, IndicatorRead, LatestDataRead, RegionRead


router = APIRouter(prefix="/api", tags=["data"])


@router.get("/regions", response_model=list[RegionRead])
def get_regions(db: Session = Depends(get_db)) -> list[Region]:
    return db.scalars(select(Region).order_by(Region.name.asc())).all()


@router.get("/indicators", response_model=list[IndicatorRead])
def get_indicators(
    theme: str | None = Query(None),
    db: Session = Depends(get_db),
) -> list[Indicator]:
    query = select(Indicator).where(Indicator.theme.is_not(None), Indicator.theme != "Legacy")
    if theme:
        query = query.where(Indicator.theme == theme)
    query = query.order_by(Indicator.theme.asc(), Indicator.name.asc())
    return db.scalars(query).all()


@router.get("/themes", response_model=list[str])
def get_themes(db: Session = Depends(get_db)) -> list[str]:
    rows = db.scalars(
        select(Indicator.theme)
        .where(Indicator.theme.is_not(None), Indicator.theme != "Legacy")
        .distinct()
        .order_by(Indicator.theme.asc()),
    ).all()
    return rows


@router.get("/data", response_model=list[DataPointRead])
def get_data(
    region_id: int = Query(..., ge=1),
    indicator_id: int = Query(..., ge=1),
    start_year: int = Query(2014, ge=1900),
    end_year: int = Query(2100, ge=1900),
    db: Session = Depends(get_db),
) -> list[DataPointRead]:
    query = (
        select(DataPoint)
        .where(
            DataPoint.region_id == region_id,
            DataPoint.indicator_id == indicator_id,
            DataPoint.year >= start_year,
            DataPoint.year <= end_year,
        )
        .order_by(DataPoint.year.asc())
    )
    rows = db.scalars(query).all()
    return [DataPointRead(year=row.year, value=row.value) for row in rows]


@router.get("/data/latest", response_model=LatestDataRead)
def get_latest_data(
    region_id: int = Query(..., ge=1),
    indicator_id: int = Query(1, ge=1),
    db: Session = Depends(get_db),
) -> LatestDataRead:
    latest = db.scalar(
        select(DataPoint)
        .where(
            DataPoint.region_id == region_id,
            DataPoint.indicator_id == indicator_id,
        )
        .order_by(desc(DataPoint.year))
        .limit(1),
    )
    if not latest:
        raise HTTPException(status_code=404, detail="No data found for this region/indicator.")

    previous = db.scalar(
        select(DataPoint)
        .where(
            DataPoint.region_id == region_id,
            DataPoint.indicator_id == indicator_id,
            DataPoint.year < latest.year,
        )
        .order_by(desc(DataPoint.year))
        .limit(1),
    )

    change_abs = None
    change_pct = None
    if previous and previous.value:
        change_abs = latest.value - previous.value
        change_pct = (change_abs / previous.value) * 100.0

    return LatestDataRead(
        region_id=region_id,
        year=latest.year,
        value=latest.value,
        change_absolute=change_abs,
        change_percent=change_pct,
    )


@router.post("/etl/run", response_model=ETLResult)
def trigger_etl(db: Session = Depends(get_db)) -> ETLResult:
    try:
        touched = run_population_etl(db)
    except GenesisClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    indicator = db.scalar(select(Indicator).where(Indicator.code == "BEV_TOTAL"))
    if not indicator:
        raise HTTPException(status_code=500, detail="Indicator not found after ETL run.")
    return ETLResult(indicator_id=indicator.id, inserted_or_updated=touched)


@router.get("/etl/areas", response_model=list[str])
def get_etl_areas() -> list[str]:
    return ETL_AREA_ORDER


@router.post("/etl/run-sequential", response_model=ETLBatchResult)
def trigger_etl_sequential(
    areas: str | None = Query(
        None,
        description="Kommagetrennte Liste von ETL-Bereichen. Leer = alle Bereiche.",
    ),
    start_year: int | None = Query(
        None,
        ge=1900,
        le=2100,
        description="Optionales Startjahr fuer den ETL-Lauf.",
    ),
    db: Session = Depends(get_db),
) -> ETLBatchResult:
    selected_areas = ETL_AREA_ORDER
    if areas:
        requested = [item.strip() for item in areas.split(",") if item.strip()]
        invalid = [item for item in requested if item not in ETL_AREA_ORDER]
        if invalid:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown ETL areas: {', '.join(invalid)}",
            )
        selected_areas = requested

    try:
        touched_by_area = run_population_etl_by_areas_with_status(
            db=db,
            areas=selected_areas,
            start_year=start_year,
        )
    except GenesisClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    indicator = db.scalar(select(Indicator).where(Indicator.code == "BEV_TOTAL"))
    if not indicator:
        raise HTTPException(status_code=500, detail="Indicator not found after ETL run.")

    area_results = [
        ETLAreaResult(
            area=area,
            inserted_or_updated=int(touched_by_area.get(area, {}).get("inserted_or_updated", 0)),
            status=str(touched_by_area.get(area, {}).get("status", "ok")),
            message=(
                str(touched_by_area.get(area, {}).get("message"))
                if touched_by_area.get(area, {}).get("message") is not None
                else None
            ),
        )
        for area in selected_areas
    ]
    total = sum(item.inserted_or_updated for item in area_results)
    return ETLBatchResult(
        indicator_id=indicator.id,
        total_inserted_or_updated=total,
        results=area_results,
    )


@router.post("/etl/run-aggregates", response_model=ETLResult)
def trigger_etl_aggregates(db: Session = Depends(get_db)) -> ETLResult:
    try:
        touched = run_population_etl_aggregates(db)
    except GenesisClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    indicator = db.scalar(select(Indicator).where(Indicator.code == "BEV_TOTAL"))
    if not indicator:
        raise HTTPException(status_code=500, detail="Indicator not found after ETL run.")
    return ETLResult(indicator_id=indicator.id, inserted_or_updated=touched)
