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
# from ...core.domain_models import ConceptType # Para generar datos de ejemplo

@router.get(
    "/visualization/hierarchy_graph/{concept_id}",
    response_model=HierarchyGraphResponseSchema,
    summary="Obtiene datos para visualizar la jerarquía de un concepto sintetizado.",
    dependencies=[Depends(require_roles(["researcher", "admin"]))],
)
async def get_hierarchy_graph(
    concept_id: str,
    # concept_repo: IConceptRepository = Depends(get_concept_repository) # Para implementación real
):
    """
    Devuelve los nodos y aristas para construir un grafo de jerarquía
    para un concepto de alto nivel (ej. Modelo Unificado, Teoría Comprehensiva).
    Por ahora, devuelve datos simulados.
    """
    # TODO: Implementar lógica real para construir el grafo de jerarquía
    #       consultando el concept_repo y relationship_repo.
    #       Se necesitaría recorrer las propiedades "member_..." recursivamente.
    if concept_id == "unifiedm_placeholder_0" or concept_id.startswith("unifiedm_"): # Simular para un ID conocido
        nodes = [
            HierarchyGraphNodeSchema(id=concept_id, label=f"Modelo Unificado ({concept_id[:6]})", type="UNIFIED_MODEL", level=0),
            HierarchyGraphNodeSchema(id="compth_1", label="Teoría Comp. 1", type="COMPREHENSIVE_THEORY", level=1),
            HierarchyGraphNodeSchema(id="minit_a", label="Mini-Teoría A", type="MINI_THEORY", level=2),
            HierarchyGraphNodeSchema(id="prop_x", label="Proposición X", type="PROPOSITION", level=3),
        ]
        edges = [
            HierarchyGraphEdgeSchema(from_node=concept_id, to_node="compth_1", label="compuesto_de"),
            HierarchyGraphEdgeSchema(from_node="compth_1", to_node="minit_a", label="compuesto_de"),
            HierarchyGraphEdgeSchema(from_node="minit_a", to_node="prop_x", label="basado_en"),
        ]
        return HierarchyGraphResponseSchema(nodes=nodes, edges=edges)

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Concepto con ID '{concept_id}' no encontrado o no es un modelo/teoría visualizable en jerarquía (simulado).")

@router.get(
    "/visualization/synthesis_statistics",
    response_model=SynthesisStatisticsResponseSchema,
    summary="Obtiene estadísticas generales sobre el grafo de conocimiento sintetizado.",
    dependencies=[Depends(require_roles(["researcher", "admin"]))],
)
async def get_synthesis_statistics(
    # concept_repo: IConceptRepository = Depends(get_concept_repository) # Para implementación real
):
    """
    Devuelve estadísticas agregadas sobre los conceptos y su proceso de síntesis.
    Por ahora, devuelve datos simulados.
    """
    # TODO: Implementar lógica real para calcular estadísticas desde el concept_repo.
    overall_stats = [
        SynthesisStatisticItemSchema(name="Total Conceptos", value=150),
        SynthesisStatisticItemSchema(name="Total Relaciones", value=300), # Asumir que se obtendría de relationship_repo
        SynthesisStatisticItemSchema(name="Documentos Procesados", value=10),
    ]
    type_distribution = {
        "DOCUMENT_SOURCE": 10,
        "UCM": 80,
        "CLUSTER": 25,
        "PROPOSITION": 20,
        "MINI_THEORY": 10,
        "COMPREHENSIVE_THEORY": 3,
        "UNIFIED_MODEL": 2,
    }
    return SynthesisStatisticsResponseSchema(
        overall_stats=overall_stats,
        type_distribution=type_distribution
    )

```
