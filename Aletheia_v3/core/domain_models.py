from typing import List, Set, Dict, Optional
from dataclasses import dataclass, field
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity # For ConceptualUnit.similarity_to
import networkx as nx # For ConceptCluster._build_concept_graph

# From mdu_cube_system.py (Section 2.3: Domain Layer)
@dataclass
class ConceptualUnit:
    """Unidad conceptual mínima - entidad de dominio"""
    id: str
    content: str
    embeddings: np.ndarray
    relations: Set[str]
    metadata: dict

    def similarity_to(self, other: 'ConceptualUnit') -> float:
        """Calcula similitud semántica"""
        if self.embeddings.ndim == 1: self_embeddings = self.embeddings.reshape(1, -1)
        else: self_embeddings = self.embeddings
        if other.embeddings.ndim == 1: other_embeddings = other.embeddings.reshape(1, -1)
        else: other_embeddings = other.embeddings
        return float(cosine_similarity(self_embeddings, other_embeddings)[0, 0])

class ConceptCluster:
    """Cluster de conceptos relacionados"""
    def __init__(self, units: List[ConceptualUnit]):
        self.units = units
        self.centroid = self._calculate_centroid() if units else np.array([])
        self.cohesion = self._calculate_cohesion() if units else 0.0
        self.graph = self._build_concept_graph() if units else nx.Graph()

    def _calculate_centroid(self) -> np.ndarray:
        """Calcula el centroide del cluster"""
        if not self.units: return np.array([])
        embeddings = np.array([u.embeddings for u in self.units if u.embeddings is not None and u.embeddings.size > 0])
        if embeddings.size == 0: return np.array([])
        return np.mean(embeddings, axis=0)

    def _calculate_cohesion(self) -> float:
        """Métrica de cohesión interna del cluster"""
        if len(self.units) < 2:
            return 1.0
        similarities = []
        for i, u1 in enumerate(self.units):
            for u2 in self.units[i+1:]:
                similarities.append(u1.similarity_to(u2))
        return np.mean(similarities) if similarities else 0.0

    def _build_concept_graph(self) -> nx.Graph:
        """Construye grafo de relaciones conceptuales"""
        G = nx.Graph()
        if not self.units: return G
        for unit in self.units:
            G.add_node(unit.id, data=unit)
        for unit in self.units:
            for relation_id in unit.relations:
                if relation_id in [u.id for u in self.units]: # Check if related unit is in the same cluster
                    G.add_edge(unit.id, relation_id)
        return G

@dataclass
class Pattern:
    id: str
    description: str
    elements: List[str]

@dataclass
class UnifiedTheory:
    id: str
    patterns: List[Pattern]
    principles: List[str]
    relations: Dict[str, List[str]]
    validation_metrics: Dict[str, float]
    # Added for repository saving and testing
    session_id: Optional[str] = None
    model_data: Optional[Dict] = field(default_factory=dict)
    metrics: Optional[Dict] = field(default_factory=dict)

    def to_dict(self): # For repository
        return {
            "id": self.id,
            "session_id": self.session_id,
            "model_data": {
                "patterns": [p.__dict__ for p in self.patterns],
                "principles": self.principles,
                "relations": self.relations,
                "validation_metrics": self.validation_metrics,
                "levels": self.model_data.get("levels", []) # Preserve levels if set
            },
            "metrics": self.metrics,
        }
