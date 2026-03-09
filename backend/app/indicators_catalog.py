from dataclasses import dataclass


@dataclass(frozen=True)
class IndicatorDef:
    code: str
    theme: str
    name: str
    genesis_table: str | None
    unit: str
    description: str
    selector_tokens: tuple[str, ...] = ()
    derived_from: tuple[str, ...] = ()
    derived_op: str | None = None


INDICATOR_DEFS: list[IndicatorDef] = [
    IndicatorDef(
        code="BEV_TOTAL",
        theme="Bevoelkerung",
        name="Bevoelkerung gesamt",
        genesis_table="12411-01-01-4",
        unit="Personen",
        description="Bevoelkerung nach Geschlecht - Stichtag 31.12.",
        selector_tokens=("insgesamt",),
    ),
    IndicatorDef(
        code="BEV_FOREIGN",
        theme="Bevoelkerung",
        name="Auslaender",
        genesis_table="12411-03-03-4",
        unit="Personen",
        description="Auslaendische Bevoelkerung.",
        selector_tokens=("auslaender", "insgesamt"),
    ),
    IndicatorDef(
        code="BEV_FOREIGN_SHARE",
        theme="Bevoelkerung",
        name="Auslaender Anteil %",
        genesis_table=None,
        unit="%",
        description="Auslaendische Bevoelkerung in Prozent der Gesamtbevoelkerung.",
        derived_from=("BEV_FOREIGN", "BEV_TOTAL"),
        derived_op="percent",
    ),
    IndicatorDef(
        code="AGE_TOTAL",
        theme="Bevoelkerung",
        name="Durchschnittsalter gesamt",
        genesis_table="12411KJ019",
        unit="Jahre",
        description="Durchschnittsalter der Gesamtbevoelkerung.",
        selector_tokens=("insgesamt",),
    ),
    IndicatorDef(
        code="AGE_GERMAN",
        theme="Bevoelkerung",
        name="Durchschnittsalter Deutsch",
        genesis_table="12411-113r",
        unit="Jahre",
        description="Durchschnittsalter der deutschen Bevoelkerung.",
        selector_tokens=("deutsch",),
    ),
    IndicatorDef(
        code="AGE_FOREIGN",
        theme="Bevoelkerung",
        name="Durchschnittsalter Auslaender",
        genesis_table="12411-113r",
        unit="Jahre",
        description="Durchschnittsalter der auslaendischen Bevoelkerung.",
        selector_tokens=("auslaender|auslaendisch",),
    ),
    IndicatorDef(
        code="MIG_INFLOW",
        theme="Bevoelkerung",
        name="Zuzuege ueber die Kreisgrenzen",
        genesis_table="12711KJ005",
        unit="Personen",
        description="Zuzuege ueber die Kreisgrenzen (Wanderungsstatistik, Jahresdaten).",
        selector_tokens=("zuzuege|zuzug", "kreisgrenzen"),
    ),
    IndicatorDef(
        code="MIG_OUTFLOW",
        theme="Bevoelkerung",
        name="Fortzuege ueber die Kreisgrenzen",
        genesis_table="12711KJ005",
        unit="Personen",
        description="Fortzuege ueber die Kreisgrenzen (Wanderungsstatistik, Jahresdaten).",
        selector_tokens=("fortzuege|fortzug", "kreisgrenzen"),
    ),
    IndicatorDef(
        code="AL_TOTAL",
        theme="Arbeitsmarkt",
        name="Arbeitslose gesamt",
        genesis_table="13211KJ009",
        unit="Personen",
        description="Arbeitslose insgesamt.",
        selector_tokens=("insgesamt",),
    ),
    IndicatorDef(
        code="AL_FOREIGN",
        theme="Arbeitsmarkt",
        name="Arbeitslose Auslaender",
        genesis_table="13211KJ008",
        unit="Personen",
        description="Arbeitslose Auslaender.",
        selector_tokens=("auslaender",),
    ),
    IndicatorDef(
        code="AL_GERMAN",
        theme="Arbeitsmarkt",
        name="Arbeitslose DE",
        genesis_table=None,
        unit="Personen",
        description="Arbeitslose Deutsche (berechnet aus Gesamt minus Auslaender).",
        derived_from=("AL_TOTAL", "AL_FOREIGN"),
        derived_op="difference",
    ),
    IndicatorDef(
        code="AL_LONGTERM",
        theme="Arbeitsmarkt",
        name="Langzeitarbeitslose",
        genesis_table="13211KJ008",
        unit="Personen",
        description="Langzeitarbeitslose.",
        selector_tokens=("langzeitarbeitslose",),
    ),
    IndicatorDef(
        code="AL_RATE",
        theme="Arbeitsmarkt",
        name="Arbeitslosenquote",
        genesis_table="13211KJ009",
        unit="%",
        description="Arbeitslosenquote.",
        selector_tokens=("arbeitslosenquote",),
    ),
]
