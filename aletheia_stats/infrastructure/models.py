import uuid as uuid_pkg
from datetime import datetime
from typing import Any, Dict, List, Optional  # Added import

import sqlalchemy as sa  # Added import
from sqlalchemy import (  # Not strictly needed if using Mapped
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

# Importar Base desde el database.py del módulo aletheia_stats
from .database import Base


class TTestResultModel(Base):
    __tablename__ = "ttest_results"

    id: Mapped[uuid_pkg.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4
    )
    experiment_id: Mapped[uuid_pkg.UUID] = mapped_column(
        ForeignKey("experiments.id"), unique=True
    )  # One-to-one

    statistic: Mapped[float] = mapped_column(Float, nullable=False)
    p_value: Mapped[float] = mapped_column(Float, nullable=False)
    degrees_freedom: Mapped[float] = mapped_column(Float, nullable=False)
    mean_group_a: Mapped[float] = mapped_column(Float, nullable=False)
    variance_group_a: Mapped[float] = mapped_column(Float, nullable=False)
    mean_group_b: Mapped[float] = mapped_column(Float, nullable=False)
    variance_group_b: Mapped[float] = mapped_column(Float, nullable=False)

    # Storing list as JSONB. For simple list of 2 floats, could also use two separate columns.
    confidence_interval_95_lower: Mapped[float] = mapped_column(
        Float, nullable=False
    )
    confidence_interval_95_upper: Mapped[float] = mapped_column(
        Float, nullable=False
    )

    is_significant_05: Mapped[bool] = mapped_column(sa.Boolean, nullable=False)

    normality_p_value_group_a: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    normality_p_value_group_b: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationship back to Experiment (optional if access is always Experiment -> Result)
    # experiment: Mapped["ExperimentModel"] = relationship(back_populates="result_model")

    def __repr__(self):
        return f"<TTestResultModel(experiment_id='{self.experiment_id}', p_value={self.p_value:.4f})>"


class ExperimentModel(Base):
    __tablename__ = "experiments"

    id: Mapped[uuid_pkg.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4
    )
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Storing lists of floats as JSONB. Could also be separate tables if more complex querying on data needed.
    group_a_data: Mapped[List[float]] = mapped_column(JSONB, nullable=False)
    group_b_data: Mapped[List[float]] = mapped_column(JSONB, nullable=False)

    parameters: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )

    mlflow_run_id: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True, index=True
    )  # MLflow run IDs are typically 32 chars

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationship to TTestResultModel (one-to-one)
    # The result might be populated after the experiment is initially created.
    result_model: Mapped[Optional["TTestResultModel"]] = relationship(
        "TTestResultModel",
        # back_populates="experiment", # Si se define el backref en TTestResultModel
        uselist=False,  # Indicates one-to-one
        cascade="all, delete-orphan",  # If experiment is deleted, delete its result
    )

    # Field for storing MLflow interaction warnings (new field from plan)
    tracking_warnings: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, nullable=True
    )

    def __repr__(self):
        return f"<ExperimentModel(id='{self.id}', name='{self.name}')>"


# Nota: Para usar Mapped y mapped_column, se necesita SQLAlchemy 1.4+ (idealmente 2.0).
# El requirements.txt de aletheia_stats debería especificar SQLAlchemy >= 1.4 o >= 2.0.
# Si se usa una versión anterior, se debe usar la sintaxis tradicional de Column.
# El requirements.txt raíz tiene sqlalchemy>=2.0.0. Asumiré que el de aletheia_stats también es compatible.
# He usado `sa.Boolean` y `Optional` de typing para los campos.
# Se añadió `tracking_warnings` al `ExperimentModel`.
