<div align="center">
<br/>
<h1>Framework Aletheia v4.0</h1>
<p><strong>Un Ecosistema Computacional para la Gnoseología Aplicada y el Descubrimiento Científico</strong></p>
<p>Modelado, Descubrimiento y Comprensión (MDU) de conocimiento científico mediante la síntesis jerárquica y la optimización de principios.</p>

<p>
<a href="./Aletheia_v3/LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="Licencia"></a>
<a href="./MDU_CORE_PRINCIPLES.md"><img src="https://img.shields.io/badge/MDU-Compliant-brightgreen.svg" alt="Cumplimiento MDU"></a>
<a href="#"><img src="https://img.shields.io/badge/Python-3.11-3776AB?logo=python" alt="Python"></a>
<a href="#"><img src="https://img.shields.io/badge/FastAPI-0.103+-009688?logo=fastapi" alt="FastAPI"></a>
<a href="#"><img src="https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?logo=sqlalchemy" alt="SQLAlchemy"></a>
<a href="#"><img src="https://img.shields.io/badge/Status-Research%20Prototype-orange" alt="Estado"></a>
</p>
</div>

> **Prólogo:** Aletheia es un artefacto computacional que se propone como un **laboratorio para la epistemología**. Trascendiendo su aplicación inicial en la Conjetura ABC, su arquitectura ha evolucionado para implementar un sistema de **síntesis de conocimiento jerárquico**. El framework modela el proceso de descubrimiento no como una búsqueda de resultados aislados, sino como un ascenso inductivo desde unidades conceptuales mínimas (UCMs) extraídas de datos, hasta la formulación de modelos teóricos unificados. Este proceso está gobernado por el **Principio de Mínima Longitud Descriptiva (MDL)**, posicionando a Aletheia como una herramienta para investigar la estructura y la emergencia del propio conocimiento científico.

---

## **Índice Analítico**
1.  [**Fundamento Teórico y Filosófico**](#1-fundamento-teórico-y-filosófico)
2.  [**Arquitectura y Ecosistema de Componentes**](#2-arquitectura-y-ecosistema-de-componentes)
3.  [**El Pipeline de Síntesis de Conocimiento (Eje Y)**](#3-el-pipeline-de-síntesis-de-conocimiento-eje-y)
4.  [**El Motor de Optimización MDL**](#4-el-motor-de-optimización-mdl)
5.  [**Validación Empírica y Benchmarks**](#5-validación-empírica-y-benchmarks)
6.  [**Guía de Inicio y Uso Avanzado**](#6-guía-de-inicio-y-uso-avanzado)
7.  [**Contribuciones y Hoja de Ruta**](#7-contribuciones-y-hoja-de-ruta)
8.  [**Licencia, Disclaimer y Citación**](#8-licencia-disclaimer-y-citación)

## **1. Fundamento Teórico y Filosófico**

Aletheia se fundamenta en la premisa de que la ciencia es un proceso inherentemente dinámico y de compresión de información. La arquitectura del framework refleja esta visión a través de principios clave:

### **1.1 Principios Fundacionales**

-   **Gnoseología Computacional**: El objetivo del framework no es meramente generar "insights", sino modelar el **proceso de construcción de conocimiento** (`gnosis`). El pipeline de síntesis del Eje Y formaliza un ascenso inductivo desde la evidencia (`DOCUMENT_SOURCE`) hasta la abstracción teórica (`UNIFIED_MODEL`).
-   **Principio Variacional de Mínima Longitud Descriptiva (MDL)**: Aletheia se adhiere al principio MDL, una formalización de la Navaja de Ockham. La selección del "mejor" modelo en cada etapa de la síntesis se realiza minimizando la función de coste, análoga a una energía libre informacional:
    $$ L(M, D) = \lambda \cdot K(M) - \log P(D|M) $$
    donde \(K(M)\) es la complejidad de Kolmogorov del modelo (aproximada por su longitud comprimida) y \(P(D|M)\) es la verosimilitud de los datos dado el modelo. Aletheia busca el balance óptimo entre la **simplicidad del modelo** y su **poder explicativo**.
-   **Emergencia y Jerarquía**: El conocimiento es jerárquico. El sistema modela explícitamente esta estructura a través del `ConceptType` Enum, donde cada nivel superior es una síntesis emergente de los componentes del nivel inferior, validada a través del principio MDL.

### **1.2 Marco Teórico Extendido**
- **Teoría de la Información Algorítmica**: La complejidad de Kolmogorov (`KolmogorovComplexityProxyService`) es el pilar para medir la simplicidad del modelo.
- **Inferencia Bayesiana**: El término de verosimilitud \(\log P(D|M)\) enmarca la evaluación del modelo como un problema de inferencia bayesiana.
- **Teoría de Grafos**: La ontología subyacente de `ScientificConcept` y `DirectedRelationship` forma un grafo de conocimiento dirigido, permitiendo análisis estructurales y de trayectoria.

## **2. Arquitectura y Ecosistema de Componentes**

La plataforma está diseñada como un conjunto de servicios modulares y desacoplados, orquestados a través de Docker Compose y preparados para Kubernetes, siguiendo los principios de la **Arquitectura Hexagonal**.

```mermaid
graph TD
    User["Usuario con imagen"] -->|Interactúa vía Navegador| Dashboard["Dashboard Streamlit con emoji"]

    subgraph "Plataforma Aletheia Servicios en Docker"
        Dashboard --> API["Servidor API FastAPI con emoji"]
        API --> DB["BD PostgreSQL con emoji y parentesis"]
        API --> MQ["Cola de Mensajes Redis con emoji"]
        Worker["Worker Celery sin emoji"] --> MQ
        Worker --> AISearch["Caso de Uso IA core use cases"]
        AISearch --> DomainLogic["Logica de Dominio con emoji"]
        Worker --> DB
        Worker --> MLflowServer["Tracking Experimentos MLflow con emoji y parentesis"]
        MLflowServer --> DB
        MLflowServer --> ArtifactStore["Artefactos S3 MinIO con emoji y parentesis"]
    end

    User --> MLflowUI["MLflow UI con imagen"]
    MLflowUI --> MLflowServer

    style User fill:#fff,stroke:#333,stroke-width:2px
    style Dashboard fill:#FF4B4B,stroke:#333,stroke-width:2px,color:#fff
    style API fill:#009688,stroke:#333,stroke-width:2px,color:#fff
    style DB fill:#336791,stroke:#333,stroke-width:2px,color:#fff
    style MQ fill:#DC382D,stroke:#333,stroke-width:2px,color:#fff
    style Worker fill:#fcf,stroke:#333,stroke-width:2px
    style AISearch fill:#ddf,stroke:#333,stroke-width:2px
    style DomainLogic fill:#eef,stroke:#333,stroke-width:2px
    style MLflowServer fill:#00AEEC,stroke:#333,stroke-width:2px,color:#fff
    style MLflowUI fill:#fff,stroke:#333,stroke-width:2px
    style ArtifactStore fill:#eee,stroke:#333,stroke-width:2px


Módulo Principal (Aletheia_v3): Contiene el núcleo lógico, dividido en capas: api, application, core, infrastructure, y dashboard.

Módulo Común (aletheia_common): Librería compartida para utilidades transversales como autenticación JWT.

Contenerización y Orquestación: Dockerfile y docker-compose.yml aseguran un entorno de ejecución reproducible.

Migraciones: Alembic gestiona la evolución del esquema de la base de datos de forma controlada y versionada.

3. El Pipeline de Síntesis de Conocimiento (Eje Y)

El corazón funcional de Aletheia es el pipeline de síntesis del Eje Y. Cada transición entre niveles es un proceso competitivo de selección de modelos basado en MDL.

Ingesta (Eje X): Un documento (DOCUMENT_SOURCE) es procesado para extraer Unidades Conceptuales Mínimas (UCM).

Clusterización: Se generan múltiples CLUSTERs candidatos a partir de las UCMs. El FindOptimalModelUseCase selecciona el clúster que mejor comprime la información de sus UCMs miembros.

Derivación de Proposiciones: De cada CLUSTER se derivan candidatas a PROPOSITION. Se selecciona la proposición que ofrece la descripción más concisa y explicativa.

Construcción de Teorías: El proceso se repite en niveles superiores, integrando MINI_THEORYs en COMPREHENSIVE_THEORYs y estas en UNIFIED_MODELs.

4. El Motor de Optimización MDL

El FindOptimalModelUseCase es el componente central que implementa el principio MDL.

Generación de Candidatos: Para cada etapa, se generan múltiples modelos candidatos.

Evaluación MDL: Cada candidato es evaluado usando la función de coste. El LikelihoodService es crucial aquí, evaluando L(D|M) (ej. midiendo la cohesión semántica de los miembros de un clúster).

Selección: El modelo con el coste MDL más bajo es seleccionado.

5. Validación Empírica y Benchmarks
5.1 Validación del Agente de Búsqueda ABC

El script experimento_validacion_agi.py valida la hipótesis de que la plasticidad sináptica mejora la adaptación en entornos no estacionarios.

Para ejecutar: python experimento_validacion_agi.py

Resultado Esperado: Se genera el gráfico adaptacion_comparison.png, donde el agente con plasticidad (azul) muestra una recuperación más rápida y robusta tras un cambio en el entorno.

<div align="center">
<img src="./adaptacion_comparison.png" alt="Gráfico de comparación de rendimiento entre un DQN Plástico y un DQN Estándar durante un cambio de entorno." width="800"/>
<p><i><b>Figura 2:</b> Resultado empírico de la validación del agente.</i></p>
</div>

5.2 Benchmarks de la Síntesis de Conocimiento

La validación del pipeline de síntesis del Eje Y es un área de investigación activa.

Coherencia: Se mide la coherencia semántica de los conceptos generados en cada nivel jerárquico.

Compresión: Se evalúa la reducción en la longitud total de descripción a medida que se asciende en la jerarquía, validando el principio MDL.

Comparación: Los grafos de conocimiento generados se comparan con ontologías de referencia construidas por expertos en dominios específicos.

6. Guía de Inicio y Uso Avanzado
Instalación con Docker (Recomendado)
Generated bash
# Desde el directorio raíz del proyecto
docker-compose up --build
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

Acceda a las interfaces en http://localhost:PUERTO, donde los puertos por defecto son 8000 (API), 8501/8502 (Dashboards), y 5000 (MLflow).

Uso Programático de la API
Generated python
# Script para ejecutar un pipeline de síntesis completo
import requests, uuid

API_URL = "http://localhost:8000/api/v1"
HEADERS = {"Authorization": "Bearer <TU_TOKEN_JWT>"}

def run_full_synthesis(document_text: str):
    # 1. Ingesta
    ingest_payload = {"document_text": document_text, "source_doi": f"doi:demo/{uuid.uuid4()}"}
    response = requests.post(f"{API_URL}/eje-x/ingest-document", json=ingest_payload, headers=HEADERS)
    response.raise_for_status()
    ucm_ids = [ucm['id'] for ucm in response.json()['ucm_extraction_result']['extracted_concepts']]
    print(f"Documento ingerido, {len(ucm_ids)} UCMs extraídos.")

    # 2. Clusterización
    cluster_payload = {"ucm_ids": ucm_ids}
    response = requests.post(f"{API_URL}/eje-y/cluster-formation", json=cluster_payload, headers=HEADERS)
    # ... continuar con los siguientes pasos del pipeline ...
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Python
IGNORE_WHEN_COPYING_END
7. Contribuciones y Hoja de Ruta

Aletheia es un proyecto de investigación abierta. Las contribuciones teóricas y técnicas son bienvenidas.

Hoja de Ruta Q4 2024: Refinamiento de las funciones de verosimilitud L(D|M); integración de LLMs para la generación de descripciones en PROPOSITIONs.

Hoja de Ruta 2025: Implementación de un Motor Dialéctico para la refutación y evolución de teorías; integración con bases de datos de grafos nativas (e.g., Neo4j).

8. Licencia, Disclaimer y Citación

Distribuido bajo la Licencia Apache 2.0. Consulte los archivos LICENSE y DISCLAIMER.md para un entendimiento completo de las responsabilidades y el uso previsto del software.

Citación:

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
