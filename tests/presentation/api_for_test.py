"""
Test-local FastAPI application setup.

This module creates a FastAPI app instance using components from their
test-local temporary locations to ensure they are importable in the sandbox.
"""
import uuid
from typing import List, Dict, Set, Optional, Any
from collections import defaultdict, deque

from fastapi import FastAPI, Depends, HTTPException, status, Query

from tests.application.use_cases.use_cases_for_test import (
    KnowledgeSynthesisUseCase, CreateConceptInput, ExtractUCMsUseCase, ExtractUCMsInput, UCMExtractionResult,
    FormClustersUseCase, FormClusterInput, ClusterFormationResult, DerivePropositionsUseCase, DerivePropositionInput,
    PropositionDerivationResult, ConstructMiniTheoryUseCase, ConstructMiniTheoryInput, MiniTheoryConstructionResult,
    ConstructComprehensiveTheoryUseCase, ConstructComprehensiveTheoryInput, ComprehensiveTheoryResult,
    ConstructUnifiedModelUseCase, ConstructUnifiedModelInput, UnifiedModelResult, IngestDocumentUseCase,
    IngestDocumentInput, IngestDocumentResult, LinkConceptsUseCase, LinkConceptsInput, LinkConceptsResult
)
from tests.application.ports.ports_for_test import (
    ConceptRepository as ConceptRepoProtocol, RelationshipRepository as RelationshipRepoProtocol
)
from tests.domain.domain_for_test import ScientificConcept, ConceptType
from tests.infrastructure.database.repos_for_test import (
    InMemoryConceptRepository, InMemoryRelationshipRepository
)

_test_concept_repo_singleton = InMemoryConceptRepository()
_test_relationship_repo_singleton = InMemoryRelationshipRepository()

# --- Visualization Helper Functions ---

def _get_hierarchy_level(concept_type: ConceptType) -> int:
    levels = {
        ConceptType.UCM: 0, ConceptType.CLUSTER: 1, ConceptType.PROPOSITION: 2,
        ConceptType.MINI_THEORY: 3, ConceptType.COMPREHENSIVE_THEORY: 4,
        ConceptType.UNIFIED_MODEL: 5, ConceptType.DOCUMENT_SOURCE: -1
    }
    return levels.get(concept_type, -2)

def _calculate_max_depth(
    concept: Optional[ScientificConcept],
    repo: ConceptRepoProtocol,
    # visited_in_path is not directly used in this BFS version in the same way as recursion for cycle detection per path,
    # BFS naturally handles shortest paths and avoids cycles in its own traversal if nodes are marked visited globally for the BFS.
    # However, to keep function signature same if other parts of code expect it, it's kept.
    # For this BFS, we use a local 'bfs_visited_nodes'
    visited_in_path_placeholder: Optional[Set[uuid.UUID]] = None
) -> int:
    if not concept:
        return -1
    if concept.type == ConceptType.UCM:
        return 0

    # BFS queue stores (concept_object, current_depth_from_original_start_concept)
    queue = deque([(concept, 0)])
    # Visited set specifically for this BFS traversal to avoid re-queuing and cycles
    bfs_visited_this_traversal: Set[uuid.UUID] = {concept.id}

    max_depth_to_any_ucm = -1 # Max depth found so far to any UCM from the starting 'concept'

    while queue:
        current_c, depth_from_start = queue.popleft()

        # If current_c is a UCM, this path ends. Update max_depth if this path is longer.
        if current_c.type == ConceptType.UCM:
            if depth_from_start > max_depth_to_any_ucm:
                max_depth_to_any_ucm = depth_from_start
            # Continue processing other paths in queue; a UCM is a leaf in downward traversal for depth.

        # Explore children (members, derived UCMs for propositions, or derived cluster for propositions)
        children_to_visit: List[ScientificConcept] = []
        if current_c.member_concept_ids:
            for member_id in current_c.member_concept_ids:
                member = repo.get_by_id(member_id)
                if member:
                    children_to_visit.append(member)

        # If current_c is a PROPOSITION, also consider its derived_from_cluster_id as a child
        if current_c.type == ConceptType.PROPOSITION and current_c.derived_from_cluster_id:
            cluster_child = repo.get_by_id(current_c.derived_from_cluster_id)
            if cluster_child:
                # Avoid adding duplicate if already present (e.g. if somehow it was also a direct member)
                if cluster_child.id not in {c.id for c in children_to_visit}:
                    children_to_visit.append(cluster_child)

        # If current_c is a PROPOSITION, also consider its derived_from_ucm_ids as children
        # These are typically UCMs and act as leaf nodes for depth calculation path.
        if current_c.type == ConceptType.PROPOSITION and current_c.derived_from_ucm_ids:
            for ucm_id in current_c.derived_from_ucm_ids:
                ucm_child = repo.get_by_id(ucm_id)
                if ucm_child and ucm_child.type == ConceptType.UCM: # Ensure it's a UCM
                    if ucm_child.id not in {c.id for c in children_to_visit}:
                        children_to_visit.append(ucm_child)

        for child_c in children_to_visit:
            if child_c.id not in bfs_visited_this_traversal:
                bfs_visited_this_traversal.add(child_c.id)
                queue.append((child_c, depth_from_start + 1))

    return max_depth_to_any_ucm


def _trace_to_ucms(
    concept: Optional[ScientificConcept], repo: ConceptRepoProtocol, visited_in_path: Optional[Set[uuid.UUID]] = None
) -> Set[uuid.UUID]:
    # This remains recursive as it's a set collection, not just path length.
    if not concept: return set()
    if visited_in_path is None: visited_in_path = set()
    if concept.id in visited_in_path: return set()

    current_path_visited = visited_in_path.copy()
    current_path_visited.add(concept.id)

    if concept.type == ConceptType.UCM: return {concept.id}

    ucms_found: Set[uuid.UUID] = set()
    if concept.member_concept_ids:
        for member_id in concept.member_concept_ids:
            member = repo.get_by_id(member_id)
            if member: ucms_found.update(_trace_to_ucms(member, repo, current_path_visited))

    if concept.type == ConceptType.PROPOSITION and concept.derived_from_ucm_ids:
        for ucm_id in concept.derived_from_ucm_ids:
            ucm_cpt = repo.get_by_id(ucm_id)
            if ucm_cpt and ucm_cpt.type == ConceptType.UCM:
                 ucms_found.add(ucm_id)
    return ucms_found

def _trace_to_unified_models(
    concept: Optional[ScientificConcept], repo: ConceptRepoProtocol,
    all_concepts_list: List[ScientificConcept], visited_in_path: Optional[Set[uuid.UUID]] = None
) -> Set[uuid.UUID]:
    # This remains recursive.
    if not concept: return set()
    if visited_in_path is None: visited_in_path = set()
    if concept.id in visited_in_path: return set()

    current_path_visited = visited_in_path.copy()
    current_path_visited.add(concept.id)

    found_models: Set[uuid.UUID] = set()
    if concept.type == ConceptType.UNIFIED_MODEL:
        found_models.add(concept.id)

    for potential_parent in all_concepts_list:
        if potential_parent.member_concept_ids and concept.id in potential_parent.member_concept_ids:
            found_models.update(
                _trace_to_unified_models(potential_parent, repo, all_concepts_list, current_path_visited)
            )

    # Also consider relationships where the current 'concept' is a child referenced by a specific field in a PROPOSITION
    # Case 1: Current concept is a CLUSTER, find PROPOSITIONs derived from it.
    if concept.type == ConceptType.CLUSTER:
        for potential_parent_prop in all_concepts_list:
            if potential_parent_prop.type == ConceptType.PROPOSITION and \
               potential_parent_prop.derived_from_cluster_id == concept.id:
                # potential_parent_prop is a proposition derived from this cluster.
                # Trace upwards from this proposition.
                found_models.update(
                    _trace_to_unified_models(potential_parent_prop, repo, all_concepts_list, current_path_visited)
                )

    # Case 2: Current concept is a UCM, find PROPOSITIONs derived directly from it.
    if concept.type == ConceptType.UCM:
        for potential_parent_prop_ucm in all_concepts_list:
            if potential_parent_prop_ucm.type == ConceptType.PROPOSITION and \
               potential_parent_prop_ucm.derived_from_ucm_ids and \
               concept.id in potential_parent_prop_ucm.derived_from_ucm_ids:
                # potential_parent_prop_ucm is a proposition derived directly from this UCM.
                # Trace upwards from this proposition.
                found_models.update(
                    _trace_to_unified_models(potential_parent_prop_ucm, repo, all_concepts_list, current_path_visited)
                )

    return found_models


def _calculate_depth_to_ucm(
    concept: Optional[ScientificConcept], repo: ConceptRepoProtocol, visited_in_path: Optional[Set[uuid.UUID]] = None
) -> int:
    # This remains recursive.
    _infinity = float('inf')
    if not concept: return -1
    if visited_in_path is None: visited_in_path = set()
    if concept.id in visited_in_path: return -1

    current_path_visited = visited_in_path.copy()
    current_path_visited.add(concept.id)

    if concept.type == ConceptType.UCM: return 0

    min_child_depth = _infinity
    if concept.member_concept_ids:
        for member_id in concept.member_concept_ids:
            member = repo.get_by_id(member_id)
            depth = _calculate_depth_to_ucm(member, repo, current_path_visited)
            if depth != -1:
                 min_child_depth = min(min_child_depth, float(depth) + 1.0)

    if concept.type == ConceptType.PROPOSITION and concept.derived_from_ucm_ids:
        if any( (m := repo.get_by_id(ucm_id)) and m.type == ConceptType.UCM for ucm_id in concept.derived_from_ucm_ids ):
            min_child_depth = min(min_child_depth, 1.0)

    return -1 if min_child_depth == _infinity else int(min_child_depth)


def _calculate_depth_to_model(
    concept: Optional[ScientificConcept], repo: ConceptRepoProtocol,
    all_concepts_list: List[ScientificConcept], visited_in_path: Optional[Set[uuid.UUID]] = None
) -> int:
    # This remains recursive.
    _infinity = float('inf')
    if not concept: return -1
    if visited_in_path is None: visited_in_path = set()
    if concept.id in visited_in_path: return -1

    current_path_visited = visited_in_path.copy()
    current_path_visited.add(concept.id)

    if concept.type == ConceptType.UNIFIED_MODEL: return 0

    min_parent_depth = _infinity
    for potential_parent in all_concepts_list:
        if potential_parent.member_concept_ids and concept.id in potential_parent.member_concept_ids:
            depth = _calculate_depth_to_model(potential_parent, repo, all_concepts_list, current_path_visited)
            if depth != -1:
                min_parent_depth = min(min_parent_depth, float(depth) + 1.0)

    return -1 if min_parent_depth == _infinity else int(min_parent_depth)

# --- End Visualization Helper Functions ---

def get_test_concept_repo() -> ConceptRepoProtocol: return _test_concept_repo_singleton
def get_test_relationship_repo() -> RelationshipRepoProtocol: return _test_relationship_repo_singleton

# ... (DI functions)
def get_test_knowledge_synthesis_use_case(concept_repo: ConceptRepoProtocol = Depends(get_test_concept_repo), relationship_repo: RelationshipRepoProtocol = Depends(get_test_relationship_repo)) -> KnowledgeSynthesisUseCase: return KnowledgeSynthesisUseCase(concept_repo, relationship_repo)
def get_extract_ucms_use_case(concept_repo: ConceptRepoProtocol = Depends(get_test_concept_repo)) -> ExtractUCMsUseCase: return ExtractUCMsUseCase(concept_repo=concept_repo)
def get_form_clusters_use_case(concept_repo: ConceptRepoProtocol = Depends(get_test_concept_repo)) -> FormClustersUseCase: return FormClustersUseCase(concept_repo=concept_repo)
def get_derive_propositions_use_case(concept_repo: ConceptRepoProtocol = Depends(get_test_concept_repo), relationship_repo: RelationshipRepoProtocol = Depends(get_test_relationship_repo)) -> DerivePropositionsUseCase: return DerivePropositionsUseCase(concept_repo=concept_repo, relationship_repo=relationship_repo)
def get_construct_mini_theory_use_case(concept_repo: ConceptRepoProtocol = Depends(get_test_concept_repo)) -> ConstructMiniTheoryUseCase: return ConstructMiniTheoryUseCase(concept_repo=concept_repo)
def get_construct_comprehensive_theory_use_case(concept_repo: ConceptRepoProtocol = Depends(get_test_concept_repo)) -> ConstructComprehensiveTheoryUseCase: return ConstructComprehensiveTheoryUseCase(concept_repo=concept_repo)
def get_construct_unified_model_use_case(concept_repo: ConceptRepoProtocol = Depends(get_test_concept_repo)) -> ConstructUnifiedModelUseCase: return ConstructUnifiedModelUseCase(concept_repo=concept_repo)
def get_ingest_document_use_case(concept_repo: ConceptRepoProtocol = Depends(get_test_concept_repo), extract_ucms_uc: ExtractUCMsUseCase = Depends(get_extract_ucms_use_case) ) -> IngestDocumentUseCase: return IngestDocumentUseCase(concept_repo=concept_repo, extract_ucms_use_case=extract_ucms_uc)
def get_link_concepts_use_case(concept_repo: ConceptRepoProtocol = Depends(get_test_concept_repo), relationship_repo: RelationshipRepoProtocol = Depends(get_test_relationship_repo)) -> LinkConceptsUseCase: return LinkConceptsUseCase(concept_repo=concept_repo, relationship_repo=relationship_repo)


def create_test_app() -> FastAPI:
    app = FastAPI(title="Aletheia Test API", description="Test API", version="0.1.0-test")

    # ... (Basic Concept, Eje Y Construction, Eje X Endpoints)
    @app.post("/concepts/", response_model=ScientificConcept, status_code=status.HTTP_201_CREATED, tags=["Concepts"])
    def create_new_concept_endpoint(input_data: CreateConceptInput, use_case: KnowledgeSynthesisUseCase = Depends(get_test_knowledge_synthesis_use_case)): return use_case.create_concept(input_data)
    @app.get("/concepts/", response_model=List[ScientificConcept], tags=["Concepts"])
    def list_all_concepts_endpoint(use_case: KnowledgeSynthesisUseCase = Depends(get_test_knowledge_synthesis_use_case)): return use_case.get_all_concepts()
    @app.get("/concepts/{concept_id}", response_model=ScientificConcept, tags=["Concepts"])
    def get_single_concept_endpoint(concept_id: uuid.UUID, use_case: KnowledgeSynthesisUseCase = Depends(get_test_knowledge_synthesis_use_case)):
        try: return use_case.get_concept_details(concept_id)
        except ValueError as e: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    @app.post("/eje_y/ucm_extraction/", response_model=UCMExtractionResult, status_code=status.HTTP_201_CREATED, tags=["Eje Y - Construction"])
    def extract_ucms_endpoint(input_data: ExtractUCMsInput, use_case: ExtractUCMsUseCase = Depends(get_extract_ucms_use_case)): return use_case.execute(input_data)
    @app.post("/eje_y/cluster_formation/", response_model=ClusterFormationResult, status_code=status.HTTP_201_CREATED, tags=["Eje Y - Construction"])
    def form_cluster_endpoint(input_data: FormClusterInput, use_case: FormClustersUseCase = Depends(get_form_clusters_use_case)):
        try: return use_case.execute(input_data)
        except ValueError as e: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    @app.post("/eje_y/proposition_derivation/", response_model=PropositionDerivationResult, status_code=status.HTTP_201_CREATED, tags=["Eje Y - Construction"])
    def derive_proposition_endpoint(input_data: DerivePropositionInput, use_case: DerivePropositionsUseCase = Depends(get_derive_propositions_use_case)):
        try: return use_case.execute(input_data)
        except ValueError as e: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    @app.post("/eje_y/mini_theory_construction/", response_model=MiniTheoryConstructionResult, status_code=status.HTTP_201_CREATED, tags=["Eje Y - Construction"])
    def construct_mini_theory_endpoint(input_data: ConstructMiniTheoryInput, use_case: ConstructMiniTheoryUseCase = Depends(get_construct_mini_theory_use_case)):
        try: return use_case.execute(input_data)
        except ValueError as e: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    @app.post("/eje_y/comprehensive_theories/", response_model=ComprehensiveTheoryResult, status_code=status.HTTP_201_CREATED, tags=["Eje Y - Construction"])
    def construct_comprehensive_theory_endpoint(input_data: ConstructComprehensiveTheoryInput, use_case: ConstructComprehensiveTheoryUseCase = Depends(get_construct_comprehensive_theory_use_case)):
        try: return use_case.execute(input_data)
        except ValueError as e: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    @app.post("/eje_y/unified_models/", response_model=UnifiedModelResult, status_code=status.HTTP_201_CREATED, tags=["Eje Y - Construction"])
    def construct_unified_model_endpoint(input_data: ConstructUnifiedModelInput, use_case: ConstructUnifiedModelUseCase = Depends(get_construct_unified_model_use_case)):
        try: return use_case.execute(input_data)
        except ValueError as e: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    @app.post("/eje_x/documents/ingest/", response_model=IngestDocumentResult, status_code=status.HTTP_201_CREATED, tags=["Eje X - Ingestion"])
    def ingest_document_endpoint(input_data: IngestDocumentInput, use_case: IngestDocumentUseCase = Depends(get_ingest_document_use_case)):
        try: return use_case.execute(input_data)
        except Exception as e: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error: {str(e)}")
    @app.post("/eje_x/relationships/", response_model=LinkConceptsResult, status_code=status.HTTP_201_CREATED, tags=["Eje X - Ontology"])
    def link_concepts_endpoint(input_data: LinkConceptsInput, use_case: LinkConceptsUseCase = Depends(get_link_concepts_use_case)):
        try: return use_case.execute(input_data)
        except ValueError as e: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except Exception as e: raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error: {str(e)}")


    # --- Eje Y - Visualization Endpoints ---
    @app.get("/eje_y/visualization/hierarchy_graph/{concept_id}", response_model=Dict[str, Any], tags=["Eje Y - Visualization"])
    def get_hierarchy_graph_endpoint(
        concept_id: uuid.UUID, max_depth_param: int = Query(5, alias="max_depth", ge=1, le=10),
        concept_repo: ConceptRepoProtocol = Depends(get_test_concept_repo),
    ):
        root_concept = concept_repo.get_by_id(concept_id)
        if not root_concept: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Concept not found")

        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []
        globally_added_nodes: Set[uuid.UUID] = set()

        # Iterative BFS for graph building
        queue = deque([(root_concept, 0)]) # (concept, current_depth_from_root)
        # Path visited is not needed for BFS cycle detection if we use globally_added_nodes for queuing

        while queue:
            current_c, current_d = queue.popleft()

            if current_c.id not in globally_added_nodes:
                globally_added_nodes.add(current_c.id)
                nodes.append({
                    "id": str(current_c.id), "label": current_c.name[:50], "type": current_c.type.value,
                    "level": _get_hierarchy_level(current_c.type),
                    "properties": {
                        "description_snippet": current_c.description[:100] + ("..." if len(current_c.description) > 100 else ""),
                        "member_count": len(current_c.member_concept_ids or [])
                    }
                })

            if current_d >= max_depth_param:
                continue # Don't explore children if max depth reached for this node

            # Process members
            children_to_explore: List[ScientificConcept] = []
            edge_type_for_children = "contains"

            if current_c.member_concept_ids:
                for member_id in current_c.member_concept_ids:
                    member = concept_repo.get_by_id(member_id)
                    if member:
                        children_to_explore.append(member)

            # If current_c is a PROPOSITION, also consider its derived_from_cluster_id as a child for graph traversal
            if current_c.type == ConceptType.PROPOSITION and current_c.derived_from_cluster_id:
                cluster_child = concept_repo.get_by_id(current_c.derived_from_cluster_id)
                if cluster_child:
                    # Avoid adding duplicate if cluster is somehow also in member_concept_ids (should not happen for PROPOSITION)
                    if cluster_child.id not in {c.id for c in children_to_explore}:
                        children_to_explore.append(cluster_child)
                    # We might want a specific edge type here, e.g., "derived_into_proposition" if source=cluster, target=prop
                    # Or, if source=prop, target=cluster, "derived_from_cluster"
                    # For now, let's add edge from Prop to Cluster, similar to how Prop -> UCM works.
                    # The existing "contains" might be confusing. Let's add a specific edge for this.
                    # This part of the code is adding children to the queue, so edges are from current_c to child.
                    # The edge creation for this specific link (Prop->Cluster) will be handled below.

            for child_c in children_to_explore:
                # Determine edge type. Default is "contains".
                # If current_c is PROPOSITION and child_c is its derived_from_cluster_id, type is "derived_from_cluster".
                # This logic is getting complicated here. Let's simplify edge creation.
                # Edges for "member_concept_ids" are "contains".
                # Edge for "derived_from_cluster_id" will be "derived_from_cluster".
                # Edge for "derived_from_ucm_ids" is "derived_from_ucm".

                # Standard "contains" edge for member_concept_ids
                if current_c.member_concept_ids and child_c.id in current_c.member_concept_ids:
                    edges.append({"source": str(current_c.id), "target": str(child_c.id), "type": "contains"})

                if child_c.id not in globally_added_nodes:
                    queue.append((child_c, current_d + 1))

            # Special handling for PROPOSITION children (Cluster and UCMs)
            if current_c.type == ConceptType.PROPOSITION:
                # Link to derived Cluster
                if current_c.derived_from_cluster_id:
                    cluster_child = concept_repo.get_by_id(current_c.derived_from_cluster_id)
                    if cluster_child:
                        edges.append({"source": str(current_c.id), "target": str(cluster_child.id), "type": "derived_from_cluster"})
                        if cluster_child.id not in globally_added_nodes:
                             # It might have been added to queue above if it wasn't in globally_added_nodes.
                             # Ensure it's in queue if not processed. If already in children_to_explore, it's handled.
                             # This logic is slightly redundant with the generic children_to_explore loop if we add it there.
                             # Let's ensure it's added to queue if not already processed.
                             # The children_to_explore loop already handles adding to queue.
                             pass # Already handled by children_to_explore logic if correctly added there.

                # Link to derived UCMs
                if current_c.derived_from_ucm_ids and current_d < max_depth_param:
                    for ucm_id in current_c.derived_from_ucm_ids:
                        ucm_child = concept_repo.get_by_id(ucm_id)
                        if ucm_child:
                            edges.append({"source": str(current_c.id), "target": str(ucm_id), "type": "derived_from_ucm"})
                            if ucm_child.id not in globally_added_nodes:
                                globally_added_nodes.add(ucm_child.id) # Add UCM to nodes list directly
                                nodes.append({
                                    "id": str(ucm_child.id), "label": ucm_child.name[:50],
                                    "type": ucm_child.type.value, "level": _get_hierarchy_level(ucm_child.type),
                                    "properties": {"description_snippet": ucm_child.description[:100],"member_count": 0}
                                })
                                # UCMs are leaves, don't add to queue from here

        actual_max_depth_val = 0
        if nodes and root_concept:
            root_level = _get_hierarchy_level(root_concept.type)
            node_levels = [n["level"] for n in nodes if isinstance(n.get("level"), int) and n["level"] >= 0]
            if node_levels:
                 max_node_abs_level = max(node_levels)
                 if root_level >= 0 and max_node_abs_level >= root_level:
                     actual_max_depth_val = max_node_abs_level - root_level
                 elif node_levels :
                     actual_max_depth_val = max_node_abs_level
                 actual_max_depth_val = max(0, actual_max_depth_val)

        return {
            "nodes": nodes, "edges": edges,
            "metadata": {
                "root_id": str(concept_id), "requested_max_depth": max_depth_param,
                "actual_max_depth_rendered": actual_max_depth_val,
                "total_nodes_rendered": len(nodes), "total_edges_rendered": len(edges),
            }
        }

    @app.get("/eje_y/visualization/synthesis_statistics", response_model=Dict[str, Any], tags=["Eje Y - Visualization"])
    def get_synthesis_statistics_endpoint(concept_repo: ConceptRepoProtocol = Depends(get_test_concept_repo)):
        all_concepts = concept_repo.list_all()
        type_counts: defaultdict[str, int] = defaultdict(int)
        for c_obj in all_concepts: type_counts[c_obj.type.value] += 1

        ucm_c = type_counts.get(ConceptType.UCM.value,0); cl_c = type_counts.get(ConceptType.CLUSTER.value,0)
        prop_c = type_counts.get(ConceptType.PROPOSITION.value,0); mt_c = type_counts.get(ConceptType.MINI_THEORY.value,0)
        ct_c = type_counts.get(ConceptType.COMPREHENSIVE_THEORY.value,0); um_c = type_counts.get(ConceptType.UNIFIED_MODEL.value,0)

        ratios = {"ucm_to_cluster": cl_c/ucm_c if ucm_c else 0,
                  "cluster_to_proposition": prop_c/cl_c if cl_c else 0,
                  "proposition_to_mini_theory": mt_c/prop_c if prop_c else 0,
                  "mini_theory_to_comprehensive": ct_c/mt_c if mt_c else 0,
                  "comprehensive_to_unified": um_c/ct_c if ct_c else 0}

        deep_paths: List[Dict[str, Any]] = []
        ums = [c_obj for c_obj in all_concepts if c_obj.type == ConceptType.UNIFIED_MODEL]
        for m in sorted(ums, key=lambda x: x.name)[:5]:
            depth = _calculate_max_depth(m, concept_repo, set()) # Pass empty set for visited
            deep_paths.append({"model_id":str(m.id),"model_name":m.name,"depth_to_ucm": depth})
        deep_paths_sorted = sorted(deep_paths, key=lambda x: x["depth_to_ucm"] if x["depth_to_ucm"] != -1 else -float('inf'), reverse=True)
        for item in deep_paths_sorted: item["depth_to_ucm"] = item["depth_to_ucm"] if item["depth_to_ucm"] != -1 else "N/A"


        return {"total_concepts":len(all_concepts),"type_distribution":dict(type_counts),"synthesis_ratios":ratios,
                "deepest_hierarchies_sample":deep_paths_sorted[:3],
                "synthesis_efficiency":{"total_ucms":ucm_c,"total_unified_models":um_c,
                                      "compression_ratio":ucm_c/um_c if um_c else 0}}

    @app.get("/eje_y/visualization/concept_lineage/{concept_id}", response_model=Dict[str, Any], tags=["Eje Y - Visualization"])
    def get_concept_lineage_endpoint(concept_id: uuid.UUID, concept_repo: ConceptRepoProtocol = Depends(get_test_concept_repo)):
        concept = concept_repo.get_by_id(concept_id)
        if not concept: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Concept not found")
        all_concepts_list = concept_repo.list_all()

        ucm_ids = _trace_to_ucms(concept, concept_repo, set())
        um_ids = _trace_to_unified_models(concept, concept_repo, all_concepts_list, set())

        ucm_srcs = []
        for uid in ucm_ids:
            c_obj = concept_repo.get_by_id(uid)
            ucm_srcs.append({"id":str(uid),"name": (c_obj.name if c_obj else "Unknown UCM")})

        um_parts = []
        for uid_model in um_ids:
            c_obj_model = concept_repo.get_by_id(uid_model)
            um_parts.append({"id":str(uid_model),"name": (c_obj_model.name if c_obj_model else "Unknown Model")})

        return {"target_concept":{"id":str(concept.id),"name":concept.name,"type":concept.type.value},
                "ucm_sources":ucm_srcs, "part_of_unified_models":um_parts,
                "calculated_depths":{
                    "min_depth_to_ucm":_calculate_depth_to_ucm(concept,concept_repo,set()),
                    "min_depth_to_model":_calculate_depth_to_model(concept,concept_repo,all_concepts_list,set())}}
    return app

app_for_testing = create_test_app()

def reset_test_repo_singletons():
    global _test_concept_repo_singleton, _test_relationship_repo_singleton
    _test_concept_repo_singleton = InMemoryConceptRepository()
    _test_relationship_repo_singleton = InMemoryRelationshipRepository()
