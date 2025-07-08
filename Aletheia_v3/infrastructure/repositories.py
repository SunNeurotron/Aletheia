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

# Importaciones de la aplicación
from ..application.ports import AnalysisData, IAnalysisRepository # IAnalysisRepository para implementar la interfaz
from .models import AnalysisModel # El nuevo modelo ORM SQLAlchemy

# No más asyncpg o create_engine directamente aquí si la sesión es inyectada
# No más Base = declarative_base() aquí, está en models.py

class PostgreSQLRepository(IAnalysisRepository):
    """
    Adaptador de repositorio que utiliza SQLAlchemy ORM para interactuar con la base de datos PostgreSQL.
    Este repositorio maneja la persistencia de los datos de análisis.
    """
    def __init__(self, db: Session): # Inyectar la sesión de DB
        self.db = db

    async def save(self, analysis_data_obj: AnalysisData) -> str:
        """
        Guarda o actualiza un objeto de análisis en la base de datos.
        Si el objeto ya existe (mismo ID), se actualiza. Sino, se crea uno nuevo.
        """
        # Convertir ID de string a UUID si el modelo lo espera como UUID y Pydantic lo da como str
        # En AnalysisModel, id es Mapped[uuid_pkg.UUID] y AnalysisData.id es str.
        # SQLAlchemy con PG_UUID(as_uuid=True) debería manejar la conversión de str a UUID automáticamente
        # para la consulta y la inserción/actualización.
        obj_id = uuid.UUID(analysis_data_obj.id) if isinstance(analysis_data_obj.id, str) else analysis_data_obj.id


        db_obj = self.db.query(AnalysisModel).filter(AnalysisModel.id == obj_id).first()

        if db_obj:
            # Actualizar campos existentes
            db_obj.session_id = analysis_data_obj.session_id
            db_obj.model_data = analysis_data_obj.model_data # SQLAlchemy maneja JSONB
            db_obj.metrics = analysis_data_obj.metrics     # SQLAlchemy maneja JSONB
            db_obj.status = analysis_data_obj.status
            # created_at es server_default y no debería actualizarse en un save normal.
            # Si se necesita un campo 'updated_at', debería añadirse al modelo AnalysisModel con onupdate=func.now().
        else:
            # Crear nueva instancia de AnalysisModel
            db_obj = AnalysisModel(
                id=obj_id, # Usar el ID convertido si es necesario
                session_id=analysis_data_obj.session_id,
                # created_at es manejado por server_default=func.now() en el modelo,
                # no necesita ser pasado aquí a menos que se quiera sobreescribir.
                # Si Pydantic model tiene created_at y queremos usarlo:
                # created_at=analysis_data_obj.created_at or datetime.utcnow(),
                # pero es mejor dejar que la BD lo maneje con server_default.
                model_data=analysis_data_obj.model_data,
                metrics=analysis_data_obj.metrics,
                status=analysis_data_obj.status
            )
            self.db.add(db_obj)

        try:
            self.db.commit()
            self.db.refresh(db_obj)
        except Exception as e:
            self.db.rollback()
            # print(f"Error en PostgreSQLRepository.save: {e}") # O usar logging
            raise # Re-lanzar para que la capa de servicio/API lo maneje

        return str(db_obj.id) # Devolver ID como string, según la interfaz

    async def get(self, analysis_id_str: str) -> Optional[AnalysisData]:
        """Recupera un análisis por su ID."""
        try:
            # Convertir string ID a UUID para la consulta
            obj_id = uuid.UUID(analysis_id_str)
        except ValueError:
            # print(f"ID de análisis inválido: {analysis_id_str}") # O logging
            return None # ID no es un UUID válido

        db_obj = self.db.query(AnalysisModel).filter(AnalysisModel.id == obj_id).first()

        if db_obj:
            # Mapear de AnalysisModel (SQLAlchemy) a AnalysisData (Pydantic)
            return AnalysisData(
                id=str(db_obj.id), # Asegurar que el ID sea string para Pydantic
                session_id=db_obj.session_id,
                created_at=db_obj.created_at, # SQLAlchemy debería devolver datetime
                model_data=db_obj.model_data,
                metrics=db_obj.metrics,
                status=db_obj.status
            )
        return None

    async def update(self, analysis_id_str: str, data_to_update: Dict[str, Any]) -> None:
        """Actualiza campos específicos de un análisis existente."""
        try:
            obj_id = uuid.UUID(analysis_id_str)
        except ValueError:
            # print(f"ID de análisis inválido para update: {analysis_id_str}") # O logging
            raise ValueError(f"Analysis with id {analysis_id_str} not found for update due to invalid ID format.")


        db_obj = self.db.query(AnalysisModel).filter(AnalysisModel.id == obj_id).first()

        if not db_obj:
            raise ValueError(f"Analysis with id {analysis_id_str} not found for update.")

        for key, value in data_to_update.items():
            if hasattr(db_obj, key):
                # Casos especiales: si el modelo espera UUID para 'id' pero se pasa str
                if key == "id" and isinstance(value, str):
                    try:
                        setattr(db_obj, key, uuid.UUID(value))
                    except ValueError:
                        # print(f"Valor de ID inválido '{value}' para actualización.")
                        pass # O manejar el error
                else:
                    setattr(db_obj, key, value)
            # else:
                # print(f"Advertencia: Campo '{key}' no existe en AnalysisModel, omitido en update.")

        try:
            self.db.commit()
            self.db.refresh(db_obj)
        except Exception as e:
            self.db.rollback()
            # print(f"Error en PostgreSQLRepository.update: {e}") # O logging
            raise
