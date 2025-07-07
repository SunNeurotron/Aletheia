from fastapi import APIRouter, Depends, HTTPException, status

# Importar Schemas desde api.schemas
from ..schemas import (
    UCMExtractionRequestSchema, UCMExtractionResponseSchema,
    FormClusterInputSchema, FormClusterResultSchema,
    PropositionDerivationInputSchema, PropositionDerivationResultSchema,
    MiniTheoryConstructionInputSchema, MiniTheoryConstructionResultSchema,
    ComprehensiveTheoriesInputSchema, ComprehensiveTheoriesResultSchema,
    UnifiedModelsInputSchema, UnifiedModelsResultSchema
)

# Importar Casos de Uso (Clases concretas)
from ...application.use_cases import (
    ExtractUCMsUseCase,
    FormClustersUseCase,
    DerivePropositionsUseCase, # Nombre actualizado
    MiniTheoryConstructionUseCase,
    ComprehensiveTheoriesUseCase,
    UnifiedModelsUseCase
)

# Importar dependencias para obtener instancias de casos de uso y seguridad
from ..dependencies import (
    get_extract_ucms_use_case,
    get_form_clusters_use_case,
    get_derive_propositions_use_case, # Nombre actualizado
    get_mini_theory_construction_use_case,
    get_comprehensive_theories_use_case,
    get_unified_models_use_case
)
from ..security import require_roles

# Renombrar Schemas de Resultado para consistencia en el router
from ..schemas import (
    FormClusterResponseSchema,
    PropositionDerivationResponseSchema,
    MiniTheoryConstructionResponseSchema,
    ComprehensiveTheoriesResponseSchema,
    UnifiedModelsResponseSchema
)

router = APIRouter(
    prefix="/eje-y",
    tags=["Eje Y - Knowledge Synthesis"],
    responses={404: {"description": "Not found"}},
)

# --- Endpoint para Extracción de UCMs ---
@router.post(
    "/ucm-extraction",
    response_model=UCMExtractionResponseSchema,
    status_code=status.HTTP_200_OK, # O 201 si se considera creación de un "trabajo de extracción"
    summary="Extrae Unidades Conceptuales Mínimas (UCMs) de un texto.",
    dependencies=[Depends(require_roles(["researcher", "admin"]))],
)
async def ucm_extraction_endpoint(
    request_data: UCMExtractionRequestSchema,
    extract_use_case: ExtractUCMsUseCase = Depends(get_extract_ucms_use_case),
):
    """
    Endpoint para la extracción de UCMs.
    - Procesa el texto de entrada para identificar y extraer conceptos y relaciones.
    """
    try:
        # En use_cases.py, UCMExtractionInput es un alias de UCMExtractionRequestSchema
        result = await extract_use_case.execute(request_data)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        # Loggear el error 'e'
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal server error occurred during UCM extraction.")

# --- Endpoints Placeholder para otros Casos de Uso del Eje Y ---
# Estos necesitarán sus propios Schemas de Input/Result y Casos de Uso (Protocolos y luego implementaciones)

@router.post(
    "/cluster-formation",
    response_model=FormClusterResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Forma clústeres de conceptos a partir de UCMs.",
    dependencies=[Depends(require_roles(["researcher", "admin"]))],
)
async def form_clusters_endpoint(
    request_data: FormClusterInputSchema,
    form_clusters_use_case: FormClustersUseCase = Depends(get_form_clusters_use_case),
):
    """
    Endpoint para la formación de clústeres de UCMs.
    - Recibe una lista de IDs de UCMs.
    - Aplica una lógica de clustering simple basada en palabras clave.
    - Crea y persiste nuevos conceptos de tipo CLUSTER.
    - Devuelve información sobre los clústeres creados.
    """
    try:
        result = await form_clusters_use_case.execute(request_data)
        # Si el caso de uso devuelve un mensaje de que no se crearon clusters pero no es un error,
        # podríamos querer un código de estado 200 en lugar de 201.
        # Por ahora, si no hay error, es 201 si algo *podría* haberse creado.
        if not result.created_clusters and input_data.ucm_ids:
             # Podríamos devolver 200 OK con el mensaje, o mantener 201 si la operación fue "exitosa"
             # en el sentido de que no hubo error, aunque no se creara nada.
             # Opcionalmente, lanzar un HTTP 400 si se considera un input que no lleva a nada.
             pass # Mantener 201 y devolver el resultado con mensaje.
        return result
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        # Log e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno formando clústeres.")

@router.post(
    "/proposition-derivation",
    response_model=PropositionDerivationResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Deriva proposiciones a partir de clústeres.",
    dependencies=[Depends(require_roles(["researcher", "admin"]))],
)
async def derive_propositions_endpoint(
    request_data: PropositionDerivationInputSchema,
    derive_propositions_use_case: DerivePropositionsUseCase = Depends(get_derive_propositions_use_case),
):
    """
    Endpoint para la derivación de proposiciones.
    - Recibe una lista de IDs de clústeres.
    - Genera proposiciones basadas en los miembros y temas de cada clúster.
    - Crea y persiste nuevos conceptos de tipo PROPOSITION.
    - Devuelve información sobre las proposiciones creadas.
    """
    try:
        result = await derive_propositions_use_case.execute(request_data)
        return result
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        # Log e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno derivando proposiciones.")

@router.post(
    "/mini-theory-construction",
    response_model=MiniTheoryConstructionResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Construye una mini-teoría a partir de proposiciones.",
    dependencies=[Depends(require_roles(["researcher", "admin"]))],
)
async def mini_theory_construction_endpoint(
    request_data: MiniTheoryConstructionInputSchema,
    mini_theory_use_case: MiniTheoryConstructionUseCase = Depends(get_mini_theory_construction_use_case),
):
    """
    Endpoint para la construcción de mini-teorías.
    - Recibe una lista de IDs de proposiciones.
    - Crea un nuevo concepto de tipo MINI_THEORY que agrupa estas proposiciones.
    - Devuelve información sobre la mini-teoría creada.
    """
    try:
        result = await mini_theory_use_case.execute(request_data)
        if not result.created_mini_theory and request_data.proposition_ids:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.message or "No se pudo crear la mini-teoría con las proposiciones dadas.")
        return result
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno construyendo mini-teoría.")

@router.post(
    "/comprehensive-theories",
    response_model=ComprehensiveTheoriesResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Construye una teoría comprehensiva a partir de mini-teorías.",
    dependencies=[Depends(require_roles(["researcher", "admin"]))],
)
async def comprehensive_theories_endpoint(
    request_data: ComprehensiveTheoriesInputSchema,
    comp_theories_use_case: ComprehensiveTheoriesUseCase = Depends(get_comprehensive_theories_use_case),
):
    """
    Endpoint para la construcción de teorías comprehensivas.
    - Recibe una lista de IDs de mini-teorías.
    - Crea un nuevo concepto de tipo COMPREHENSIVE_THEORY.
    - Devuelve información sobre la teoría creada.
    """
    try:
        result = await comp_theories_use_case.execute(request_data)
        if not result.created_comprehensive_theory and request_data.mini_theory_ids:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.message or "No se pudo crear la teoría comprehensiva.")
        return result
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno construyendo teoría comprehensiva.")

@router.post(
    "/unified-models",
    response_model=UnifiedModelsResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Sintetiza un modelo unificado a partir de teorías comprehensivas.",
    dependencies=[Depends(require_roles(["researcher", "admin"]))],
)
async def unified_models_endpoint(
    request_data: UnifiedModelsInputSchema,
    unified_models_use_case: UnifiedModelsUseCase = Depends(get_unified_models_use_case),
):
    """
    Endpoint para la síntesis de modelos unificados.
    - Recibe una lista de IDs de teorías comprehensivas.
    - Crea un nuevo concepto de tipo UNIFIED_MODEL.
    - Devuelve información sobre el modelo creado.
    """
    try:
        result = await unified_models_use_case.execute(request_data)
        if not result.created_unified_model and request_data.comprehensive_theory_ids:
             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.message or "No se pudo crear el modelo unificado.")
        return result
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno sintetizando modelo unificado.")

# --- Endpoints de Visualización del Eje Y ---
from ..schemas import HierarchyGraphResponseSchema, SynthesisStatisticsResponseSchema # Nuevos Schemas
# (IConceptRepository y dependencias ya importados)
from ...application.ports import IConceptRepository # Asegurar que esté importado
from ...core.domain_models import ConceptType # Para lógica interna
from ..dependencies import get_concept_repository # Para la dependencia
from fastapi import Query # Nueva importación
from collections import deque # Para BFS
from typing import List, Dict, Optional, Any # Para tipos internos

@router.get(
    "/visualization/hierarchy_graph/{concept_id}",
    response_model=HierarchyGraphResponseSchema,
    summary="Obtiene datos para visualizar la jerarquía de un concepto sintetizado.",
    dependencies=[Depends(require_roles(["researcher", "admin"]))],
)
async def get_hierarchy_graph(
    concept_id: str,
    max_depth: Optional[int] = Query(3, ge=1, le=5, description="Profundidad máxima de la jerarquía a explorar."),
    concept_repo: IConceptRepository = Depends(get_concept_repository)
):
    """
    Devuelve los nodos y aristas para construir un grafo de jerarquía
    para un concepto de alto nivel (ej. Modelo Unificado, Teoría Comprehensiva).
    Explora los conceptos miembro recursivamente hasta la profundidad especificada.
    """
    root_concept = await concept_repo.get_by_id(concept_id)
    if not root_concept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Concepto raíz con ID '{concept_id}' no encontrado.")

    nodes_map: Dict[str, HierarchyGraphNodeSchema] = {}
    edges: List[HierarchyGraphEdgeSchema] = []

    queue = deque([(root_concept, 0)]) # (concepto_dominio, nivel_actual)
    # visited_ids se usa para controlar los nodos que se añaden a la cola del BFS,
    # no necesariamente los que ya están en nodes_map, ya que un nodo puede ser
    # añadido a nodes_map como target de una arista antes de ser procesado él mismo.
    ids_in_bfs_queue_or_processed = {root_concept.id}


    while queue:
        current_concept_domain, level = queue.popleft()

        if current_concept_domain.id not in nodes_map:
            nodes_map[current_concept_domain.id] = HierarchyGraphNodeSchema(
                id=current_concept_domain.id,
                label=current_concept_domain.name,
                title=f"Nombre: {current_concept_domain.name}\nTipo: {current_concept_domain.concept_type.value}\nID: {current_concept_domain.id}",
                type=current_concept_domain.concept_type.value,
                level=level
            )
        else:
            # Si el nodo ya existe (añadido como target de una arista), actualizar su nivel si este es menor
            if nodes_map[current_concept_domain.id].level is None or level < nodes_map[current_concept_domain.id].level:
                nodes_map[current_concept_domain.id].level = level


        if level >= max_depth:
            continue

        member_ids_property_key: Optional[str] = None
        edge_label = "contiene"

        # Mapeo de tipos de concepto a la clave de propiedad que contiene sus miembros
        type_to_member_key_map = {
            ConceptType.CLUSTER: "member_concept_ids",
            ConceptType.PROPOSITION: "involved_ucm_ids", # O podría ser based_on_cluster_id si es singular
            ConceptType.MINI_THEORY: "member_proposition_ids",
            ConceptType.COMPREHENSIVE_THEORY: "member_mini_theory_ids",
            ConceptType.UNIFIED_MODEL: "member_comprehensive_theory_ids",
        }
        # Mapeo de etiquetas de aristas (opcional, para mayor claridad)
        edge_labels_map = {
            ConceptType.CLUSTER: "agrupa_ucm",
            ConceptType.PROPOSITION: "involucra_ucm",
            ConceptType.MINI_THEORY: "compuesto_de_prop",
            ConceptType.COMPREHENSIVE_THEORY: "compuesto_de_minit",
            ConceptType.UNIFIED_MODEL: "compuesto_de_compth",
        }

        member_ids_property_key = type_to_member_key_map.get(current_concept_domain.concept_type)
        edge_label = edge_labels_map.get(current_concept_domain.concept_type, "relacionado_con")

        if member_ids_property_key and member_ids_property_key in current_concept_domain.properties:
            member_ids = current_concept_domain.properties[member_ids_property_key]

            if isinstance(member_ids, list): # Asegurarse de que es una lista de IDs
                for member_id in member_ids:
                    # Añadir arista primero
                    edges.append(HierarchyGraphEdgeSchema(
                        from_node=current_concept_domain.id,
                        to_node=member_id,
                        label=edge_label
                    ))

                    # Añadir nodo miembro a la cola si no ha sido procesado/encolado y obtenerlo
                    if member_id not in ids_in_bfs_queue_or_processed:
                        member_concept_domain = await concept_repo.get_by_id(member_id)
                        if member_concept_domain:
                            ids_in_bfs_queue_or_processed.add(member_id)
                            queue.append((member_concept_domain, level + 1))
                            # Pre-añadir nodo a nodes_map para asegurar que exista para futuras aristas
                            if member_id not in nodes_map:
                                nodes_map[member_id] = HierarchyGraphNodeSchema(
                                    id=member_concept_domain.id,
                                    label=member_concept_domain.name,
                                    title=f"Nombre: {member_concept_domain.name}\nTipo: {member_concept_domain.concept_type.value}\nID: {member_concept_domain.id}",
                                    type=member_concept_domain.concept_type.value,
                                    level=level + 1 # Nivel tentativo, podría actualizarse si se alcanza por un camino más corto
                                )
            # Manejar caso especial como 'based_on_cluster_id' que podría ser un solo ID
            elif isinstance(member_ids, str) and member_ids_property_key == "involved_ucm_ids": # Ejemplo si fuera un solo id
                 # Esta parte es un ejemplo, la propiedad involved_ucm_ids ya es una lista
                 pass


    return HierarchyGraphResponseSchema(nodes=list(nodes_map.values()), edges=edges)


@router.get(
    "/visualization/synthesis_statistics",
    response_model=SynthesisStatisticsResponseSchema,
    summary="Obtiene estadísticas generales sobre el grafo de conocimiento sintetizado.",
    dependencies=[Depends(require_roles(["researcher", "admin"]))],
)
async def get_synthesis_statistics(
    concept_repo: IConceptRepository = Depends(get_concept_repository),
    relationship_repo: IRelationshipRepository = Depends(get_relationship_repository)
):
    """
    Devuelve estadísticas agregadas sobre los conceptos y su proceso de síntesis,
    calculadas a partir de los datos reales en los repositorios.
    """
    try:
        all_concepts = await concept_repo.list_all()
        all_relationships = await relationship_repo.list_all()

        num_total_concepts = len(all_concepts)
        num_total_relationships = len(all_relationships)

        num_documents_processed = 0
        type_distribution: Dict[str, int] = defaultdict(int)

        for concept in all_concepts:
            concept_type_str = concept.concept_type.value
            type_distribution[concept_type_str] += 1
            if concept.concept_type == ConceptType.DOCUMENT_SOURCE:
                num_documents_processed += 1

        overall_stats = [
            SynthesisStatisticItemSchema(name="Total Conceptos Registrados", value=num_total_concepts),
            SynthesisStatisticItemSchema(name="Total Relaciones Registradas", value=num_total_relationships),
            SynthesisStatisticItemSchema(name="Documentos Fuente Procesados", value=num_documents_processed),
        ]

        return SynthesisStatisticsResponseSchema(
            overall_stats=overall_stats,
            type_distribution=dict(type_distribution)
        )
    except Exception as e:
        # Log e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno calculando estadísticas: {str(e)}")

```
