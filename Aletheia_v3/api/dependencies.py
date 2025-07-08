from functools import lru_cache
from typing import Any, Dict # Añadido Dict para PlaceholderTaskQueue
from fastapi import Depends # Importar Depends aquí

# Repositorios (Implementaciones en Memoria y SQLAlchemy)
from ..infrastructure.in_memory_repositories import (
    # InMemoryConceptRepository, # Será reemplazado
    # InMemoryRelationshipRepository, # Será reemplazado
    InMemoryAnalysisRepository # Se mantiene por ahora para MDU si no se migra
)
from ..infrastructure.sqlalchemy_repositories import (
    SQLAlchemyConceptRepository,
    SQLAlchemyRelationshipRepository
)
# Puertos de Repositorio (Interfaces)
from ..application.ports import (
    IConceptRepository,
    IRelationshipRepository,
    IAnalysisRepository,
    IExperimentTracker,
    ITaskQueue
)

# Casos de Uso (Clases e Interfaces/Protocolos)
from ..application.use_cases import (
    IngestDocumentUseCase,
    LinkConceptsUseCase,
    ExtractUCMsUseCase,
    FormClustersUseCase,
    DerivePropositionsUseCase, # Nombre actualizado
    MiniTheoryConstructionUseCase,
    ComprehensiveTheoriesUseCase,
    UnifiedModelsUseCase,
    DomainService,
    TheoryBuilder,
    ApplicationServiceFacade
)

# DTOs/Schemas (necesarios para los casos de uso placeholder)
# Estos se importan aquí porque las implementaciones placeholder de los casos de uso los necesitan.
from .schemas import (
    UCMExtractionRequestSchema as UCMExtractionInput, # Alias para compatibilidad con Protocol
    UCMExtractionResponseSchema, ExtractedUCMSchema, ExtractedRelationshipSchema,
    FormClusterInputSchema, FormClusterResultSchema,
    PropositionDerivationInputSchema, PropositionDerivationResultSchema,
    MiniTheoryConstructionInputSchema, MiniTheoryConstructionResultSchema,
    ComprehensiveTheoriesInputSchema, ComprehensiveTheoriesResultSchema,
    UnifiedModelsInputSchema, UnifiedModelsResultSchema
)

# Infraestructura (Trackers, Queues - Implementaciones directas o mocks simples)
class PlaceholderExperimentTracker(IExperimentTracker):
    def start_run(self, name: str) -> str: return "placeholder_run_id"
    def log_params(self, params: dict) -> None: pass
    def log_metrics(self, metrics: dict) -> None: pass
    def end_run(self) -> None: pass

class PlaceholderTaskQueue(ITaskQueue):
    async def enqueue_task(self, task_name: str, params: Dict[str, Any]) -> str: return "placeholder_task_id"
    async def get_task_status(self, task_id: str) -> Dict[str, Any]: return {"status": "PENDING"}


# --- Singletons para Repositorios en Memoria ---
# --- Singletons para Repositorios en Memoria (y ahora SQLAlchemy) ---

# Para SQLAlchemyConceptRepository y SQLAlchemyRelationshipRepository,
# la sesión de BD (db: Session) es inyectada por FastAPI en sus constructores
# porque sus __init__ están definidos con `db: Session = Depends(get_db_session)`.
# Por lo tanto, estas funciones 'get' simplemente necesitan instanciar la clase.
# No se usa @lru_cache aquí porque la instancia del repo depende de la sesión de BD (que es por request).

def get_concept_repository() -> IConceptRepository:
    # SQLAlchemyConceptRepository() será instanciado, y FastAPI inyectará la sesión de BD.
    return SQLAlchemyConceptRepository()

def get_relationship_repository() -> IRelationshipRepository:
    # SQLAlchemyRelationshipRepository() será instanciado, y FastAPI inyectará la sesión de BD.
    return SQLAlchemyRelationshipRepository()

# --- Gestor de Sesión de Base de Datos ---
# Esta función es crucial para inyectar la sesión de BD en los repositorios SQLAlchemy.
# Debe estar definida ANTES de que los repositorios la usen como dependencia.
# Asumimos que esta función ya existe o se definirá en el contexto de la app FastAPI.
# Si no existe, necesitaría ser añadida, típicamente algo así:
# from ..infrastructure.database import SessionLocal
# def get_db_session():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()
# Por ahora, asumiremos que `get_db_session` está disponible globalmente o importado.
# Para el propósito de este refactor, la clave es cómo se usa en get_analysis_repository.

# Importar el repositorio PostgreSQL refactorizado
from ..infrastructure.repositories import PostgreSQLRepository
from sqlalchemy.orm import Session # Necesario para el tipado de db: Session

# Ya no usar @lru_cache(None) porque el repositorio ahora depende de una sesión de BD por request.
def get_analysis_repository(db: Session = Depends(get_db_session)) -> IAnalysisRepository: # db: Session = Depends(...)
    # Devuelve la implementación real de SQLAlchemy que usa la sesión de BD inyectada.
    return PostgreSQLRepository(db=db)


@lru_cache(None)
def get_experiment_tracker() -> IExperimentTracker:
    # TODO: Reemplazar con implementación real (ej. MLflowTracker).
    return PlaceholderExperimentTracker()

@lru_cache(None)
def get_task_queue() -> ITaskQueue:
    # TODO: Reemplazar con implementación real (ej. CeleryTaskQueue).
    return PlaceholderTaskQueue()

# --- Singletons para Servicios de Dominio ---
@lru_cache(None)
def get_theory_builder() -> TheoryBuilder:
    return TheoryBuilder()

@lru_cache(None)
def get_domain_service(theory_builder: TheoryBuilder = Depends(get_theory_builder)) -> DomainService:
    return DomainService(theory_builder=theory_builder)

# --- Funciones de Dependencia para Casos de Uso ---

# Eje X
def get_extract_ucms_use_case(
    concept_repo: IConceptRepository = Depends(get_concept_repository),
    relationship_repo: IRelationshipRepository = Depends(get_relationship_repository)
) -> ExtractUCMsUseCase:
    # Ahora devuelve la implementación real de application.use_cases
    return ExtractUCMsUseCase(concept_repo=concept_repo, relationship_repo=relationship_repo)

def get_ingest_document_use_case(
    concept_repo: IConceptRepository = Depends(get_concept_repository),
    extract_ucms_uc: ExtractUCMsUseCase = Depends(get_extract_ucms_use_case)
) -> IngestDocumentUseCase:
    return IngestDocumentUseCase(concept_repo=concept_repo, extract_ucms_use_case=extract_ucms_uc)

def get_link_concepts_use_case(
    concept_repo: IConceptRepository = Depends(get_concept_repository),
    relationship_repo: IRelationshipRepository = Depends(get_relationship_repository)
) -> LinkConceptsUseCase:
    return LinkConceptsUseCase(concept_repo=concept_repo, relationship_repo=relationship_repo)

# Eje Y (Actualizado para usar implementaciones reales)

def get_form_clusters_use_case(
    concept_repo: IConceptRepository = Depends(get_concept_repository)
) -> FormClustersUseCase:
    return FormClustersUseCase(concept_repo=concept_repo)

def get_derive_propositions_use_case( # Nombre de función actualizado
    concept_repo: IConceptRepository = Depends(get_concept_repository)
) -> DerivePropositionsUseCase: # Tipo de retorno actualizado
    return DerivePropositionsUseCase(concept_repo=concept_repo) # Clase actualizada

def get_mini_theory_construction_use_case(
    concept_repo: IConceptRepository = Depends(get_concept_repository)
) -> MiniTheoryConstructionUseCase:
    return MiniTheoryConstructionUseCase(concept_repo=concept_repo)

def get_comprehensive_theories_use_case(
    concept_repo: IConceptRepository = Depends(get_concept_repository)
) -> ComprehensiveTheoriesUseCase:
    return ComprehensiveTheoriesUseCase(concept_repo=concept_repo)

def get_unified_models_use_case(
    concept_repo: IConceptRepository = Depends(get_concept_repository)
) -> UnifiedModelsUseCase:
    return UnifiedModelsUseCase(concept_repo=concept_repo)

# ApplicationServiceFacade (para los endpoints de MDU existentes)
@lru_cache(None)
def get_application_service_facade(
    domain_service: DomainService = Depends(get_domain_service),
    repo: IAnalysisRepository = Depends(get_analysis_repository),
    tracker: IExperimentTracker = Depends(get_experiment_tracker),
    queue: ITaskQueue = Depends(get_task_queue)
) -> ApplicationServiceFacade:
    return ApplicationServiceFacade(domain_service=domain_service, repo=repo, tracker=tracker, queue=queue)

```
