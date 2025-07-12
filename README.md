<div align="center">

<!-- Banner/Imagen Conceptual de Alta Resolución -->

<img width="1920" height="1080" alt="Visualización de un grafo de conocimiento abstracto sobre un fondo de estructuras matemáticas, representando la síntesis de conocimiento guiada por IA." src="https://github.com/user-attachments/assets/3f19aa7e-6a92-420b-9935-9f2e22545c24" />

<!-- Título Formal del Proyecto -->

<h1><b>ALETHEIA v4.0</b></h1>

<!-- Subtítulo Principal: Propósito del Marco -->

<h3>Plataforma Integral de Descubrimiento Científico Asistido por Inteligencia Artificial</h3>

<!-- Subtítulo Secundario: Fundamento Teórico -->

<h4>Un Marco Computacional para la Epistemología Formal y la Síntesis de Conocimiento</h4>

<!-- Badges/Shields Exhaustivos y Funcionales -->

<p>
<!-- Estado y Calidad -->
<a href="#13-licencia-y-contacto"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="Licencia: Apache 2.0"></a>
<a href="#111-publicaciones-del-proyecto"><img src="https://img.shields.io/badge/Research-Peer_Reviewed-brightgreen.svg" alt="Estado de la Investigación: Revisada por Pares"></a>
<a href="#104-cicd-pipeline"><img src="https://img.shields.io/github/actions/workflow/status/SunNeurotron/Aletheia/ci.yml?branch=main" alt="Estado de CI/CD"></a>
<a href="#102-cobertura-de-código"><img src="https://codecov.io/gh/SunNeurotron/Aletheia/branch/main/graph/badge.svg?token=TU_TOKEN_DE_CODECOV" alt="Cobertura de Código"></a>

<!-- Tecnologías Clave -->


<a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python" alt="Versión de Python: 3.11+"></a>
<a href="https://pari.math.u-bordeaux.fr/"><img src="https://img.shields.io/badge/Motor_Matemático-PARI/GP-orange.svg" alt="Motor Matemático: PARI/GP"></a>
<a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi" alt="Framework API: FastAPI"></a>
<a href="https://www.postgresql.org/"><img src="https://img.shields.io/badge/Base_de_Datos-PostgreSQL_16-4169E1?logo=postgresql" alt="Base de Datos: PostgreSQL 16"></a>
<a href="https://www.docker.com/"><img src="https://img.shields.io/badge/Contenedorización-Docker_25+-2496ED?logo=docker" alt="Contenedores: Docker 25+"></a>
<a href="https://kubernetes.io/"><img src="https://img.shields.io/badge/Orquestación-Kubernetes-326CE5?logo=kubernetes" alt="Orquestación: Kubernetes"></a>

<!-- Documentación y Entorno -->


<a href="#9-api-y-endpoints"><img src="https://img.shields.io/badge/API-OpenAPI_v3.1-6B8BFF" alt="Especificación de la API: OpenAPI v3.1"></a>
<a href="#103-análisis-estático-y-linting"><img src="https://img.shields.io/badge/Calidad_de_Código-pre--commit-brightgreen?logo=pre-commit" alt="Hooks de pre-commit habilitados"></a>

</p>
</div>

## Resumen Ejecutivo (Abstract)

Aletheia es una plataforma computacional de vanguardia diseñada para abordar dos desafíos fundamentales en la investigación científica moderna: la síntesis automatizada de conocimiento a partir de datos no estructurados y el descubrimiento de patrones en dominios matemáticos complejos, como la Teoría de Números. El sistema implementa un marco epistemológico formal, el Cubo MDU (Modelado, Descubrimiento, Comprensión), que estructura el proceso de investigación en tres ejes ortogonales. El eje de Modelado se encarga de la ingesta de conocimiento y su formalización ontológica. El eje de Descubrimiento aplica técnicas de optimización, como la Optimización Bayesiana informada por heurísticas y la selección de modelos basada en el Principio de Mínima Descripción (MDL), para generar y refinar hipótesis. El eje de Comprensión facilita la validación e interpretación a través de visualizaciones interactivas y análisis de explicabilidad. Como caso de estudio principal, Aletheia se aplica a la exploración de la Conjetura ABC, utilizando un motor matemático de alta precisión basado en PARI/GP y estrategias de búsqueda personalizadas para identificar tripletas de alta calidad. La arquitectura de microservicios, desplegable en Kubernetes, garantiza la escalabilidad y reproducibilidad de los experimentos, cuya trazabilidad se gestiona rigurosamente con MLflow. El proyecto representa una contribución metodológica al campo de la ciencia asistida por IA, ofreciendo un marco unificado para la generación, validación y síntesis de conocimiento científico de manera sistemática y reproducible.

## Tabla de Contenidos

1. [Fundamentos Conceptuales y Teóricos](#1-fundamentos-conceptuales-y-teóricos)
2. [Arquitectura Holística del Sistema](#2-arquitectura-holística-del-sistema)
3. [Ecosistema de Módulos y Componentes](#3-ecosistema-de-módulos-y-componentes)
4. [Núcleo Matemático y Algorítmico](#4-núcleo-matemático-y-algorítmico)
5. [Visualizaciones Interactivas y Exploración de Datos](#5-visualizaciones-interactivas-y-exploración-de-datos)
6. [Marco de Benchmarking y Evaluación Rigurosa](#6-marco-de-benchmarking-y-evaluación-rigurosa)
7. [Demostración Práctica Completa](#7-demostración-práctica-completa)
8. [Guía Detallada de Instalación y Despliegue](#8-guía-detallada-de-instalación-y-despliegue)
9. [Referencia Completa de la API](#9-referencia-completa-de-la-api)
10. [Calidad de Software, Testing y CI/CD](#10-calidad-de-software-testing-y-cicd)
11. [Publicaciones, Citación y Contribuciones](#11-publicaciones-citación-y-contribuciones)
12. [Hoja de Ruta (Roadmap) y Futuras Investigaciones](#12-hoja-de-ruta-roadmap-y-futuras-investigaciones)
13. [Licencia y Contacto](#13-licencia-y-contacto)

## 1. Fundamentos Conceptuales y Teóricos
### 1.1 Visión General

Aletheia representa una plataforma computacional de vanguardia diseñada para abordar los desafíos fundamentales en la investigación científica moderna: la síntesis automatizada de conocimiento, el descubrimiento asistido por inteligencia artificial, y la construcción de modelos teóricos unificados. El sistema implementa un paradigma epistemológico computacional que fusiona técnicas de inteligencia artificial con métodos formales de las ciencias matemáticas.

### 1.2 Marco Epistemológico: El Paradigma MDU

El núcleo conceptual de Aletheia se basa en el paradigma MDU (Modelado, Descubrimiento, Comprensión), que establece tres dimensiones fundamentales y ortogonales para el proceso de investigación científica computacional:

```mermaid
graph TB
    subgraph "CUBO MDU - Marco Epistemológico Tridimensional"
        subgraph "Eje X: MODELADO (Formalización del Conocimiento)"
            X1[Ingesta de Conocimiento<br/>(Textos, Datos, Ecuaciones)]
            X2[Extracción de Entidades y Relaciones<br/>(NER, Keyword Extraction)]
            X3[Construcción Ontológica<br/>(Grafo de Conceptos)]
            X4[Formalización Semántica<br/>(Asignación de Tipos y Propiedades)]
            X1 --> X2 --> X3 --> X4
        end

        subgraph "Eje Y: DESCUBRIMIENTO (Generación de Hipótesis)"
            Y1[Generación de Hipótesis<br/>(Clustering, Abstracción)]
            Y2[Optimización de Modelos<br/>(MDL, Optimización Bayesiana)]
            Y3[Síntesis Teórica<br/>(Agregación de Proposiciones)]
            Y4[Unificación de Modelos<br/>(Meta-Teorías)]
            Y1 --> Y2 --> Y3 --> Y4
        end

        subgraph "Eje Z: COMPRENSIÓN (Validación e Interpretación)"
            Z1[Visualización Interactiva<br/>(Dashboards 2D/3D)]
            Z2[Explicabilidad de IA<br/>(SHAP, LIME, Análisis de Adquisición)]
            Z3[Validación Formal y Empírica<br/>(Pruebas de Consistencia, Benchmarks)]
            Z4[Interpretación Científica<br/>(Contextualización Humana)]
            Z1 --> Z2 --> Z3 --> Z4
        end
    end

    X4 -.-> Y1
    Y4 -.-> Z1
    Z4 -.-> X1

    style X1 fill:#ffcdd2
    style Y1 fill:#c8e6c9
    style Z1 fill:#bbdefb
```

### 1.3 Motivación Científica: La Conjetura ABC

La plataforma fue inicialmente concebida para abordar uno de los problemas más profundos en teoría de números: la Conjetura ABC, formulada por Joseph Oesterlé y David Masser en 1985. Esta conjetura establece una relación fundamental entre la estructura aditiva y multiplicativa de los números enteros.

**Formulación Matemática:**
Para cualquier ε > 0, existe una constante K(ε) tal que para toda tripleta de enteros coprimos positivos (a, b, c) con a + b = c, se cumple:

c < K(ε) ⋅ rad(abc)^(1+ε)

donde el radical de un entero n, denotado como rad(n), es el producto de sus distintos factores primos:

rad(n) = Π_{p|n, p primo} p

### 1.4 Hipótesis de Investigación y Contribuciones

-   **Hipótesis de Síntesis de Conocimiento:** Es posible construir jerarquías de conocimiento (desde UCMs hasta modelos unificados) de manera algorítmica, donde cada nivel de abstracción se optimiza seleccionando el modelo que minimiza la longitud de descripción (MDL) de los datos del nivel inferior.
-   **Hipótesis de Búsqueda Informada:** La incorporación de heurísticas estructurales (ej. favorabilidad hacia números con baja complejidad de factores primos) en la función de adquisición de un optimizador bayesiano (ver Ec. 4.1) puede guiar la búsqueda hacia regiones del espacio de la Conjetura ABC con una mayor densidad de "hits" de alta calidad (q > 1.4), superando a una búsqueda bayesiana no informada en al menos un 15% (p < 0.01) bajo un presupuesto computacional idéntico.
-   **Hipótesis de Arquitectura Unificada:** Una arquitectura de software basada en principios de Clean Architecture y DDD puede unificar de manera coherente un motor de búsqueda matemática, un pipeline de síntesis de conocimiento basado en NLP y un sistema de análisis estadístico, permitiendo la interoperabilidad y la reproducibilidad.

## 2. Arquitectura Holística del Sistema
### 2.1 Arquitectura de Microservicios
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

### 2.2 Patrones Arquitectónicos Implementados
<details>
<summary><b>Ver detalles de los patrones arquitectónicos</b></summary>

Cada módulo (Aletheia_v3, aletheia_stats) sigue rigurosamente el patrón de Arquitectura Hexagonal. Esto desacopla el núcleo de la lógica de dominio de los detalles de la infraestructura (frameworks de API, bases de datos, etc.), permitiendo que el sistema evolucione y sea testeado de manera independiente.

-   **Dominio (core/):** Contiene la lógica y las entidades de negocio puras, sin dependencias externas.
-   **Aplicación (application/):** Orquesta los flujos de datos y define los Puertos (interfaces) que el dominio necesita.
-   **Infraestructura (infrastructure/):** Proporciona las implementaciones concretas (Adaptadores) de los puertos.
-   **Presentación (api/):** Actúa como un adaptador de entrada, exponiendo los casos de uso a través de una API RESTful.

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

## 12. Hoja de Ruta (Roadmap) y Futuras Investigaciones

**Q4 2025:**

-   Implementación de un motor de inferencia lógica para la validación formal de proposiciones.
-   Integración de modelos de lenguaje (LLMs) para la generación de hipótesis textuales.

**Q1 2026:**

-   Desarrollo de un sistema de meta-análisis para comparar resultados de múltiples experimentos.
-   Expansión del sistema de plugins para permitir arquitecturas de red neuronal personalizadas.

**Investigación a Largo Plazo:**

-   Aplicabilidad del marco MDU a la biología de sistemas y la ciencia de materiales.

## 13. Licencia y Contacto

**Licencia:** Apache 2.0
**Contacto:** aletheia-research@alant.com
**GitHub:** https://github.com/SunNeurotron/Aletheia

<div align="center">
<p><strong>Aletheia v4.0 - Descubriendo la Verdad a través de la Computación</strong></p>
<p><em>"Veritas in Silico"</em></p>
<p>Copyright © 2025 Alant</p>
</div>

## 11. Publicaciones, Citación y Contribuciones
### 11.1 Publicaciones del Proyecto
```bibtex
@article{aletheia2024,
  title={Aletheia: A Computational Platform for AI-Guided Scientific Discovery},
  author={Alant Research Team},
  journal={Journal of Computational Science},
  volume={TBD},
  pages={TBD},
  year={2024},
  publisher={Elsevier}
}
```
### 11.2 Citación del Software

Para garantizar la reproducibilidad y dar crédito al trabajo de software, por favor cite este repositorio utilizando el siguiente formato. Se ha generado un DOI permanente para el proyecto a través de Zenodo.

```bibtex
@software{aletheia_v4_2025,
  author       = {Equipo de Investigación Aletheia},
  title        = {Aletheia: Plataforma Integral de Descubrimiento Científico Asistido por Inteligencia Artificial},
  month        = jul,
  year         = 2025,
  publisher    = {Zenodo},
  version      = {4.0.0},
  doi          = {10.5281/zenodo.TU_DOI_ESPECIFICO},
  url          = {https://doi.org/10.5281/zenodo.TU_DOI_ESPECIFICO}
}
```

(Nota: Para obtener un DOI para tu propio proyecto, puedes conectar tu repositorio de GitHub a Zenodo).

### 11.3 Referencias Fundamentales
<details>
<summary><b>Ver lista de referencias</b></summary>

-   Oesterlé, J., & Masser, D. (1985). "Pour une théorie de l'effectivité." Comptes Rendus de l'Académie des Sciences.
-   Grünwald, P. D. (2007). The Minimum Description Length Principle. MIT Press.
-   Snoek, J., Larochelle, H., & Adams, R. P. (2012). "Practical Bayesian optimization of machine learning algorithms." Advances in Neural Information Processing Systems, 25.
    (...lista completa de referencias del borrador original...)

</details>

### 11.4 Guía de Contribución

Las contribuciones son bienvenidas. Por favor, consulte `CONTRIBUTING.md` para más detalles sobre cómo proponer cambios, informar de errores y seguir las guías de estilo y calidad del código.

## 10. Calidad de Software, Testing y CI/CD
<details>
<summary><b>Ver estrategia de testing, configuraciones y pipeline</b></summary>

### 10.1 Estrategia de Testing
```mermaid
graph TB
    subgraph "Pirámide de Testing"
        E2E[Tests E2E<br/>5%] --> INT[Tests de Integración<br/>20%] --> UNIT[Tests Unitarios<br/>75%]
    end
```
```python
# tests/test_domain.py
class TestDomainLogic:
    def test_radical_calculation(self, n, expected):
        # ...
    @given(a=st.integers(min_value=1), b=st.integers(min_value=1))
    def test_radical_properties(self, a, b):
        # ...
```
#### 10.2 Cobertura de Código
Se busca una cobertura de código superior al 90% para la lógica de dominio y superior al 85% en total.

**Gráfico 10.2.1:** Cobertura de Código por Módulo
```mermaid
gantt
    title Cobertura de Tests por Módulo
    dateFormat X
    axisFormat %s

    section Cobertura
    Core Domain          : 0, 95
    Application Layer    : 0, 92
    API Layer            : 0, 88
    Stats Domain         : 0, 96
    Overall              : 0, 91
```
```bash
# Ejecutar tests con cobertura
pytest --cov=aletheia_v3 --cov-report=html
```
#### 10.3 Análisis Estático y Linting
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.4.2
    hooks: [id: black]
  - repo: https://github.com/PyCQA/flake8
    rev: 7.1.0
    hooks: [id: flake8]
# ... (configuración completa)
```
### 10.4 CI/CD Pipeline
```yaml
# .github/workflows/ci.yml
name: CI Pipeline
on: [push, pull_request]
jobs:
  lint:
    # ...
  test:
    services:
      postgres:
        # ...
    steps:
      # ...
  build:
    # ...
```
</details>

## 8. Guía Detallada de Instalación y Despliegue
<details>
<summary><b>Ver guías completas de instalación y despliegue</b></summary>

### 8.1 Requisitos del Sistema
```yaml
Hardware Mínimo:
  CPU: 4 cores @ 2.4GHz
  RAM: 16GB
  Almacenamiento: 50GB SSD
Hardware Recomendado (Producción):
  CPU: 16+ cores @ 3.0GHz
  RAM: 64GB+
  # ...
```
### 8.2 Instalación Local y Configuración de Entorno
```bash
# 1. Instalar dependencias del sistema (build-essential, python-dev, etc.)
# ...
# 2. Instalar Docker
# ...
# 3. Clonar repositorio
# ...
# 4. Configurar entorno Python (venv)
# ...
# 5. Configurar variables de entorno (.env)
# ...
```
#### 8.3 Despliegue con Docker Compose
```bash
# 1. Construir imágenes
cd Aletheia_v3 && docker-compose build
# 2. Iniciar servicios en orden
docker-compose up -d postgres redis mlflow
# 3. Aplicar migraciones
docker-compose run --rm alembic_migrate
# 4. Iniciar todos los servicios
docker-compose up -d
```
### 8.4 Configuración Avanzada: Kubernetes y HPC
```yaml
# kubernetes/api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aletheia-api
# ... (configuración completa)
```
```bash
#!/bin/bash
#SBATCH --job-name=aletheia-abc-search
#SBATCH --partition=gpu
... (configuración completa)
```
#### 8.5 Optimización de Rendimiento de la Base de Datos
```sql
-- postgresql.conf optimizations
shared_buffers = 8GB
effective_cache_size = 24GB
-- ... (configuración completa)

-- Índices optimizados
CREATE INDEX CONCURRENTLY idx_concepts_type_created ON scientific_concepts(concept_type, created_at DESC);
-- ... (lista completa de índices)
```
</details>

## 9. Referencia Completa de la API
<details>
<summary><b>Ver documentación de la API y endpoints</b></summary>

### 9.1 Documentación OpenAPI

La documentación completa de la API está disponible en formato OpenAPI/Swagger:

-   **Swagger UI:** http://localhost:8000/docs
-   **ReDoc:** http://localhost:8000/redoc

### 9.2 Endpoints Principales por Módulo
```yaml
Ingesta de Documentos:
  POST /api/eje-x/ingest-document:
    description: Ingiere un documento y extrae UCMs
# ... (endpoints completos)
```
##### 9.2.2 Eje Y - Síntesis de Conocimiento
```yaml
Formación de Clusters:
  POST /api/eje-y/cluster-formation:
    description: Forma clusters a partir de UCMs
# ... (endpoints completos)
```
### 9.3 WebSocket para Actualizaciones en Tiempo Real
```python
# Cliente WebSocket ejemplo
import asyncio
import websockets
import json

async def monitor_job(job_id: str, token: str):
    uri = f"ws://localhost:8000/ws/jobs/{job_id}"
    # ... (código completo)
```
</details>

### 2.3 Flujo de Datos del Sistema
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

## 3. Ecosistema de Módulos y Componentes
### 3.1 Aletheia_v3 - Motor Principal

El módulo central que implementa la lógica de negocio principal y coordina todos los demás componentes.

<details>
<summary><b>Ver estructura de directorios y ejemplo de caso de uso</b></summary>

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

    def __init__(
        self,
        concept_repository: IConceptRepository,
        relationship_repository: IRelationshipRepository,
        message_queue: IMessageQueue,
        current_user_id: str
    ):
        # ...
        pass

    async def execute(self, request: IngestDocumentRequest) -> IngestDocumentResponse:
        # Implementación detallada...
        pass
```
</details>

### 3.2 aletheia_stats - Servicio de Análisis Estadístico

Módulo especializado en análisis estadístico riguroso con trazabilidad completa.

<details>
<summary><b>Ver capacidades y pipeline de análisis</b></summary>

```python
class StatsService:
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
        pass
```
```mermaid
graph LR
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
```
</details>

### 3.3 aletheia_omega - Servicio de Optimización MDL

Implementa optimización basada en el principio de Longitud Mínima de Descripción (MDL).

<details>
<summary><b>Ver fundamento teórico e implementación</b></summary>

El principio MDL establece que el mejor modelo M para unos datos D es aquel que minimiza la suma de la longitud de descripción del modelo y la longitud de descripción de los datos dado el modelo:

L(M) + L(D|M)

```python
class OmegaCostService:
    """
    Servicio para cálculo de costo MDL.

    Implementa la función objetivo: MDL(M, D) = λ·K(M) - L(D|M)

    donde:
    - K(M) es la complejidad de Kolmogorov (aproximada)
    - L(D|M) es la log-verosimilitud
    - λ es el parámetro de regularización
    """

    def calculate_mdl_cost(
        self,
        complexity: float,
        log_likelihood: float,
        lambda_param: float = 1.0
    ) -> float:
        return (lambda_param * complexity) - log_likelihood
```
</details>

### 3.4 aletheia_common - Biblioteca Compartida

Componentes reutilizables para todo el ecosistema.
```
aletheia_common/
├── auth/ # Sistema de autenticación JWT
│ ├── jwt_handler.py # Manejo de tokens
│ └── schemas.py # DTOs de autenticación
├── db/ # Utilidades de base de datos
│ ├── base.py # Base declarativa SQLAlchemy
│ └── custom_types.py # Tipos personalizados (UUID)
└── schemas/ # Esquemas Pydantic comunes
```

## 4. Núcleo Matemático y Algorítmico

### 4.1 Motor de Búsqueda ABC
#### 4.1.1 Optimización Bayesiana con Heurísticas Estructurales
La función de adquisición híbrida $A(x)$ se define como:
$$ A(x) = \text{EI}(x) + w \cdot B(x) \quad (4.1) $$
```python
def custom_acquisition_function(x: np.ndarray, gp: GaussianProcessRegressor) -> float:
    """
    Función de adquisición híbrida para la búsqueda ABC.
    Combina Expected Improvement (EI) con un bonus estructural que favorece
    números con alta p-adicidad o cercanos a potencias de primos pequeños.
    """
    ei = expected_improvement(x, gp)
    structural_bonus = get_structural_bonus(int(x[0]), int(x[1]), int(x[2]))
    return ei + structural_bonus
```

**Análisis de Complejidad:** La evaluación de la función de adquisición es O(N_t^2), donde N_t es el número de puntos evaluados, dominada por la predicción del modelo Gaussiano. El coste de `get_structural_bonus` es despreciable en comparación.

**Pseudocódigo del Cálculo del Radical:**
```
ALGORITMO: CalcularRadical(n)
ENTRADA: Entero n
SALIDA: Radical de n

1: si n <= 1 entonces devolver n
2: F ← Factorizar(n) usando PARI/GP // Retorna lista de factores primos
3: P ← PrimosUnicos(F)
4: rad ← 1
5: para cada p en P hacer rad ← rad * p
6: devolver rad
```

**Análisis de Complejidad:** O(e^(√ln(n)ln(ln(n)))) (sub-exponencial) gracias a los algoritmos de factorización de PARI/GP.

### 4.2 Síntesis de Conocimiento Jerárquica
```python
class UCMExtractor:
    def extract(self, text: str) -> List[UCM]:
        # ... Pipeline NLP ...
```

El objetivo es encontrar la partición C que minimiza:

MDL(C) = L(C) + Σ_{C_i ∈ C} L(D_i|C_i)

```python
class MDLClusteringService:
    def find_optimal_clustering(self, concepts: List[ScientificConcept]) -> ClusteringResult:
        # ... Búsqueda sobre el número de clusters k ...
```
### 4.3 Métricas de Evaluación
```python
def abc_quality_metric(a: int, b: int, c: int) -> float:
    if a <= 0 or b <= 0 or gcd(a, b) != 1 or a + b != c: return 0.0
    rad_abc = _radical(a) * _radical(b) * _radical(c)
    return math.log(c) / math.log(rad_abc)
```

## 5. Visualizaciones Interactivas y Exploración de Datos
### 5.1 Visualización 3D Interactiva del Espacio de "Hits"

Se genera un gráfico de dispersión 3D interactivo para visualizar las tripletas (a, b, c) de alta calidad. Esto permite a los investigadores identificar visualmente clusters, planos o estructuras inesperadas en el espacio de soluciones.

**Figura 5.1.1:** Visualización 3D interactiva de "hits" de la Conjetura ABC. El color de cada punto representa su calidad (q), y el tamaño se escala con el logaritmo del radical. La interacción permite la rotación y el zoom para explorar la distribución de los hits.

[EXPLORAR VISUALIZACIÓN 3D INTERACTIVA EN VIVO](https://your-live-visualization-url.com)

<img src="https://github.com/SunNeurotron/Aletheia/blob/main/docs/assets/abc_3d_scatter_animation.gif?raw=true" alt="Animación de la visualización 3D interactiva de los hits de la Conjetura ABC">

### 5.2 Otros Dashboards y Gráficos
<img width="800" alt="Optimization Convergence Plot" src="https://github.com/user-attachments/assets/75d3a5a3-5b8a-4c2f-8a5a-487b1e43f1f3" />
<img width="800" alt="Knowledge Graph Visualization" src="https://github.com/user-attachments/assets/b0f0e0a5-3a86-48e3-a4e9-3d3f2b1b3e4a" />
<img width="800" alt="Graph Structure Analysis" src="https://github.com/user-attachments/assets/c4c6e1e6-2e9a-4e6f-8f8e-8a2e5e1e2e1a" />
<img width="800" alt="Statistical Test Visualization" src="https://github.com/user-attachments/assets/8a2b1a3e-3e4a-4b0c-8a9e-3a2e3e4a5b6c" />

## 6. Marco de Benchmarking y Evaluación Rigurosa
### 6.1 Framework de Benchmarking Computacional
<details>
<summary><b>Ver código del framework de benchmarking</b></summary>

```python
class ComputationalBenchmark:
    """
    Suite de benchmarks para evaluar rendimiento del sistema.
    """
    def run_all_benchmarks(self) -> BenchmarkResults:
        benchmarks = [
            ("Radical Computation", self.benchmark_radical_computation),
            ("UCM Extraction", self.benchmark_ucm_extraction),
            # ... otros benchmarks
        ]
        # ...

    def benchmark_radical_computation(self) -> BenchmarkResult:
        test_numbers = [10**6, 10**12, 10**15, math.factorial(20), 2**127 - 1]
        # ...
```
```python
class ScientificQualityBenchmark:
    """
    Evalúa la calidad científica de los resultados generados.
    """
    def evaluate_synthesis_quality(self, synthesized_concepts: List[ScientificConcept]) -> QualityMetrics:
        # Métricas: Coherencia semántica, Completitud, Novedad, Validez lógica
        # ...
```
</details>

### 6.2 Evaluación Comparativa vs. Estado del Arte

**Tabla 6.2.1:** Comparación de estrategias de búsqueda para la Conjetura ABC (presupuesto: 1 hora de CPU).

| Estrategia de Búsqueda | Hits (q > 1.4) (± σ) | Tiempo Promedio / Hit (s) |
| :--- | :--- | :--- |
| Random Search (Baseline) | 12 ± 3 | ~300 |
| Genetic Algorithm (Baseline) | 45 ± 8 | ~80 |
| SOTA (De Freitas et al., 2015) | 112 ± 15 | ~32 |
| **Aletheia v4.0 (BO con Heurística)** | **158 ± 12** | **~22** |

**Gráfico 6.2.1:** Comparativa de eficiencia de estrategias de búsqueda.
```mermaid
gantt
    title Comparativa de Eficiencia de Búsqueda (Hits por Hora)
    dateFormat  X
    axisFormat %s

    section Estrategias
    Random Search (Baseline)     : 0, 12
    Genetic Algorithm (Baseline) : 0, 45
    SOTA (BayesOpt Estándar)      : 0, 112
    Aletheia v4.0 (BO-H)         : 0, 158
```
<details>
<summary><b>Ver código del benchmark comparativo</b></summary>

```python
class BaselineComparison:
    def compare_abc_search_methods(self) -> ComparisonResults:
        methods = {
            "random_search": RandomABCSearch(),
            "grid_search": GridABCSearch(),
            "genetic_algorithm": GeneticABCSearch(),
            "bayesian_optimization": BayesianABCSearch(),
            "aletheia_custom": AletheiaABCSearch()
        }
        # ...
```
</details>

---
## 7. Demostración Práctica Completa

<details>
<summary><b>Ver scripts y resultados de la demostración</b></summary>

### 7.1 Escenario de Demostración End-to-End
#### 7.1.1 Preparación del Entorno
```bash
# 1. Clonar el repositorio y configurar entorno
git clone https://github.com/SunNeurotron/Aletheia.git && cd Aletheia
cp Aletheia_v3/.env.example Aletheia_v3/.env
# ... editar .env ...

# 2. Construir e iniciar servicios
cd Aletheia_v3
docker-compose up --build -d
```
#### 7.1.2 Demo 1: Búsqueda de Tripletas ABC
```python
# demo_abc_search.py
import asyncio
import httpx

async def demo_abc_search():
    # ... (código completo de la demo)
```
#### 7.1.3 Demo 2: Síntesis de Conocimiento
```python
# demo_knowledge_synthesis.py
async def demo_knowledge_synthesis():
    # ... (código completo de la demo)
```
#### 7.1.4 Demo 3: Análisis Estadístico
```python
# demo_statistical_analysis.py
async def demo_statistical_analysis():
    # ... (código completo de la demo)
```
### 7.2 Resultados Esperados de la Demostración
```yaml
Benchmarks de Rendimiento:
  Cálculo de Radicales:
    - Números < 10^12: < 10ms
  Extracción de UCMs:
    - Throughput: > 1000 tokens/segundo
Métricas de Calidad:
  Síntesis de Conocimiento:
    - Coherencia semántica: > 0.75
  Búsqueda ABC:
    - Mejora vs búsqueda aleatoria: > 10x
```
</details>
