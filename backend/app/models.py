from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Region(Base):
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ags_code: Mapped[str] = mapped_column(String(5), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    type: Mapped[str] = mapped_column(String(40))

    data_points: Mapped[list["DataPoint"]] = relationship(
        "DataPoint",
        back_populates="region",
        cascade="all, delete-orphan",
    )


class Indicator(Base):
    __tablename__ = "indicators"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    theme: Mapped[str] = mapped_column(String(80), index=True, default="Bevoelkerung")
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    unit: Mapped[str] = mapped_column(String(50))
    genesis_table: Mapped[str] = mapped_column(String(50))

    data_points: Mapped[list["DataPoint"]] = relationship(
        "DataPoint",
        back_populates="indicator",
        cascade="all, delete-orphan",
    )


class DataPoint(Base):
    __tablename__ = "data_points"
    __table_args__ = (
        UniqueConstraint(
            "region_id",
            "indicator_id",
            "year",
            name="uq_region_indicator_year",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    region_id: Mapped[int] = mapped_column(ForeignKey("regions.id"), index=True)
    indicator_id: Mapped[int] = mapped_column(ForeignKey("indicators.id"), index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    value: Mapped[float] = mapped_column(Float)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    region: Mapped[Region] = relationship("Region", back_populates="data_points")
    indicator: Mapped[Indicator] = relationship("Indicator", back_populates="data_points")
