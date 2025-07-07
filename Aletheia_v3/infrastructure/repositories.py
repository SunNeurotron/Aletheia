from typing import Dict, Any, Optional
from sqlalchemy import create_engine, Column, String, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker # Not used in current asyncpg implementation
import asyncpg
from datetime import datetime
import hashlib

# Pydantic model for Analysis data structure (also used as port's data contract)
# If this is used by Application ports, it ideally should be in a shared location (like application/ports.py or a common schemas.py)
# to avoid infra layer leaking into application layer via type hints.
# For now, keeping it here as it's tightly coupled with how PostgreSQLRepository returns data.
# This was previously in mdu_cube_system.py and also defined in application/ports.py as AnalysisData.
# To avoid redefinition, we should import it from ports.py.
from ..application.ports import AnalysisData # Use AnalysisData from ports

Base = declarative_base()

class AnalysisModel(Base):
    """Modelo de persistencia para análisis SQLAlchemy."""
    __tablename__ = 'analyses' # Matches table name in mdu_cube_system

    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    model_data = Column(JSON)
    metrics = Column(JSON)
    status = Column(String)

class PostgreSQLRepository: # Implements IAnalysisRepository from application.ports
    """Adaptador PostgreSQL implementando IAnalysisRepository."""
    def __init__(self, connection_string: str):
        self.raw_connection_string = connection_string # Keep original for reference if needed
        # Prepare a DSN suitable for asyncpg (remove specific dialect part if present)
        if "postgresql+asyncpg://" in connection_string:
            self.asyncpg_connection_string = connection_string.replace("postgresql+asyncpg://", "postgresql://")
        elif "postgres+asyncpg://" in connection_string: # Some might use this
            self.asyncpg_connection_string = connection_string.replace("postgres+asyncpg://", "postgres://")
        else:
            self.asyncpg_connection_string = connection_string

        try:
            # Synchronous engine for initial table creation (if not handled by Alembic)
            sync_conn_str = connection_string.replace("postgresql+asyncpg://", "postgresql://") \
                                             .replace("postgresql+psycopg2://", "postgresql://") \
                                             .replace("postgres+asyncpg://", "postgres://")
            if "postgresql://" not in sync_conn_str and "postgres://" not in sync_conn_str:
                # Attempt to construct a basic DSN if it's just host/db etc.
                # This is a fallback and might not always be correct.
                if '://' not in sync_conn_str: # e.g. just "localhost"
                    sync_conn_str = f"postgresql://{sync_conn_str}"
                else: # e.g. someotherdialect://...
                    sync_conn_str = f"postgresql://{sync_conn_str.split('://',1)[-1]}"

            # Check if '?' exists in the connection string, it may cause issues with create_engine if not handled
            if '?' in sync_conn_str:
                # Basic attempt to clean common problematic query params for sync engine
                # This is a heuristic and might not cover all cases. Proper config is better.
                base_sync_conn_str, query_params = sync_conn_str.split('?',1)
                allowed_params = {} # Example: filter params if needed, or just use base
                # For now, using base string if '?' is present, assuming core part is okay.
                # This could be risky if essential params for sync connection are in query part.
                # print(f"Warning: '?' in DB connection string '{sync_conn_str}', attempting to use base part '{base_sync_conn_str}' for sync engine.")
                # sync_conn_str = base_sync_conn_str
                # Safer: Let create_engine try with the full string first, then fallback or error.
                # For now, assume the provided string is manageable by create_engine after dialect swap.
                pass


            self.engine = create_engine(sync_conn_str) # Use the modified string
            Base.metadata.create_all(self.engine)
            # print(f"PostgreSQLRepository: Tables checked/created using sync engine with '{sync_conn_str}'.")
        except Exception as e:
            print(f"PostgreSQLRepository: Error creating SQLAlchemy engine or tables with '{sync_conn_str}': {e}. Schema might not be up to date.")
            # In a real app, this might raise an error or have a more robust fallback/logging.

    async def save(self, analysis_obj: AnalysisData) -> str: # Expects AnalysisData Pydantic model
        """Guarda análisis con transacciones ACID."""
        # Data is already structured by AnalysisData Pydantic model
        try:
            conn = await asyncpg.connect(self.asyncpg_connection_string)
            async with conn.transaction():
                result = await conn.fetchrow(
                    """
                    INSERT INTO analyses (id, session_id, created_at, model_data, metrics, status)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (id) DO UPDATE SET
                        session_id = EXCLUDED.session_id,
                        created_at = EXCLUDED.created_at,
                        model_data = EXCLUDED.model_data,
                        metrics = EXCLUDED.metrics,
                        status = EXCLUDED.status
                    RETURNING id
                    """,
                    analysis_obj.id,
                    analysis_obj.session_id,
                    analysis_obj.created_at or datetime.utcnow(), # Ensure created_at
                    analysis_obj.model_data,
                    analysis_obj.metrics,
                    analysis_obj.status
                )
            await conn.close()
            return result['id'] if result else analysis_obj.id
        except Exception as e:
            print(f"PostgreSQLRepository Save Error with '{self.asyncpg_connection_string}': {e}") # Use asyncpg_connection_string for logging
            raise # Re-raise the exception to be handled by the caller

    async def get(self, analysis_id: str) -> Optional[AnalysisData]:
        """Recupera un análisis por ID."""
        try:
            conn = await asyncpg.connect(self.asyncpg_connection_string)
            row = await conn.fetchrow(
                "SELECT id, session_id, created_at, model_data, metrics, status FROM analyses WHERE id = $1",
                analysis_id
            )
            await conn.close()
            if row:
                # Convert row (asyncpg Record) to dict, then to AnalysisData Pydantic model
                return AnalysisData(**dict(row))
            return None
        except Exception as e:
            print(f"PostgreSQLRepository Get Error for ID '{analysis_id}' with '{self.connection_string}': {e}")
            return None # Or raise, depending on desired error handling

    async def update(self, analysis_id: str, data_to_update: Dict[str, Any]) -> None:
        """Actualiza un análisis existente."""
        set_clauses = []
        values = []
        param_idx = 1
        for key, value in data_to_update.items():
            # Ensure key is a valid column name to prevent SQL injection if keys are not controlled
            # For this system, keys are likely controlled (e.g., 'status', 'metrics').
            if key in AnalysisModel.__table__.columns.keys(): # Check against SQLAlchemy model columns
                set_clauses.append(f"{key} = ${param_idx}")
                values.append(value)
                param_idx += 1
            else:
                print(f"PostgreSQLRepository Update Warning: Invalid field '{key}' skipped for update.")


        if not set_clauses:
            print(f"PostgreSQLRepository Update: No valid fields to update for ID '{analysis_id}'.")
            return

        values.append(analysis_id) # For WHERE clause
        stmt = f"UPDATE analyses SET {', '.join(set_clauses)} WHERE id = ${param_idx}"

        try:
            conn = await asyncpg.connect(self.asyncpg_connection_string)
            await conn.execute(stmt, *values)
            await conn.close()
        except Exception as e:
            print(f"PostgreSQLRepository Update Error for ID '{analysis_id}' with '{self.asyncpg_connection_string}': {e}")
            # Consider re-raising or specific error handling
            raise
