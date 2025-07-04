# Copyright 2025 Alant
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# aletheia_omega/infrastructure/models.py

import uuid
from datetime import datetime
from typing import Any, Dict, List # List es necesario para Mapped[List["OptimizationRunDB"]]

from sqlalchemy import Column, DateTime, Float, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB # Usar JSONB para request_parameters si es PG
from sqlalchemy.sql import func

# Intentamos importar la Base común. Si no existe, crearemos una placeholder.
try:
    from aletheia_common.db.base import Base
except ImportError:
    from sqlalchemy.orm import declarative_base
    Base = declarative_base()


class TrajectoryDB(Base):
    __tablename__ = "omega_trajectories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=True, index=True) # Un nombre opcional para la trayectoria
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relación uno-a-muchos: una trayectoria tiene muchos pasos (OptimizationRunDB)
    # `steps` será una lista de objetos OptimizationRunDB asociados con esta trayectoria.
    # `order_by` asegura que los pasos se carguen en el orden correcto.
    steps: Mapped[List["OptimizationRunDB"]] = relationship(
        back_populates="trajectory",
        cascade="all, delete-orphan",
        order_by="OptimizationRunDB.step_index" # Importante para recuperar en orden
    )

    def __repr__(self):
        return f"<TrajectoryDB(id={self.id}, name='{self.name}', steps_count='{len(self.steps) if self.steps else 0}')>"


class OptimizationRunDB(Base):
    __tablename__ = "omega_optimization_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # --- Vinculación a la Trayectoria ---
    trajectory_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("omega_trajectories.id", name="fk_optimization_run_trajectory"),
        index=True,
        nullable=False # Un run ahora siempre pertenece a una trayectoria
    )
    step_index: Mapped[int] = mapped_column(Integer, nullable=False) # Índice del paso dentro de la trayectoria (0, 1, 2...)

    # Relación muchos-a-uno: un run pertenece a una trayectoria
    trajectory: Mapped["TrajectoryDB"] = relationship(back_populates="steps")

    # --- Campos existentes (mantenidos y revisados) ---
    status: Mapped[str] = mapped_column(String, index=True, default="PENDING", nullable=False)

    # Parámetros de la ejecución de este paso/run
    lambda_param: Mapped[float] = mapped_column(Float, nullable=False)
    search_space_size: Mapped[int] = mapped_column(Integer, nullable=False)
    # Usar JSONB si el dialecto es postgresql para mejor rendimiento y capacidades de consulta
    request_parameters: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=True)

    # El resultado final de este paso/run
    best_model_identifier: Mapped[str] = mapped_column(String, nullable=True)
    best_model_complexity: Mapped[float] = mapped_column(Float, nullable=True)
    best_model_likelihood: Mapped[float] = mapped_column(Float, nullable=True)
    best_model_mdl_cost: Mapped[float] = mapped_column(Float, nullable=True)

    # Trazabilidad y Timestamps
    mlflow_run_id: Mapped[str] = mapped_column(String, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)


    def __repr__(self):
        return (f"<OptimizationRunDB(id={self.id}, trajectory_id={self.trajectory_id}, step={self.step_index}, "
                f"status='{self.status}', model='{self.best_model_identifier}')>")
