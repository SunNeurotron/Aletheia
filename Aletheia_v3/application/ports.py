from typing import Protocol, Optional, Dict, Any, List # Added List

# Forward declaration for Analysis if needed, or import from domain/models
# For now, assume 'Analysis' is a Dict or a Pydantic model defined elsewhere (e.g. in schemas or a common models file)
# If it's the SQLAlchemy model, that's an infra detail the port shouldn't know.
# If it's a Pydantic model representing the data, it could be in a shared schema location.
# Let's use 'Any' for now for 'Analysis' type in repository to keep ports clean,
# or define a minimal Pydantic model here if it's purely for data structure contract.

# from ..core.domain_models import UnifiedTheory # Example if Analysis is UnifiedTheory
# For now, let's treat 'Analysis' as a structured dict or a Pydantic model.
# To avoid circular dependencies if Analysis Pydantic model is in infra/repo.py:
# It's better if Analysis Pydantic model is in a shared schemas.py or here.

from pydantic import BaseModel
from datetime import datetime

class AnalysisData(BaseModel): # A Pydantic model for the data structure of an analysis
    id: str
    session_id: str
    model_data: Dict[str, Any]
    metrics: Dict[str, Any]
    status: Optional[str] = 'completed'
    created_at: Optional[datetime] = None


class IExperimentTracker(Protocol):
    """Puerto para tracking de experimentos"""
    def start_run(self, name: str) -> str: ...
    def log_params(self, params: dict) -> None: ...
    def log_metrics(self, metrics: dict) -> None: ...
    def end_run(self) -> None: ...

class IAnalysisRepository(Protocol):
    """Puerto para persistencia de análisis"""
    # The 'analysis' parameter here should be a data structure (like a Pydantic model or dict)
    # not the SQLAlchemy model directly.
    async def save(self, analysis_data: AnalysisData) -> str: ... # Use AnalysisData
    async def get(self, id: str) -> Optional[AnalysisData]: ... # Use AnalysisData
    async def update(self, id: str, data: Dict[str, Any]) -> None: ... # data is a dict of fields to update

class ITaskQueue(Protocol):
    """Puerto para la cola de tareas asíncronas."""
    async def enqueue_task(self, task_name: str, params: Dict[str, Any]) -> str: ... # Returns task_id
    async def get_task_status(self, task_id: str) -> Dict[str, Any]: ... # Returns status info
    # May add other methods like cancel_task, get_task_result etc.


# --- Repositorios para Conceptos y Relaciones ---
# Necesitamos importar los modelos de dominio que estos repositorios manejan.
from ..core.domain_models import ScientificConcept, DirectedRelationship, ConceptType

class IConceptRepository(Protocol):
    """Puerto para persistencia de Conceptos Científicos (ScientificConcept)."""
    async def add(self, concept: ScientificConcept) -> None: ...
    async def get_by_id(self, concept_id: str) -> Optional[ScientificConcept]: ...
    async def list_by_type(self, concept_type: ConceptType) -> List[ScientificConcept]: ...
    async def update(self, concept: ScientificConcept) -> None: ...
    async def list_all(self, skip: int = 0, limit: int = 100) -> List[ScientificConcept]: ... # Adjusted to match typical list methods
    async def count_all(self) -> int: ... # Method for counting all concepts
    # Podrían añadirse otros métodos como search, delete, etc.

class IRelationshipRepository(Protocol):
    """Puerto para persistencia de Relaciones Dirigidas (DirectedRelationship)."""
    async def add(self, relationship: DirectedRelationship) -> None: ...
    async def get_by_id(self, relationship_id: str) -> Optional[DirectedRelationship]: ...
    async def find_by_concepts(self, source_id: str, target_id: str, rel_type: Optional[str] = None) -> List[DirectedRelationship]: ...
    async def list_by_source_id(self, source_id: str) -> List[DirectedRelationship]: ...
    async def list_by_target_id(self, target_id: str) -> List[DirectedRelationship]: ...
    async def list_all(self, skip: int = 0, limit: int = 100) -> List[DirectedRelationship]: ... # Adjusted
    async def count_all(self) -> int: ... # Method for counting all relationships
    # Podrían añadirse otros métodos
