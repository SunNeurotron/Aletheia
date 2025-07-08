# Aletheia_v3/core/mdl_synthesis/services.py
import gzip
import pickle
import random
import logging
import pickle # Added for deserialization
import math # Added for log
from typing import Any, List # Added List
import numpy as np # Added for embedding operations
from sklearn.metrics.pairwise import cosine_similarity # Added for similarity

# Import ModelRepresentation from the local entities.py
from .entities import ModelRepresentation
# Import ScientificConcept and ConceptType for type checking and value access
from ...core.domain_models import ScientificConcept, ConceptType


logger = logging.getLogger(__name__)

class KolmogorovComplexityProxyService:
    """
    Servicio de dominio para calcular un proxy de la Complejidad de Kolmogorov.
    La verdadera K(M) es incomputable. Usamos la longitud de la descripción
    comprimida como una aproximación práctica y efectiva.
    """

    def compute(self, model_content: bytes) -> float:
        """
        Calcula la complejidad de un modelo como la longitud de su representación
        serializada y comprimida con gzip.

        @equations:
            K_L(M) ≈ length(compress(describe(M, L)))
            Donde L es Python (via pickle) y compress es gzip.

        @param model_content: El contenido serializado del modelo.
        @return: Un valor de complejidad no negativo.
        """
        if not model_content:
            return 0.0
        compressed_content = gzip.compress(model_content)
        return float(len(compressed_content))


class LikelihoodService:
    """
    Servicio de dominio para calcular la log-verosimilitud de un modelo
    dado un conjunto de datos. La implementación específica depende del tipo de modelo
    y de los datos.
    """

    def _deserialize_model_content(self, model_representation: ModelRepresentation) -> dict:
        try:
            return pickle.loads(model_representation.content)
        except pickle.UnpicklingError as e:
            logger.error(f"Error deserializing model content for ID {model_representation.identifier}: {e}")
            return {} # Return empty dict on error to avoid downstream crashes

    def _calculate_embedding_cohesion(self, concepts: List[ScientificConcept]) -> float:
        """Calculates average pairwise cosine similarity for a list of concepts with embeddings."""
        embeddings = [
            np.array(concept.properties.get("embedding")).reshape(1, -1)
            for concept in concepts
            if concept.properties.get("embedding") is not None and \
               isinstance(concept.properties.get("embedding"), list) and \
               len(concept.properties.get("embedding")) > 0
        ]

        if len(embeddings) < 2:
            return 0.5  # Default for single item or no embeddings (neutral cohesion)

        cohesion_sum = 0
        pair_count = 0
        for i in range(len(embeddings)):
            for j in range(i + 1, len(embeddings)):
                similarity = cosine_similarity(embeddings[i], embeddings[j])[0, 0]
                cohesion_sum += (similarity + 1) / 2 # Scale to [0,1]
                pair_count += 1

        return cohesion_sum / pair_count if pair_count > 0 else 0.5

    def _calculate_cluster_likelihood(self, model_content: dict, data_ucms: List[ScientificConcept]) -> float:
        member_ids = set(model_content.get('properties', {}).get('member_ucm_ids', []))
        if not member_ids:
            return -1e9 # Penalize empty clusters

        members_in_cluster = [ucm for ucm in data_ucms if ucm.id in member_ids]

        if not members_in_cluster:
             # Cluster claims members not in the provided data, or claims no members from data.
            return -1e9

        cohesion_score = self._calculate_embedding_cohesion(members_in_cluster)

        # Factor in how many UCMs the cluster actually grouped from the input
        # This is a simple heuristic; could be more nuanced.
        coverage_factor = len(members_in_cluster) / len(data_ucms) if data_ucms else 0

        # Combine cohesion and a factor of how many members it has (favoring non-trivial clusters)
        # The score should be > 0 for log. Max score is around len(members_in_cluster) if cohesion is 1.
        # A simple heuristic score:
        score = (cohesion_score * 0.7 + coverage_factor * 0.3) * (1 + math.log1p(len(members_in_cluster)))
        return math.log(score + 1e-9) # Add epsilon to avoid log(0)

    def _calculate_proposition_likelihood(self, model_content: dict, data_ucms_source: List[ScientificConcept]) -> float:
        prop_desc = model_content.get('description', "")
        prop_embedding_list = model_content.get('properties', {}).get('embedding')

        if not prop_desc and not prop_embedding_list: # Need something to represent the proposition
            return -1e9

        if prop_embedding_list and isinstance(prop_embedding_list, list):
            prop_embedding = np.array(prop_embedding_list).reshape(1, -1)
        else:
            # Simulate embedding if not present (e.g. for ad-hoc candidates)
            # In a real scenario, this would use a sentence transformer
            logger.warning(f"Proposition '{model_content.get('name')}' missing pre-computed embedding. Using random placeholder.")
            # Dimension should match actual UCM embeddings
            # Assuming UCM embeddings are, e.g., 384-dimensional from a common model
            embedding_dim = len(data_ucms_source[0].properties.get("embedding", [])) if data_ucms_source and data_ucms_source[0].properties.get("embedding") else 384
            prop_embedding = np.random.rand(1, embedding_dim).astype(np.float32)


        ucm_embeddings = [
            np.array(ucm.properties.get("embedding")).reshape(1, -1)
            for ucm in data_ucms_source
            if ucm.properties.get("embedding") is not None and \
               isinstance(ucm.properties.get("embedding"), list) and \
               len(ucm.properties.get("embedding")) > 0
        ]

        if not ucm_embeddings:
            return -1e9 # No UCMs with embeddings to compare against

        similarities = [(cosine_similarity(prop_embedding, ucm_emb)[0, 0] + 1) / 2 for ucm_emb in ucm_embeddings] # Scale to [0,1]
        avg_similarity_score = np.mean(similarities) if similarities else 0.0

        return math.log(avg_similarity_score + 1e-9)

    def _calculate_mini_theory_likelihood(self, model_content: dict, data_propositions: List[ScientificConcept]) -> float:
        member_prop_ids_in_theory = set(model_content.get('properties', {}).get('member_proposition_ids', []))
        input_prop_ids = {p.id for p in data_propositions}

        if not input_prop_ids: # No input propositions to explain
            return 0.0 if not member_prop_ids_in_theory else -1e9 # Empty theory for empty data is fine

        coverage_score = len(member_prop_ids_in_theory.intersection(input_prop_ids)) / len(input_prop_ids)

        member_propositions = [p for p in data_propositions if p.id in member_prop_ids_in_theory]
        coherence_score = self._calculate_embedding_cohesion(member_propositions)

        # Weighted score
        w1_coverage = 0.6
        w2_coherence = 0.4
        score = (w1_coverage * coverage_score) + (w2_coherence * coherence_score)

        return math.log(score + 1e-9)

    def _calculate_comprehensive_theory_likelihood(self, model_content: dict, data_mini_theories: List[ScientificConcept]) -> float:
        member_mini_theory_ids = set(model_content.get('properties', {}).get('member_mini_theory_ids', []))
        input_mini_theory_ids = {mt.id for mt in data_mini_theories}

        if not input_mini_theory_ids:
            return 0.0 if not member_mini_theory_ids else -1e9

        coverage_score = len(member_mini_theory_ids.intersection(input_mini_theory_ids)) / len(input_mini_theory_ids)

        member_mini_theories = [mt for mt in data_mini_theories if mt.id in member_mini_theory_ids]
        coherence_score = self._calculate_embedding_cohesion(member_mini_theories)

        w1_coverage = 0.6
        w2_coherence = 0.4
        score = (w1_coverage * coverage_score) + (w2_coherence * coherence_score)

        return math.log(score + 1e-9)

    def compute(self, model_representation: ModelRepresentation, data: Any) -> float:
        model_content_dict = self._deserialize_model_content(model_representation)
        if not model_content_dict: # Deserialization failed
            return -1e9

        model_type_str = model_content_dict.get('concept_type')

        # Convert string to ConceptType enum member if possible for safer comparison
        try:
            model_type = ConceptType(model_type_str) if model_type_str else None
        except ValueError:
            logger.warning(f"Unknown concept type '{model_type_str}' in LikelihoodService for model ID {model_representation.identifier}. Returning very low likelihood.")
            return -1e9

        if model_type == ConceptType.CLUSTER:
            if not all(isinstance(item, ScientificConcept) for item in data):
                logger.error("LikelihoodService: Data for CLUSTER type must be List[ScientificConcept] (UCMs).")
                return -1e9
            return self._calculate_cluster_likelihood(model_content_dict, data)
        elif model_type == ConceptType.PROPOSITION:
            if not all(isinstance(item, ScientificConcept) for item in data):
                logger.error("LikelihoodService: Data for PROPOSITION type must be List[ScientificConcept] (UCMs).")
                return -1e9
            return self._calculate_proposition_likelihood(model_content_dict, data)
        elif model_type == ConceptType.MINI_THEORY:
            if not all(isinstance(item, ScientificConcept) for item in data):
                logger.error("LikelihoodService: Data for MINI_THEORY type must be List[ScientificConcept] (Propositions).")
                return -1e9
            return self._calculate_mini_theory_likelihood(model_content_dict, data)
        elif model_type == ConceptType.COMPREHENSIVE_THEORY:
            if not all(isinstance(item, ScientificConcept) for item in data):
                logger.error("LikelihoodService: Data for COMPREHENSIVE_THEORY type must be List[ScientificConcept] (MiniTheories).")
                return -1e9
            return self._calculate_comprehensive_theory_likelihood(model_content_dict, data)
        # Add elif for UNIFIED_MODEL when its likelihood logic is defined
        # elif model_type == ConceptType.UNIFIED_MODEL:
        #     return self._calculate_unified_model_likelihood(model_content_dict, data)
        else:
            logger.warning(
                f"LikelihoodService.compute called for unhandled or unknown model type: '{model_type_str}' "
                f"for model ID {model_representation.identifier}. Review data or add specific likelihood logic. "
                "Devolviendo un valor aleatorio como fallback."
            )
            return random.uniform(-50.0, -1.0) # Fallback to original placeholder for unhandled


class OmegaCostService:
    """
    Implementa el núcleo del Axioma 1 del modelo Ω: el Principio de Mínima Descripción.
    """

    def calculate_mdl_cost(
        self, complexity: float, log_likelihood: float, lambda_param: float
    ) -> float:
        """
        Calcula el coste total de un modelo. El objetivo es minimizar este coste.

        @equations:
            Cost(M) = λ * K(M) - L(D|M)

        @param complexity: La complejidad calculada del modelo, K(M).
        @param log_likelihood: La log-verosimilitud del modelo, L(D|M).
        @param lambda_param: El parámetro de regularización λ, que balancea
                             simplicidad vs. precisión.
        @return: El coste MDL del modelo.
        """
        if lambda_param < 0:
            raise ValueError("El parámetro de regularización λ no puede ser negativo.")

        return (lambda_param * complexity) - log_likelihood
