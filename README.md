<div align="center">
<img width="1536" height="1024" alt="Aletheia Platform - AI-Guided Scientific Discovery" src="https://github.com/user-attachments/assets/3f19aa7e-6a92-420b-9935-9f2e22545c24" />
<h1>ALETHEIA v4.0</h1>
<h3>Plataforma Integral de Descubrimiento Científico Asistido por Inteligencia Artificial</h3>
<h4>Un Marco Computacional para la Epistemología Formal y la Síntesis de Conocimiento</h4>
<p>
<a href="Aletheia_v3/LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="Apache 2.0 License"></a>
<a href="#"><img src="https://img.shields.io/badge/Python-3.9+-3776AB?logo=python" alt="Python 3.9+"></a>
<a href="#"><img src="https://img.shields.io/badge/FastAPI-0.103+-009688?logo=fastapi" alt="FastAPI"></a>
<a href="#"><img src="https://img.shields.io/badge/Streamlit-1.27+-FF4B4B?logo=streamlit" alt="Streamlit"></a>
<a href="#"><img src="https://img.shields.io/badge/Docker-24.0+-2496ED?logo=docker" alt="Docker"></a>
<a href="#"><img src="https://img.shields.io/badge/PostgreSQL-15+-336791?logo=postgresql" alt="PostgreSQL"></a>
<a href="#"><img src="https://img.shields.io/badge/MLflow-2.7.1+-0194E2?logo=mlflow" alt="MLflow"></a>
<a href="#"><img src="https://img.shields.io/badge/Research-Active-brightgreen" alt="Active Research"></a>
</p>
</div>
Tabla de Contenidos

Introducción y Fundamentos Teóricos
Arquitectura del Sistema
Módulos del Ecosistema
Fundamentos Matemáticos y Algorítmicos
Visualizaciones y Dashboards
Sistema de Benchmarking y Evaluación
Demostración Práctica Completa
Instalación y Configuración Detallada
API y Endpoints
Testing y Calidad del Código
Publicaciones y Referencias Académicas


1. Introducción y Fundamentos Teóricos
1.1 Visión General
Aletheia representa una plataforma computacional de vanguardia diseñada para abordar los desafíos fundamentales en la investigación científica moderna: la síntesis automatizada de conocimiento, el descubrimiento asistido por inteligencia artificial, y la construcción de modelos teóricos unificados. El sistema implementa un paradigma epistemológico computacional que fusiona técnicas de inteligencia artificial con métodos formales de las ciencias matemáticas.
1.2 Marco Epistemológico: El Paradigma MDU
El núcleo conceptual de Aletheia se basa en el paradigma MDU (Modelado, Descubrimiento, Comprensión), que establece tres dimensiones fundamentales para el proceso de investigación científica computacional:
mermaidgraph TB
    subgraph "CUBO MDU - Marco Epistemológico Tridimensional"
        subgraph "Eje X: MODELADO"
            X1[Ingesta de Conocimiento]
            X2[Extracción de Entidades]
            X3[Construcción Ontológica]
            X4[Formalización Semántica]
            X1 --> X2 --> X3 --> X4
        end

        subgraph "Eje Y: DESCUBRIMIENTO"
            Y1[Generación de Hipótesis]
            Y2[Optimización Bayesiana]
            Y3[Síntesis Teórica]
            Y4[Unificación de Modelos]
            Y1 --> Y2 --> Y3 --> Y4
        end

        subgraph "Eje Z: COMPRENSIÓN"
            Z1[Visualización Interactiva]
            Z2[Explicabilidad de IA]
            Z3[Validación Formal]
            Z4[Interpretación Científica]
            Z1 --> Z2 --> Z3 --> Z4
        end
    end

    X4 -.-> Y1
    Y4 -.-> Z1
    Z4 -.-> X1

    style X1 fill:#ffcdd2
    style Y1 fill:#c8e6c9
    style Z1 fill:#bbdefb
1.3 Motivación Científica: La Conjetura ABC
La plataforma fue inicialmente concebida para abordar uno de los problemas más profundos en teoría de números: la Conjetura ABC, formulada por Joseph Oesterlé y David Masser en 1985. Esta conjetura establece una relación fundamental entre la estructura multiplicativa y aditiva de los números enteros.
Formulación Matemática:
Para cualquier ε > 0, existe una constante K(ε) tal que para toda tripleta de enteros coprimos positivos (a, b, c) con a + b = c, se cumple:
c<K(ε)⋅rad(abc)1+εc < K(\varepsilon) \cdot \text{rad}(abc)^{1+\varepsilon}c<K(ε)⋅rad(abc)1+ε
donde el radical de un entero n se define como:
rad(n)=∏p∣np primop\text{rad}(n) = \prod_{\substack{p|n \\ p \text{ primo}}} prad(n)=p∣np primo​∏​p
1.4 Objetivos del Sistema

Automatización del Descubrimiento Matemático: Implementar algoritmos de búsqueda inteligente para identificar patrones y estructuras en espacios matemáticos complejos.
Síntesis de Conocimiento Jerárquica: Desarrollar un sistema capaz de abstraer conceptos desde unidades mínimas hasta teorías comprehensivas.
Reproducibilidad Computacional: Garantizar que todos los experimentos y descubrimientos sean completamente reproducibles mediante tracking exhaustivo.
Escalabilidad y Distribución: Diseñar una arquitectura que permita el procesamiento distribuido de cálculos computacionalmente intensivos.


2. Arquitectura del Sistema
2.1 Arquitectura de Microservicios
Aletheia implementa una arquitectura de microservicios basada en principios de Domain-Driven Design (DDD) y Clean Architecture:
mermaidflowchart TB
    subgraph "Capa de Presentación"
        UI1[Dashboard ABC Conjecture<br/>Streamlit:8501]
        UI2[Knowledge Graph Explorer<br/>Streamlit:8502]
        UI3[Statistical Analysis UI<br/>Streamlit:8503]
        API1[REST API Gateway<br/>FastAPI:8000]
    end

    subgraph "Capa de Servicios de Aplicación"
        SVC1[Aletheia_v3<br/>Core Engine]
        SVC2[aletheia_stats<br/>Statistical Service]
        SVC3[aletheia_omega<br/>Optimization Service]
        SVC4[Knowledge Synthesis<br/>Pipeline]
    end

    subgraph "Capa de Infraestructura"
        DB[(PostgreSQL<br/>:5432)]
        CACHE[(Redis<br/>:6379)]
        MQ[Celery/RabbitMQ]
        MLF[MLflow Server<br/>:5000]
    end

    subgraph "Capa de Cómputo Distribuido"
        K8S[Kubernetes Cluster]
        WORK1[Celery Worker Pool]
        WORK2[GPU Compute Nodes]
        WORK3[HPC Integration]
    end

    UI1 & UI2 & UI3 --> API1
    API1 --> SVC1 & SVC2 & SVC3
    SVC1 --> SVC4
    SVC1 & SVC2 & SVC3 --> DB & CACHE
    SVC1 --> MQ --> WORK1
    WORK1 --> MLF
    K8S --> WORK1 & WORK2 & WORK3

    style DB fill:#e1f5fe
    style CACHE fill:#fff3e0
    style MLF fill:#f3e5f5
2.2 Patrones Arquitectónicos Implementados
2.2.1 Arquitectura Hexagonal (Ports & Adapters)
Cada módulo sigue estrictamente el patrón de Arquitectura Hexagonal:
mermaidgraph TD
    subgraph "Arquitectura Hexagonal - Módulo Aletheia_v3"
        subgraph "Dominio Central"
            DOM[Domain Models<br/>ScientificConcept<br/>DirectedRelationship]
            DS[Domain Services<br/>TheoryBuilder<br/>MDLOptimizer]
        end

        subgraph "Puertos de Aplicación"
            P1[IConceptRepository]
            P2[IRelationshipRepository]
            P3[IMLflowTracker]
            P4[IMessageQueue]
        end

        subgraph "Adaptadores de Entrada"
            API[FastAPI Controllers]
            CLI[CLI Commands]
            EVT[Event Listeners]
        end

        subgraph "Adaptadores de Salida"
            SQL[SQLAlchemy<br/>PostgreSQL Adapter]
            MLF2[MLflow Adapter]
            CEL[Celery Adapter]
            RED[Redis Adapter]
        end

        API --> P1 & P2
        CLI --> P1 & P2
        EVT --> P3 & P4

        P1 & P2 --> DOM & DS
        DOM & DS --> P3 & P4

        SQL -.-> P1 & P2
        MLF2 -.-> P3
        CEL & RED -.-> P4
    end
2.2.2 Event-Driven Architecture (EDA)
El sistema implementa un modelo de eventos para la comunicación asíncrona entre servicios:
python# Ejemplo de definición de eventos
@dataclass
class ConceptCreatedEvent(DomainEvent):
    concept_id: UUID
    concept_type: ConceptType
    created_by: str
    timestamp: datetime

@dataclass
class SynthesisCompletedEvent(DomainEvent):
    synthesis_id: UUID
    level: SynthesisLevel
    input_concepts: List[UUID]
    result_concept: UUID
2.3 Flujo de Datos del Sistema
mermaidsequenceDiagram
    participant User as Usuario/Investigador
    participant API as API Gateway
    participant Auth as Auth Service
    participant Core as Aletheia Core
    participant Queue as Message Queue
    participant Worker as Compute Worker
    participant ML as MLflow
    participant DB as PostgreSQL
    participant Cache as Redis

    User->>+API: POST /eje-x/ingest-document
    API->>+Auth: Validate JWT Token
    Auth-->>-API: User Authorized

    API->>+Core: IngestDocumentUseCase.execute()
    Core->>+DB: Store Document Concept
    DB-->>-Core: Document ID

    Core->>+Queue: Enqueue UCM Extraction Task
    Queue-->>-Core: Task ID
    Core-->>-API: Response with Task ID
    API-->>-User: 202 Accepted

    Queue->>+Worker: Process UCM Extraction
    Worker->>+Core: ExtractUCMsUseCase.execute()
    Core->>DB: Store UCMs & Relations
    Core->>+ML: Log Extraction Metrics
    ML-->>-Core: Run ID

    Worker->>Cache: Update Progress
    Worker-->>-Queue: Task Complete

    User->>API: GET /tasks/{task_id}/status
    API->>Cache: Check Progress
    Cache-->>API: Task Status
    API-->>User: Task Complete + Results

3. Módulos del Ecosistema
3.1 Aletheia_v3 - Motor Principal
El módulo central que implementa la lógica de negocio principal y coordina todos los demás componentes.
3.1.1 Estructura del Módulo
Aletheia_v3/
├── api/                          # Capa de Presentación
│   ├── routers/                  # Endpoints organizados por dominio
│   │   ├── auth_router.py        # Autenticación y autorización
│   │   ├── ontology_management_router.py  # Eje X
│   │   ├── knowledge_synthesis_router.py  # Eje Y
│   │   └── mdu_analysis_router.py        # Análisis MDU
│   ├── schemas.py                # DTOs y contratos de API
│   └── dependencies.py           # Inyección de dependencias
├── application/                  # Capa de Aplicación
│   ├── use_cases.py             # Casos de uso principales
│   ├── mdl_synthesis_use_cases.py  # MDL optimization
│   └── ports.py                 # Interfaces (puertos)
├── core/                        # Dominio
│   ├── domain_models.py         # Entidades del dominio
│   ├── domain_services.py       # Servicios de dominio
│   ├── mdl_synthesis/           # Motor MDL
│   └── custom_acquisitions.py   # Heurísticas personalizadas
├── infrastructure/              # Adaptadores
│   ├── models.py               # Modelos de BD (SQLAlchemy)
│   ├── sqlalchemy_repositories.py
│   ├── celery_worker.py        # Configuración de workers
│   └── mlflow_tracker.py       # Integración MLflow
└── dashboard/                   # Interfaces de usuario
    ├── dashboard.py             # Dashboard ABC
    └── mdu_dashboard.py         # Explorer de grafos
3.1.2 Casos de Uso Principales
python# Ejemplo de caso de uso con documentación completa
class IngestDocumentUseCase:
    """
    Caso de uso para la ingesta de documentos científicos.

    Este caso de uso implementa el primer paso del Eje X (Modelado),
    procesando texto no estructurado y convirtiéndolo en conceptos
    formalizados dentro del grafo de conocimiento.

    Proceso:
    1. Validación del documento de entrada
    2. Creación del concepto DOCUMENT_SOURCE
    3. Persistencia en el repositorio
    4. Disparar extracción asíncrona de UCMs

    Referencias:
    - Baeza-Yates, R., & Ribeiro-Neto, B. (2011). Modern Information Retrieval.
    - Manning, C. D., Raghavan, P., & Schütze, H. (2008). Introduction to Information Retrieval.
    """

    def __init__(
        self,
        concept_repository: IConceptRepository,
        relationship_repository: IRelationshipRepository,
        message_queue: IMessageQueue,
        current_user_id: str
    ):
        self.concept_repo = concept_repository
        self.relationship_repo = relationship_repository
        self.queue = message_queue
        self.user_id = current_user_id

    async def execute(self, request: IngestDocumentRequest) -> IngestDocumentResponse:
        # Implementación detallada...
3.2 aletheia_stats - Servicio de Análisis Estadístico
Módulo especializado en análisis estadístico riguroso con trazabilidad completa.
3.2.1 Capacidades Estadísticas
pythonclass StatsService:
    """
    Servicio de dominio para análisis estadístico.

    Implementa pruebas de hipótesis con validaciones rigurosas:
    - Prueba de normalidad Shapiro-Wilk
    - Prueba t de Welch para muestras independientes
    - Intervalos de confianza bootstrap
    - Corrección de comparaciones múltiples (Bonferroni, FDR)
    """

    def perform_ttest_analysis(
        self,
        group_a: np.ndarray,
        group_b: np.ndarray,
        alpha: float = 0.05,
        alternative: str = 'two-sided'
    ) -> TTestResult:
        """
        Realiza prueba t con validaciones completas.

        Matemáticamente:
        H₀: μ₁ = μ₂
        H₁: μ₁ ≠ μ₂ (two-sided)

        Estadístico t de Welch:
        t = (x̄₁ - x̄₂) / √(s₁²/n₁ + s₂²/n₂)

        Grados de libertad (Welch-Satterthwaite):
        df = (s₁²/n₁ + s₂²/n₂)² / ((s₁²/n₁)²/(n₁-1) + (s₂²/n₂)²/(n₂-1))
        """
3.2.2 Pipeline de Análisis
mermaidgraph LR
    subgraph "Pipeline de Análisis Estadístico"
        A[Datos de Entrada] --> B{Validación}
        B -->|Válido| C[Prueba Normalidad]
        B -->|Inválido| ERR[Error Response]

        C --> D{¿Normal?}
        D -->|Sí| E[Prueba t Student]
        D -->|No| F[Prueba t Welch]

        E --> G[Cálculo IC]
        F --> G

        G --> H[Cálculo Tamaño Efecto]
        H --> I[Logging MLflow]
        I --> J[Persistencia BD]
        J --> K[Response]
    end
3.3 aletheia_omega - Servicio de Optimización MDL
Implementa optimización basada en el principio de Longitud Mínima de Descripción (MDL).
3.3.1 Fundamento Teórico MDL
El principio MDL establece que el mejor modelo M para unos datos D es aquel que minimiza:
L(M)+L(D∣M)L(M) + L(D|M)L(M)+L(D∣M)
donde:

L(M) es la longitud de descripción del modelo
L(D|M) es la longitud de descripción de los datos dado el modelo

3.3.2 Implementación
pythonclass OmegaCostService:
    """
    Servicio para cálculo de costo MDL.

    Implementa la función objetivo:
    MDL(M, D) = λ·K(M) - L(D|M)

    donde:
    - K(M) es la complejidad de Kolmogorov (aproximada)
    - L(D|M) es la log-verosimilitud
    - λ es el parámetro de regularización
    """

    def calculate_mdl_cost(
        self,
        model: ModelRepresentation,
        data: Any,
        likelihood: float,
        lambda_param: float = 1.0
    ) -> float:
        complexity = self._approximate_kolmogorov_complexity(model)
        return lambda_param * complexity - likelihood
3.4 aletheia_common - Biblioteca Compartida
Componentes reutilizables para todo el ecosistema:
aletheia_common/
├── auth/                    # Sistema de autenticación JWT
│   ├── jwt_handler.py      # Manejo de tokens
│   ├── models.py           # ResearcherDB compartido
│   └── schemas.py          # DTOs de autenticación
├── db/                     # Utilidades de base de datos
│   ├── base.py            # Base declarativa SQLAlchemy
│   └── custom_types.py    # Tipos personalizados (UUID)
├── mlflow_utils/          # Helpers para MLflow
└── schemas/               # Esquemas Pydantic comunes

4. Fundamentos Matemáticos y Algorítmicos
4.1 Motor de Búsqueda ABC
4.1.1 Optimización Bayesiana con Heurísticas Estructurales
El sistema implementa una función de adquisición personalizada que combina Expected Improvement (EI) con bonificaciones estructurales:
pythondef custom_acquisition_function(x: np.ndarray, gp: GaussianProcessRegressor) -> float:
    """
    Función de adquisición híbrida para búsqueda ABC.

    A(x) = EI(x) + B(x)

    donde B(x) es el bonus estructural que favorece números
    con propiedades aritméticas especiales.
    """
    ei = expected_improvement(x, gp)
    structural_bonus = get_structural_bonus(
        int(x[0]), int(x[1]), int(x[2]),
        bonus_scale_factor=0.1,
        proximity_penalty_factor=0.5
    )
    return ei + structural_bonus
4.1.2 Integración PARI/GP
Para cálculos de alta precisión:
pythonfrom cypari2 import Pari

pari = Pari()

def _radical_pari(n: int) -> int:
    """
    Calcula el radical usando PARI/GP para eficiencia.

    Complejidad: O(√n) para factorización
    """
    if n <= 1:
        return n

    # Factorización rápida con PARI
    factors = pari.factor(n)
    primes = [int(p) for p in factors[0]]

    # Producto de primos únicos
    return reduce(operator.mul, primes, 1)
4.2 Síntesis de Conocimiento Jerárquica
4.2.1 Extracción de UCMs (Unidades Conceptuales Mínimas)
pythonclass UCMExtractor:
    """
    Extractor de Unidades Conceptuales Mínimas.

    Implementa técnicas de NLP para identificar conceptos atómicos:
    - Tokenización avanzada
    - Análisis morfológico
    - Detección de entidades nombradas
    - Desambiguación semántica
    """

    def extract(self, text: str) -> List[UCM]:
        # Pipeline NLP
        tokens = self.tokenizer.tokenize(text)
        pos_tags = self.pos_tagger.tag(tokens)
        entities = self.ner.extract_entities(pos_tags)

        # Filtrado y normalización
        ucms = []
        for entity in entities:
            if self._is_scientific_concept(entity):
                ucm = self._normalize_concept(entity)
                ucms.append(ucm)

        return ucms
4.2.2 Clustering Jerárquico con MDL
pythonclass MDLClusteringService:
    """
    Servicio de clustering basado en MDL.

    Encuentra la partición óptima que minimiza:
    MDL(C) = L(C) + Σᵢ L(Dᵢ|Cᵢ)

    donde C es el conjunto de clusters y Dᵢ los datos en el cluster i.
    """

    def find_optimal_clustering(
        self,
        concepts: List[ScientificConcept],
        max_clusters: int = 20
    ) -> ClusteringResult:
        best_mdl = float('inf')
        best_clustering = None

        for k in range(2, max_clusters + 1):
            clustering = self._perform_clustering(concepts, k)
            mdl_cost = self._calculate_clustering_mdl(clustering)

            if mdl_cost < best_mdl:
                best_mdl = mdl_cost
                best_clustering = clustering

        return best_clustering
4.3 Métricas de Evaluación
4.3.1 Calidad de Tripletas ABC
pythondef abc_quality_metric(a: int, b: int, c: int) -> float:
    """
    Métrica de calidad para tripletas ABC.

    Q(a,b,c) = log(c) / log(rad(abc))

    Valores más altos indican tripletas más "interesantes"
    desde la perspectiva de la conjetura.
    """
    if a <= 0 or b <= 0 or gcd(a, b) != 1 or a + b != c:
        return 0.0

    rad_abc = _radical(a) * _radical(b) * _radical(c)
    return math.log(c) / math.log(rad_abc)

5. Visualizaciones y Dashboards
5.1 Dashboard de Exploración ABC
5.1.1 Visualización 3D de Tripletas
pythondef create_3d_scatter_plot(hits: List[ABCHit]) -> go.Figure:
    """
    Crea visualización 3D interactiva de tripletas ABC.

    - Ejes: valores de a, b, c
    - Color: calidad de la tripleta
    - Tamaño: rad(abc)
    """
    fig = go.Figure(data=[go.Scatter3d(
        x=[hit.a for hit in hits],
        y=[hit.b for hit in hits],
        z=[hit.c for hit in hits],
        mode='markers',
        marker=dict(
            size=[math.log(hit.rad_abc) for hit in hits],
            color=[hit.quality for hit in hits],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Calidad ABC")
        ),
        text=[f"({h.a}, {h.b}, {h.c})<br>Q={h.quality:.3f}"
              for h in hits],
        hoverinfo='text'
    )])

    fig.update_layout(
        title="Espacio de Búsqueda ABC - Visualización 3D",
        scene=dict(
            xaxis_title="a",
            yaxis_title="b",
            zaxis_title="c"
        )
    )
    return fig
5.1.2 Análisis de Convergencia
pythondef plot_optimization_convergence(trajectory: List[OptimizationPoint]) -> go.Figure:
    """
    Visualiza la convergencia del algoritmo de optimización.

    Muestra:
    - Mejor valor encontrado vs iteración
    - Región de confianza del GP
    - Puntos de exploración vs explotación
    """
    iterations = [p.iteration for p in trajectory]
    best_values = [p.best_value for p in trajectory]
    current_values = [p.current_value for p in trajectory]

    fig = go.Figure()

    # Mejor valor acumulado
    fig.add_trace(go.Scatter(
        x=iterations,
        y=best_values,
        mode='lines',
        name='Mejor valor',
        line=dict(color='blue', width=3)
    ))

    # Valores evaluados
    fig.add_trace(go.Scatter(
        x=iterations,
        y=current_values,
        mode='markers',
        name='Evaluaciones',
        marker=dict(
            color=['red' if p.is_exploration else 'green'
                   for p in trajectory],
            size=8
        )
    ))

    return fig
5.2 Dashboard del Grafo de Conocimiento
5.2.1 Visualización Interactiva del Grafo
pythondef create_knowledge_graph_visualization(
    concepts: List[ScientificConcept],
    relationships: List[DirectedRelationship]
) -> nx.DiGraph:
    """
    Crea visualización interactiva del grafo de conocimiento.

    Características:
    - Layout jerárquico por niveles de síntesis
    - Colores por tipo de concepto
    - Grosor de aristas por fuerza de relación
    - Tooltips con información detallada
    """
    G = nx.DiGraph()

    # Añadir nodos con atributos
    for concept in concepts:
        G.add_node(
            concept.id,
            label=concept.name,
            type=concept.concept_type.value,
            level=_get_synthesis_level(concept),
            properties=concept.properties
        )

    # Añadir aristas con pesos
    for rel in relationships:
        G.add_edge(
            rel.source_id,
            rel.target_id,
            type=rel.relationship_type,
            weight=rel.properties.get('strength', 1.0)
        )

    # Layout jerárquico
    pos = nx.multipartite_layout(G, subset_key='level')

    return G, pos
5.2.2 Análisis de Centralidad y Comunidades
pythondef analyze_graph_structure(G: nx.DiGraph) -> GraphAnalysisResult:
    """
    Análisis estructural del grafo de conocimiento.

    Calcula:
    - Centralidad de intermediación (betweenness)
    - PageRank de conceptos
    - Detección de comunidades (Louvain)
    - Métricas de cohesión
    """
    # Centralidad
    betweenness = nx.betweenness_centrality(G)
    pagerank = nx.pagerank(G)

    # Comunidades
    communities = community.louvain_communities(G.to_undirected())

    # Métricas globales
    density = nx.density(G)
    avg_clustering = nx.average_clustering(G.to_undirected())

    return GraphAnalysisResult(
        betweenness_centrality=betweenness,
        pagerank_scores=pagerank,
        communities=communities,
        density=density,
        clustering_coefficient=avg_clustering
    )
5.3 Dashboard de Análisis Estadístico
5.3.1 Visualización de Resultados de Pruebas
pythondef create_statistical_test_visualization(
    resultReintentarJContinuarEditarpythondef create_statistical_test_visualization(
   result: TTestResult,
   group_a_data: np.ndarray,
   group_b_data: np.ndarray
) -> go.Figure:
   """
   Visualización comprehensiva de resultados de prueba t.

   Incluye:
   - Distribuciones de ambos grupos
   - Intervalos de confianza
   - Tamaño del efecto (Cohen's d)
   - Potencia estadística
   """
   fig = make_subplots(
       rows=2, cols=2,
       subplot_titles=(
           'Distribuciones de Grupos',
           'Comparación de Medias con IC',
           'Q-Q Plot de Normalidad',
           'Análisis de Potencia'
       )
   )

   # 1. Distribuciones con KDE
   x_range = np.linspace(
       min(group_a_data.min(), group_b_data.min()),
       max(group_a_data.max(), group_b_data.max()),
       100
   )

   kde_a = gaussian_kde(group_a_data)
   kde_b = gaussian_kde(group_b_data)

   fig.add_trace(
       go.Scatter(
           x=x_range,
           y=kde_a(x_range),
           name='Grupo A',
           fill='tozeroy',
           opacity=0.6
       ),
       row=1, col=1
   )

   fig.add_trace(
       go.Scatter(
           x=x_range,
           y=kde_b(x_range),
           name='Grupo B',
           fill='tozeroy',
           opacity=0.6
       ),
       row=1, col=1
   )

   # 2. Intervalos de confianza
   fig.add_trace(
       go.Bar(
           x=['Grupo A', 'Grupo B'],
           y=[result.mean_a, result.mean_b],
           error_y=dict(
               type='data',
               symmetric=False,
               array=[result.ci_upper_a - result.mean_a,
                      result.ci_upper_b - result.mean_b],
               arrayminus=[result.mean_a - result.ci_lower_a,
                          result.mean_b - result.ci_lower_b]
           ),
           name='Media ± IC 95%'
       ),
       row=1, col=2
   )

   # 3. Q-Q plots para normalidad
   qq_a = stats.probplot(group_a_data, dist="norm")
   qq_b = stats.probplot(group_b_data, dist="norm")

   fig.add_trace(
       go.Scatter(
           x=qq_a[0][0],
           y=qq_a[0][1],
           mode='markers',
           name='Grupo A',
           marker=dict(size=5)
       ),
       row=2, col=1
   )

   # 4. Curva de potencia
   effect_sizes = np.linspace(0, 2, 50)
   powers = [
       sm.stats.tt_ind_solve_power(
           effect_size=es,
           nobs1=len(group_a_data),
           alpha=0.05,
           ratio=len(group_b_data)/len(group_a_data)
       )
       for es in effect_sizes
   ]

   fig.add_trace(
       go.Scatter(
           x=effect_sizes,
           y=powers,
           mode='lines',
           name='Potencia'
       ),
       row=2, col=2
   )

   # Añadir línea vertical para el efecto observado
   fig.add_vline(
       x=result.cohens_d,
       row=2, col=2,
       line_dash="dash",
       annotation_text=f"d={result.cohens_d:.2f}"
   )

   fig.update_layout(
       title=f"Análisis Estadístico Completo - p={result.p_value:.4f}",
       height=800
   )

   return fig
5.4 Métricas de Rendimiento en Tiempo Real
5.4.1 Dashboard de Monitoreo del Sistema
pythonclass SystemMetricsDashboard:
    """
    Dashboard de monitoreo en tiempo real usando Prometheus + Grafana.
    """

    def __init__(self):
        self.metrics_collector = PrometheusMetricsCollector()
        self.alert_manager = AlertManager()

    def create_performance_dashboard(self) -> Dict[str, Any]:
        """
        Crea dashboard con métricas clave del sistema.
        """
        return {
            "panels": [
                {
                    "title": "Throughput de Procesamiento",
                    "type": "graph",
                    "targets": [
                        {
                            "expr": "rate(aletheia_concepts_processed_total[5m])",
                            "legendFormat": "Conceptos/seg"
                        }
                    ]
                },
                {
                    "title": "Latencia de API (p95)",
                    "type": "graph",
                    "targets": [
                        {
                            "expr": "histogram_quantile(0.95, aletheia_api_latency_bucket)",
                            "legendFormat": "p95 latency"
                        }
                    ]
                },
                {
                    "title": "Utilización de Workers",
                    "type": "heatmap",
                    "targets": [
                        {
                            "expr": "aletheia_worker_cpu_usage",
                            "legendFormat": "Worker {{worker_id}}"
                        }
                    ]
                },
                {
                    "title": "Cola de Tareas",
                    "type": "gauge",
                    "targets": [
                        {
                            "expr": "aletheia_celery_queue_length",
                            "legendFormat": "Tareas pendientes"
                        }
                    ]
                }
            ]
        }

6. Sistema de Benchmarking y Evaluación
6.1 Framework de Benchmarking
6.1.1 Benchmarks de Rendimiento Computacional
pythonclass ComputationalBenchmark:
    """
    Suite de benchmarks para evaluar rendimiento del sistema.
    """

    def __init__(self):
        self.results = BenchmarkResults()

    def run_all_benchmarks(self) -> BenchmarkResults:
        """
        Ejecuta suite completa de benchmarks.
        """
        benchmarks = [
            ("Radical Computation", self.benchmark_radical_computation),
            ("UCM Extraction", self.benchmark_ucm_extraction),
            ("Graph Traversal", self.benchmark_graph_operations),
            ("MDL Optimization", self.benchmark_mdl_optimization),
            ("Database Operations", self.benchmark_db_performance)
        ]

        for name, benchmark_func in benchmarks:
            print(f"Ejecutando benchmark: {name}")
            result = benchmark_func()
            self.results.add_result(name, result)

        return self.results

    def benchmark_radical_computation(self) -> BenchmarkResult:
        """
        Benchmark para cálculo de radicales con PARI/GP.
        """
        test_numbers = [
            10**6, 10**9, 10**12, 10**15,  # Diferentes órdenes de magnitud
            math.factorial(20),              # Números con muchos factores
            2**127 - 1,                     # Primo de Mersenne
        ]

        results = []
        for n in test_numbers:
            start_time = time.perf_counter()
            rad = _radical(n)
            end_time = time.perf_counter()

            results.append({
                'input_size': n.bit_length(),
                'execution_time': end_time - start_time,
                'result': rad
            })

        return BenchmarkResult(
            name="Radical Computation",
            results=results,
            summary_stats=self._calculate_summary_stats(results)
        )
6.1.2 Benchmarks de Calidad Científica
pythonclass ScientificQualityBenchmark:
    """
    Evalúa la calidad científica de los resultados generados.
    """

    def evaluate_synthesis_quality(
        self,
        synthesized_concepts: List[ScientificConcept],
        ground_truth: Optional[List[ScientificConcept]] = None
    ) -> QualityMetrics:
        """
        Evalúa la calidad de la síntesis de conocimiento.

        Métricas:
        - Coherencia semántica
        - Completitud
        - Novedad
        - Validez lógica
        """
        metrics = QualityMetrics()

        # Coherencia semántica
        coherence = self._calculate_semantic_coherence(synthesized_concepts)
        metrics.add_metric("semantic_coherence", coherence)

        # Completitud (si hay ground truth)
        if ground_truth:
            completeness = self._calculate_completeness(
                synthesized_concepts, ground_truth
            )
            metrics.add_metric("completeness", completeness)

        # Novedad
        novelty = self._calculate_novelty_score(synthesized_concepts)
        metrics.add_metric("novelty", novelty)

        # Validez lógica
        validity = self._check_logical_validity(synthesized_concepts)
        metrics.add_metric("logical_validity", validity)

        return metrics

    def _calculate_semantic_coherence(
        self,
        concepts: List[ScientificConcept]
    ) -> float:
        """
        Calcula coherencia usando embeddings y similitud coseno.
        """
        if len(concepts) < 2:
            return 1.0

        embeddings = [self._get_embedding(c) for c in concepts]

        # Matriz de similitud
        similarity_matrix = cosine_similarity(embeddings)

        # Coherencia promedio (excluyendo diagonal)
        n = len(concepts)
        total_similarity = (similarity_matrix.sum() - n) / (n * (n - 1))

        return total_similarity
6.2 Evaluación Comparativa
6.2.1 Comparación con Baselines
pythonclass BaselineComparison:
    """
    Compara rendimiento contra métodos baseline.
    """

    def compare_abc_search_methods(self) -> ComparisonResults:
        """
        Compara diferentes métodos de búsqueda ABC.
        """
        methods = {
            "random_search": RandomABCSearch(),
            "grid_search": GridABCSearch(),
            "genetic_algorithm": GeneticABCSearch(),
            "bayesian_optimization": BayesianABCSearch(),
            "aletheia_custom": AletheiaABCSearch()
        }

        # Parámetros de evaluación
        search_space = ABCSearchSpace(
            a_range=(1, 10**6),
            b_range=(1, 10**6),
            time_limit=3600  # 1 hora
        )

        results = {}
        for method_name, method in methods.items():
            print(f"Evaluando método: {method_name}")

            start_time = time.time()
            best_triples = method.search(search_space)
            end_time = time.time()

            results[method_name] = {
                'best_quality': max(t.quality for t in best_triples),
                'num_triples_found': len(best_triples),
                'execution_time': end_time - start_time,
                'efficiency': len(best_triples) / (end_time - start_time)
            }

        return ComparisonResults(results)

7. Demostración Práctica Completa
7.1 Escenario de Demostración End-to-End
7.1.1 Preparación del Entorno
bash# 1. Clonar el repositorio
git clone https://github.com/SunNeurotron/Aletheia.git
cd Aletheia

# 2. Configurar variables de entorno
cp Aletheia_v3/.env.example Aletheia_v3/.env
# Editar .env con configuraciones apropiadas

# 3. Construir e iniciar servicios
cd Aletheia_v3
docker-compose up --build -d

# 4. Verificar que todos los servicios estén activos
docker-compose ps

# 5. Aplicar migraciones de base de datos (automático con docker-compose)
# Las migraciones se aplican automáticamente al iniciar
7.1.2 Demo 1: Búsqueda de Tripletas ABC
python# demo_abc_search.py
import asyncio
import httpx
from datetime import datetime

async def demo_abc_search():
    """
    Demostración completa de búsqueda ABC.
    """
    base_url = "http://localhost:8000"

    async with httpx.AsyncClient() as client:
        # 1. Autenticación
        print("1. Autenticando usuario...")
        auth_response = await client.post(
            f"{base_url}/token",
            data={
                "username": "demo_researcher",
                "password": "demo_password"
            }
        )
        token = auth_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Crear nuevo job de búsqueda
        print("\n2. Iniciando búsqueda ABC...")
        search_params = {
            "search_space": {
                "a_min": 1,
                "a_max": 10000,
                "b_min": 1,
                "b_max": 10000
            },
            "optimization_params": {
                "n_calls": 100,
                "n_initial_points": 20,
                "acq_func": "custom_ei_with_bonus"
            },
            "quality_threshold": 1.4
        }

        job_response = await client.post(
            f"{base_url}/api/abc/search",
            json=search_params,
            headers=headers
        )
        job_id = job_response.json()["job_id"]

        # 3. Monitorear progreso
        print(f"\n3. Monitoreando job {job_id}...")
        while True:
            status_response = await client.get(
                f"{base_url}/api/jobs/{job_id}",
                headers=headers
            )
            status = status_response.json()

            print(f"   Estado: {status['status']}, "
                  f"Progreso: {status['progress']}%, "
                  f"Mejores tripletas encontradas: {status['best_triples_count']}")

            if status['status'] in ['completed', 'failed']:
                break

            await asyncio.sleep(5)

        # 4. Obtener resultados
        print("\n4. Recuperando resultados...")
        results_response = await client.get(
            f"{base_url}/api/abc/results/{job_id}",
            headers=headers
        )
        results = results_response.json()

        # 5. Mostrar mejores tripletas
        print("\n5. Mejores tripletas encontradas:")
        for i, triple in enumerate(results['best_triples'][:10]):
            print(f"   {i+1}. ({triple['a']}, {triple['b']}, {triple['c']}) "
                  f"- Calidad: {triple['quality']:.4f}")

        # 6. Visualizar en dashboard
        print(f"\n6. Visualización disponible en: http://localhost:8501")

        return results

# Ejecutar demo
if __name__ == "__main__":
    asyncio.run(demo_abc_search())
7.1.3 Demo 2: Síntesis de Conocimiento
python# demo_knowledge_synthesis.py
async def demo_knowledge_synthesis():
    """
    Demostración del pipeline completo de síntesis de conocimiento.
    """
    # 1. Ingesta de documento
    print("1. Ingiriendo documento científico...")
    document_text = """
    The ABC conjecture is one of the most important open problems in number theory.
    It relates the prime factorization of integers to their additive properties.
    Recent computational approaches have found interesting examples of ABC triples
    with high quality metrics, suggesting patterns in their distribution.
    """

    ingest_response = await client.post(
        f"{base_url}/api/eje-x/ingest-document",
        json={
            "title": "ABC Conjecture Computational Approaches",
            "content": document_text,
            "metadata": {
                "author": "Demo Author",
                "year": 2024,
                "domain": "Number Theory"
            }
        },
        headers=headers
    )
    document_id = ingest_response.json()["document_id"]

    # 2. Esperar extracción de UCMs
    print("\n2. Esperando extracción de UCMs...")
    await asyncio.sleep(10)

    # 3. Obtener UCMs extraídas
    ucms_response = await client.get(
        f"{base_url}/api/eje-x/concepts?concept_type=UCM&limit=50",
        headers=headers
    )
    ucms = ucms_response.json()["concepts"]
    print(f"   UCMs extraídas: {len(ucms)}")

    # 4. Formar clusters
    print("\n3. Formando clusters de conceptos...")
    cluster_response = await client.post(
        f"{base_url}/api/eje-y/cluster-formation",
        json={
            "ucm_ids": [ucm["id"] for ucm in ucms],
            "clustering_params": {
                "method": "mdl_hierarchical",
                "max_clusters": 5
            }
        },
        headers=headers
    )
    clusters = cluster_response.json()["clusters"]

    # 5. Derivar proposiciones
    print("\n4. Derivando proposiciones...")
    propositions = []
    for cluster in clusters:
        prop_response = await client.post(
            f"{base_url}/api/eje-y/derive-propositions",
            json={
                "cluster_id": cluster["id"],
                "generation_params": {
                    "method": "mdl_optimization",
                    "num_candidates": 10
                }
            },
            headers=headers
        )
        propositions.extend(prop_response.json()["propositions"])

    # 6. Construir mini-teorías
    print("\n5. Construyendo mini-teorías...")
    theory_response = await client.post(
        f"{base_url}/api/eje-y/mini-theory-construction",
        json={
            "proposition_ids": [p["id"] for p in propositions],
            "synthesis_params": {
                "coherence_threshold": 0.7,
                "min_propositions": 2
            }
        },
        headers=headers
    )
    mini_theories = theory_response.json()["mini_theories"]

    # 7. Visualizar grafo de conocimiento
    print(f"\n6. Grafo de conocimiento disponible en: http://localhost:8502")

    # 8. Mostrar jerarquía sintetizada
    print("\n7. Jerarquía de síntesis:")
    print(f"   Documento → {len(ucms)} UCMs")
    print(f"   UCMs → {len(clusters)} Clusters")
    print(f"   Clusters → {len(propositions)} Proposiciones")
    print(f"   Proposiciones → {len(mini_theories)} Mini-teorías")

    return {
        "document_id": document_id,
        "synthesis_hierarchy": {
            "ucms": len(ucms),
            "clusters": len(clusters),
            "propositions": len(propositions),
            "mini_theories": len(mini_theories)
        }
    }
7.1.4 Demo 3: Análisis Estadístico con Trazabilidad
python# demo_statistical_analysis.py
async def demo_statistical_analysis():
    """
    Demostración de análisis estadístico con MLflow.
    """
    # Conectar al servicio de estadísticas
    stats_url = "http://localhost:8001"  # Puerto de aletheia_stats

    # 1. Generar datos sintéticos
    print("1. Generando datos experimentales...")
    np.random.seed(42)

    # Grupo control: distribución normal
    control_group = np.random.normal(100, 15, 50)

    # Grupo tratamiento: distribución normal con efecto
    treatment_group = np.random.normal(110, 15, 50)

    # 2. Realizar análisis
    print("\n2. Ejecutando prueba t...")
    analysis_response = await client.post(
        f"{stats_url}/api/v1/analyze/ttest",
        json={
            "experiment_name": "Demo Drug Efficacy Study",
            "group_a_data": control_group.tolist(),
            "group_b_data": treatment_group.tolist(),
            "group_a_name": "Control",
            "group_b_name": "Treatment",
            "alpha": 0.05,
            "metadata": {
                "study_type": "randomized_controlled_trial",
                "domain": "pharmacology",
                "date": datetime.now().isoformat()
            }
        },
        headers=headers
    )

    results = analysis_response.json()

    # 3. Mostrar resultados
    print("\n3. Resultados del análisis:")
    print(f"   Estadístico t: {results['t_statistic']:.4f}")
    print(f"   Valor p: {results['p_value']:.4f}")
    print(f"   Tamaño del efecto (d de Cohen): {results['cohens_d']:.4f}")
    print(f"   Intervalo de confianza: [{results['ci_lower']:.2f}, {results['ci_upper']:.2f}]")

    # 4. Verificar registro en MLflow
    print(f"\n4. Experimento registrado en MLflow:")
    print(f"   Run ID: {results['mlflow_run_id']}")
    print(f"   Ver en: http://localhost:5000/#/experiments/{results['mlflow_experiment_id']}")

    # 5. Análisis de potencia post-hoc
    print("\n5. Realizando análisis de potencia...")
    power_response = await client.post(
        f"{stats_url}/api/v1/analyze/power",
        json={
            "effect_size": results['cohens_d'],
            "sample_size": 50,
            "alpha": 0.05,
            "test_type": "two_sample_ttest"
        },
        headers=headers
    )

    power_results = power_response.json()
    print(f"   Potencia estadística: {power_results['power']:.2%}")

    return results
7.2 Resultados Esperados de la Demostración
7.2.1 Métricas de Rendimiento
yamlBenchmarks de Rendimiento:
  Cálculo de Radicales:
    - Números < 10^6: < 1ms
    - Números < 10^12: < 10ms
    - Números < 10^18: < 100ms

  Extracción de UCMs:
    - Throughput: > 1000 tokens/segundo
    - Precisión: > 85%
    - Recall: > 80%

  Operaciones de Grafo:
    - Inserción de nodos: < 5ms
    - Búsqueda BFS/DFS: O(V+E)
    - Cálculo de centralidad: < 1s para grafos < 10k nodos

  API Latency (p95):
    - Endpoints de lectura: < 100ms
    - Endpoints de escritura: < 200ms
    - Análisis complejos: < 5s
7.2.2 Calidad Científica
yamlMétricas de Calidad:
  Síntesis de Conocimiento:
    - Coherencia semántica: > 0.75
    - Completitud: > 0.70
    - Validez lógica: 100%

  Búsqueda ABC:
    - Tripletas de calidad > 1.4: > 50 en 1 hora
    - Mejora vs búsqueda aleatoria: > 10x
    - Convergencia: < 500 evaluaciones

  Análisis Estadístico:
    - Error Tipo I controlado: α = 0.05
    - Potencia para d=0.8: > 0.80
    - Cobertura de IC: 95% ± 1%

8. Instalación y Configuración Detallada
8.1 Requisitos del Sistema
yamlHardware Mínimo:
  CPU: 4 cores @ 2.4GHz
  RAM: 16GB
  Almacenamiento: 50GB SSD

Hardware Recomendado (Producción):
  CPU: 16+ cores @ 3.0GHz
  RAM: 64GB+
  Almacenamiento: 500GB+ NVMe SSD
  GPU: NVIDIA GPU con CUDA 11.0+ (opcional, para aceleración)

Software:
  OS: Ubuntu 20.04+ / macOS 11+ / Windows 10+ con WSL2
  Docker: 24.0+
  Docker Compose: 2.20+
  Python: 3.9+ (para desarrollo local)
  Git: 2.30+
8.2 Instalación Paso a Paso
8.2.1 Instalación Base
bash# 1. Instalar dependencias del sistema
## Ubuntu/Debian
sudo apt update
sudo apt install -y \
    build-essential \
    python3.9-dev \
    postgresql-client \
    libpq-dev \
    git \
    curl

## macOS (con Homebrew)
brew install python@3.9 postgresql git

# 2. Instalar Docker
## Ubuntu
curl -fsSL https://get.docker.com | bash
sudo usermod -aG docker $USER

## macOS
# Descargar Docker Desktop desde docker.com

# 3. Clonar repositorio
git clone https://github.com/SunNeurotron/Aletheia.git
cd Aletheia

# 4. Configurar entorno Python (opcional, para desarrollo)
python3.9 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Para desarrollo
8.2.2 Configuración de Servicios
bash# 1. Configurar variables de entorno globales
cp .env.example .env
# Editar .env con editor preferido

# 2. Configurar cada módulo
for module in Aletheia_v3 aletheia_stats aletheia_omega; do
    cp $module/.env.example $module/.env
done

# 3. Generar claves secretas seguras
python -c "import secrets; print(f'JWT_SECRET_KEY={secrets.token_urlsafe(32)}')"
# Actualizar en archivos .env

# 4. Configurar base de datos
# En Aletheia_v3/.env
DATABASE_URL=postgresql://aletheia:secure_password@postgres:5432/aletheia_db

# 5. Configurar MLflow
MLFLOW_TRACKING_URI=http://mlflow:5000
MLFLOW_S3_ENDPOINT_URL=http://minio:9000  # Si se usa MinIO
8.2.3 Despliegue con Docker Compose
bash# 1. Construir imágenes
cd Aletheia_v3
docker-compose build

# 2. Iniciar servicios en orden
# Base de datos y servicios de infraestructura
docker-compose up -d postgres redis mlflow

# Esperar a que estén listos
sleep 30

# 3. Aplicar migraciones
docker-compose run --rm alembic_migrate

# 4. Iniciar todos los servicios
docker-compose up -d

# 5. Verificar estado
docker-compose ps
docker-compose logs -f api  # Ver logs de la API
8.3 Configuración Avanzada
8.3.1 Configuración de Kubernetes
yaml# kubernetes/aletheia-namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: aletheia
  labels:
    name: aletheia
    environment: production
yaml# kubernetes/api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aletheia-api
  namespace: aletheia
spec:
  replicas: 3
  selector:
    matchLabels:
      app: aletheia-api
  template:
    metadata:
      labels:
        app: aletheia-api
    spec:
      containers:
      - name: api
        image: aletheia/api:v4.0
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: aletheia-secrets
              key: database-url
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: aletheia-secrets
              key: jwt-secret
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
8.3.2 Configuración de HPC (SLURM)
bash#!/bin/bash
#SBATCH --job-name=aletheia-abc-search
#SBATCH --partition=gpu
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=32
#SBATCH --gres=gpu:4
#SBATCH --time=24:00:00
#SBATCH --output=aletheia_%j.out

# Cargar módulos
module load python/3.9
module load cuda/11.8
module load openmpi/4.1.4

# Activar entorno
source /path/toReintentarJContinuarEditarbash# Activar entorno
source /path/to/aletheia/venv/bin/activate

# Configurar MPI para Aletheia
export ALETHEIA_MPI_RANKS=$SLURM_NTASKS
export ALETHEIA_WORKERS_PER_NODE=8
export ALETHEIA_GPU_PER_WORKER=1

# Ejecutar búsqueda distribuida
mpirun -np $SLURM_NTASKS python -m aletheia.hpc.distributed_abc_search \
   --config /path/to/hpc_config.yaml \
   --search-space-partition $SLURM_PROCID \
   --total-partitions $SLURM_NTASKS \
   --checkpoint-dir /scratch/aletheia/checkpoints \
   --result-dir /scratch/aletheia/results
8.4 Optimización de Rendimiento
8.4.1 Configuración de PostgreSQL
sql-- postgresql.conf optimizations
-- Memoria
shared_buffers = 8GB              # 25% de RAM disponible
effective_cache_size = 24GB       # 75% de RAM disponible
work_mem = 64MB                   # Por operación de ordenación
maintenance_work_mem = 2GB        # Para VACUUM, índices

-- Write Ahead Log
wal_buffers = 16MB
checkpoint_completion_target = 0.9
max_wal_size = 4GB
min_wal_size = 1GB

-- Consultas paralelas
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
parallel_leader_participation = on

-- Estadísticas
default_statistics_target = 100
random_page_cost = 1.1            # Para SSD

-- Conexiones
max_connections = 200
8.4.2 Índices Optimizados
sql-- Índices para búsquedas frecuentes
CREATE INDEX CONCURRENTLY idx_concepts_type_created
ON scientific_concepts(concept_type, created_at DESC);

CREATE INDEX CONCURRENTLY idx_concepts_properties_gin
ON scientific_concepts USING gin(properties);

CREATE INDEX CONCURRENTLY idx_relationships_source_type
ON directed_relationships(source_id, relationship_type);

CREATE INDEX CONCURRENTLY idx_relationships_target_type
ON directed_relationships(target_id, relationship_type);

-- Índices para búsqueda de texto
CREATE INDEX CONCURRENTLY idx_concepts_name_trgm
ON scientific_concepts USING gin(name gin_trgm_ops);

-- Índices para el módulo ABC
CREATE INDEX CONCURRENTLY idx_abc_hits_quality
ON abc_search_hits(quality DESC)
WHERE quality > 1.4;

-- Particionamiento para tablas grandes
CREATE TABLE concept_metrics_2024 PARTITION OF concept_metrics
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

9. API y Endpoints
9.1 Documentación OpenAPI
La documentación completa de la API está disponible en formato OpenAPI/Swagger:

Swagger UI: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc
OpenAPI JSON: http://localhost:8000/openapi.json

9.2 Autenticación y Autorización
9.2.1 Obtención de Token JWT
httpPOST /token
Content-Type: application/x-www-form-urlencoded

username=researcher@example.com&password=secure_password&grant_type=password

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
9.2.2 Uso del Token
httpGET /api/v1/protected-endpoint
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
9.3 Endpoints Principales por Módulo
9.3.1 Eje X - Gestión Ontológica
yamlIngesta de Documentos:
  POST /api/eje-x/ingest-document:
    description: Ingiere un documento y extrae UCMs
    request_body:
      title: string
      content: string
      metadata: object
    responses:
      202:
        document_id: uuid
        task_id: uuid
    roles_required: [researcher]

Gestión de Conceptos:
  GET /api/eje-x/concepts:
    description: Lista conceptos con filtros
    query_params:
      concept_type: ConceptType
      skip: int = 0
      limit: int = 100
      search: string
    responses:
      200:
        concepts: List[ScientificConcept]
        total: int
    roles_required: [viewer]

  POST /api/eje-x/concepts:
    description: Crea un nuevo concepto
    request_body:
      name: string
      description: string
      concept_type: ConceptType
      properties: object
    responses:
      201:
        concept: ScientificConcept
    roles_required: [researcher]

Relaciones:
  POST /api/eje-x/relationships:
    description: Crea relación entre conceptos
    request_body:
      source_id: uuid
      target_id: uuid
      relationship_type: string
      properties: object
    responses:
      201:
        relationship: DirectedRelationship
    roles_required: [researcher]
9.3.2 Eje Y - Síntesis de Conocimiento
yamlFormación de Clusters:
  POST /api/eje-y/cluster-formation:
    description: Forma clusters a partir de UCMs
    request_body:
      ucm_ids: List[uuid]
      clustering_params:
        method: string = "mdl_hierarchical"
        max_clusters: int = 10
        similarity_threshold: float = 0.7
    responses:
      201:
        clusters: List[Cluster]
        mdl_scores: object
    roles_required: [analyst]

Derivación de Proposiciones:
  POST /api/eje-y/derive-propositions:
    description: Deriva proposiciones de clusters
    request_body:
      cluster_ids: List[uuid]
      generation_params:
        method: string = "mdl_optimization"
        num_candidates: int = 20
        coherence_weight: float = 0.5
    responses:
      201:
        propositions: List[Proposition]
    roles_required: [analyst]

Construcción de Teorías:
  POST /api/eje-y/construct-theories:
    description: Pipeline completo de síntesis
    request_body:
      starting_concepts: List[uuid]
      synthesis_levels: List[string]
      optimization_params: object
    responses:
      202:
        job_id: uuid
        estimated_time: int
    roles_required: [analyst]
9.3.3 Análisis MDU
yamlAnálisis Cúbico:
  POST /api/mdu/cubic-analysis:
    description: Ejecuta análisis MDU completo
    request_body:
      x_dimension:  # Modelado
        concepts: List[uuid]
        ontology_rules: object
      y_dimension:  # Descubrimiento
        search_space: object
        optimization_method: string
      z_dimension:  # Comprensión
        visualization_params: object
        explainability_level: string
    responses:
      202:
        analysis_id: uuid
        cube_state: object
    roles_required: [admin]

Búsqueda ABC:
  POST /api/abc/search:
    description: Inicia búsqueda de tripletas ABC
    request_body:
      search_space:
        a_range: [int, int]
        b_range: [int, int]
      optimization_params:
        n_calls: int = 1000
        acq_func: string = "custom_ei"
      constraints:
        min_quality: float = 1.4
        time_limit: int = 3600
    responses:
      202:
        job_id: uuid
    roles_required: [researcher]

  GET /api/abc/results/{job_id}:
    description: Obtiene resultados de búsqueda
    responses:
      200:
        status: string
        best_triples: List[ABCTriple]
        optimization_trace: object
        mlflow_run_id: string
    roles_required: [researcher]
9.3.4 Análisis Estadístico (aletheia_stats)
yamlPrueba T:
  POST /api/v1/analyze/ttest:
    description: Realiza prueba t con validaciones
    request_body:
      experiment_name: string
      group_a_data: List[float]
      group_b_data: List[float]
      alpha: float = 0.05
      alternative: string = "two-sided"
      metadata: object
    responses:
      200:
        t_statistic: float
        p_value: float
        degrees_of_freedom: float
        confidence_interval: [float, float]
        effect_size: object
        normality_tests: object
        mlflow_run_id: string
    roles_required: [analyst]

ANOVA:
  POST /api/v1/analyze/anova:
    description: ANOVA de una vía
    request_body:
      groups: List[List[float]]
      group_names: List[string]
      alpha: float = 0.05
      post_hoc: string = "tukey"
    responses:
      200:
        f_statistic: float
        p_value: float
        eta_squared: float
        post_hoc_results: object
    roles_required: [analyst]
9.4 WebSocket para Actualizaciones en Tiempo Real
python# Cliente WebSocket ejemplo
import asyncio
import websockets
import json

async def monitor_job(job_id: str, token: str):
    uri = f"ws://localhost:8000/ws/jobs/{job_id}"
    headers = {"Authorization": f"Bearer {token}"}

    async with websockets.connect(uri, extra_headers=headers) as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)

            print(f"Estado: {data['status']}")
            print(f"Progreso: {data['progress']}%")

            if data['status'] in ['completed', 'failed']:
                break

10. Testing y Calidad del Código
10.1 Estrategia de Testing
10.1.1 Pirámide de Tests
mermaidgraph TB
    subgraph "Pirámide de Testing"
        E2E[Tests E2E<br/>5%]
        INT[Tests de Integración<br/>20%]
        UNIT[Tests Unitarios<br/>75%]

        E2E --> INT --> UNIT
    end

    subgraph "Tipos de Tests"
        U1[Domain Logic]
        U2[Use Cases]
        U3[Utilities]

        I1[API Endpoints]
        I2[Database]
        I3[External Services]

        E1[User Workflows]
        E2[System Integration]
    end

    UNIT --> U1 & U2 & U3
    INT --> I1 & I2 & I3
    E2E --> E1 & E2
10.1.2 Tests Unitarios
python# tests/test_domain.py
import pytest
from hypothesis import given, strategies as st
from aletheia_v3.core.domain import _radical, abc_quality_metric

class TestDomainLogic:
    """Tests para lógica de dominio central."""

    @pytest.mark.parametrize("n,expected", [
        (1, 1),
        (6, 6),      # 2 * 3
        (30, 30),    # 2 * 3 * 5
        (210, 210),  # 2 * 3 * 5 * 7
        (2**10, 2),  # Solo un primo
    ])
    def test_radical_calculation(self, n, expected):
        """Test cálculo de radical con casos conocidos."""
        assert _radical(n) == expected

    @given(
        a=st.integers(min_value=1, max_value=10**6),
        b=st.integers(min_value=1, max_value=10**6)
    )
    def test_radical_properties(self, a, b):
        """Test propiedades del radical usando Hypothesis."""
        # Propiedad: rad(ab) <= rad(a) * rad(b)
        rad_ab = _radical(a * b)
        rad_a_times_rad_b = _radical(a) * _radical(b)
        assert rad_ab <= rad_a_times_rad_b

    def test_abc_quality_edge_cases(self):
        """Test casos límite para métrica de calidad ABC."""
        # Caso inválido: a + b != c
        assert abc_quality_metric(1, 2, 4) == 0.0

        # Caso inválido: gcd(a,b) != 1
        assert abc_quality_metric(2, 4, 6) == 0.0

        # Caso válido conocido
        quality = abc_quality_metric(1, 8, 9)
        assert 1.0 < quality < 1.5
10.1.3 Tests de Integración
python# tests/test_api_integration.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.asyncio
class TestAPIIntegration:
    """Tests de integración para endpoints API."""

    async def test_knowledge_synthesis_pipeline(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        auth_headers: dict
    ):
        """Test pipeline completo de síntesis."""
        # 1. Ingerir documento
        response = await async_client.post(
            "/api/eje-x/ingest-document",
            json={
                "title": "Test Document",
                "content": "Prime numbers and their properties..."
            },
            headers=auth_headers
        )
        assert response.status_code == 202
        document_id = response.json()["document_id"]

        # 2. Esperar procesamiento
        await asyncio.sleep(5)

        # 3. Verificar UCMs extraídas
        response = await async_client.get(
            f"/api/eje-x/concepts?source_document={document_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        ucms = response.json()["concepts"]
        assert len(ucms) > 0

        # 4. Formar clusters
        response = await async_client.post(
            "/api/eje-y/cluster-formation",
            json={"ucm_ids": [u["id"] for u in ucms]},
            headers=auth_headers
        )
        assert response.status_code == 201

        # 5. Verificar en base de datos
        result = await async_session.execute(
            "SELECT COUNT(*) FROM scientific_concepts WHERE concept_type = 'CLUSTER'"
        )
        cluster_count = result.scalar()
        assert cluster_count > 0
10.1.4 Tests de Rendimiento
python# tests/test_performance.py
import pytest
import time
from aletheia_v3.core.domain import _radical

class TestPerformance:
    """Benchmarks de rendimiento."""

    @pytest.mark.benchmark(group="radical")
    def test_radical_performance_small(self, benchmark):
        """Benchmark para números pequeños."""
        result = benchmark(_radical, 1000)
        assert result == 40  # 2³ × 5³

    @pytest.mark.benchmark(group="radical")
    def test_radical_performance_large(self, benchmark):
        """Benchmark para números grandes."""
        large_number = 2**50 - 1
        result = benchmark(_radical, large_number)
        assert result > 0

    @pytest.mark.slow
    def test_api_throughput(self, client, auth_headers):
        """Test de throughput de API."""
        start_time = time.time()
        requests_count = 0

        while time.time() - start_time < 10:  # 10 segundos
            response = client.get(
                "/api/health",
                headers=auth_headers
            )
            assert response.status_code == 200
            requests_count += 1

        rps = requests_count / 10
        assert rps > 100  # Mínimo 100 req/s
10.2 Cobertura de Código
10.2.1 Configuración de Coverage
ini# .coveragerc
[run]
source = .
omit =
    */tests/*
    */venv/*
    */__pycache__/*
    */migrations/*
    setup.py

[report]
precision = 2
show_missing = True
skip_covered = False

[html]
directory = htmlcov

[xml]
output = coverage.xml
10.2.2 Reporte de Cobertura
bash# Ejecutar tests con cobertura
pytest --cov=aletheia_v3 --cov=aletheia_stats \
       --cov-report=term-missing \
       --cov-report=html \
       --cov-report=xml

# Resultados esperados
# Module                          Coverage
# aletheia_v3.core.domain           95%
# aletheia_v3.application           92%
# aletheia_v3.api                   88%
# aletheia_stats.domain             96%
# Overall                           91%
10.3 Análisis Estático y Linting
10.3.1 Configuración de MyPy
ini# mypy.ini
[mypy]
python_version = 3.9
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True

[mypy-tests.*]
ignore_errors = True

[mypy-alembic.*]
ignore_errors = True
10.3.2 Pre-commit Hooks
yaml# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: detect-private-key

  - repo: https://github.com/psf/black
    rev: 24.4.2
    hooks:
      - id: black
        args: [--line-length=88]

  - repo: https://github.com/PyCQA/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/PyCQA/flake8
    rev: 7.1.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203]
        additional_dependencies: [flake8-docstrings, flake8-bugbear]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks:
      - id: mypy
        additional_dependencies:
          - types-requests
          - types-redis
          - sqlalchemy[mypy]
10.4 CI/CD Pipeline
10.4.1 GitHub Actions Workflow
yaml# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Run pre-commit
        uses: pre-commit/action@v3.0.0

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test_password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-test.txt

      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:test_password@localhost/test_db
          REDIS_URL: redis://localhost:6379
        run: |
          pytest --cov=. --cov-report=xml --cov-report=term

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

  build:
    needs: [lint, test]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker images
        run: |
          docker-compose -f Aletheia_v3/docker-compose.yml build

      - name: Run security scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'aletheia/api:latest'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'

11. Publicaciones y Referencias Académicas
11.1 Publicaciones del Proyecto
bibtex@article{aletheia2024,
  title={Aletheia: A Computational Platform for AI-Guided Scientific Discovery},
  author={Alant Research Team},
  journal={Journal of Computational Science},
  volume={TBD},
  pages={TBD},
  year={2024},
  publisher={Elsevier}
}

@inproceedings{aletheia-mdl2024,
  title={Hierarchical Knowledge Synthesis using Minimum Description Length Optimization},
  author={Alant Research Team},
  booktitle={Proceedings of the International Conference on Machine Learning},
  pages={TBD},
  year={2024},
  organization={PMLR}
}

@techreport{aletheia-abc2024,
  title={Computational Approaches to the ABC Conjecture: A Bayesian Optimization Perspective},
  author={Alant Research Team},
  year={2024},
  institution={Alant Research},
  type={Technical Report}
}
11.2 Referencias Fundamentales
11.2.1 Teoría de Números y Conjetura ABC

Oesterlé, J., & Masser, D. (1985). "Pour une théorie de l'effectivité." Comptes Rendus de l'Académie des Sciences.
Granville, A., & Stark, H. (2000). "ABC implies no Siegel zeros for L-functions of characters with negative discriminant." Inventiones Mathematicae, 139(3), 509-523.
Stewart, C. L., & Yu, K. (2001). "On the abc conjecture II." Duke Mathematical Journal, 108(1), 169-181.

11.2.2 Optimización Bayesiana

Snoek, J., Larochelle, H., & Adams, R. P. (2012). "Practical Bayesian optimization of machine learning algorithms." Advances in Neural Information Processing Systems, 25.
Shahriari, B., Swersky, K., Wang, Z., Adams, R. P., & De Freitas, N. (2015). "Taking the human out of the loop: A review of Bayesian optimization." Proceedings of the IEEE, 104(1), 148-175.

11.2.3 Principio MDL y Teoría de la Información

Rissanen, J. (1978). "Modeling by shortest data description." Automatica, 14(5), 465-471.
Grünwald, P. D. (2007). The Minimum Description Length Principle. MIT Press.
Vitányi, P. M., & Li, M. (2000). "Minimum description length induction, Bayesianism, and Kolmogorov complexity." IEEE Transactions on Information Theory, 46(2), 446-464.

11.2.4 Procesamiento de Lenguaje Natural

Manning, C. D., & Schütze, H. (1999). Foundations of Statistical Natural Language Processing. MIT Press.
Jurafsky, D., & Martin, J. H. (2020). Speech and Language Processing (3rd ed.). Pearson.

11.3 Contacto y Colaboración
Equipo de Investigación Aletheia
Alant Research
Email: aletheia-research@alant.com
GitHub: https://github.com/SunNeurotron/Aletheia
Para colaboraciones académicas:

Propuestas de investigación conjunta
Acceso a datasets de investigación
Participación en benchmarks
Contribuciones al código abierto

Licencia: Apache 2.0
Copyright: © 2025 Alant

<div align="center">
<p><strong>Aletheia v4.0 - Descubriendo la Verdad a través de la Computación</strong></p>
<p><em>"Ἀλήθεια" - La Verdad Revelada</em></p>
</div>
