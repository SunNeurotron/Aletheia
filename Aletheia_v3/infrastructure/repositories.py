from typing import Dict, Any, Optional
from sqlalchemy import create_engine, Column, String, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker # Not used in current asyncpg implementation
import asyncpg
from datetime import datetime
import hashlib

# Importaciones de SQLAlchemy y Python
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime # Usado en Pydantic model, no directamente en repo si SQLAlchemy maneja timestamps
import uuid # Para convertir string ID a UUID si es necesario

# Importaciones de SQLAlchemy y Python
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
# from datetime import datetime # No es directamente necesario aquí si SQLAlchemy y el modelo lo manejan.
import uuid

# Importaciones de la aplicación
from ..application.ports import AnalysisData, IAnalysisRepository
from .models import AnalysisModel # El modelo ORM SQLAlchemy

class PostgreSQLRepository(IAnalysisRepository):
    """
    Adaptador de repositorio que utiliza SQLAlchemy ORM para interactuar con la base de datos PostgreSQL.
    Este repositorio maneja la persistencia de los datos de análisis.
    Sus métodos son síncronos ya que operan con una sesión síncrona de SQLAlchemy.
    """
    def __init__(self, db: Session):
        self.db = db

    def save(self, analysis_data_obj: AnalysisData) -> str:
        """
        Guarda o actualiza un objeto de análisis en la base de datos.
        Si el objeto ya existe (mismo ID), se actualiza. Sino, se crea uno nuevo.
        """
        obj_id = uuid.UUID(analysis_data_obj.id) if isinstance(analysis_data_obj.id, str) else analysis_data_obj.id

        db_obj = self.db.query(AnalysisModel).filter(AnalysisModel.id == obj_id).first()

        if db_obj:
            db_obj.session_id = analysis_data_obj.session_id
            db_obj.model_data = analysis_data_obj.model_data
            db_obj.metrics = analysis_data_obj.metrics
            db_obj.status = analysis_data_obj.status
            # created_at es server_default y no se actualiza aquí.
            # updated_at se manejaría con un server_onupdate en el modelo si existiera.
        else:
            db_obj = AnalysisModel(
                id=obj_id,
                session_id=analysis_data_obj.session_id,
                model_data=analysis_data_obj.model_data,
                metrics=analysis_data_obj.metrics,
                status=analysis_data_obj.status
                # created_at es manejado por server_default en el modelo.
            )
            self.db.add(db_obj)

        try:
            self.db.commit()
            self.db.refresh(db_obj)
        except Exception:
            self.db.rollback()
            raise

        return str(db_obj.id)

    def get(self, analysis_id_str: str) -> Optional[AnalysisData]:
        """Recupera un análisis por su ID."""
        try:
            obj_id = uuid.UUID(analysis_id_str)
        except ValueError:
            return None

        db_obj = self.db.query(AnalysisModel).filter(AnalysisModel.id == obj_id).first()

        if db_obj:
            return AnalysisData(
                id=str(db_obj.id),
                session_id=db_obj.session_id,
                created_at=db_obj.created_at,
                model_data=db_obj.model_data,
                metrics=db_obj.metrics,
                status=db_obj.status
            )
        return None

    def update(self, analysis_id_str: str, data_to_update: Dict[str, Any]) -> None:
        """Actualiza campos específicos de un análisis existente."""
        try:
            obj_id = uuid.UUID(analysis_id_str)
        except ValueError:
            raise ValueError(f"Formato de ID inválido para la actualización: {analysis_id_str}.")

        db_obj = self.db.query(AnalysisModel).filter(AnalysisModel.id == obj_id).first()

        if not db_obj:
            raise ValueError(f"Análisis con ID {analysis_id_str} no encontrado para actualizar.")

        for key, value in data_to_update.items():
            if hasattr(db_obj, key):
                if key == "id" and isinstance(value, str): # Prevenir cambio de ID a través de este método si es PK
                    try:
                        if uuid.UUID(value) != obj_id: # No permitir cambiar el ID primario
                             # print(f"No se permite cambiar el ID primario del objeto AnalysisModel.")
                             continue # Omitir este campo
                    except ValueError:
                         # print(f"Valor de ID inválido '{value}' para actualización, omitido.")
                         continue # Omitir
                setattr(db_obj, key, value)

        try:
            self.db.commit()
            self.db.refresh(db_obj)
        except Exception:
            self.db.rollback()
            raise
