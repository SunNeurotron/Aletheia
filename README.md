<div align="center">
<img width="1536" height="1024" alt="Aletheia Unificada - Un Organismo Científico Digital" src="https://github.com/user-attachments/assets/3f19aa7e-6a92-420b-9935-9f2e22545c24" />
<h1>ALETHEIA UNIFICADA v5.0</h1>
<h3>Un Organismo Científico Digital Auto-Reflexivo</h3>
<h4>Un Marco Computacional para la Gnoseología Aplicada y el Descubrimiento Científico Autónomo</h4>
<p>
<a href="LICENSE"><img src="https://img.shields.io/badge/License-AUEPL-red.svg" alt="AUEPL License"></a>
<img src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python" alt="Python 3.11+">
<img src="https://img.shields.io/badge/Status-Hoja%20de%20Ruta%20Activa-blueviolet" alt="Active Roadmap">
<img src="https://img.shields.io/badge/Paradigm-Cognitive%20Architecture-9cf" alt="Cognitive Architecture">
<img src="https://img.shields.io/badge/Docker-24.0+-2496ED?logo=docker" alt="Docker">
<img src="https://img.shields.io/badge/PostgreSQL-15+-336791?logo=postgresql" alt="PostgreSQL">
<img src="https://img.shields.io/badge/PyTorch-2.2+-EE4C2C?logo=pytorch" alt="PyTorch">
<img src="https://img.shields.io/badge/MLflow-2.7+-0194E2?logo=mlflow" alt="MLflow">
</p>
</div>

**Tabla de Contenidos**

1.  [Visión y Fundamento Filosófico: El Organismo Científico Digital](#1-visión-y-fundamento-filosófico-el-organismo-científico-digital)
    1.1. [Los Cuatro Pilares Cognitivos](#11-los-cuatro-pilares-cognitivos)
    1.2. [Objetivo Final del Sistema](#12-objetivo-final-del-sistema)
2.  [Arquitectura Cognitiva General](#2-arquitectura-cognitiva-general)
3.  [La Hoja de Ruta de Unificación (Roadmap v5.0+)](#3-la-hoja-de-ruta-de-unificación-roadmap-v50)
4.  [Componentes Clave del Ecosistema Unificado](#4-componentes-clave-del-ecosistema-unificado)
5.  [Gobernanza: Principios del MDU y Licenciamiento Ético](#5-gobernanza-principios-del-mdu-y-licenciamiento-ético)
6.  [Instalación y Estado Actual](#6-instalación-y-estado-actual)
7.  [Demostración Práctica Completa](#7-demostración-práctica-completa)
    7.1. [Escenario de Demostración End-to-End](#71-escenario-de-demostración-end-to-end)
    7.2. [Resultados Esperados de la Demostración](#72-resultados-esperados-de-la-demostración)
8.  [API y Endpoints](#8-api-y-endpoints)
    8.1. [Documentación OpenAPI](#81-documentación-openapi)
    8.2. [Autenticación y Autorización](#82-autenticación-y-autorización)
    8.3. [Endpoints Principales por Módulo](#83-endpoints-principales-por-módulo)
    8.4. [WebSocket para Actualizaciones en Tiempo Real](#84-websocket-para-actualizaciones-en-tiempo-real)
9.  [Testing y Calidad del Código](#9-testing-y-calidad-del-código)
    9.1. [Estrategia de Testing](#91-estrategia-de-testing)
    9.2. [Cobertura de Código](#92-cobertura-de-código)
    9.3. [Análisis Estático y Linting](#93-análisis-estático-y-linting)
    9.4. [CI/CD Pipeline](#94-cicd-pipeline)
10. [Publicaciones y Referencias Fundamentales](#10-publicaciones-y-referencias-fundamentales)
    10.1. [Publicaciones del Proyecto](#101-publicaciones-del-proyecto)
    10.2. [Referencias Fundamentales](#102-referencias-fundamentales)
    10.3. [Contacto y Colaboración](#103-contacto-y-colaboración)

---

## 1. Visión y Fundamento Filosófico: El Organismo Científico Digital

Aletheia Unificada representa la siguiente etapa evolutiva del proyecto Aletheia. Trascendemos el concepto de una "plataforma" para construir un **Organismo Científico Digital (OCD)**: un sistema computacional unificado capaz de un ciclo de investigación autónomo, desde la formulación de hipótesis hasta la síntesis de teorías, la autocrítica metodológica y la evolución de sus propios procesos de descubrimiento.

Nuestro marco filosófico se basa en la **Gnoseología Aplicada**, donde la computación no es solo una herramienta para la ciencia, sino un laboratorio para modelar y entender la naturaleza misma del conocimiento.

### 1.1. Los Cuatro Pilares Cognitivos

El sistema integra cuatro paradigmas conceptuales en una arquitectura sinérgica:

*   **Aletheia (Neocórtex):** El motor de síntesis de conocimiento a gran escala, responsable de la ingesta de datos, la construcción de grafos de conocimiento y la orquestación de la infraestructura.
*   **Carlota (Córtex Prefrontal):** El motor de meta-cognición y crítica. Utiliza el Principio de Mínima Descripción (MDL) y la computación de paisajes de atractores (ASC) para evaluar la robustez, coherencia y los sesgos de las trayectorias de investigación del propio sistema.
*   **AGIHD (Sistema Límbico/Hipocampo):** El motor de aprendizaje y adaptación. Implementa agentes con plasticidad sináptica y meta-plasticidad, permitiendo que el sistema no solo aprenda sobre el mundo, sino que *aprenda a aprender mejor*.
*   **Plaskitcs (Cerebelo/Computación Emergente):** Un paradigma de cómputo no neuronal basado en autómatas celulares sobre grafos. Proporciona un modo de razonamiento alternativo para problemas de satisfacción de restricciones y reconocimiento de patrones complejos.

### 1.2. Objetivo Final del Sistema

El objetivo no es crear una "IA que responde preguntas", sino un **agente epistémico autónomo** capaz de:

1.  **Generar Conocimiento Nuevo y Verificable:** Producir hipótesis, teorías y modelos que sean matemáticamente válidos y empíricamente falsables.
2.  **Auto-Mejora Metodológica:** Analizar su propio rendimiento y evolucionar sus estrategias de descubrimiento para ser más eficiente y robusto.
3.  **Operar dentro de un Marco Ético Computacional:** Integrar la gobernanza ética como un mecanismo funcional intrínseco.

## 2. Arquitectura Cognitiva General

Aletheia Unificada está diseñada como una jerarquía de sistemas cognitivos interdependientes, donde Aletheia Core actúa como el orquestador ejecutivo.

```mermaid
graph TD
    subgraph "Aletheia Unificada: Organismo Científico Digital"
        direction LR

        subgraph "Capa de Ejecución e Interfaz (Neocórtex)"
            ALETHEIA[Aletheia Core Engine<br/>API Gateway & Orquestación]
        end

        subgraph "Capa de Crítica y Meta-Cognición (Córtex Prefrontal)"
            CARLOTA[Motor Dialéctico & Validador ASC<br/>(MDL, Estabilidad Conceptual, Sesgos)]
        end

        subgraph "Capa de Aprendizaje y Descubrimiento (Sistema Límbico)"
            AGIHD[Agente Adaptativo<br/>(Plasticidad, Meta-Plasticidad)]
        end

        subgraph "Capa de Cómputo Alternativo (Computación Emergente)"
            PLASKITCS[Núcleo de Autómata Celular<br/>(Inhibición, Satisfacción de Restricciones)]
        end
    end

    ALETHEIA -- "1. Delega Tarea de Descubrimiento" --> AGIHD
    ALETHEIA -- "5. Delega Problema de Patrones" --> PLASKITCS

    AGIHD -- "2. Produce Trayectoria de Hipótesis" --> CARLOTA
    CARLOTA -- "3. Analiza Sesgos y Estabilidad" --> AGIHD
    AGIHD -- "4. Adapta Mecanismos de Aprendizaje" --> AGIHD

    CARLOTA -- "6. Modula 'Física' del Cómputo" --> PLASKITCS

    style Aletheia fill:#d2eaff
    style Carlota fill:#e8dff5
    style AGIHD fill:#d5f4e6
    style Plaskitcs fill:#fcf6bd
```
## 3. La Hoja de Ruta de Unificación (Roadmap v5.0+)

La construcción de Aletheia Unificada es un proceso iterativo y metódico. La siguiente hoja de ruta describe las fases principales del desarrollo.

### Fase 0: Consolidación Arquitectónica (Completada)

*   **Unificación de la Base Común (`aletheia_common`):** Centralización de la autenticación (`jwt_handler.py`, `schemas.py`), modelos de base de datos (`ResearcherDB` en `auth/models.py`), y tipos de base de datos (`db/base.py`, `db/custom_types.py`).
*   **Refactorización de Módulos:** Adaptación de `Aletheia_v3` y `aletheia_stats` para consumir la nueva base común, eliminando código redundante.
*   **Estabilización de la Suite de Pruebas:** Corrección de todos los errores de integración (`OperationalError`, `AttributeError`), sintaxis y dependencias (`ImportError`, `NameError`) hasta que `pytest` se ejecute sin fallos en ambos módulos.

### Fase 1: Implementación del Marco de Gobernanza (Completada)

*   **Transición de Licencia:** Reemplazo de la licencia Apache 2.0 por la **AUEPL (Aletheia Unificada Ethical Public License)**, una licencia dual que combina Apache 2.0 con un addendum ético y comercial.
*   **Actualización de Documentación:** Reflejo del nuevo marco de licenciamiento en todos los archivos `README.md` y `NOTICE`.
*   **Creación de `CONTRIBUTING.md`:** Documentación de las nuevas directrices para contribuidores bajo la AUEPL.
*   **Etiquetado de Versión:** Creación del tag de Git `v4.2.0-apache-final` para marcar la última versión puramente Apache 2.0.

### Fase 2: Integración de la Crítica y la Optimización (En Progreso)

*   **Tarea `TASK-SYNTHESIS-P2-001`:**
    *   **Creación del Paquete `mdl_synthesis`:** Crear la estructura de directorios `Aletheia_v3/core/mdl_synthesis/` y `Aletheia_v3/application/mdl_synthesis_use_cases.py`. Portar los componentes de `aletheia_omega` (entidades, servicios de complejidad y coste).
    *   **Implementación de `LikelihoodService`:** Implementar una nueva `LikelihoodService` en `Aletheia_v3` que defina la función `L(D|M)` para, como mínimo, la probabilidad de un conjunto de UCMs dado un modelo de clúster `L(UCMs | Cluster)` y la probabilidad de un conjunto de proposiciones dada una mini-teoría `L(Proposiciones | Mini-Teoría)`. La implementación debe ser robusta y estar documentada.
    *   **Refactorización de Casos de Uso del Eje Y:** Modificar `FormClustersUseCase`, `DerivePropositionsUseCase`, etc., para que generen un conjunto de modelos candidatos y utilicen el `FindOptimalModelUseCase` para seleccionar el mejor candidato según el coste MDL.
    *   **Almacenamiento de Metadatos MDL:** Cuando un `ScientificConcept` es creado vía optimización MDL, sus `properties` deben ser enriquecidas con los detalles de la optimización (`complexity`, `log_likelihood`, `mdl_cost`, etc.).
    *   **Pruebas de Validación:** Crear una nueva suite de pruebas en `Aletheia_v3/tests/core/mdl_synthesis/` y actualizar las pruebas de integración existentes para el Eje Y para validar el nuevo flujo basado en MDL.

### Fase 3: Integración del Motor de Aprendizaje Adaptativo (Q2 2025)

*   **Reemplazo del Motor de Descubrimiento:** El `IntelligentSearchUseCase` de Aletheia será reemplazado por una interfaz que delega las tareas de descubrimiento al motor **AGIHD**.
*   **Implementación del Bucle de Retroalimentación:** Conectar la salida del Motor Dialéctico de Carlota (análisis de sesgos y estabilidad) con el `MetaPlasticityController` de AGIHD para permitir que el agente ajuste sus propias estrategias de aprendizaje.

### Fase 4: Integración del Cómputo Pluralista y Despliegue Alfa (Q3-Q4 2025)

*   **Integración del Núcleo Plaskitcs:** Implementar en Aletheia un despachador de tareas que pueda enrutar ciertos tipos de problemas (ej. satisfacción de restricciones) al motor de cómputo emergente.
*   **Gobernanza Ética Activa:** Implementar los "ganchos" inhibitorios para que el orquestador de Aletheia pueda vetar computacionalmente tareas que violen las directivas éticas.
*   **Versión Alfa de Aletheia Unificada:** Desplegar una primera versión del sistema unificado completo en un entorno de staging en Kubernetes para pruebas y validación a gran escala.

## 4. Componentes Clave del Ecosistema Unificado

La arquitectura unificada se apoya en los siguientes componentes de software y tecnológicos:

| Componente                | Tecnología Principal          | Propósito en el Ecosistema Unificado                                                  |
| ------------------------- | ----------------------------- | ------------------------------------------------------------------------------------- |
| Orquestador y API         | FastAPI, Python 3.11+         | Proporciona la interfaz principal con el mundo y coordina los motores cognitivos.     |
| Bases de Conocimiento     | PostgreSQL 15+, SQLAlchemy 2.0 | Almacena el grafo de conocimiento (`scientific_concepts`), datos de investigadores, etc. |
| Motor de Aprendizaje      | PyTorch 2.2+                  | Implementa las redes neuronales con plasticidad y meta-plasticidad del motor AGIHD.   |
| Procesamiento Asíncrono   | Celery, Redis                 | Gestiona las tareas de descubrimiento y síntesis de larga duración.                   |
| Seguimiento de Experimentos | MLflow                        | Registra cada trayectoria de investigación, garantizando la reproducibilidad (Axioma MDU). |
| Visualización             | Streamlit                     | Proporciona dashboards interactivos para explorar el grafo de conocimiento y los resultados. |
| Despliegue                | Docker, Kubernetes            | Asegura la escalabilidad, resiliencia y gestión declarativa del sistema completo.    |

## 5. Gobernanza: Principios del MDU y Licenciamiento Ético

El desarrollo de Aletheia Unificada se rige por dos documentos fundacionales:

*   **`MDU_CORE_PRINCIPLES.md`:** La constitución técnica del proyecto. Define los estándares no negociables de calidad, rigor científico, arquitectura y reproducibilidad.
*   **`LICENSE`:** La licencia **AUEPL**, que establece el marco legal y ético. Garantiza la apertura para la investigación y la colaboración, mientras implementa restricciones de uso vinculantes y reserva los derechos comerciales. Incluye una cláusula de no responsabilidad explícita.

## 6. Instalación y Estado Actual

El proyecto se encuentra actualmente en la **Fase 2** de la hoja de ruta de unificación. La base de código ha sido consolidada y el marco de gobernanza legal ha sido implementado.

Para ejecutar el estado actual del proyecto (Aletheia v5.0-dev):

```bash
# 1. Clonar el repositorio
git clone https://github.com/SunNeurotron/Aletheia.git
cd Aletheia

# 2. Configurar variables de entorno
# Copie .env.example en Aletheia_v3/ y aletheia_stats/ y ajústelos si es necesario.
# Por ejemplo:
cp Aletheia_v3/.env.example Aletheia_v3/.env
cp aletheia_stats/.env.example aletheia_stats/.env

# 3. Construir e iniciar todos los servicios con Docker Compose
cd Aletheia_v3
docker-compose up --build -d

# 4. Verificar el estado de los servicios
docker-compose ps
```

Los servicios estarán disponibles en los puertos definidos en `docker-compose.yml` (API en 8000, Dashboard de Conocimiento en 8502, etc.).

## 7. Demostración Práctica Completa

Esta sección proporciona un escenario end-to-end para demostrar las capacidades actuales de Aletheia Unificada. Se ejecutará una secuencia de operaciones que incluyen la búsqueda de tripletas ABC, la síntesis de conocimiento a partir de un documento y el análisis estadístico.

### 7.1. Escenario de Demostración End-to-End

Primero, asegúrese de que todos los servicios estén en ejecución siguiendo los pasos de instalación anteriores. Las migraciones de la base de datos se aplican automáticamente al iniciar los servicios con Docker Compose.

Luego, puede ejecutar el siguiente script Python para ver el sistema en acción:

```python
# run_all_demos.py
import asyncio
import httpx
import numpy as np
from datetime import datetime
import json
import time # For monitoring job status more cleanly

async def demo_abc_search(client: httpx.AsyncClient, headers: dict):
    """
    Demostración completa de búsqueda ABC.
    """
    base_url = "http://localhost:8000"
    print("Iniciando búsqueda ABC...")
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
    print(f"Búsqueda ABC iniciada, Job ID: {job_id}")

    print(f"Monitoreando job {job_id}...")
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

    print("Recuperando resultados...")
    results_response = await client.get(
        f"{base_url}/api/abc/results/{job_id}",
        headers=headers
    )
    results = results_response.json()

    print("Mejores tripletas encontradas:")
    for i, triple in enumerate(results['best_triples'][:10]):
        print(f"   {i+1}. ({triple['a']}, {triple['b']}, {triple['c']}) "
              f"- Calidad: {triple['quality']:.4f}")
    print(f"Visualización disponible en: http://localhost:8501 (para dashboard de búsqueda)")
    return results

async def demo_knowledge_synthesis(client: httpx.AsyncClient, headers: dict):
    """
    Demostración del pipeline completo de síntesis de conocimiento.
    """
    base_url = "http://localhost:8000"
    print("Ingiriendo documento científico...")
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
    print(f"Documento ingerido, Document ID: {document_id}")

    print("Esperando extracción de UCMs (puede tomar un momento)...")
    await asyncio.sleep(10) # Give time for asynchronous UCM extraction

    ucms_response = await client.get(
        f"{base_url}/api/eje-x/concepts?concept_type=UCM&limit=50",
        headers=headers
    )
    ucms = ucms_response.json()["concepts"]
    print(f"   UCMs extraídas: {len(ucms)}")

    print("Formando clusters de conceptos...")
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
    print(f"   Clusters formados: {len(clusters)}")

    print("Derivando proposiciones...")
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
    print(f"   Proposiciones derivadas: {len(propositions)}")

    print("Construyendo mini-teorías...")
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
    print(f"   Mini-teorías construidas: {len(mini_theories)}")

    print(f"Grafo de conocimiento disponible en: http://localhost:8502 (para dashboard de conocimiento)")

    print("Jerarquía de síntesis:")
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

async def demo_statistical_analysis(client: httpx.AsyncClient, headers: dict):
    """
    Demostración de análisis estadístico con MLflow.
    """
    stats_url = "http://localhost:8001"
    print("Generando datos experimentales sintéticos...")
    np.random.seed(42)

    control_group = np.random.normal(100, 15, 50)
    treatment_group = np.random.normal(110, 15, 50)

    print("Ejecutando prueba t...")
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

    print("Resultados del análisis:")
    print(f"   Estadístico t: {results['t_statistic']:.4f}")
    print(f"   Valor p: {results['p_value']:.4f}")
    print(f"   Tamaño del efecto (d de Cohen): {results['cohens_d']:.4f}")
    print(f"   Intervalo de confianza: [{results['ci_lower']:.2f}, {results['ci_upper']:.2f}]")
    print(f"Experimento registrado en MLflow (Run ID: {results['mlflow_run_id']})")
    print(f"Ver en: http://localhost:5000/#/experiments/{results['mlflow_experiment_id']}")

    print("Realizando análisis de potencia...")
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

async def run_all_demos():
    base_url = "http://localhost:8000"

    print("Iniciando demostraciones de Aletheia Unificada...\n")

    async with httpx.AsyncClient(timeout=60.0) as client: # Increased timeout for long-running jobs
        # 1. Autenticación global para todas las demos
        print("1. Autenticando usuario para todas las demostraciones...")
        try:
            auth_response = await client.post(
                f"{base_url}/token",
                data={
                    "username": "demo_researcher",
                    "password": "demo_password"
                }
            )
            auth_response.raise_for_status() # Raise an exception for bad status codes
            token = auth_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print("   Autenticación exitosa.\n")
        except httpx.HTTPStatusError as e:
            print(f"   Error de autenticación: {e.response.status_code} - {e.response.text}")
            print("   Asegúrese de que el servicio de API esté corriendo y las credenciales sean correctas.")
            return
        except httpx.RequestError as e:
            print(f"   Error de conexión durante la autenticación: {e}")
            print("   Asegúrese de que el servicio de API esté corriendo en http://localhost:8000.")
            return

        # 2. Demostración de Búsqueda ABC
        print("\n--- INICIANDO DEMOSTRACIÓN DE BÚSQUEDA ABC ---")
        try:
            await demo_abc_search(client, headers)
        except Exception as e:
            print(f"   Ocurrió un error durante la demostración de búsqueda ABC: {e}")
            print("   Continuando con la siguiente demostración...")
        print("--- DEMOSTRACIÓN DE BÚSQUEDA ABC COMPLETADA ---\n")

        # 3. Demostración de Síntesis de Conocimiento
        print("\n--- INICIANDO DEMOSTRACIÓN DE SÍNTESIS DE CONOCIMIENTO ---")
        try:
            await demo_knowledge_synthesis(client, headers)
        except Exception as e:
            print(f"   Ocurrió un error durante la demostración de síntesis de conocimiento: {e}")
            print("   Continuando con la siguiente demostración...")
        print("--- DEMOSTRACIÓN DE SÍNTESIS DE CONOCIMIENTO COMPLETADA ---\n")

        # 4. Demostración de Análisis Estadístico
        print("\n--- INICIANDO DEMOSTRACIÓN DE ANÁLISIS ESTADÍSTICO ---")
        try:
            await demo_statistical_analysis(client, headers)
        except Exception as e:
            print(f"   Ocurrió un error durante la demostración de análisis estadístico: {e}")
        print("--- DEMOSTRACIÓN DE ANÁLISIS ESTADÍSTICO COMPLETADA ---\n")

    print("Todas las demostraciones principales han finalizado.")

if __name__ == "__main__":
    asyncio.run(run_all_demos())
```

### 7.2. Resultados Esperados de la Demostración

Estos son los puntos de referencia de rendimiento y las métricas de calidad que se esperan del sistema:

```yaml
Benchmarks de Rendimiento:
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
```

```yaml
Métricas de Calidad:
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
```

## 8. API y Endpoints

### 8.1. Documentación OpenAPI

La documentación completa de la API está disponible en formato OpenAPI/Swagger:

*   **Swagger UI:** `http://localhost:8000/docs`
*   **ReDoc:** `http://localhost:8000/redoc`
*   **OpenAPI JSON:** `http://localhost:8000/openapi.json`

### 8.2. Autenticación y Autorización

```http
POST /token
Content-Type: application/x-www-form-urlencoded

username=researcher@example.com&password=secure_password&grant_type=password

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

```http
GET /api/v1/protected-endpoint
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 8.3. Endpoints Principales por Módulo

```yaml
Ingesta de Documentos:
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

Formación de Clusters:
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

Análisis Cúbico:
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

Prueba T:
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
```

### 8.4. WebSocket para Actualizaciones en Tiempo Real

```python
# Cliente WebSocket ejemplo
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

if __name__ == "__main__":
    # Este es un ejemplo. Deberías obtener un token de autenticación válido primero.
    # Por ejemplo, ejecutando la demo completa y extrayendo el token.
    # asyncio.run(monitor_job("your_job_id_here", "your_auth_token_here"))
    print("Para ejecutar este ejemplo, reemplace 'your_job_id_here' y 'your_auth_token_here' con valores reales.")
```

## 9. Testing y Calidad del Código

### 9.1. Estrategia de Testing

```mermaid
graph TB
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
```

```python
# tests/test_domain.py
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
```

```python
# tests/test_api_integration.py
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession # Assuming this fixture is provided by pytest config

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
        await asyncio.sleep(5) # Give time for asynchronous processing

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
```

```python
# tests/test_performance.py
import pytest
import time
from aletheia_v3.core.domain import _radical
from httpx import Client # Assuming Client fixture for sync calls or AsyncClient for async

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
    def test_api_throughput(self, client: Client, auth_headers: dict):
        """Test de throughput de API."""
        start_time = time.time()
        requests_count = 0

        # Ensure the client is properly configured for the base URL if not a fixture
        # For a simple test, assuming 'client' is an httpx.Client already pointed to the API
        while time.time() - start_time < 10:  # 10 segundos
            response = client.get(
                "http://localhost:8000/api/health", # Explicitly using localhost for demo
                headers=auth_headers
            )
            assert response.status_code == 200
            requests_count += 1

        rps = requests_count / 10
        assert rps > 100  # Mínimo 100 req/s
```

### 9.2. Cobertura de Código

```ini
# .coveragerc
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
```

Para ejecutar tests con cobertura:

```bash
pytest --cov=aletheia_v3 --cov=aletheia_stats \
       --cov-report=term-missing \
       --cov-report=html \
       --cov-report=xml
```

Resultados esperados de ejemplo:

```
# Module                          Coverage
# aletheia_v3.core.domain           95%
# aletheia_v3.application           92%
# aletheia_v3.api                   88%
# aletheia_stats.domain             96%
# Overall                           91%
```

### 9.3. Análisis Estático y Linting

```ini
# mypy.ini
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
```

```yaml
# .pre-commit-config.yaml
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
```

### 9.4. CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
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
```

## 10. Publicaciones y Referencias Fundamentales

### 10.1. Publicaciones del Proyecto

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
```

### 10.2. Referencias Fundamentales

*   Oesterlé, J., & Masser, D. (1985). "Pour une théorie de l'effectivité." *Comptes Rendus de l'Académie des Sciences*.
*   Granville, A., & Stark, H. (2000). "ABC implies no Siegel zeros for L-functions of characters with negative discriminant." *Inventiones Mathematicae, 139*(3), 509-523.
*   Stewart, C. L., & Yu, K. (2001). "On the abc conjecture II." *Duke Mathematical Journal, 108*(1), 169-181.
*   Snoek, J., Larochelle, H., & Adams, R. P. (2012). "Practical Bayesian optimization of machine learning algorithms." *Advances in Neural Information Processing Systems, 25*.
*   Shahriari, B., Swersky, K., Wang, Z., Adams, R. P., & De Freitas, N. (2015). "Taking the human out of the loop: A review of Bayesian optimization." *Proceedings of the IEEE, 104*(1), 148-175.
*   Rissanen, J. (1978). "Modeling by shortest data description." *Automatica, 14*(5), 465-471.
*   Grünwald, P. D. (2007). *The Minimum Description Length Principle*. MIT Press.
*   Vitányi, P. M., & Li, M. (2000). "Minimum description length induction, Bayesianism, and Kolmogorov complexity." *IEEE Transactions on Information Theory, 46*(2), 446-464.
*   Manning, C. D., & Schütze, H. (1999). *Foundations of Statistical Natural Language Processing*. MIT Press.
*   Jurafsky, D., & Martin, J. H. (2020). *Speech and Language Processing* (3rd ed.). Pearson.

### 10.3. Contacto y Colaboración

**Equipo de Investigación Aletheia**

Alant Research

*   **Email:** `aletheia-research@alant.com`
*   **GitHub:** `https://github.com/SunNeurotron/Aletheia`

Para colaboraciones académicas:

*   Propuestas de investigación conjunta
*   Acceso a datasets de investigación
*   Participación en benchmarks
*   Contribuciones al código abierto

**Licencia:** AUEPL
**Copyright:** © 2025 Alant

<div align="center">
<p><strong>Aletheia Unificada v5.0 - La Verdad Revelada a través de la Cognición Computacional</strong></p>
<p><em>"Nosce te ipsum" - Conócete a ti mismo</em></p>
</div>
