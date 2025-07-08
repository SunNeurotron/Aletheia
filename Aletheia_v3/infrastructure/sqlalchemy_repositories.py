from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import Depends # Para la inyección de la sesión de BD

from Aletheia_v3.application.ports import IConceptRepository, IRelationshipRepository
from Aletheia_v3.core.domain_models import ScientificConcept, DirectedRelationship, ConceptType
from Aletheia_v3.infrastructure.models import ScientificConceptDB, DirectedRelationshipDB
from Aletheia_v3.infrastructure.database import get_db_session
import uuid # Para generar IDs si el modelo de dominio no lo hace por defecto al mapear

# --- Funciones de Mapeo Helper ---

def _map_concept_db_to_domain(db_concept: ScientificConceptDB) -> Optional[ScientificConcept]:
    """Mapea un objeto ScientificConceptDB (SQLAlchemy) a un ScientificConcept (dominio)."""
    if not db_concept:
        return None
    return ScientificConcept(
        id=str(db_concept.id), # Asegurar que el UUID se convierta a string para el modelo de dominio
        name=db_concept.name,
        description=db_concept.description,
        concept_type=db_concept.concept_type, # SAEnum debería devolver la instancia del Enum de dominio
        properties=db_concept.properties or {},
        created_at=db_concept.created_at,
        updated_at=db_concept.updated_at
    )

def _map_relationship_db_to_domain(db_relationship: DirectedRelationshipDB) -> Optional[DirectedRelationship]:
    """Mapea un objeto DirectedRelationshipDB (SQLAlchemy) a un DirectedRelationship (dominio)."""
    if not db_relationship:
        return None
    return DirectedRelationship(
        id=str(db_relationship.id),
        source_concept_id=str(db_relationship.source_concept_id),
        target_concept_id=str(db_relationship.target_concept_id),
        type=db_relationship.type,
        description=db_relationship.description,
        properties=db_relationship.properties or {},
        created_at=db_relationship.created_at,
        updated_at=db_relationship.updated_at
    )

# --- Repositorios SQLAlchemy ---

class SQLAlchemyConceptRepository(IConceptRepository):
    """
    Implementación de IConceptRepository utilizando SQLAlchemy para la persistencia
    de entidades ScientificConcept en una base de datos relacional.
    """
    def __init__(self, db: Session = Depends(get_db_session)):
        """
        Inicializa el repositorio con una sesión de base de datos SQLAlchemy.

        Args:
            db: La sesión de SQLAlchemy inyectada por FastAPI.
        """
        self.db = db

    async def add(self, concept: ScientificConcept) -> None:
        """
        Añade un nuevo ScientificConcept a la base de datos.
        El concepto de dominio se mapea a un ScientificConceptDB antes de la persistencia.
        Realiza un commit después de añadir.
        """
        db_concept = ScientificConceptDB(
            id=uuid.UUID(concept.id) if isinstance(concept.id, str) else concept.id, # Convertir str ID a UUID para la BD
            name=concept.name,
            description=concept.description,
            concept_type=concept.concept_type, # El enum de dominio se pasa directamente a SAEnum
            properties=concept.properties,
            created_at=concept.created_at, # Asumir que el dominio ya los tiene o usar server_default
            updated_at=concept.updated_at
        )
        self.db.add(db_concept)
        self.db.commit() # En un sistema real, el commit podría manejarse a nivel de UoW o caso de uso

    async def get_by_id(self, concept_id: str) -> Optional[ScientificConcept]:
        """
        Obtiene un ScientificConcept por su ID.
        Devuelve el concepto de dominio mapeado o None si no se encuentra o el ID es inválido.
        """
        try:
            concept_uuid = uuid.UUID(concept_id) # Convertir str a UUID para la consulta
        except ValueError:
            return None # ID inválido
        db_concept = self.db.query(ScientificConceptDB).filter(ScientificConceptDB.id == concept_uuid).first()
        return _map_concept_db_to_domain(db_concept)

    async def list_by_type(self, concept_type: ConceptType) -> List[ScientificConcept]:
        """
        Lista todos los ScientificConcepts de un tipo específico.
        Devuelve una lista de conceptos de dominio mapeados.
        """
        db_concepts = self.db.query(ScientificConceptDB).filter(ScientificConceptDB.concept_type == concept_type).all()
        return [_map_concept_db_to_domain(c) for c in db_concepts if c]

    async def update(self, concept: ScientificConcept) -> None:
        """
        Actualiza un ScientificConcept existente en la base de datos.
        Busca el concepto por ID, actualiza sus campos y realiza un commit.
        Lanza ValueError si el concepto no se encuentra o el ID es inválido.
        """
        try:
            concept_uuid = uuid.UUID(concept.id)
        except ValueError:
            raise ValueError("Invalid concept ID for update.")

        db_concept = self.db.query(ScientificConceptDB).filter(ScientificConceptDB.id == concept_uuid).first()
        if not db_concept:
            raise ValueError(f"Concept with id {concept.id} not found for update.")

        # Actualizar campos
        db_concept.name = concept.name
        db_concept.description = concept.description
        db_concept.concept_type = concept.concept_type
        db_concept.properties = concept.properties
        db_concept.updated_at = concept.updated_at # El modelo de dominio debería haber actualizado esto

        self.db.commit()

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[ScientificConcept]:
        """Lista todos los ScientificConcepts con paginación."""
        db_concepts = self.db.query(ScientificConceptDB).offset(skip).limit(limit).all()
        return [_map_concept_db_to_domain(c) for c in db_concepts if c]

    async def count_all(self) -> int:
        """Cuenta todos los ScientificConcepts."""
        from sqlalchemy.sql import func # Import func for count
        return self.db.query(func.count(ScientificConceptDB.id)).scalar() or 0

class SQLAlchemyRelationshipRepository(IRelationshipRepository):
    """
    Implementación de IRelationshipRepository utilizando SQLAlchemy para la persistencia
    de entidades DirectedRelationship.
    """
    def __init__(self, db: Session = Depends(get_db_session)):
        """
        Inicializa el repositorio con una sesión de base de datos SQLAlchemy.

        Args:
            db: La sesión de SQLAlchemy inyectada por FastAPI.
        """
        self.db = db

    async def add(self, relationship: DirectedRelationship) -> None:
        """
        Añade una nueva DirectedRelationship a la base de datos.
        La relación de dominio se mapea a DirectedRelationshipDB. Realiza commit.
        """
        db_relationship = DirectedRelationshipDB(
            id=uuid.UUID(relationship.id) if isinstance(relationship.id, str) else relationship.id,
            source_concept_id=uuid.UUID(relationship.source_concept_id),
            target_concept_id=uuid.UUID(relationship.target_concept_id),
            type=relationship.type,
            description=relationship.description,
            properties=relationship.properties,
            created_at=relationship.created_at,
            updated_at=relationship.updated_at
        )
        self.db.add(db_relationship)
        self.db.commit()

    async def get_by_id(self, relationship_id: str) -> Optional[DirectedRelationship]:
        """
        Obtiene una DirectedRelationship por su ID.
        Devuelve la relación de dominio mapeada o None si no se encuentra o el ID es inválido.
        """
        try:
            rel_uuid = uuid.UUID(relationship_id)
        except ValueError:
            return None
        db_relationship = self.db.query(DirectedRelationshipDB).filter(DirectedRelationshipDB.id == rel_uuid).first()
        return _map_relationship_db_to_domain(db_relationship)

    async def find_by_concepts(self, source_id: str, target_id: str, rel_type: Optional[str] = None) -> List[DirectedRelationship]:
        """
        Encuentra relaciones entre un concepto origen y destino específicos,
        opcionalmente filtradas por tipo de relación.
        Devuelve una lista de relaciones de dominio mapeadas.
        """
        try:
            source_uuid = uuid.UUID(source_id)
            target_uuid = uuid.UUID(target_id)
        except ValueError:
            return [] # IDs inválidos

        query = self.db.query(DirectedRelationshipDB).filter(
            DirectedRelationshipDB.source_concept_id == source_uuid,
            DirectedRelationshipDB.target_concept_id == target_uuid
        )
        if rel_type:
            query = query.filter(DirectedRelationshipDB.type == rel_type)

        db_relationships = query.all()
        return [_map_relationship_db_to_domain(r) for r in db_relationships if r]

    async def list_by_source_id(self, source_id: str) -> List[DirectedRelationship]:
        """
        Lista todas las relaciones donde el concepto especificado es el origen.
        Devuelve una lista de relaciones de dominio mapeadas.
        """
        try:
            source_uuid = uuid.UUID(source_id)
        except ValueError:
            return []
        db_relationships = self.db.query(DirectedRelationshipDB).filter(DirectedRelationshipDB.source_concept_id == source_uuid).all()
        return [_map_relationship_db_to_domain(r) for r in db_relationships if r]

    async def list_by_target_id(self, target_id: str) -> List[DirectedRelationship]:
        """
        Lista todas las relaciones donde el concepto especificado es el destino.
        Devuelve una lista de relaciones de dominio mapeadas.
        """
        try:
            target_uuid = uuid.UUID(target_id)
        except ValueError:
            return []
        db_relationships = self.db.query(DirectedRelationshipDB).filter(DirectedRelationshipDB.target_concept_id == target_uuid).all()
        return [_map_relationship_db_to_domain(r) for r in db_relationships if r]

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[DirectedRelationship]:
        """Lista todas las DirectedRelationships con paginación."""
        db_relationships = self.db.query(DirectedRelationshipDB).offset(skip).limit(limit).all()
        return [_map_relationship_db_to_domain(r) for r in db_relationships if r]

    async def count_all(self) -> int:
        """Cuenta todas las DirectedRelationships."""
        from sqlalchemy.sql import func # Import func for count
        return self.db.query(func.count(DirectedRelationshipDB.id)).scalar() or 0

```
