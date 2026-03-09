from pydantic import BaseModel


class RegionRead(BaseModel):
    id: int
    ags_code: str
    name: str
    type: str

    model_config = {"from_attributes": True}


class IndicatorRead(BaseModel):
    id: int
    code: str
    theme: str
    name: str
    description: str | None = None
    unit: str
    genesis_table: str

    model_config = {"from_attributes": True}


class DataPointRead(BaseModel):
    year: int
    value: float


class LatestDataRead(BaseModel):
    region_id: int
    year: int
    value: float
    change_absolute: float | None
    change_percent: float | None


class ETLResult(BaseModel):
    indicator_id: int
    inserted_or_updated: int


class ETLAreaResult(BaseModel):
    area: str
    inserted_or_updated: int
    status: str = "ok"
    message: str | None = None


class ETLBatchResult(BaseModel):
    indicator_id: int
    total_inserted_or_updated: int
    results: list[ETLAreaResult]
