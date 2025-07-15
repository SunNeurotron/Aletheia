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

Unificación de la Base Común (aletheia_common): Centralización de la autenticación (jwt_handler.py, schemas.py), modelos de base de datos (ResearcherDB en auth/models.py), y tipos de base de datos (db/base.py, db/custom_types.py).

Refactorización de Módulos: Adaptación de Aletheia_v3 y aletheia_stats para consumir la nueva base común, eliminando código redundante.

Estabilización de la Suite de Pruebas: Corrección de todos los errores de integración (OperationalError, AttributeError), sintaxis y dependencias (ImportError, NameError) hasta que pytest se ejecute sin fallos en ambos módulos.

### Fase 1: Implementación del Marco de Gobernanza (Completada)

Transición de Licencia: Reemplazo de la licencia Apache 2.0 por la AUEPL (Aletheia Unificada Ethical Public License), una licencia dual que combina Apache 2.0 con un addendum ético y comercial.

Actualización de Documentación: Reflejo del nuevo marco de licenciamiento en todos los archivos README.md y NOTICE.

Creación de CONTRIBUTING.md: Documentación de las nuevas directrices para contribuidores bajo la AUEPL.

Etiquetado de Versión: Creación del tag de Git v4.2.0-apache-final para marcar la última versión puramente Apache 2.0.

### Fase 2: Integración de la Crítica y la Optimización (En Progreso)

Tarea TASK-SYNTHESIS-P2-001:

Creación del Paquete mdl_synthesis: Crear la estructura de directorios Aletheia_v3/core/mdl_synthesis/ y Aletheia_v3/application/mdl_synthesis_use_cases.py. Portar los componentes de aletheia_omega (entidades, servicios de complejidad y coste).

Implementación de LikelihoodService: Implementar una nueva LikelihoodService en Aletheia_v3 que defina la función L(D|M) para, como mínimo, la probabilidad de un conjunto de UCMs dado un modelo de clúster L(UCMs | Cluster) y la probabilidad de un conjunto de proposiciones dada una mini-teoría L(Proposiciones | Mini-Teoría). La implementación debe ser robusta y estar documentada.

Refactorización de Casos de Uso del Eje Y: Modificar FormClustersUseCase, DerivePropositionsUseCase, etc., para que generen un conjunto de modelos candidatos y utilicen el FindOptimalModelUseCase para seleccionar el mejor candidato según el coste MDL.

Almacenamiento de Metadatos MDL: Cuando un ScientificConcept es creado vía optimización MDL, sus properties deben ser enriquecidas con los detalles de la optimización (complexity, log_likelihood, mdl_cost, etc.).

Pruebas de Validación: Crear una nueva suite de pruebas en Aletheia_v3/tests/core/mdl_synthesis/ y actualizar las pruebas de integración existentes para el Eje Y para validar el nuevo flujo basado en MDL.

### Fase 3: Integración del Motor de Aprendizaje Adaptativo (Q2 2025)

Reemplazo del Motor de Descubrimiento: El IntelligentSearchUseCase de Aletheia será reemplazado por una interfaz que delega las tareas de descubrimiento al motor AGIHD.

Implementación del Bucle de Retroalimentación: Conectar la salida del Motor Dialéctico de Carlota (análisis de sesgos y estabilidad) con el MetaPlasticityController de AGIHD para permitir que el agente ajuste sus propias estrategias de aprendizaje.

### Fase 4: Integración del Cómputo Pluralista y Despliegue Alfa (Q3-Q4 2025)

Integración del Núcleo Plaskitcs: Implementar en Aletheia un despachador de tareas que pueda enrutar ciertos tipos de problemas (ej. satisfacción de restricciones) al motor de cómputo emergente.

Gobernanza Ética Activa: Implementar los "ganchos" inhibitorios para que el orquestador de Aletheia pueda vetar computacionalmente tareas que violen las directivas éticas.

Versión Alfa de Aletheia Unificada: Desplegar una primera versión del sistema unificado completo en un entorno de staging en Kubernetes para pruebas y validación a gran escala.

## 4. Componentes Clave del Ecosistema Unificado

La arquitectura unificada se apoya en los siguientes componentes de software y tecnológicos:

| Componente                | Tecnología Principal          | Propósito en el Ecosistema Unificado                                                  |
| ------------------------- | ----------------------------- | ------------------------------------------------------------------------------------- |
| **Orquestador y API**     | FastAPI, Python 3.11+         | Proporciona la interfaz principal con el mundo y coordina los motores cognitivos.     |
| **Bases de Conocimiento** | PostgreSQL 15+, SQLAlchemy 2.0 | Almacena el grafo de conocimiento (`scientific_concepts`), datos de investigadores, etc. |
| **Motor de Aprendizaje**  | PyTorch 2.2+                  | Implementa las redes neuronales con plasticidad y meta-plasticidad del motor AGIHD.   |
| **Procesamiento Asíncrono**| Celery, Redis                 | Gestiona las tareas de descubrimiento y síntesis de larga duración.                   |
| **Seguimiento de Experimentos**| MLflow                   | Registra cada trayectoria de investigación, garantizando la reproducibilidad (Axioma MDU). |
| **Visualización**         | Streamlit                     | Proporciona dashboards interactivos para explorar el grafo de conocimiento y los resultados. |
| **Despliegue**            | Docker, Kubernetes            | Asegura la escalabilidad, resiliencia y gestión declarativa del sistema completo.      |

## 5. Gobernanza: Principios del MDU y Licenciamiento Ético

El desarrollo de Aletheia Unificada se rige por dos documentos fundacionales:

*   **MDU_CORE_PRINCIPLES.md:** La constitución técnica del proyecto. Define los estándares no negociables de calidad, rigor científico, arquitectura y reproducibilidad.
*   **LICENSE:** La licencia AUEPL, que establece el marco legal y ético. Garantiza la apertura para la investigación y la colaboración, mientras implementa restricciones de uso vinculantes y reserva los derechos comerciales. Incluye una cláusula de no responsabilidad explícita.

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

Los servicios estarán disponibles en los puertos definidos en docker-compose.yml (API en 8000, Dashboard de Conocimiento en 8502, etc.).

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

*   **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
*   **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
*   **OpenAPI JSON:** [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

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
...
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
### 9.3. Análisis Estático y Linting
```ini
# mypy.ini
[mypy]
python_version = 3.9
warn_return_any = True
...
```
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
...
```
### 9.4. CI/CD Pipeline
```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
...
```
## 10. Publicaciones y Referencias Fundamentales
### 10.1. Publicaciones del Proyecto
```bibtex
@article{aletheia2024,
...
}
```
### 10.2. Referencias Fundamentales
...
### 10.3. Contacto y Colaboración
...
---
<div align="center">
<p><strong>Aletheia Unificada v5.0 - La Verdad Revelada a través de la Cognición Computacional</strong></p>
<p><em>"Nosce te ipsum" - Conócete a ti mismo</em></p>
</div>
