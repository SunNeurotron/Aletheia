# Design Document: Unification of Knowledge Synthesis Engine

**Version:** 1.0
**Date:** 2024-07-26
**Author:** Google Jules (AI Assistant)

## 1. Introduction

This document outlines the plan to refactor Aletheia_v3's Eje Y (knowledge synthesis axis) by integrating a Minimum Description Length (MDL) based optimization engine, inspired by and adapting components from the `aletheia_omega` module. The goal is to replace the current heuristic-based synthesis steps with a more principled MDL-driven approach for selecting optimal conceptual models (clusters, propositions, theories).

This document addresses five key design areas: module integration, concept mapping, refactoring of Eje Y use cases, definition of a new likelihood function, and unification of trajectory/hierarchy representation.

## 2. Design Decisions

### 2.1. Integration of Modules (from `aletheia_omega` into `Aletheia_v3`)

**2.1.1. Components to be Integrated:**

The core MDL optimization logic and relevant data structures from `aletheia_omega` will be adapted and incorporated into `Aletheia_v3`.

*   **Domain Entities (from `aletheia_omega.domain.entities`):**
    *   `ModelRepresentation(BaseModel)`: Represents a model `M` with `identifier: str` and `content: bytes`.
    *   `ModelMetrics(BaseModel)`: Stores `complexity`, `log_likelihood`, and `mdl_cost`.
    *   `OptimizationResult(BaseModel)`: Output of the optimization, containing `best_model` and `best_model_metrics`.
*   **Domain Services (from `aletheia_omega.domain.services`):**
    *   `KolmogorovComplexityProxyService`: Reusable as is (gzipped length of pickled content).
    *   `LikelihoodService`: Class structure to be reused, but `compute` method requires a new domain-specific implementation for `Aletheia_v3` concepts.
    *   `OmegaCostService`: Reusable as is (`calculate_mdl_cost` implementing `λ*K(M) - L(D|M)`).
*   **Application Use Cases (from `aletheia_omega.application.use_cases`):**
    *   `FindOptimalModelUseCase`: To be adapted for use within `Aletheia_v3`'s application layer.

*(Trajectory-related components from `aletheia_omega` like `Trajectory`, `TrajectoryStep`, `TrajectoryAnalysisService`, `EvolveTrajectoryUseCase`, `ClassifyTrajectoryUseCase` are not directly ported; their concerns are addressed in section 2.5.)*

**2.1.2. Proposed New Location within `Aletheia_v3`:**

To maintain modularity and clarity:

*   **Core MDL Components (Entities & Services):**
    *   `Aletheia_v3/core/mdl_synthesis/entities.py`: For `ModelRepresentation`, `ModelMetrics`, `OptimizationResult`.
    *   `Aletheia_v3/core/mdl_synthesis/services.py`: For `KolmogorovComplexityProxyService`, the new `LikelihoodService`, and `OmegaCostService`.
    *   `Aletheia_v3/core/mdl_synthesis/adapters.py`: For the `map_concept_to_representation` adapter (see section 2.2).
*   **Application-Level MDL Components (Use Cases):**
    *   `Aletheia_v3/application/mdl_synthesis_use_cases.py`: For the adapted `FindOptimalModelUseCase`.

**2.1.3. Dependency Management:**

*   **`pydantic`**: Already a core dependency of `Aletheia_v3`.
*   **Standard Python Libraries** (`gzip`, `pickle`, `uuid`, `enum`, `logging`, `dataclasses`, `math`): Available.
*   **`scikit-learn`**: The new `LikelihoodService` for `Aletheia_v3` concepts might require `scikit-learn` for functionalities like cosine similarity if embeddings are used. If not already present, `scikit-learn` **must be added to `Aletheia_v3/requirements.txt`**.

### 2.2. Mapeo de Conceptos (Ontología Unificada)

A mapping is required to convert `Aletheia_v3`'s `ScientificConcept` domain objects into `ModelRepresentation` objects that the MDL engine can process.

**2.2.1. Adapter Function:**

An adapter function, `map_concept_to_representation`, will be created.
*   **Location**: `Aletheia_v3/core/mdl_synthesis/adapters.py`
*   **Signature**: `def map_concept_to_representation(concept: ScientificConcept) -> ModelRepresentation:`

**2.2.2. Serialization Strategy for `ModelRepresentation.content`:**

The `content: bytes` of `ModelRepresentation` will be a pickled dictionary containing key descriptive attributes of the `ScientificConcept`.

*   **Attributes to include in the pickled dictionary:**
    1.  `id: str` (from `concept.id`, converted to string if UUID type)
    2.  `name: str` (from `concept.name`)
    3.  `description: Optional[str]` (from `concept.description`)
    4.  `concept_type: str` (the string value of `concept.concept_type` enum)
    5.  `properties: Dict[str, Any]` (from `concept.properties`). This dictionary is critical as it can hold:
        *   For clusters: `member_ucm_ids`, `shared_keywords`, potentially a `centroid_embedding`.
        *   For propositions: `involved_ucm_ids`, structural elements.
        *   For any concept: Pre-computed embeddings (e.g., `concept.properties['embedding']`).
*   **Serialization Method**: `pickle.dumps()` on the dictionary.
*   **`ModelRepresentation.identifier`**: Will be populated with `str(concept.id)`.

**Implementation Sketch:**
```python
# In Aletheia_v3/core/mdl_synthesis/adapters.py
import pickle
# from Aletheia_v3.core.mdl_synthesis.entities import ModelRepresentation
# from Aletheia_v3.core.domain_models import ScientificConcept

def map_concept_to_representation(concept: ScientificConcept) -> ModelRepresentation:
    model_content_dict = {
        "id": str(concept.id),
        "name": concept.name,
        "description": concept.description,
        "concept_type": concept.concept_type.value,
        "properties": concept.properties,
    }
    serialized_content: bytes = pickle.dumps(model_content_dict)
    return ModelRepresentation(
        identifier=str(concept.id),
        content=serialized_content
    )
```

### 2.3. Refactorización de Casos de Uso del Eje Y

All Eje Y use cases in `Aletheia_v3/application/use_cases.py` (`FormClustersUseCase`, `DerivePropositionsUseCase`, etc.) will be refactored from heuristic-only logic to an MDL-driven selection process.

**General Pattern:**
1.  **Input**: Receive current inputs (e.g., list of UCM IDs).
2.  **Candidate Generation**: Heuristically generate a diverse set of candidate `ScientificConcept`s for the current synthesis stage (e.g., candidate clusters).
3.  **Conversion**: Map each candidate `ScientificConcept` to `ModelRepresentation` using `map_concept_to_representation`.
4.  **Define Data `D`**: Identify the relevant data `D` for likelihood calculation (e.g., for clustering, `D` = original list of UCMs).
5.  **Invoke Optimization**: Call the adapted `FindOptimalModelUseCase.execute()` with the list of candidate `ModelRepresentation`s, data `D`, and a tuned `lambda_param`.
6.  **Process Result**: The `OptimizationResult.best_model.identifier` gives the ID of the chosen `ScientificConcept`.
7.  **Persist**: Save the selected `ScientificConcept` (which was generated in step 2).

**Specifics for `FormClustersUseCase` (Example):**
*   **Lógica Antigua**: Keyword-based heuristic clustering.
*   **Lógica Nueva**:
    1.  Input: List of UCM `ScientificConcept`s.
    2.  Candidate Generation: Create various candidate clusters (e.g., by varying K in K-Means on UCM embeddings, or using different linkage in agglomerative clustering). Each is a `ScientificConcept` of type `CLUSTER`.
    3.  Conversion: Map candidate clusters to `ModelRepresentation`.
    4.  Data `D`: The input list of UCM `ScientificConcept`s.
    5.  Invoke `FindOptimalModelUseCase`. The `LikelihoodService` will evaluate `L(UCMs | CandidateCluster)`.
    6.  Persist the best cluster found.

*(Similar refactoring logic applies to `DerivePropositionsUseCase`, `MiniTheoryConstructionUseCase`, `ComprehensiveTheoriesUseCase`, and `UnifiedModelsUseCase`, with appropriate definitions for candidate generation and data `D` at each stage.)*

### 2.4. Definición de la Función de Verosimilitud L(D|M)

A new `LikelihoodService` will be implemented in `Aletheia_v3/core/mdl_synthesis/services.py`. Its `compute` method will deserialize the `ModelRepresentation.content` and dispatch to specific internal methods based on the `concept_type` of the model `M`.

**`compute(model_representation: ModelRepresentation, data: Any) -> float`**

**Conceptual Likelihood Calculations (Placeholders, require significant refinement):**

*   **For a Cluster Model (`M_cluster`), Data (`D_ucms` - list of UCMs):**
    *   `L(D_ucms | M_cluster)`: Function of intra-cluster cohesion.
        *   Requires UCM embeddings.
        *   `members_of_M = [ucm for ucm in D_ucms if ucm.id in M_cluster.properties['member_ucm_ids']]`
        *   `cohesion_score = calculate_average_pairwise_cosine_similarity(embeddings_of_members_of_M)` (or similarity to centroid).
        *   `log_likelihood = math.log(cohesion_score * len(members_of_M) + 1e-9)` (heuristic, needs proper formulation).

*   **For a Proposition Model (`M_prop`), Data (`D_ucms_source` - UCMs from source cluster):**
    *   `L(D_ucms_source | M_prop)`: Function of relevance/support of proposition to UCMs.
        *   `prop_embedding = embedding(M_prop.description)`
        *   `ucm_embeddings = [ucm.embedding for ucm in D_ucms_source]`
        *   `semantic_similarity_score = mean(cosine_similarity(prop_embedding, ucm_emb))`
        *   `num_involved_ucms = len(M_prop.properties.get('involved_ucm_ids', []))`
        *   `log_likelihood = math.log(semantic_similarity_score * (num_involved_ucms + 1) + 1e-9)` (heuristic).

*   **For a Theory Model (`M_theory`), Data (`D_components` - e.g., list of Propositions for a MiniTheory):**
    *   `L(D_components | M_theory)`: Function of coverage and coherence.
        *   `coverage_score = count(included_components_from_D) / count(D_components)`
        *   `coherence_score = average_semantic_similarity_among_member_components_embeddings`
        *   `log_likelihood = math.log((w1*coverage_score + w2*coherence_score) + 1e-9)` (heuristic).

**Implementation Notes:**
*   The actual formulas for likelihood are critical and will require careful design, possibly involving normalization and ensuring they represent log-probabilities or scores that behave appropriately when subtracted in the MDL formula.
*   Availability of embeddings for `ScientificConcept` instances is a prerequisite for most semantic likelihood calculations.

### 2.5. Unificación de `TrajectoryDB` y la Jerarquía de Conceptos

The Eje Y synthesis creates a hierarchy of increasingly abstract concepts. `aletheia_omega`'s `TrajectoryDB` tracks iterative model selection.

**Recommendation: Leverage `ScientificConceptDB` and `DirectedRelationshipDB`; do NOT port `TrajectoryDB`/`OptimizationRunDB` directly.**

1.  **MDL Metadata Storage**:
    *   When a `ScientificConcept` (`M_new`) is selected by `FindOptimalModelUseCase` during an Eje Y step, its associated `OptimizationResult` (metrics like complexity, likelihood, MDL cost, and parameters like lambda) will be stored within the `properties` field of the `M_new` (`ScientificConceptDB` instance). A suggested key is `mdl_synthesis_details`.
    ```json
    // Example for M_new.properties.mdl_synthesis_details
    {
        "complexity": 105.3,
        "log_likelihood": -20.1,
        "mdl_cost": 125.4, // Assuming lambda=1 for this example
        "parameters": {"lambda": 1.0, "search_space_size": 50},
        "source_concept_ids": ["ucm_id1", "ucm_id2"] // IDs of concepts in D
    }
    ```

2.  **Representing Derivation and Hierarchy**:
    *   The hierarchical relationships (e.g., a Cluster is formed from UCMs, a Proposition from a Cluster) will continue to be represented by:
        *   The `properties` of a higher-level concept storing IDs of its constituents (e.g., `Cluster.properties['member_ucm_ids']`).
        *   Optionally, explicit `DirectedRelationshipDB` entries with types like `CONTAINS_ELEMENT`, `DERIVED_INTO`, or `SYNTHESIZED_FROM`.
    *   The "evolution" or "synthesis path" is thus a traversable path within the existing concept graph stored in `ScientificConceptDB` and `DirectedRelationshipDB`.

3.  **Trajectory Analysis (If Needed)**:
    *   If features like classifying a synthesis path as "stationary," "oscillatory," or "progressive" (from `aletheia_omega.TrajectoryAnalysisService`) are desired, this service would be adapted.
    *   It would operate on a sequence of `ScientificConcept`s (extracted by traversing the concept graph) and their MDL metrics (retrieved from their `properties`).

This approach maintains `Aletheia_v3`'s concept-centric graph model as the primary store of knowledge and its structure, while enriching concepts with metadata about their MDL-based selection.

## 3. Next Steps

This design document provides the blueprint for the refactoring task. Upon approval, a detailed implementation plan based on these design decisions will be formulated, followed by code implementation.
