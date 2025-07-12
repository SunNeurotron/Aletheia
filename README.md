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
5.  [**Validación Empírica y Visualización de Resultados**](#5-validación-empírica-y-visualización-de-resultados)
6.  [**Guía de Inicio y Uso Avanzado**](#6-guía-de-inicio-y-uso-avanzado)
7.  [**Licencia y Consideraciones Éticas**](#7-licencia-y-consideraciones-éticas)
8.  [**Hoja de Ruta y Contribuciones**](#8-hoja-de-ruta-y-contribuciones)

## **1. Fundamento Teórico y Filosófico**

Aletheia se fundamenta en la premisa de que la ciencia es un proceso inherentemente dinámico y de compresión de información. La arquitectura del framework refleja esta visión a través de principios clave:

-   **Gnoseología Computacional**: El objetivo del framework no es meramente generar "insights", sino modelar el **proceso de construcción de conocimiento** (`gnosis`). El pipeline de síntesis del Eje Y formaliza un ascenso inductivo desde la evidencia (`DOCUMENT_SOURCE`) hasta la abstracción teórica (`UNIFIED_MODEL`).
-   **Principio Variacional de Mínima Longitud Descriptiva (MDL)**: Aletheia se adhiere al principio MDL, una formalización de la Navaja de Ockham. La selección de la "mejor" teoría o modelo en cada etapa de la síntesis se realiza minimizando la función de coste, análoga a una energía libre informacional:
    $$ L(M, D) = \lambda \cdot K(M) - \log P(D|M) $$
    donde \(K(M)\) es la complejidad de Kolmogorov del modelo (aproximada por su longitud comprimida) y \(P(D|M)\) es la verosimilitud de los datos dado el modelo. Aletheia busca el balance óptimo entre la **simplicidad del modelo** y su **poder explicativo**.
-   **Emergencia y Jerarquía**: El conocimiento es jerárquico. El sistema modela explícitamente esta estructura a través del `ConceptType` Enum, donde cada nivel superior es una síntesis emergente de los componentes del nivel inferior, validada a través del principio MDL.

## **2. Arquitectura del Ecosistema Aletheia**

La plataforma está diseñada como un conjunto de servicios modulares y desacoplados, orquestados a través de Docker Compose y preparados para Kubernetes, siguiendo los principios de la **Arquitectura Hexagonal**.

```mermaid
graph LR
    subgraph Externo
        A["<br>Usuario/Investigador<br><br>🔬"]
    end

    subgraph "Capa de Presentación"
        B(API FastAPI<br>/api/v1)
        C(Dashboard<br>Streamlit)
    end

    subgraph "Capa de Aplicación"
        D[Casos de Uso<br>Eje Y (Síntesis)<br>Eje X (Ingesta)<br>Búsqueda ABC]
    end

    subgraph "Núcleo de Dominio"
        E[Entidades<br>ScientificConcept<br>ABCTriple]
        F[Servicios de Dominio<br>MDL Engine<br>StatsService]
    end

    subgraph "Infraestructura"
        G["<br>PostgreSQL<br>(SQLAlchemy)<br><br>🐘"]
        H["<br>Redis<br>(Celery Broker)<br><br>🏎️"]
        I["<br>MLflow<br>(Tracking)<br><br>📈"]
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

Módulo Principal (Aletheia_v3): Contiene el núcleo lógico, dividido en capas: api, application, core, infrastructure, y dashboard.

Módulo Común (aletheia_common): Librería compartida para utilidades transversales como autenticación JWT.

Contenerización y Orquestación: Dockerfile y docker-compose.yml aseguran un entorno de ejecución reproducible. Alembic gestiona las migraciones de base de datos.

3. El Pipeline de Síntesis de Conocimiento (Eje Y)

El corazón funcional de Aletheia es el pipeline de síntesis del Eje Y. Cada transición entre niveles es un proceso competitivo de selección de modelos basado en MDL.

Ingesta (Eje X): Un documento (DOCUMENT_SOURCE) es procesado para extraer Unidades Conceptuales Mínimas (UCM).

Clusterización: Se generan múltiples CLUSTERs candidatos. El FindOptimalModelUseCase selecciona el que mejor comprime la información de sus UCMs miembros.

Derivación de Proposiciones: De cada CLUSTER se derivan candidatas a PROPOSITION. Se selecciona la más concisa y explicativa.

Construcción de Teorías: El proceso se repite en niveles superiores, integrando MINI_THEORYs en COMPREHENSIVE_THEORYs y estas en UNIFIED_MODELs.

4. El Motor de Optimización MDL

El FindOptimalModelUseCase es el componente central que implementa el principio MDL.

Generación de Candidatos: Para cada etapa, se generan múltiples modelos candidatos.

Evaluación MDL: Cada candidato es evaluado usando la función de coste. El LikelihoodService es crucial aquí, evaluando L(D|M).

Selección: El modelo con el coste MDL más bajo es seleccionado.

5. Validación Empírica y Visualización de Resultados

La validación empírica es un pilar del proyecto. A continuación se presentan los resultados visuales generados directamente por los componentes del framework.

5.1 Validación del Agente de Búsqueda ABC

El script experimento_validacion_agi.py valida la hipótesis de que la plasticidad sináptica mejora la adaptación en entornos no estacionarios.

<div align="center">
<img src="./adaptacion_comparison.png" alt="Gráfico de comparación de rendimiento entre un DQN Plástico y un DQN Estándar durante un cambio de entorno." width="800"/>
<p><i><b>Figura 1:</b> Resultado empírico de la validación del agente. La curva azul (agente plástico) muestra una capacidad de recuperación marcadamente superior tras la perturbación del entorno (línea vertical).</i></p>
</div>

5.2 Dashboards de Análisis Comprehensivo

Los componentes de visualización en React (AGIComprehensiveVisualizations.jsx) ofrecen un análisis holístico de las arquitecturas AGI.

<div align="center">
<img src="./assets/comprehensive_dashboard_overview.png" alt="Vista del Dashboard de Análisis Comprehensivo para AGI v3.0" width="900"/>
<p><i><b>Figura 2:</b> Vista general del Dashboard de Análisis para el sistema AGI v3.0, mostrando múltiples facetas del rendimiento, evolución y potencial de mercado.</i></p>
</div>

<br>

<div style="display: flex; justify-content: space-around; gap: 20px; flex-wrap: wrap;">
<div style="text-align: center; flex: 1; min-width: 400px;">
<img src="./assets/performance_radar_chart.png" alt="Gráfico de radar comparando las capacidades de diferentes versiones de AGI." width="450"/>
<p><i><b>Figura 3:</b> Comparativa de capacidades clave donde AGI v3 (azul) supera a modelos tradicionales.</i></p>
</div>
<div style="text-align: center; flex: 1; min-width: 400px;">
<img src="./assets/roi_projection_chart.png" alt="Gráfico de proyección de ROI, inversión y ingresos." width="450"/>
<p><i><b>Figura 4:</b> Proyección de Retorno de Inversión (ROI) y flujo de caja del proyecto.</i></p>
</div>
</div>


NOTA: Para generar estos gráficos, ejecute los scripts experimento_validacion_agi.py y el servidor de desarrollo de React (npm start) y capture las imágenes correspondientes, ubicándolas en las rutas ./ y ./assets/.

6. Guía de Inicio y Uso Avanzado
Instalación con Docker (Recomendado)
Generated bash
# Desde el directorio raíz del proyecto
docker-compose -f Aletheia_v3/docker-compose.yml up --build
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

    # ... continuar con los siguientes pasos del pipeline ...
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Python
IGNORE_WHEN_COPYING_END
7. Licencia y Consideraciones Éticas

Distribuido bajo la Licencia Apache 2.0. Consulte LICENSE y DISCLAIMER.md. Se espera que los usuarios actúen con integridad científica y ética.

8. Hoja de Ruta y Contribuciones

Q4 2024: Refinamiento de las funciones de verosimilitud L(D|M); integración de LLMs para la generación de descripciones en PROPOSITIONs.

Q1 2025: Implementación de un Motor Dialéctico para la refutación y evolución de teorías.

Q2 2025: Integración con bases de datos de grafos nativas.

Las contribuciones son bienvenidas. Por favor, siga el proceso estándar de Fork y Pull Request.

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
