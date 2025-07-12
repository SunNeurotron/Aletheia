<div align="center">
<img width="1536" height="1024" alt="Image" src="https://github.com/user-attachments/assets/3f19aa7e-6a92-420b-9935-9f2e22545c24" />
(https://github.com/SunNeurotron/Aletheia/issues/102)
<h1>Aletheia: Un Ecosistema para la Epistemología Asistida por IA</h1>
<p><strong>Un paradigma computacional para modelar la dinámica del descubrimiento científico.</strong></p>

<p>
<a href="./LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="License: Apache 2.0"></a>
<a href="#"><img src="https://img.shields.io/badge/Paradigm-MDU_&_Knowledge_Synthesis-blueviolet" alt="Paradigm: MDU & Knowledge Synthesis"></a>
<a href="#"><img src="https://img.shields.io/badge/python-3.9+-yellow.svg" alt="Python Version"></a>
<a href="#"><img src="https://img.shields.io/badge/version-4.0.0-blue.svg" alt="Version"></a>
<a href="./docs/THEORY.md"><img src="https://img.shields.io/badge/docs-theoretical-green.svg" alt="Documentation"></a>
</p>
</div>

> **Prólogo:** Aletheia es un artefacto computacional que va más allá de la mera computación científica para convertirse en un laboratorio de gnoseología aplicada. No es simplemente una herramienta, sino un ecosistema de software donde la dinámica del descubrimiento —la emergencia de la estructura desde el caos de los datos, la formulación de conjeturas y la validación rigurosa— puede ser modelada, ejecutada y analizada. Su arquitectura propone un modelo sobre cómo la computación puede servir de andamiaje para la epistemología, explorando la estabilidad, la emergencia y la evolución de las ideas científicas.

---

## **Índice Analítico**
1.  [**Fundamento Epistemológico y Filosófico**](#1-fundamento-epistemológico-y-filosófico)
2.  [**Arquitectura y Ecosistema de Componentes**](#2-arquitectura-y-ecosistema-de-componentes)
3.  [**Modelos Computacionales del Descubrimiento**](#3-modelos-computacionales-del-descubrimiento)
    *   [El Motor de Síntesis de Conocimiento: Del Dato a la Teoría](#el-motor-de-síntesis-de-conocimiento)
    *   [El Motor de Búsqueda de Conjeturas: Falsacionismo Aplicado](#el-motor-de-búsqueda-de-conjeturas)
4.  [**Guía de Inicio y Uso**](#4-guía-de-inicio-y-uso)
5.  [**Validación, Pruebas y Benchmarks**](#5-validación-pruebas-y-benchmarks)
6.  [**Hoja de Ruta y Futuras Direcciones**](#6-hoja-de-ruta-y-futuras-direcciones)
7.  [**Licencia y Citación**](#7-licencia-y-citación)

---

## **1. Fundamento Epistemológico y Filosófico**

Aletheia se construye sobre la premisa de que la ciencia es un proceso dinámico y jerárquico. La arquitectura del framework refleja esta visión a través de varios principios clave:

-   **Jerarquía de Abstracción Epistémica**: Inspirado en la forma en que el conocimiento científico se estructura, el sistema modela explícitamente una jerarquía de entidades epistémicas. El conocimiento no es plano; emerge de la síntesis de componentes más simples. El **Motor de Síntesis** es la encarnación de este principio, transformando datos brutos en conceptos, conceptos en proposiciones y proposiciones en teorías.

-   **Falsacionismo Computacional**: En línea con la filosofía de Karl Popper, Aletheia no busca "probar" teorías, sino someterlas a un estrés riguroso. El **Motor de Búsqueda de Conjeturas** está diseñado para buscar activamente contraejemplos o "cisnes negros" que pongan a prueba los límites de una conjetura matemática, como la Conjetura ABC.

-   **Modelado, Descubrimiento y Comprensión (MDU)**: Este es el paradigma operativo central.
    -   **Modelado**: Representación del conocimiento en estructuras formales (grafos, ontologías).
    -   **Descubrimiento**: Generación de nuevas hipótesis y relaciones a través de la síntesis y la búsqueda heurística.
    -   **Comprensión**: Facilitación de la interpretación humana a través de visualizaciones interactivas y análisis estadísticos.

-   **Rigor Estadístico como Precondición**: Cualquier análisis cuantitativo dentro de Aletheia debe ser validado. El módulo `aletheia_stats` no solo calcula, sino que evalúa las condiciones de aplicabilidad de sus pruebas (ej. tests de normalidad), encarnando el principio de que la validez estadística es una precondición para la inferencia.

## **2. Arquitectura y Ecosistema de Componentes**

Aletheia está diseñada como un ecosistema de microservicios que colaboran para ofrecer una funcionalidad completa. El siguiente diagrama ilustra la arquitectura de alto nivel y las interacciones entre los componentes principales.

```mermaid
graph TD
    subgraph "User Layer"
        U[Investigador]
    end

    subgraph "Presentation Layer"
        DASH[Dashboard (Streamlit)]
    end

    subgraph "Core Services (Aletheia_v3)"
        API[API Principal (FastAPI)]
        WORKER[Worker (Celery)]
        DB_NUCLEO[(DB Principal: Grafo de Conocimiento)]
    end

    subgraph "Satellite Services"
        STATS[aletheia_stats API]
        OMEGA[aletheia_omega API]
        DB_STATS[(DB Stats: Experimentos Estadísticos)]
        DB_OMEGA[(DB Omega: Trayectorias de Optimización)]
    end

    subgraph "Supporting Infrastructure"
        MQ[Redis (Broker)]
        MLFLOW[MLflow (Tracking)]
    end

    U -- Interacciona con --> DASH
    DASH -- Peticiones HTTP --> API

    API -- Encola Tarea --> MQ
    WORKER -- Consume Tarea --> MQ
    WORKER -- Lógica de Dominio/Síntesis --> DB_NUCLEO
    WORKER -- Registra Experimento --> MLFLOW

    WORKER -- Petición de Análisis Estadístico --> STATS
    STATS -- Realiza Prueba t --> DB_STATS

    WORKER -- Petición de Optimización --> OMEGA
    OMEGA -- Registra Trayectoria --> DB_OMEGA

    style U fill:#fff,stroke:#333,stroke-width:2px
    style DASH fill:#f9f,stroke:#333,stroke-width:2px
    style API fill:#ccf,stroke:#333,stroke-width:2px
    style WORKER fill:#fcf,stroke:#333,stroke-width:2px
    style STATS fill:#c8e6c9,stroke:#333,stroke-width:2px
    style OMEGA fill:#bbdefb,stroke:#333,stroke-width:2px
```

### **Componentes del Ecosistema**
-   **Núcleo de Grafo de Conocimiento (`Aletheia_v3`)**: El corazón de la plataforma. Gestiona la ingesta (Eje X) y síntesis (Eje Y) del conocimiento. Su principal artefacto es un grafo de conocimiento persistido en PostgreSQL, compuesto por una tipología de nodos (`DOCUMENT_SOURCE`, `UCM`, `CLUSTER`, `PROPOSITION`, `MINI_THEORY`) que representan la jerarquía epistémica.

-   **Servicio de Análisis Estadístico (`aletheia_stats`)**: Un microservicio experto que proporciona endpoints para realizar pruebas de hipótesis. Cada análisis es un experimento trazable en MLflow, y sus resultados, incluyendo estadísticos clave e **intervalos de confianza**, se visualizan en el Dashboard.

-   **Servicio de Trayectorias de Optimización (`aletheia_omega`)**: Dedicado a gestionar y persistir los resultados de ejecuciones de algoritmos de búsqueda y optimización. Almacena la "trayectoria" completa de cada ejecución para permitir un análisis detallado post-hoc.

-   **Biblioteca Común (`aletheia_common`)**: Paquete interno con utilidades compartidas (autenticación, esquemas Pydantic) para garantizar la consistencia.

## **3. Modelos Computacionales del Descubrimiento**

### **El Motor de Síntesis de Conocimiento**
Este motor implementa el **Eje Y** del paradigma MDU. Es un pipeline algorítmico que construye niveles de abstracción crecientes.
1.  **Entrada**: Un conjunto de nodos de conocimiento de nivel $N$ (ej. UCMs).
2.  **Clustering**: Se agrupan los nodos basándose en métricas de similitud semántica o estructural (`FormClustersUseCase`).
3.  **Derivación de Proposiciones**: A partir de cada clúster, se intenta formular una proposición que capture la relación común (`DerivePropositionsUseCase`).
4.  **Construcción de Teorías**: Las proposiciones coherentes se agregan para formar "mini-teorías" (`MiniTheoryConstructionUseCase`).
5.  **Salida**: Un nuevo conjunto de nodos de nivel $N+1$ que se integra en el grafo de conocimiento.
Este proceso es recursivo y permite al sistema "escalar" la pirámide del conocimiento de forma autónoma.

### **El Motor de Búsqueda de Conjeturas**
Este motor, aplicado a la Conjetura ABC, es un ejemplo de **falsacionismo computacional**.
1.  **Espacio de Búsqueda**: El espacio de los enteros $(a, b, c)$.
2.  **Función Objetivo**: Se busca maximizar la "calidad" de una tripleta, definida como $q(a,b,c) = \log(c) - (1+\varepsilon)\log(\text{rad}(abc))$.
3.  **Optimización Bayesiana con Heurística**: En lugar de una búsqueda por fuerza bruta, se utiliza un modelo subrogante (Proceso Gaussiano) para predecir qué regiones del espacio de búsqueda son más prometedoras. La función de adquisición se modifica con la **heurística de optimización estructural** para sesgar la búsqueda hacia áreas con mayor probabilidad de contener contraejemplos interesantes.
4.  **Resultado**: No se busca una "solución", sino un conjunto de "candidatos anómalos" que merecen un estudio más profundo.

## **4. Guía de Inicio y Uso**
### **Instalación y Configuración**
**Requisitos**: Docker Engine y Docker Compose.
1.  **Clonar:** `git clone https://github.com/SunNeurotron/Aletheia.git && cd Aletheia`
2.  **Construir e Iniciar:** Desde `Aletheia_v3/`, ejecute `docker-compose up --build`. La primera vez puede tardar varios minutos.

### **Acceso a los Servicios**
-   **Dashboard (Conjetura ABC):** `http://localhost:8501`
-   **Dashboard (Grafo de Conocimiento):** `http://localhost:8502`
-   **API (Swagger UI):** `http://localhost:8000/docs`
-   **MLflow UI:** `http://localhost:5000`

## **5. Validación, Pruebas y Benchmarks**
La robustez se garantiza mediante una estrategia de pruebas multinivel.
- **Pruebas de Módulo**: Cada módulo (`Aletheia_v3`, `aletheia_stats`, etc.) tiene su propio conjunto de tests unitarios y de integración.
- **Pruebas de Ecosistema (`/tests`)**: El directorio `tests` en la raíz contiene pruebas de integración E2E que validan los flujos de trabajo entre servicios.

### **Resultados de Benchmarks (Ilustrativos)**
| Métrica | Aletheia_v3 | aletheia_stats | aletheia_omega | Ecosistema |
|---|---|---|---|---|
| **Tests Unitarios (s)** | 15.2 | 5.1 | 4.3 | N/A |
| **Tests de Integración (s)** | 45.8 | 12.3 | 10.9 | 125.7 |
| **Cobertura de Código** | 92% | 95% | 96% | 88% |

```mermaid
graph LR
    title Tiempos de Ejecución de Suites de Pruebas (CI)

    subgraph Módulo
        A[Aletheia_v3]
        B[aletheia_stats]
        C[aletheia_omega]
        D[Ecosistema]
    end

    subgraph "Tests Unitarios (s)"
        P1[15.2s]
        S1[5.1s]
        O1[4.3s]
        E1[N/A]
    end

    subgraph "Tests de Integración (s)"
        P2[45.8s]
        S2[12.3s]
        O2[10.9s]
        E2[125.7s]
    end

    A -- "Unit" --> P1; A -- "Integration" --> P2
    B -- "Unit" --> S1; B -- "Integration" --> S2
    C -- "Unit" --> O1; C -- "Integration" --> O2
    D -- " " --> E1; D -- "Integration" --> E2
```

## **6. Hoja de Ruta y Futuras Direcciones**
- **IA Generativa para Síntesis**: Integrar LLMs (Modelos de Lenguaje Grandes) para la generación automática de proposiciones y teorías (Eje Y).
- **Análisis Avanzado**: Expandir `aletheia_stats` con más métodos estadísticos (regresión, series temporales) y `aletheia_omega` con más algoritmos de optimización.
- **Inferencia de Relaciones**: Desarrollar modelos para inferir automáticamente relaciones entre conceptos en el grafo de conocimiento.
- **Interfaz Unificada**: Consolidar los múltiples dashboards en una única interfaz de usuario más cohesiva y potente.
- **Computación de Alto Rendimiento**: Investigar el uso de Dask o Ray para la computación distribuida a gran escala.

## **7. Licencia y Citación**
### **Licencia**
Distribuido bajo la Licencia Apache, Versión 2.0. Ver [`LICENSE`](./LICENSE) para detalles.

### **Citación**
Si utiliza Aletheia en su investigación, por favor cite:
```bibtex
@software{aletheia2025,
  title = {Aletheia: An Ecosystem for AI-Assisted Epistemology},
  author = {Alant, et al.},
  year = {2025},
  version = {4.0.0},
  url = {https://github.com/SunNeurotron/Aletheia}
}
```

---
<p align="center">
<i>"La computación no es solo una herramienta para la ciencia; <br/>
es un nuevo medio para explorar la naturaleza misma del conocimiento."</i><br/>
<br/>
<b>Aletheia</b> — Donde la epistemología encuentra su expresión computacional.
</p>
