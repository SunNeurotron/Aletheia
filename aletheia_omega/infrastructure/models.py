# aletheia_omega/infrastructure/models.py

import uuid
from datetime import datetime
from typing import Any, Dict # Quitamos List que no se usa aquí

from sqlalchemy import Column, DateTime, Float, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column # relationship no se usa aquí
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

# Intentamos importar la Base común. Si no existe, crearemos una placeholder.
try:
    from aletheia_common.db.base import Base
except ImportError:
    from sqlalchemy.orm import declarative_base
    Base = declarative_base()


class OptimizationRunDB(Base):
    __tablename__ = "omega_optimization_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status: Mapped[str] = mapped_column(String, index=True, default="PENDING") # Podría ser un Enum

    # Parámetros de la ejecución
    lambda_param: Mapped[float] = mapped_column(Float, nullable=False)
    search_space_size: Mapped[int] = mapped_column(Integer, nullable=False)
    # Renombrado de optimization_params a request_parameters para claridad
    request_parameters: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=True)

    # El resultado final (una vez completado)
    best_model_identifier: Mapped[str] = mapped_column(String, nullable=True)
    best_model_complexity: Mapped[float] = mapped_column(Float, nullable=True)
    best_model_likelihood: Mapped[float] = mapped_column(Float, nullable=True)
    best_model_mdl_cost: Mapped[float] = mapped_column(Float, nullable=True)

    # Trazabilidad y Timestamps
    mlflow_run_id: Mapped[str] = mapped_column(String, nullable=True, index=True) # Opcional
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    # Podríamos añadir una relación a una tabla de "modelos candidatos evaluados" si quisiéramos
    # guardar detalles de cada modelo en el espacio de búsqueda, pero por ahora lo mantenemos simple.

    def __repr__(self):
        return f"<OptimizationRunDB(id={self.id}, status='{self.status}', best_model='{self.best_model_identifier}')>"
