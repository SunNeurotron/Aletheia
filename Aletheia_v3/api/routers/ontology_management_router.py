from fastapi import APIRouter, Depends, HTTPException, status

# Importar Schemas desde api.schemas
from ..schemas import (
    IngestDocumentRequest, IngestDocumentResponse,
    LinkConceptsRequest, LinkConceptsResponse
)

# Importar Casos de Uso desde application.use_cases
from ...application.use_cases import IngestDocumentUseCase, LinkConceptsUseCase

# Importar dependencias para obtener instancias de casos de uso y seguridad
# Estas rutas son asumidas y pueden necesitar ajuste según la estructura real del proyecto.
from ..dependencies import get_ingest_document_use_case, get_link_concepts_use_case
from ..security import require_roles # Asumiendo que require_roles está en api.security

router = APIRouter(
    prefix="/eje-x",
    tags=["Eje X - Ontology Management"],
    responses={404: {"description": "Not found"}},
)

@router.post(
    "/ingest-document",
    response_model=IngestDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingesta un nuevo documento y extrae sus UCMs.",
    dependencies=[Depends(require_roles(["researcher", "admin"]))], # Ejemplo de roles
)
async def ingest_document_endpoint(
    request_data: IngestDocumentRequest,
    ingest_use_case: IngestDocumentUseCase = Depends(get_ingest_document_use_case),
):
    """
    Endpoint para ingerir un documento.
    - Crea un concepto de tipo DOCUMENT_SOURCE para el documento.
    - Inicia la extracción de Unidades Conceptuales Mínimas (UCMs) del texto.
    - Devuelve el ID del concepto fuente y el resultado de la extracción.
    """
    try:
        # Los DTOs de entrada para los casos de uso ahora son los Schemas de la API
        # gracias a los alias en la importación de use_cases.py, o si los nombres coinciden.
        # Si IngestDocumentUseCase espera IngestDocumentInput y el schema es IngestDocumentRequest,
        # el alias IngestDocumentRequest as IngestDocumentInput en use_cases.py lo maneja.
        # O, si los use_cases se actualizan para usar los schemas de API directamente, no hay problema.
        # Por ahora, asumo que la compatibilidad de tipos está manejada.
        result = await ingest_use_case.execute(request_data) # FastAPI maneja la conversión de JSON a Pydantic model
        return result
    except ValueError as ve: # Por ejemplo, si ExtractUCMsUseCase lanza un error específico
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e: # Captura general para errores inesperados del servidor
        # Loggear el error 'e' en un sistema de logging real
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal server error occurred during document ingestion.")


@router.post(
    "/link-concepts",
    response_model=LinkConceptsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crea una relación dirigida entre dos conceptos existentes.",
    dependencies=[Depends(require_roles(["researcher", "admin"]))], # Ejemplo de roles
)
async def link_concepts_endpoint(
    request_data: LinkConceptsRequest,
    link_use_case: LinkConceptsUseCase = Depends(get_link_concepts_use_case),
):
    """
    Endpoint para vincular dos conceptos científicos.
    - Valida la existencia de los conceptos de origen y destino.
    - Crea y guarda una nueva relación dirigida entre ellos.
    - Devuelve la relación creada.
    """
    try:
        result = await link_use_case.execute(request_data)
        return result
    except ValueError as ve: # Capturado si un concepto no se encuentra
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve)) # 404 es más apropiado para "no encontrado"
    except Exception as e:
        # Loggear el error 'e'
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal server error occurred while linking concepts.")

```
