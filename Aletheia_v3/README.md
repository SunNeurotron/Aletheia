<div align="center">
<br/>
<h1>Framework Aletheia v4.0</h1>
<p><strong>Un Ecosistema Computacional para la Gnoseología Aplicada y el Descubrimiento Científico</strong></p>
<p>Modelado, Descubrimiento y Comprensión (MDU) de conocimiento científico mediante la síntesis jerárquica y la optimización de principios.</p>

<p>
<a href="./Aletheia_v3/LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="Licencia"></a>
<a href="./Aletheia_v3/MDU_CORE_PRINCIPLES.md"><img src="https://img.shields.io/badge/MDU-Compliant-brightgreen.svg" alt="Cumplimiento MDU"></a>
<a href="#"><img src="https://img.shields.io/badge/Python-3.11-3776AB?logo=python" alt="Python"></a>
<a href="#"><img src="https://img.shields.io/badge/FastAPI-0.103+-009688?logo=fastapi" alt="FastAPI"></a>
<a href="#"><img src="https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?logo=sqlalchemy" alt="SQLAlchemy"></a>
<a href="#"><img src="https://img.shields.io/badge/MLflow-2.5+-00AEEC?logo=mlflow" alt="MLflow"></a>
<a href="#"><img src="https://img.shields.io/badge/Status-Research%20Prototype-orange" alt="Estado"></a>
</p>
</div>

> **Prólogo:** Aletheia es un artefacto computacional que se propone como un **laboratorio para la epistemología**. Trascendiendo su aplicación inicial en la Conjetura ABC, su arquitectura ha evolucionado para implementar un sistema de **síntesis de conocimiento jerárquico**. El framework modela el proceso de descubrimiento no como una búsqueda de resultados aislados, sino como un ascenso inductivo desde unidades conceptuales mínimas (UCMs) extraídas de datos, hasta la formulación de modelos teóricos unificados. Este proceso está gobernado por el **Principio de Mínima Longitud Descriptiva (MDL)**, posicionando a Aletheia como una herramienta para investigar la estructura y la emergencia del propio conocimiento científico.

---

## **Índice Analítico**
1.  [**Fundamento Teórico y Filosófico**](#1-fundamento-teórico-y-filosófico)
2.  [**Arquitectura del Ecosistema Aletheia**](#2-arquitectura-del-ecosistema-aletheia)
3.  [**El Pipeline de Síntesis de Conocimiento (Eje Y)**](#3-el-pipeline-de-síntesis-de-conocimiento-eje-y)
4.  [**El Motor de Optimización MDL**](#4-el-motor-de-optimización-mdl)
5.  [**Despliegue y Operación de la Plataforma**](#5-despliegue-y-operación-de-la-plataforma)
6.  [**Guía de Contribución y Desarrollo**](#6-guía-de-contribución-y-desarrollo)
7.  [**Licencia y Consideraciones Éticas**](#7-licencia-y-consideraciones-éticas)
8.  [**Citación y Referencias**](#8-citación-y-referencias)

## **1. Fundamento Teórico y Filosófico**

Aletheia se construye sobre una base que fusiona la filosofía de la ciencia con la ciencia de la computación.

-   **Gnoseología Computacional**: El objetivo principal no es solo "encontrar patrones", sino modelar el **proceso de construcción de conocimiento**. El framework formaliza un flujo inductivo que va desde la evidencia textual (`DOCUMENT_SOURCE`) hasta la abstracción máxima (`UNIFIED_MODEL`), reflejando una visión estructurada de la epistemología.
-   **Principio de Mínima Longitud Descriptiva (MDL)**: En su núcleo, el sistema se adhiere al principio de MDL, una formalización de la Navaja de Ockham. La selección de la "mejor" teoría o modelo en cada etapa de la síntesis se realiza minimizando la función de coste:
    $$ L(M, D) = \lambda \cdot K(M) - \log P(D|M) $$
    donde \(K(M)\) es la complejidad del modelo (su longitud descriptiva) y \(P(D|M)\) es la verosimilitud de los datos dado el modelo. Aletheia busca el balance óptimo entre la **simplicidad del modelo** y su **poder explicativo**.
-   **Emergencia y Jerarquía**: El conocimiento no es plano. El sistema modela explícitamente una jerarquía de conceptos (`ConceptType`), donde cada nivel superior es una síntesis emergente de los componentes del nivel inferior.

## **2. Arquitectura del Ecosistema Aletheia**

La plataforma está diseñada como un conjunto de servicios modulares y desacoplados, orquestados a través de Docker Compose y preparados para Kubernetes, siguiendo los principios de la **Arquitectura Hexagonal**.

```mermaid
graph TD
    subgraph "Interfaz de Usuario"
        UI[<img src='https://streamlit.io/images/brand/logo-mark-light.png' width='30'/> Dashboard Streamlit]
    end

    subgraph "Capa de Aplicación y API"
        API[<img src='https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png' width='25'/> API FastAPI]
        Worker[<img src='https://www.celeryproject.org/img/logo.png' width='25'/> Worker Celery]
    end

    subgraph "Núcleo de Dominio (Aletheia_v3)"
        UseCase[Casos de Uso del Eje Y]
        MDL[Motor MDL]
        DomainModels[Conceptos y Relaciones]
    end

    subgraph "Infraestructura Persistente y de Soporte"
        DB[(<img src='https://upload.wikimedia.org/wikipedia/commons/2/29/Postgresql_elephant.svg' width='25'/> PostgreSQL)]
        Queue[(<img src='https://redis.io/wp-content/uploads/2024/04/logomark-light.svg' width='25'/> Redis)]
        Tracker[(<img src='https://www.mlflow.org/docs/latest/_static/MLflow-logo-final-black.png' width='60'/> MLflow)]
    end

    UI -->|Peticiones HTTP| API
    API -->|Interactúa con| UseCase
    API -- Encola Tareas --> Queue
    Worker -- Procesa Tareas --> Queue
    Worker -- Ejecuta --> UseCase
    UseCase -- Usa --> MDL
    UseCase -- Usa --> DomainModels
    UseCase -- Persiste/Recupera --> DB
    Worker -- Registra --> Tracker
    Tracker -- Almacena --> DB


Módulo Principal (Aletheia_v3): Contiene el núcleo lógico:

api/: Endpoints FastAPI para la ingesta, síntesis y visualización.

application/: Casos de uso que orquestan la lógica de negocio (Eje X y Eje Y).

core/: Modelos y servicios de dominio, incluyendo la implementación del motor MDL.

infrastructure/: Adaptadores para PostgreSQL (con SQLAlchemy), Celery y MLflow.

dashboard/: Aplicaciones Streamlit para la visualización interactiva.

Módulo Común (aletheia_common): Librería compartida para utilidades transversales como autenticación JWT y tipos de base dedatos personalizados.

Contenerización: El Dockerfile y docker-compose.yml aseguran un entorno de ejecución reproducible y escalable.

Migraciones: Alembic gestiona la evolución del esquema de la base de datos de forma controlada y versionada.

3. El Pipeline de Síntesis de Conocimiento (Eje Y)

El corazón funcional de Aletheia es el pipeline de síntesis del Eje Y, que construye conocimiento de forma ascendente.

<div align="center">
<img src="https://i.imgur.com/your_synthesis_pipeline_diagram.png" alt="Diagrama del Pipeline de Síntesis del Eje Y" width="800"/>
<p><i><b>Figura 1:</b> Fases de la síntesis jerárquica de conocimiento, desde UCMs hasta Modelos Unificados. Cada transición es gobernada por una optimización MDL. (Imagen conceptual).</i></p>
</div>


Ingesta (Eje X): Un documento (DOCUMENT_SOURCE) es procesado para extraer Unidades Conceptuales Mínimas (UCM).

Clusterización: Las UCMs se agrupan en CLUSTERs basados en similitud semántica o de palabras clave.

Derivación de Proposiciones: De cada CLUSTER se deriva una PROPOSITION que enuncia una relación o afirmación elemental.

Construcción de Mini-Teorías: Un conjunto coherente de PROPOSITIONs se sintetiza en una MINI_THEORY.

Teorías Comprehensivas: Múltiples MINI_THEORYs se integran en una COMPREHENSIVE_THEORY.

Modelos Unificados: La cúspide de la jerarquía, un UNIFIED_MODEL emerge de la síntesis de teorías comprehensivas, representando el nivel más alto de abstracción.

4. El Motor de Optimización MDL

En lugar de depender de heurísticas fijas, cada paso de síntesis en el Eje Y es un problema de optimización. El FindOptimalModelUseCase es invocado para seleccionar el mejor modelo (ej. el mejor CLUSTER) de un conjunto de candidatos.

Generación de Candidatos: Para cada etapa, se generan múltiples modelos candidatos (ej. diferentes agrupaciones de UCMs para formar clústeres).

Evaluación MDL: Cada candidato es evaluado usando la función de coste MDL:

Complejidad
𝐾
(
𝑀
)
K(M)
: Medida como la longitud de la descripción comprimida del modelo (KolmogorovComplexityProxyService). Un modelo más simple es más corto.

Verosimilitud (\log P(D|M)): Medida por una LikelihoodService específica del dominio. Evalúa cuán bien el modelo candidato (M) explica los datos (D) del nivel inferior. Por ejemplo, un buen CLUSTER tendrá una alta cohesión semántica entre sus UCMs miembros.

Selección: El modelo con el coste MDL más bajo es seleccionado como el resultado de la síntesis para esa etapa.

5. Despliegue y Operación de la Plataforma
Requisitos

Docker y Docker Compose.

Variables de entorno configuradas (copiar .env.example a .env si existe).

Ejecución

Construir e Iniciar Servicios: Desde el directorio que contiene docker-compose.yml (Aletheia_v3/):

Generated bash
docker-compose up --build
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

Aplicar Migraciones: El servicio alembic_migrate se ejecuta automáticamente al iniciar, aplicando cualquier migración de base de datos pendiente.

Acceder a las Interfaces:

Dashboard de Conocimiento: http://localhost:8502

Dashboard de Descubrimiento ABC: http://localhost:8501

API Docs (Swagger): http://localhost:8000/docs

MLflow UI: http://localhost:5000

Uso de la API

La API, protegida por JWT, permite la interacción programática con los pipelines de ingesta y síntesis.

Generated bash
# Ejemplo: Ingestar un documento
curl -X POST "http://localhost:8000/api/v1/eje-x/ingest-document" \
-H "Authorization: Bearer <TU_TOKEN_JWT>" \
-H "Content-Type: application/json" \
-d '{
  "document_text": "Dark energy is a form of energy that is hypothesized to permeate all of space, tending to accelerate the expansion of the universe.",
  "source_doi": "10.1000/j.cosmology.2024.01",
  "source_citation": "Einstein, A. (et al.) 2024, Journal of Cosmic Stuff"
}'

# Ejemplo: Formar clústeres a partir de las UCMs extraídas
curl -X POST "http://localhost:8000/api/v1/eje-y/cluster-formation" \
-H "Authorization: Bearer <TU_TOKEN_JWT>" \
-H "Content-Type: application/json" \
-d '{
  "ucm_ids": ["uuid_de_ucm1", "uuid_de_ucm2", "uuid_de_ucm3"]
}'
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END
6. Guía de Contribución y Desarrollo

Aletheia es un proyecto de investigación activa. Las contribuciones deben seguir los principios del Marco de Desarrollo Unificado (MDU), detallados en MDU_CORE_PRINCIPLES.md.

Pruebas: Ejecute la suite de pruebas completa con pytest.

Calidad de Código: Utilice pre-commit para asegurar el cumplimiento de black, isort, flake8 y mypy.

Nuevos Módulos: Siga la plantilla en _module_template/ para mantener la consistencia arquitectónica.

7. Licencia y Consideraciones Éticas

Este proyecto se distribuye bajo la Licencia Apache 2.0 (ver LICENSE). Adicionalmente, el DISCLAIMER.md especifica las responsabilidades y el uso esperado del software con fines de investigación. Se espera que los usuarios actúen con integridad científica y ética.

8. Citación y Referencias

Si utiliza Aletheia en su investigación, por favor, cite este repositorio.

Generated bibtex
@software{Aletheia_Framework_2024,
  author = {Alant},
  title = {{Aletheia v4.0: A Computational Ecosystem for Applied Gnoseology and Scientific Discovery}},
  year = {2024},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/SunNeurotron/Aletheia}}
}
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bibtex
IGNORE_WHEN_COPYING_END
<p align="center"><i>“El objetivo de la ciencia no es abrir una puerta a la sabiduría infinita, sino poner un límite al error infinito.”</i><br/>— Bertolt Brecht, <em>Vida de Galileo</em></p>
