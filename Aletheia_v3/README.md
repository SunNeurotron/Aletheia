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
2.  [**Arquitectura del Ecosistema Aletheia**](#2-arquitectura-del-ecosistema-aletheia)
3.  [**El Pipeline de Síntesis de Conocimiento (Eje Y)**](#3-el-pipeline-de-síntesis-de-conocimiento-eje-y)
4.  [**El Motor de Optimización MDL**](#4-el-motor-de-optimización-mdl)
5.  [**Validación Empírica y Reproducibilidad**](#5-validación-empírica-y-reproducibilidad)
6.  [**Guía de Instalación y Uso Avanzado**](#6-guía-de-instalación-y-uso-avanzado)
7.  [**Licencia y Consideraciones Éticas**](#7-licencia-y-consideraciones-éticas)
8.  [**Hoja de Ruta y Contribuciones**](#8-hoja-de-ruta-y-contribuciones)

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
graph LR
    subgraph Externo
        A[<br>Usuario/Cliente API<br><br>🔬]
    end

    subgraph "Capa de Presentación"
        B(API FastAPI<br>/api/v1)
        C(Dashboard<br>Streamlit)
    end

    subgraph "Capa de Aplicación"
        D[Casos de Uso<br>Eje Y (Síntesis)<br>Eje X (Ingesta)]
    end

    subgraph "Núcleo de Dominio"
        E[Entidades<br>ScientificConcept<br>DirectedRelationship]
        F[Servicios de Dominio<br>MDL Engine<br>TheoryBuilder]
    end

    subgraph "Capa de Infraestructura"
        G[<br>PostgreSQL<br>(SQLAlchemy)<br><br>🐘]
        H[<br>Redis<br>(Celery Broker)<br><br>🏎️]
        I[<br>MLflow<br>(Tracking)<br><br>📈]
    end

    A -- HTTP/HTTPS --> B
    A -- Interacción Web --> C
    C -- Peticiones API --> B
    B -- Invoca --> D
    D -- Usa --> F
    F -- Opera sobre --> E
    D -- Persiste/Lee vía Puerto --> G
    D -- Encola Tareas vía Puerto --> H
    D -- Registra Experimentos vía Puerto --> I


Módulo Principal (Aletheia_v3): Contiene el núcleo lógico, dividido en capas:

presentation/: Endpoints FastAPI y Dashboards Streamlit.

application/: Casos de uso que orquestan la lógica de negocio (Eje X y Eje Y).

core/: Modelos y servicios de dominio, incluyendo la implementación del motor MDL.

infrastructure/: Adaptadores para PostgreSQL (con SQLAlchemy), Celery y MLflow.

Módulo Común (aletheia_common): Librería compartida para utilidades transversales como autenticación JWT y tipos de base de datos personalizados.

Contenerización y Orquestación: Dockerfile y docker-compose.yml aseguran un entorno de ejecución reproducible y escalable. Alembic gestiona las migraciones de base de datos.

3. El Pipeline de Síntesis de Conocimiento (Eje Y)

El corazón funcional de Aletheia es el pipeline de síntesis del Eje Y, que construye conocimiento de forma ascendente. Cada transición entre niveles no es una mera agregación, sino un proceso competitivo de selección de modelos basado en MDL.

Ingesta (Eje X): Un documento (DOCUMENT_SOURCE) es procesado para extraer Unidades Conceptuales Mínimas (UCM).

Clusterización: Se generan múltiples CLUSTERs candidatos a partir de las UCMs. El FindOptimalModelUseCase selecciona el clúster que mejor comprime la información de sus UCMs miembros (alta cohesión interna, baja redundancia).

Derivación de Proposiciones: De cada CLUSTER se derivan candidatas a PROPOSITION. Se selecciona la proposición que ofrece la descripción más concisa y explicativa de las relaciones dentro del clúster.

Construcción de Mini-Teorías: Se sintetizan MINI_THEORYs a partir de conjuntos de proposiciones. Se optimiza para encontrar la teoría más simple que sea consistente con las proposiciones dadas.

Teorías Comprehensivas y Modelos Unificados: El proceso se repite en niveles superiores, integrando MINI_THEORYs en COMPREHENSIVE_THEORYs y estas en UNIFIED_MODELs, siempre buscando la descripción más parsimoniosa y potente.

4. El Motor de Optimización MDL

El FindOptimalModelUseCase es el componente central que implementa el principio MDL en cada etapa de la síntesis.

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

5. Validación Empírica y Reproducibilidad

El framework incluye scripts y metodologías para su validación. No se incluyen resultados estáticos en este documento; se insta al investigador a generar los resultados para asegurar la reproducibilidad.

5.1 Experimento de Adaptación del Agente

El script experimento_validacion_agi.py valida la hipótesis de que la plasticidad sináptica mejora la adaptación en entornos no estacionarios.

Para ejecutar el experimento:

Generated bash
python experimento_validacion_agi.py
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

Resultados Esperados:
La ejecución generará un gráfico adaptacion_comparison.png. Se espera observar una caída de rendimiento en ambos agentes en el punto de cambio del entorno. Sin embargo, la curva del agente con plasticidad debería mostrar una recuperación significativamente más rápida y alcanzar un nivel de rendimiento superior post-adaptación en comparación con el agente estándar.

5.2 Análisis del Dashboard de Conocimiento

El mdu_dashboard.py permite la exploración interactiva del grafo de conocimiento generado por el pipeline de síntesis. Tras ingestar documentos y ejecutar los pasos del Eje Y a través de la API, el dashboard visualizará la jerarquía de conceptos y sus relaciones.

6. Guía de Instalación y Uso Avanzado
Instalación con Docker (Recomendado)
Generated bash
# 1. Clonar el repositorio
git clone <URL_DEL_REPOSITORIO>
cd <DIRECTORIO_RAIZ>

# 2. Construir e iniciar todos los servicios
# (Desde el directorio que contiene docker-compose.yml, ej. Aletheia_v3/)
docker-compose up --build
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END
Uso Avanzado: API Programática

La API RESTful permite la integración y automatización de los flujos de trabajo de Aletheia.

Generated python
# Ejemplo: Script para ejecutar un pipeline de síntesis completo
import requests
import time
import uuid

API_URL = "http://localhost:8000/api/v1"
HEADERS = {"Authorization": "Bearer <TU_TOKEN_JWT>"} # Reemplazar con un token válido

def run_full_synthesis(document_text: str):
    # 1. Ingesta
    ingest_payload = {"document_text": document_text, "source_doi": f"doi:demo/{uuid.uuid4()}"}
    response = requests.post(f"{API_URL}/eje-x/ingest-document", json=ingest_payload, headers=HEADERS)
    response.raise_for_status()
    ingest_data = response.json()
    ucm_ids = [ucm['id'] for ucm in ingest_data['ucm_extraction_result']['extracted_concepts']]
    print(f"Documento ingerido. {len(ucm_ids)} UCMs extraídos.")

    if not ucm_ids: return

    # 2. Clusterización
    cluster_payload = {"ucm_ids": ucm_ids}
    response = requests.post(f"{API_URL}/eje-y/cluster-formation", json=cluster_payload, headers=HEADERS)
    cluster_data = response.json()
    cluster_ids = [c['id'] for c in cluster_data.get('created_clusters', [])]
    print(f"{len(cluster_ids)} clúster(es) formados.")

    # ... continuar con los siguientes pasos del pipeline (proposiciones, teorías, etc.)

if __name__ == "__main__":
    run_full_synthesis("El concepto de energía oscura...")
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Python
IGNORE_WHEN_COPYING_END
7. Licencia y Consideraciones Éticas

Este proyecto se distribuye bajo la Licencia Apache 2.0 (ver LICENSE). Se espera que los usuarios actúen con integridad científica y ética. Consulte el DISCLAIMER.md para un entendimiento completo de las limitaciones y el uso previsto del software.

8. Hoja de Ruta y Contribuciones

Q4 2024: Refinamiento de las funciones de verosimilitud L(D|M) para cada nivel de síntesis.

Q1 2025: Implementación de un CognitiveBiasTracker para modular el parámetro (\lambda) en el motor MDL.

Q2 2025: Integración de modelos de lenguaje avanzados (Transformers) en el ABCToUCMMapper para una extracción de UCMs más semántica.

Las contribuciones son bienvenidas. Por favor, adhérase a los principios del MDU y siga el proceso estándar de Fork y Pull Request.

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
