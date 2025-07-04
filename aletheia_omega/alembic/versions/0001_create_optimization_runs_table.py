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

# aletheia_omega/alembic/versions/0001_create_optimization_runs_table.py

"""create optimization runs table

Revision ID: 0001_omega_init
Revises:
Create Date: 2024-07-28 10:00:00.000000
# La fecha de creación se actualizará al momento de generar realmente la migración
# con el comando de Alembic, pero la dejamos como placeholder.

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql # Para JSONB y UUID

# revision identifiers, used by Alembic.
revision: str = '0001_omega_init' # ID de revisión único para esta migración
down_revision: Union[str, None] = None # Indica que esta es la primera migración
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('omega_optimization_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='PENDING', index=True), # Explicitamente nullable=False
        sa.Column('lambda_param', sa.Float(), nullable=False),
        sa.Column('search_space_size', sa.Integer(), nullable=False),
        # Usar request_parameters como en el modelo SQLAlchemy
        sa.Column('request_parameters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('best_model_identifier', sa.String(), nullable=True),
        sa.Column('best_model_complexity', sa.Float(), nullable=True),
        sa.Column('best_model_likelihood', sa.Float(), nullable=True),
        sa.Column('best_model_mdl_cost', sa.Float(), nullable=True),
        sa.Column('mlflow_run_id', sa.String(), nullable=True, index=True),
        # Asegurar que created_at no sea nullable y tenga server_default
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_omega_optimization_runs')) # Nombre para el PK constraint
    )
    # Crear índices adicionales si es necesario, por ejemplo, en status o mlflow_run_id si ya no se hizo en la columna.
    # op.create_index(op.f('ix_omega_optimization_runs_status'), 'omega_optimization_runs', ['status'], unique=False)
    # op.create_index(op.f('ix_omega_optimization_runs_mlflow_run_id'), 'omega_optimization_runs', ['mlflow_run_id'], unique=False)
    # Estos ya están creados con index=True en la definición de la columna.


def downgrade() -> None:
    # Descomentar si se crearon índices explícitamente con op.create_index
    # op.drop_index(op.f('ix_omega_optimization_runs_mlflow_run_id'), table_name='omega_optimization_runs')
    # op.drop_index(op.f('ix_omega_optimization_runs_status'), table_name='omega_optimization_runs')
    op.drop_table('omega_optimization_runs')
