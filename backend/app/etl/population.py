from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.genesis.client import GenesisClient, GenesisClientError
from app.genesis.parser import (
    parse_average_age_nationality_csv_by_region,
    parse_average_age_timeseries_csv_by_region_name,
    parse_foreign_population_csv_by_region,
    parse_migration_timeseries_csv_by_region_name,
    parse_metric_csv_by_region,
    parse_unemployment_groups_timeseries_csv_by_region_name,
    parse_unemployment_metrics_timeseries_csv_by_region_name,
    parse_unemployment_csv_by_region,
    parse_unemployment_rate_csv_by_region,
)
from app.indicators_catalog import INDICATOR_DEFS
from app.models import DataPoint, Indicator, Region

ETL_AREA_ORDER = [
    "bevoelkerung_gesamt",
    "auslaender",
    "durchschnittsalter",
    "wanderung_kreisgrenzen",
    "arbeitslose_gesamt",
    "arbeitslose_auslaender",
    "langzeitarbeitslose",
    "arbeitslosenquote",
    "derived",
]


def _is_no_data_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return (
        "keine objekte" in text
        or "error 104" in text
        or "does not contain table content" in text
        or "keine tabelleninhalte" in text
    )


def _fetch_table_with_year_fallback(
    client: GenesisClient,
    table_name: str,
    start_year: int,
    min_year: int,
) -> tuple[str, int]:
    year = start_year
    while year >= min_year:
        try:
            return client.fetch_table_csv(
                table_name=table_name,
                start_year=year,
            ), year
        except GenesisClientError as exc:
            if _is_no_data_error(exc):
                year -= 1
                continue
            raise
    raise GenesisClientError(
        f"Genesis liefert keine Daten fuer Tabelle {table_name} im Bereich {min_year}-{start_year}.",
    )


def _fetch_timeseries_with_year_fallback(
    client: GenesisClient,
    table_name: str,
    start_year: int,
    min_year: int,
) -> tuple[str, int]:
    year = start_year
    while year >= min_year:
        try:
            return client.fetch_timeseries_csv(
                table_name=table_name,
                start_year=year,
            ), year
        except GenesisClientError as exc:
            if _is_no_data_error(exc):
                year -= 1
                continue
            raise
    raise GenesisClientError(
        f"Genesis liefert keine Zeitreihe fuer Tabelle {table_name} im Bereich {min_year}-{start_year}.",
    )


def _normalize_region_name(name: str) -> str:
    lowered = name.lower()
    replacements = {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "ß": "ss",
    }
    for source, target in replacements.items():
        lowered = lowered.replace(source, target)
    lowered = lowered.replace(".", "").replace(",", " ")
    lowered = " ".join(lowered.split())
    return lowered


def _upsert_datapoint(
    db: Session,
    region_id: int,
    indicator_id: int,
    year: int,
    value: float,
) -> None:
    for pending in db.new:
        if not isinstance(pending, DataPoint):
            continue
        if (
            pending.region_id == region_id
            and pending.indicator_id == indicator_id
            and pending.year == year
        ):
            pending.value = value
            pending.updated_at = datetime.now(timezone.utc)
            return

    existing = db.scalar(
        select(DataPoint).where(
            DataPoint.region_id == region_id,
            DataPoint.indicator_id == indicator_id,
            DataPoint.year == year,
        ),
    )
    if existing:
        existing.value = value
        existing.updated_at = datetime.now(timezone.utc)
    else:
        db.add(
            DataPoint(
                region_id=region_id,
                indicator_id=indicator_id,
                year=year,
                value=value,
            ),
        )


def ensure_indicators(db: Session) -> dict[str, Indicator]:
    by_code: dict[str, Indicator] = {}
    for definition in INDICATOR_DEFS:
        existing = db.scalar(select(Indicator).where(Indicator.code == definition.code))
        if existing:
            changed = False
            if existing.theme != definition.theme:
                existing.theme = definition.theme
                changed = True
            if existing.name != definition.name:
                existing.name = definition.name
                changed = True
            if existing.description != definition.description:
                existing.description = definition.description
                changed = True
            if existing.unit != definition.unit:
                existing.unit = definition.unit
                changed = True
            target_table = definition.genesis_table or "derived"
            if existing.genesis_table != target_table:
                existing.genesis_table = target_table
                changed = True
            if changed:
                db.commit()
                db.refresh(existing)
            by_code[definition.code] = existing
            continue

        indicator = Indicator(
            code=definition.code,
            theme=definition.theme,
            name=definition.name,
            description=definition.description,
            unit=definition.unit,
            genesis_table=definition.genesis_table or "derived",
        )
        db.add(indicator)
        try:
            db.commit()
            db.refresh(indicator)
            by_code[definition.code] = indicator
        except IntegrityError:
            db.rollback()
            fallback = db.scalar(select(Indicator).where(Indicator.code == definition.code))
            if fallback:
                by_code[definition.code] = fallback
    return by_code


def run_population_etl(db: Session, start_year: int | None = None) -> int:
    results = run_population_etl_by_areas(db=db, areas=ETL_AREA_ORDER, start_year=start_year)
    return sum(results.values())


def run_population_etl_by_areas(
    db: Session,
    areas: list[str],
    start_year: int | None = None,
) -> dict[str, int]:
    detailed = run_population_etl_by_areas_with_status(
        db=db,
        areas=areas,
        start_year=start_year,
    )
    return {area: payload["inserted_or_updated"] for area, payload in detailed.items()}


def run_population_etl_by_areas_with_status(
    db: Session,
    areas: list[str],
    start_year: int | None = None,
) -> dict[str, dict[str, str | int | None]]:
    start_year = start_year or settings.etl_start_year
    indicators = ensure_indicators(db)
    regions = db.scalars(select(Region).order_by(Region.ags_code.asc())).all()
    region_by_code = {region.ags_code: region for region in regions}
    region_by_name_normalized = {
        _normalize_region_name(region.name): region for region in regions
    }
    client = GenesisClient(timeout_seconds=60)
    results: dict[str, dict[str, str | int | None]] = {
        area: {"inserted_or_updated": 0, "status": "ok", "message": None} for area in areas
    }
    indicator_def_by_code = {definition.code: definition for definition in INDICATOR_DEFS}

    def set_area_error(area: str, message: str) -> None:
        results[area]["status"] = "error"
        results[area]["message"] = message

    def persist_by_region(indicator_code: str, by_region: dict[str, list[dict[str, float]]]) -> int:
        indicator = indicators.get(indicator_code)
        if not indicator:
            return 0
        # Deduplicate within the same ETL step to avoid duplicate inserts
        # when multiple source tables contain overlapping region/year rows.
        unique_values: dict[tuple[int, int], float] = {}
        for ags_code, rows in by_region.items():
            region = region_by_code.get(ags_code)
            if not region:
                continue
            for row in rows:
                unique_values[(region.id, row["year"])] = row["value"]

        changed = 0
        for (region_id, year), value in unique_values.items():
            _upsert_datapoint(
                db=db,
                region_id=region_id,
                indicator_id=indicator.id,
                year=year,
                value=value,
            )
            changed += 1
        return changed

    def persist_by_region_name(
        indicator_code: str,
        by_region_name: dict[str, list[dict[str, float]]],
    ) -> int:
        by_code: dict[str, list[dict[str, float]]] = {}
        for region_name, rows in by_region_name.items():
            region = region_by_name_normalized.get(_normalize_region_name(region_name))
            if not region:
                continue
            by_code[region.ags_code] = rows
        return persist_by_region(indicator_code, by_code)

    if "bevoelkerung_gesamt" in areas:
        try:
            csv_text, used_year = _fetch_table_with_year_fallback(
                client=client,
                table_name="12411-01-01-4",
                start_year=start_year,
                min_year=settings.etl_start_year,
            )
            touched = persist_by_region(
                "BEV_TOTAL",
                parse_metric_csv_by_region(csv_text, ("insgesamt",)),
            )
            results["bevoelkerung_gesamt"]["inserted_or_updated"] = touched
            if touched == 0:
                results["bevoelkerung_gesamt"]["status"] = "empty"
                results["bevoelkerung_gesamt"]["message"] = (
                    "Keine Werte in Antwort gefunden oder keine passenden Regionen."
                )
            elif used_year != start_year:
                results["bevoelkerung_gesamt"]["message"] = (
                    f"Datenstart automatisch auf {used_year} zurueckgesetzt (keine Daten fuer {start_year})."
                )
        except Exception as exc:
            set_area_error("bevoelkerung_gesamt", str(exc))
        finally:
            db.commit()

    if "auslaender" in areas:
        try:
            csv_text, used_year = _fetch_table_with_year_fallback(
                client=client,
                table_name="12411-03-03-4",
                start_year=start_year,
                min_year=settings.etl_start_year,
            )
            touched = persist_by_region(
                "BEV_FOREIGN",
                parse_foreign_population_csv_by_region(csv_text),
            )
            results["auslaender"]["inserted_or_updated"] = touched
            if touched == 0:
                results["auslaender"]["status"] = "empty"
                results["auslaender"]["message"] = (
                    "Keine Werte in Antwort gefunden oder keine passenden Regionen."
                )
            elif used_year != start_year:
                results["auslaender"]["message"] = (
                    f"Datenstart automatisch auf {used_year} zurueckgesetzt (keine Daten fuer {start_year})."
                )
        except Exception as exc:
            set_area_error("auslaender", str(exc))
        db.commit()

    if "durchschnittsalter" in areas:
        area_touched = 0
        used_year = start_year
        loaded_years: set[int] = set()
        loaded_years_nationality: set[int] = set()
        partial_errors: list[str] = []
        average_age_timeseries_tables = ("12411LJ019", "12411RJ019", "12411KJ019")
        for age_table in average_age_timeseries_tables:
            try:
                csv_text, fetched_year = _fetch_timeseries_with_year_fallback(
                    client=client,
                    table_name=age_table,
                    start_year=start_year,
                    min_year=settings.etl_start_year,
                )
                used_year = min(used_year, fetched_year)
                total_by_name = parse_average_age_timeseries_csv_by_region_name(csv_text)
                for rows in total_by_name.values():
                    for row in rows:
                        loaded_years.add(row["year"])
                area_touched += persist_by_region_name("AGE_TOTAL", total_by_name)
            except Exception as exc:
                partial_errors.append(f"{age_table}: {exc}")

        current_year = datetime.now(timezone.utc).year
        for year in range(start_year, current_year + 1):
            try:
                csv_text = client.fetch_table_csv(
                    table_name="12411-03-03-4",
                    start_year=year,
                )
            except Exception as exc:
                if _is_no_data_error(exc):
                    continue
                partial_errors.append(f"12411-03-03-4/{year}: {exc}")
                continue

            german_by_region, foreign_by_region = parse_average_age_nationality_csv_by_region(
                csv_text,
            )
            for rows in [*german_by_region.values(), *foreign_by_region.values()]:
                for row in rows:
                    loaded_years_nationality.add(row["year"])
            area_touched += persist_by_region("AGE_GERMAN", german_by_region)
            area_touched += persist_by_region("AGE_FOREIGN", foreign_by_region)
        results["durchschnittsalter"]["inserted_or_updated"] = area_touched
        if area_touched == 0 and not loaded_years and not loaded_years_nationality:
            if partial_errors:
                set_area_error(
                    "durchschnittsalter",
                    "Fehler beim Laden: " + "; ".join(partial_errors[:3]),
                )
            else:
                results["durchschnittsalter"]["status"] = "empty"
                results["durchschnittsalter"]["message"] = (
                    "Keine Werte in Antwort gefunden oder Selektoren passen nicht."
                )
        elif area_touched == 0 and results["durchschnittsalter"]["status"] == "ok":
            results["durchschnittsalter"]["status"] = "empty"
            results["durchschnittsalter"]["message"] = (
                "Keine Werte in Antwort gefunden oder Selektoren passen nicht."
            )
        elif used_year != start_year:
            results["durchschnittsalter"]["message"] = (
                f"Datenstart automatisch auf {used_year} zurueckgesetzt (keine Daten fuer {start_year})."
            )
        elif loaded_years and loaded_years_nationality:
            results["durchschnittsalter"]["message"] = (
                f"Gesamt-Zeitreihe direkt aus Genesis {min(loaded_years)}-{max(loaded_years)} geladen. "
                f"Deutsch/Auslaender aus Altersgruppen {min(loaded_years_nationality)}-{max(loaded_years_nationality)} berechnet."
            )
        elif loaded_years:
            results["durchschnittsalter"]["message"] = (
                f"Gesamt-Zeitreihe direkt aus Genesis {min(loaded_years)}-{max(loaded_years)} geladen. "
                "Deutsch/Auslaender konnten in diesem Lauf nicht berechnet werden."
            )
        elif loaded_years_nationality:
            results["durchschnittsalter"]["message"] = (
                f"Deutsch/Auslaender aus Altersgruppen {min(loaded_years_nationality)}-{max(loaded_years_nationality)} berechnet. "
                "Gesamtwert aus direkter Zeitreihe in diesem Lauf nicht aktualisiert."
            )
        if partial_errors and results["durchschnittsalter"]["status"] == "ok":
            extra = f" Teilweise Fehler ({len(partial_errors)}), Lauf wurde mit verfuegbaren Daten fortgesetzt."
            if results["durchschnittsalter"]["message"]:
                results["durchschnittsalter"]["message"] = (
                    f"{results['durchschnittsalter']['message']}{extra}"
                )
            else:
                results["durchschnittsalter"]["message"] = extra.strip()
        db.commit()

    if "wanderung_kreisgrenzen" in areas:
        area_touched = 0
        used_year = start_year
        migration_timeseries_tables = ("12711LJ005", "12711RJ005", "12711KJ005")
        loaded_years: set[int] = set()
        try:
            for migration_table in migration_timeseries_tables:
                csv_text, fetched_year = _fetch_timeseries_with_year_fallback(
                    client=client,
                    table_name=migration_table,
                    start_year=start_year,
                    min_year=settings.etl_start_year,
                )
                used_year = min(used_year, fetched_year)
                inflow_by_name = parse_migration_timeseries_csv_by_region_name(
                    csv_text,
                    direction="inflow",
                )
                outflow_by_name = parse_migration_timeseries_csv_by_region_name(
                    csv_text,
                    direction="outflow",
                )
                for rows in [*inflow_by_name.values(), *outflow_by_name.values()]:
                    for row in rows:
                        loaded_years.add(row["year"])
                area_touched += persist_by_region_name(
                    "MIG_INFLOW",
                    inflow_by_name,
                )
                area_touched += persist_by_region_name(
                    "MIG_OUTFLOW",
                    outflow_by_name,
                )
        except Exception as exc:
            set_area_error("wanderung_kreisgrenzen", str(exc))
            area_touched = 0
        results["wanderung_kreisgrenzen"]["inserted_or_updated"] = area_touched
        if area_touched == 0 and results["wanderung_kreisgrenzen"]["status"] == "ok":
            results["wanderung_kreisgrenzen"]["status"] = "empty"
            results["wanderung_kreisgrenzen"]["message"] = (
                "Keine Werte in Antwort gefunden oder Selektoren passen nicht."
            )
        elif used_year != start_year:
            results["wanderung_kreisgrenzen"]["message"] = (
                f"Datenstart automatisch auf {used_year} zurueckgesetzt (keine Daten fuer {start_year})."
            )
        elif loaded_years:
            results["wanderung_kreisgrenzen"]["message"] = (
                f"Zeitreihe {min(loaded_years)}-{max(loaded_years)} geladen."
            )
        db.commit()

    def _run_unemployment_area(
        target_area: str,
        indicator_code: str,
        source_kind: str,
        selector_tokens: tuple[str, ...],
    ) -> None:
        if target_area not in areas:
            return
        area_touched = 0
        loaded_years: set[int] = set()
        source_tables = (
            ("13211LJ008", "groups"),
            ("13211RJ008", "groups"),
            ("13211KJ008", "groups"),
        )
        if source_kind == "metrics":
            source_tables = (
                ("13211LJ009", "metrics"),
                ("13211RJ009", "metrics"),
                ("13211KJ009", "metrics"),
            )

        for table_name, parser_kind in source_tables:
            try:
                csv_text, _ = _fetch_timeseries_with_year_fallback(
                    client=client,
                    table_name=table_name,
                    start_year=start_year,
                    min_year=settings.etl_start_year,
                )
            except Exception as exc:
                if not _is_no_data_error(exc):
                    set_area_error(target_area, str(exc))
                continue

            if parser_kind == "groups":
                parsed = parse_unemployment_groups_timeseries_csv_by_region_name(
                    csv_text,
                    category_tokens=selector_tokens,
                )
            else:
                parsed = parse_unemployment_metrics_timeseries_csv_by_region_name(
                    csv_text,
                    metric_tokens=selector_tokens,
                )
            for rows in parsed.values():
                for row in rows:
                    loaded_years.add(row["year"])
            area_touched += persist_by_region_name(indicator_code, parsed)
        results[target_area]["inserted_or_updated"] = area_touched
        if area_touched == 0 and results[target_area]["status"] == "ok":
            results[target_area]["status"] = "empty"
            results[target_area]["message"] = (
                "Keine Werte in Antwort gefunden oder keine passenden Regionen."
            )
        elif loaded_years:
            results[target_area]["message"] = (
                f"Zeitreihe {min(loaded_years)}-{max(loaded_years)} geladen."
            )
        db.commit()

    _run_unemployment_area(
        "arbeitslose_gesamt",
        "AL_TOTAL",
        "metrics",
        ("=arbeitslose",),
    )
    _run_unemployment_area(
        "arbeitslose_auslaender",
        "AL_FOREIGN",
        "groups",
        ("auslaendisch|auslaender",),
    )
    _run_unemployment_area(
        "langzeitarbeitslose",
        "AL_LONGTERM",
        "groups",
        ("langzeitarbeitslos",),
    )

    if "arbeitslosenquote" in areas:
        try:
            loaded_years: set[int] = set()
            touched = 0
            for table_name in ("13211LJ009", "13211RJ009", "13211KJ009"):
                csv_text, _ = _fetch_timeseries_with_year_fallback(
                    client=client,
                    table_name=table_name,
                    start_year=start_year,
                    min_year=settings.etl_start_year,
                )
                parsed = parse_unemployment_metrics_timeseries_csv_by_region_name(
                    csv_text,
                    metric_tokens=("=arbeitslosenquote bez. auf alle zivile erwerbsp.",),
                )
                for rows in parsed.values():
                    for row in rows:
                        loaded_years.add(row["year"])
                touched += persist_by_region_name("AL_RATE", parsed)
            results["arbeitslosenquote"]["inserted_or_updated"] = touched
            if touched == 0:
                results["arbeitslosenquote"]["status"] = "empty"
                results["arbeitslosenquote"]["message"] = (
                    "Keine Werte in Antwort gefunden oder keine passenden Regionen."
                )
            elif loaded_years:
                results["arbeitslosenquote"]["message"] = (
                    f"Zeitreihe {min(loaded_years)}-{max(loaded_years)} geladen."
                )
        except Exception as exc:
            set_area_error("arbeitslosenquote", str(exc))
        db.commit()

    def _collect_series(indicator_code: str) -> dict[tuple[int, int], float]:
        indicator = indicators.get(indicator_code)
        if not indicator:
            return {}
        rows = db.scalars(select(DataPoint).where(DataPoint.indicator_id == indicator.id)).all()
        return {(row.region_id, row.year): row.value for row in rows}

    population_areas = {
        "bevoelkerung_gesamt",
        "auslaender",
    }
    labor_areas = {
        "arbeitslose_gesamt",
        "arbeitslose_auslaender",
        "langzeitarbeitslose",
        "arbeitslosenquote",
    }
    should_compute_population_derived = bool(population_areas & set(areas))
    should_compute_labor_derived = bool(labor_areas & set(areas))

    if "derived" in areas or should_compute_population_derived or should_compute_labor_derived:
        derived_touched = 0
        if "derived" in areas:
            derived_defs = [item for item in INDICATOR_DEFS if item.derived_op]
        else:
            derived_codes: set[str] = set()
            if should_compute_population_derived:
                derived_codes.add("BEV_FOREIGN_SHARE")
            if should_compute_labor_derived:
                derived_codes.add("AL_GERMAN")
            derived_defs = [
                item
                for item in INDICATOR_DEFS
                if item.code in derived_codes and item.derived_op
            ]

        for definition in derived_defs:
            target = indicators.get(definition.code)
            if not target or len(definition.derived_from) != 2:
                continue
            left = _collect_series(definition.derived_from[0])
            right = _collect_series(definition.derived_from[1])
            common_keys = set(left.keys()) & set(right.keys())
            for region_id, year in common_keys:
                value: float | None = None
                if definition.derived_op == "percent":
                    if right[(region_id, year)] != 0:
                        value = (left[(region_id, year)] / right[(region_id, year)]) * 100.0
                elif definition.derived_op == "difference":
                    value = left[(region_id, year)] - right[(region_id, year)]
                if value is None:
                    continue
                _upsert_datapoint(
                    db=db,
                    region_id=region_id,
                    indicator_id=target.id,
                    year=year,
                    value=value,
                )
                derived_touched += 1
        if "derived" in areas:
            results["derived"]["inserted_or_updated"] = derived_touched
            if derived_touched == 0:
                results["derived"]["status"] = "empty"
                results["derived"]["message"] = (
                    "Keine gemeinsamen Datenpunkte fuer die berechneten Kennzahlen vorhanden."
                )
        elif should_compute_population_derived or should_compute_labor_derived:
            # Derived indicators are refreshed transparently during source ETL runs.
            pass
        db.commit()

    return results


def run_population_etl_aggregates(db: Session, start_year: int | None = None) -> int:
    # Aggregates are now included in run_population_etl via all-region parsing.
    return run_population_etl(db, start_year=start_year)
