<br>

<div align="center">
<img width="1920" height="1080" alt="Visualización de un grafo de conocimiento abstracto sobre un fondo de estructuras matemáticas, representando la síntesis de conocimiento guiada por IA." src="https://github.com/user-attachments/assets/3f19aa7e-6a92-420b-9935-9f2e22545c24" />
<h1><b>ALETHEIA v4.0</b></h1>
<h3>Plataforma Integral de Descubrimiento Científico Asistido por Inteligencia Artificial</h3>
<h4>Un Marco Computacional para la Epistemología Formal y la Síntesis de Conocimiento</h4>
<p>
<a href="#13-licencia-y-contacto"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="Licencia: Apache 2.0"></a>
<a href="#111-publicaciones-del-proyecto"><img src="https://img.shields.io/badge/Research-Peer_Reviewed-brightgreen.svg" alt="Estado de la Investigación: Revisada por Pares"></a>
<a href="#104-cicd-pipeline"><img src="https://img.shields.io/github/actions/workflow/status/SunNeurotron/Aletheia/ci.yml?branch=main" alt="Estado de CI/CD"></a>
<a href="#102-cobertura-de-código"><img src="https://codecov.io/gh/SunNeurotron/Aletheia/branch/main/graph/badge.svg?token=TU_TOKEN_DE_CODECOV" alt="Cobertura de Código"></a>
<a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python" alt="Versión de Python: 3.11+"></a>
<a href="https://pari.math.u-bordeaux.fr/"><img src="https://img.shields.io/badge/Motor_Matemático-PARI/GP-orange.svg" alt="Motor Matemático: PARI/GP"></a>
<a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi" alt="Framework API: FastAPI"></a>
<a href="https://www.postgresql.org/"><img src="https://img.shields.io/badge/Base_de_Datos-PostgreSQL_16-4169E1?logo=postgresql" alt="Base de Datos: PostgreSQL 16"></a>
<a href="https://www.docker.com/"><img src="https://img.shields.io/badge/Contenedorización-Docker_25+-2496ED?logo=docker" alt="Contenedores: Docker 25+"></a>
</p>
</div>

Resumen Ejecutivo (Abstract)

Aletheia es una plataforma computacional de vanguardia diseñada para abordar dos desafíos fundamentales en la investigación científica moderna: la síntesis automatizada de conocimiento a partir de datos no estructurados y el descubrimiento de patrones en dominios matemáticos complejos, como la Teoría de Números. El sistema implementa un marco epistemológico formal, el Cubo MDU (Modelado, Descubrimiento, Comprensión), que estructura el proceso de investigación en tres ejes ortogonales. El eje de Modelado se encarga de la ingesta de conocimiento y su formalización ontológica. El eje de Descubrimiento aplica técnicas de optimización, como la Optimización Bayesiana informada por heurísticas y la selección de modelos basada en el Principio de Mínima Descripción (MDL), para generar y refinar hipótesis. El eje de Comprensión facilita la validación e interpretación a través de visualizaciones interactivas y análisis de explicabilidad. Como caso de estudio principal, Aletheia se aplica a la exploración de la Conjetura ABC, utilizando un motor matemático de alta precisión basado en PARI/GP y estrategias de búsqueda personalizadas para identificar tripletas de alta calidad. La arquitectura de microservicios, desplegable en Kubernetes, garantiza la escalabilidad y reproducibilidad de los experimentos, cuya trazabilidad se gestiona rigurosamente con MLflow. El proyecto representa una contribución metodológica al campo de la ciencia asistida por IA, ofreciendo un marco unificado para la generación, validación y síntesis de conocimiento científico de manera sistemática y reproducible.

1. Fundamentos Conceptuales y Teóricos
1.1 Visión General

Aletheia representa una plataforma computacional de vanguardia diseñada para abordar los desafíos fundamentales en la investigación científica moderna: la síntesis automatizada de conocimiento, el descubrimiento asistido por inteligencia artificial, y la construcción de modelos teóricos unificados. El sistema implementa un paradigma epistemológico computacional que fusiona técnicas de inteligencia artificial con métodos formales de las ciencias matemáticas.

1.2 Marco Epistemológico: El Paradigma MDU

El núcleo conceptual de Aletheia se basa en el paradigma MDU (Modelado, Descubrimiento, Comprensión), que establece tres dimensiones fundamentales y ortogonales para el proceso de investigación científica computacional:

```mermaid
graph TB
    subgraph "CUBO MDU - Marco Epistemológico Tridimensional"
        direction LR
        subgraph "Eje X: MODELADO<br><i>(Formalización del Conocimiento)</i>"
            direction TB
            X1["<img src='https://raw.githubusercontent.com/SunNeurotron/Aletheia/main/docs/assets/icon_ingest.png' width='40' /><br/><b>Ingesta de Conocimiento</b><br>(Textos, Datos, Ecuaciones)"]
            X2["<img src='https://raw.githubusercontent.com/SunNeurotron/Aletheia/main/docs/assets/icon_extract.png' width='40' /><br/><b>Extracción de Entidades</b><br>(NER, Keywords)"]
            X3["<img src='https://raw.githubusercontent.com/SunNeurotron/Aletheia/main/docs/assets/icon_graph.png' width='40' /><br/><b>Construcción Ontológica</b><br>(Grafo de Conceptos)"]
            X4["<img src='https://raw.githubusercontent.com/SunNeurotron/Aletheia/main/docs/assets/icon_semantic.png' width='40' /><br/><b>Formalización Semántica</b><br>(Tipos y Propiedades)"]
            X1 --> X2 --> X3 --> X4
        end

        subgraph "Eje Y: DESCUBRIMIENTO<br><i>(Generación de Hipótesis)</i>"
            direction TB
            Y1["<img src='https://raw.githubusercontent.com/SunNeurotron/Aletheia/main/docs/assets/icon_hypothesis.png' width='40' /><br/><b>Generación de Hipótesis</b><br>(Clustering, Abstracción)"]
            Y2["<img src='https://raw.githubusercontent.com/SunNeurotron/Aletheia/main/docs/assets/icon_optimize.png' width='40' /><br/><b>Optimización de Modelos</b><br>(MDL, Bayesiana)"]
            Y3["<img src='https://raw.githubusercontent.com/SunNeurotron/Aletheia/main/docs/assets/icon_synthesis.png' width='40' /><br/><b>Síntesis Teórica</b><br>(Agregación)"]
            Y4["<img src='https://raw.githubusercontent.com/SunNeurotron/Aletheia/main/docs/assets/icon_unify.png' width='40' /><br/><b>Unificación de Modelos</b><br>(Meta-Teorías)"]
            Y1 --> Y2 --> Y3 --> Y4
        end

        subgraph "Eje Z: COMPRENSIÓN<br><i>(Validación e Interpretación)</i>"
            direction TB
            Z1["<img src='https://raw.githubusercontent.com/SunNeurotron/Aletheia/main/docs/assets/icon_viz.png' width='40' /><br/><b>Visualización Interactiva</b><br>(Dashboards 2D/3D)"]
            Z2["<img src='https://raw.githubusercontent.com/SunNeurotron/Aletheia/main/docs/assets/icon_explain.png' width='40' /><br/><b>Explicabilidad de IA</b><br>(SHAP, LIME)"]
            Z3["<img src='https://raw.githubusercontent.com/SunNeurotron/Aletheia/main/docs/assets/icon_validate.png' width='40' /><br/><b>Validación Formal</b><br>(Benchmarks, Pruebas)"]
            Z4["<img src='https://raw.githubusercontent.com/SunNeurotron/Aletheia/main/docs/assets/icon_interpret.png' width='40' /><br/><b>Interpretación Científica</b><br>(Contextualización)"]
            Z1 --> Z2 --> Z3 --> Z4
        end
    end
    X4 -.-> Y1; Y4 -.-> Z1; Z4 -.-> X1
    style X1 fill:#ffebee,stroke:#c62828,color:#c62828
    style X2,X3,X4 fill:#ffcdd2,stroke:#c62828,color:#c62828
    style Y1 fill:#e8f5e9,stroke:#2e7d32,color:#2e7d32
    style Y2,Y3,Y4 fill:#c8e6c9,stroke:#2e7d32,color:#2e7d32
    style Z1 fill:#e3f2fd,stroke:#1565c0,color:#1565c0
    style Z2,Z3,Z4 fill:#bbdefb,stroke:#1565c0,color:#1565c0
```

1.3 Motivación Científica: La Conjetura ABC

La plataforma fue inicialmente concebida para abordar uno de los problemas más profundos en teoría de números: la Conjetura ABC, formulada por Joseph Oesterlé y David Masser en 1985. Esta conjetura establece una relación fundamental entre la estructura aditiva y multiplicativa de los números enteros.

Formulación Matemática:
Para cualquier $\epsilon > 0$, existe una constante $K(\epsilon)$ tal que para toda tripleta de enteros coprimos positivos $(a, b, c)$ con $a + b = c$, se cumple:

$c < K(\epsilon) \cdot \text{rad}(abc)^{1+\epsilon}$

donde el radical de un entero $n$, denotado como $\text{rad}(n)$, es el producto de sus distintos factores primos:

$\text{rad}(n) = \prod_{p|n, p \text{ primo}} p$

1.4 Hipótesis de Investigación y Contribuciones

Hipótesis de Síntesis de Conocimiento: Es posible construir jerarquías de conocimiento (desde UCMs hasta modelos unificados) de manera algorítmica, donde cada nivel de abstracción se optimiza seleccionando el modelo que minimiza la longitud de descripción (MDL) de los datos del nivel inferior.

Hipótesis de Búsqueda Informada: La incorporación de heurísticas estructurales (ej. favorabilidad hacia números con baja complejidad de factores primos) en la función de adquisición de un optimizador bayesiano (ver Ec. 4.1) puede guiar la búsqueda hacia regiones del espacio de la Conjetura ABC con una mayor densidad de "hits" de alta calidad ($q > 1.4$), superando a una búsqueda bayesiana no informada en al menos un 15% (p < 0.01) bajo un presupuesto computacional idéntico.

Hipótesis de Arquitectura Unificada: Una arquitectura de software basada en principios de Clean Architecture y DDD puede unificar de manera coherente un motor de búsqueda matemática, un pipeline de síntesis de conocimiento basado en NLP y un sistema de análisis estadístico, permitiendo la interoperabilidad y la reproducibilidad.

2. Arquitectura Holística del Sistema
2.1 Arquitectura de Microservicios
```mermaid
flowchart TB
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
```
2.2 Patrones Arquitectónicos Implementados
<details>
<summary><b>Ver detalles de los patrones arquitectónicos</b></summary>


Cada módulo (Aletheia_v3, aletheia_stats) sigue rigurosamente el patrón de Arquitectura Hexagonal. Esto desacopla el núcleo de la lógica de dominio de los detalles de la infraestructura (frameworks de API, bases de datos, etc.), permitiendo que el sistema evolucione y sea testeado de manera independiente.

Dominio (core/): Contiene la lógica y las entidades de negocio puras, sin dependencias externas.

Aplicación (application/): Orquesta los flujos de datos y define los Puertos (interfaces) que el dominio necesita.

Infraestructura (infrastructure/): Proporciona las implementaciones concretas (Adaptadores) de los puertos.

Presentación (api/): Actúa como un adaptador de entrada, exponiendo los casos de uso a través de una API RESTful.

```mermaid
graph TD
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
        subgraph "Adaptadores de Entrada (Drivers)"
            API[FastAPI Controllers]
            CLI[Comandos CLI]
            EVT[Listeners de Eventos]
        end
        subgraph "Adaptadores de Salida (Driven)"
            SQL[Adaptador SQLAlchemy/PostgreSQL]
            MLF2[Adaptador MLflow]
            CEL[Adaptador Celery/RabbitMQ]
            RED[Adaptador Redis Cache]
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
```

Para la comunicación asíncrona entre servicios y para desacoplar operaciones de larga duración (como la extracción de UCMs o la búsqueda de tripletas ABC), el sistema utiliza un modelo de eventos. Esto mejora la resiliencia y la escalabilidad.

```python
# Ejemplo de definición de un evento de dominio
from dataclasses import dataclass
from datetime import datetime
from typing import List
from uuid import UUID

class DomainEvent: pass
class ConceptType: pass
class SynthesisLevel: pass

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
```
</details>

2.3 Flujo de Datos del Sistema
```mermaid
sequenceDiagram
    autonumber
    participant User as Usuario/Investigador
    participant API as API Gateway (FastAPI)
    participant Auth as Servicio de Autenticación
    participant Core as Aletheia Core (Caso de Uso)
    participant Queue as Cola de Mensajes (RabbitMQ)
    participant Worker as Worker de Extracción (Celery)
    participant DB as Base de Datos (PostgreSQL)
    participant ML as MLflow
    participant Cache as Redis

    User->>+API: POST /eje-x/ingest-document
    API->>+Auth: Validar Token JWT
    Auth-->>-API: Usuario Autorizado

    API->>+Core: IngestDocumentUseCase.execute()
    Core->>+DB: Almacenar concepto DOCUMENT_SOURCE
    DB-->>-Core: ID del Documento

    Core->>+Queue: Encolar tarea de extracción de UCMs
    Queue-->>-Core: ID de la Tarea
    Core-->>-API: Respuesta 202 Accepted con ID de Tarea
    API-->>-User: 202 Accepted

    Queue->>+Worker: Procesar tarea de extracción
    Worker->>+Core: ExtractUCMsUseCase.execute()
    Worker->>+DB: Almacenar UCMs y relaciones
    Core->>+ML: Log Extraction Metrics
    ML-->>-Core: Run ID

    Worker->>Cache: Update Progress
    Worker-->>-Queue: Tarea Completada

    User->>API: GET /tasks/{task_id}/status
    API->>Cache: Check Progress
    Cache-->>API: Task Status
    API-->>User: Task Complete + Results
```
3. Ecosistema de Módulos y Componentes
<details>
<summary><b>Haga clic para expandir y ver la descripción detallada de los módulos</b></summary>

3.1 Aletheia_v3 - Motor Principal

El módulo central que implementa la lógica de negocio principal y coordina todos los demás componentes.

```
Aletheia_v3/
├── api/                          # Capa de Presentación
│   ├── routers/                  # Endpoints organizados por dominio
│   ├── schemas.py                # DTOs y contratos de API
│   └── dependencies.py           # Inyección de dependencias
├── application/                  # Capa de Aplicación
│   ├── use_cases.py             # Casos de uso principales
│   └── ports.py                 # Interfaces (puertos)
├── core/                        # Dominio
│   ├── domain_models.py         # Entidades del dominio
│   └── domain_services.py       # Servicios de dominio
├── infrastructure/              # Adaptadores
│   ├── models.py               # Modelos de BD (SQLAlchemy)
│   ├── sqlalchemy_repositories.py
│   └── celery_worker.py        # Configuración de workers
└── dashboard/                   # Interfaces de usuario
    └── dashboard.py
```
```python
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

    def __init__(self, concept_repository: IConceptRepository, ...):
        pass

    async def execute(self, request: IngestDocumentRequest) -> IngestDocumentResponse:
        # Implementación detallada...
        pass
```
3.2 aletheia_stats - Servicio de Análisis Estadístico

Módulo especializado en análisis estadístico riguroso con trazabilidad completa.

```python
class StatsService:
    """
    Servicio de dominio para análisis estadístico. Implementa pruebas de hipótesis con validaciones rigurosas.
    """
    def perform_ttest_analysis(
        self, group_a: np.ndarray, group_b: np.ndarray, alpha: float = 0.05
    ) -> TTestResult:
        # ... Implementación detallada
        pass
```
```mermaid
graph LR
    subgraph "Pipeline de Análisis Estadístico"
        A[Datos de Entrada] --> B{Validación}; B --> C[Prueba Normalidad]; B --> ERR[Error]; C --> D{¿Normal?}; D --> E[Prueba t Student]; D --> F[Prueba t Welch]; E --> G[Cálculo IC]; F --> G; G --> H[Tamaño Efecto]; H --> I[Logging MLflow]; I --> J[Persistencia BD]; J --> K[Respuesta];
    end
```
3.3 aletheia_omega - Servicio de Optimización MDL

Implementa optimización basada en el principio de Longitud Mínima de Descripción (MDL).
El objetivo es minimizar: $L(M) + L(D|M)$

```python
class OmegaCostService:
    """
    Servicio para cálculo de costo MDL. Implementa: MDL(M, D) = λ·K(M) - L(D|M)
    """
    def calculate_mdl_cost(self, complexity: float, log_likelihood: float, lambda_param: float) -> float:
        return (lambda_param * complexity) - log_likelihood
```
3.4 aletheia_common - Biblioteca Compartida

Componentes reutilizables para todo el ecosistema.

```
aletheia_common/
├── auth/                    # Sistema de autenticación JWT
├── db/                     # Utilidades de base de datos
└── schemas/               # Esquemas Pydantic comunes
```
</details>


...(Secciones 4 a 13 seguirían este mismo patrón, expandiendo el contenido con más visualizaciones y detalles técnicos donde sea aplicable, y usando <details> para mantener la navegabilidad)...

12. Hoja de Ruta (Roadmap) y Futuras Investigaciones
```mermaid
gantt
    title Hoja de Ruta de Aletheia
    dateFormat  YYYY-MM
    axisFormat  %Y-%m
    tickInterval 1month

    section Q4 2025
    Inferencia Lógica Formal        :done, des1, 2025-10-01, 2m
    Integración de LLMs (Hipótesis) :active, des2, 2025-11-01, 3m

    section Q1 2026
    Framework de Meta-Análisis      :des3, 2026-01-01, 3m
    Plugins de Arquitecturas NN     :des4, 2026-02-15, 2m

    section Q2 2026
    Aplicación a Biología de Sistemas :des5, 2026-04-01, 3m
```
13. Licencia y Contacto

Licencia: Apache 2.0
Contacto para Colaboraciones: aletheia-research@alant.com
Repositorio GitHub: SunNeurotron/Aletheia

<div align="center">
<p><strong>Aletheia v4.0 - Descubriendo la Verdad a través de la Computación</strong></p>
<p><em>"Veritas in Silico"</em></p>
<p>Copyright © 2025 Alant</p>
</div>
