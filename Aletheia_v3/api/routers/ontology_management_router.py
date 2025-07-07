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
    # TODO: Considerar añadir un GET para el ScientificConcept creado (document_source_id)
    # similar a como se hace en otros routers (ej. /searches/{job_id})
    # devolviendo el objeto completo o una URL para obtenerlo. Por ahora, el ID se devuelve.
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

# --- Endpoints para Listar Conceptos y Relaciones ---
from typing import List # Para el tipo de retorno List[...]
from ..schemas import ScientificConceptSchema, RelationshipSchema # Schemas para los items de la lista
from ...application.ports import IConceptRepository, IRelationshipRepository # Puertos para las dependencias
# get_concept_repository y get_relationship_repository ya están importados de ..dependencies

@router.get(
    "/concepts",
    response_model=List[ScientificConceptSchema],
    summary="Lista todos los conceptos científicos.",
    dependencies=[Depends(require_roles(["researcher", "admin"]))],
)
async def list_all_concepts(
    concept_repo: IConceptRepository = Depends(get_concept_repository),
):
    """
    Endpoint para obtener una lista de todos los conceptos científicos almacenados.
    """
    try:
        concepts_domain = await concept_repo.list_all()
        # No es necesario mapear aquí si los schemas Pydantic pueden construirse desde los objetos de dominio
        # (ej. si tienen los mismos nombres de campo o se usa orm_mode/from_attributes).
        # ScientificConceptSchema tiene Config.orm_mode = True, pero ScientificConcept (dominio) es un dataclass.
        # Por lo tanto, un mapeo explícito o asegurar compatibilidad es necesario.
        # Asumiendo que ScientificConceptSchema puede ser creado desde la entidad de dominio:
        return concepts_domain # FastAPI intentará convertir cada ScientificConcept a ScientificConceptSchema
    except Exception as e:
        # Log e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno listando conceptos.")

@router.get(
    "/relationships",
    response_model=List[RelationshipSchema],
    summary="Lista todas las relaciones dirigidas.",
    dependencies=[Depends(require_roles(["researcher", "admin"]))],
)
async def list_all_relationships(
    relationship_repo: IRelationshipRepository = Depends(get_relationship_repository),
):
    """
    Endpoint para obtener una lista de todas las relaciones dirigidas almacenadas.
    """
    try:
        relationships_domain = await relationship_repo.list_all()
        return relationships_domain # FastAPI intentará convertir cada DirectedRelationship a RelationshipSchema
    except Exception as e:
        # Log e
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno listando relaciones.")

```
