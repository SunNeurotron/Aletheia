from typing import Dict, List, Optional, Any
from collections import defaultdict
import copy # Para devolver copias y simular mejor la no modificación directa
import uuid

from Aletheia_v3.application.ports import IConceptRepository, IRelationshipRepository, IAnalysisRepository, AnalysisData
from Aletheia_v3.core.domain_models import ScientificConcept, DirectedRelationship, ConceptType

# --- Implementaciones en Memoria ---

class InMemoryConceptRepository(IConceptRepository):
    """
    Implementación en memoria de IConceptRepository.

    Utiliza un diccionario para almacenar conceptos. Principalmente para desarrollo,
    pruebas, o demostraciones donde no se requiere persistencia real.
    NOTA: Esta implementación no es segura para hilos si se comparte entre múltiples
    requests/workers sin un bloqueo adecuado, pero las funciones de dependencia
    con `@lru_cache(None)` la convierten en un singleton para la vida del proceso.
    """
    def __init__(self):
        self._concepts: Dict[str, ScientificConcept] = {}

    async def add(self, concept: ScientificConcept) -> None:
        # print(f"InMemoryConceptRepository: Adding concept {concept.id}")
        if concept.id in self._concepts:
            # En un repo real, esto podría ser un error o una actualización.
            # Para InMemory, una actualización simple si el ID ya existe.
            # O lanzar un error si los IDs deben ser únicos en la adición.
            # Por ahora, sobrescribimos para permitir "upsert" simple por ID.
            pass
        self._concepts[concept.id] = copy.deepcopy(concept)

    async def get_by_id(self, concept_id: str) -> Optional[ScientificConcept]:
        # print(f"InMemoryConceptRepository: Getting concept {concept_id}")
        concept = self._concepts.get(concept_id)
        return copy.deepcopy(concept) if concept else None

    async def list_by_type(self, concept_type: ConceptType) -> List[ScientificConcept]:
        # print(f"InMemoryConceptRepository: Listing concepts of type {concept_type.value}")
        return [copy.deepcopy(c) for c in self._concepts.values() if c.concept_type == concept_type]

    async def update(self, concept: ScientificConcept) -> None:
        # print(f"InMemoryConceptRepository: Updating concept {concept.id}")
        if concept.id not in self._concepts:
            raise ValueError(f"Concept with id {concept.id} not found for update.")
        self._concepts[concept.id] = copy.deepcopy(concept)

    def clear(self): # Método de ayuda para tests
        self._concepts = {}

    async def list_all(self) -> List[ScientificConcept]:
        return [copy.deepcopy(c) for c in self._concepts.values()]


class InMemoryRelationshipRepository(IRelationshipRepository):
    """
    Implementación en memoria de IRelationshipRepository.

    Almacena relaciones en un diccionario y utiliza índices adicionales
    (diccionarios) para búsquedas rápidas por ID de origen o destino.
    Destinado a pruebas y desarrollo.
    """
    def __init__(self):
        self._relationships: Dict[str, DirectedRelationship] = {}
        # Índices adicionales para búsquedas eficientes
        self._by_source: Dict[str, List[DirectedRelationship]] = defaultdict(list)
        self._by_target: Dict[str, List[DirectedRelationship]] = defaultdict(list)

    async def add(self, relationship: DirectedRelationship) -> None:
        # print(f"InMemoryRelationshipRepository: Adding relationship {relationship.id}")
        if relationship.id in self._relationships:
            # Similar a ConceptRepo, manejar como upsert o error.
            pass

        rel_copy = copy.deepcopy(relationship)
        self._relationships[rel_copy.id] = rel_copy
        self._by_source[rel_copy.source_concept_id].append(rel_copy)
        self._by_target[rel_copy.target_concept_id].append(rel_copy)

    async def get_by_id(self, relationship_id: str) -> Optional[DirectedRelationship]:
        # print(f"InMemoryRelationshipRepository: Getting relationship {relationship_id}")
        rel = self._relationships.get(relationship_id)
        return copy.deepcopy(rel) if rel else None

    async def find_by_concepts(self, source_id: str, target_id: str, rel_type: Optional[str] = None) -> List[DirectedRelationship]:
        # print(f"InMemoryRelationshipRepository: Finding by concepts {source_id} -> {target_id} (type: {rel_type})")
        candidates = [r for r in self._by_source.get(source_id, []) if r.target_concept_id == target_id]
        if rel_type:
            candidates = [r for r in candidates if r.type == rel_type]
        return [copy.deepcopy(r) for r in candidates]

    async def list_by_source_id(self, source_id: str) -> List[DirectedRelationship]:
        # print(f"InMemoryRelationshipRepository: Listing by source_id {source_id}")
        return [copy.deepcopy(r) for r in self._by_source.get(source_id, [])]

    async def list_by_target_id(self, target_id: str) -> List[DirectedRelationship]:
        # print(f"InMemoryRelationshipRepository: Listing by target_id {target_id}")
        return [copy.deepcopy(r) for r in self._by_target.get(target_id, [])]

    def clear(self): # Método de ayuda para tests
        self._relationships = {}
        self._by_source = defaultdict(list)
        self._by_target = defaultdict(list)

    async def list_all(self) -> List[DirectedRelationship]:
        return [copy.deepcopy(r) for r in self._relationships.values()]

class InMemoryAnalysisRepository(IAnalysisRepository):
    """
    Implementación en memoria de IAnalysisRepository.

    Almacena objetos AnalysisData en un diccionario.
    Utilizado para pruebas de los casos de uso de análisis y la API MDU.
    """
    def __init__(self):
        self._analyses: Dict[str, AnalysisData] = {}

    async def save(self, analysis_data: AnalysisData) -> str:
        # print(f"InMemoryAnalysisRepository: Saving analysis {analysis_data.id}")
        self._analyses[analysis_data.id] = copy.deepcopy(analysis_data)
        return analysis_data.id

    async def get(self, id: str) -> Optional[AnalysisData]:
        # print(f"InMemoryAnalysisRepository: Getting analysis {id}")
        analysis = self._analyses.get(id)
        return copy.deepcopy(analysis) if analysis else None

    async def update(self, id: str, data: Dict[str, Any]) -> None:
        # print(f"InMemoryAnalysisRepository: Updating analysis {id} with {data}")
        if id not in self._analyses:
            raise ValueError(f"Analysis with id {id} not found for update.")

        analysis_to_update = self._analyses[id]
        # Pydantic model's update method is useful here if data is a dict
        # For dataclasses, you'd update fields manually or use replace.
        # AnalysisData es Pydantic, pero el método update no es estándar en Pydantic BaseModel.
        # Se puede hacer una actualización parcial:
        updated_data = analysis_to_update.model_dump() # Usar model_dump en Pydantic v2
        updated_data.update(data)
        self._analyses[id] = AnalysisData(**updated_data)

    def clear(self): # Método de ayuda para tests
        self._analyses = {}

```
