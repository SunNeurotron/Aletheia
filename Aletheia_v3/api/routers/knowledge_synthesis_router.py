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

```
