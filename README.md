<div align="center">
<img width="1536" height="1024" alt="Image" src="https://github.com/user-attachments/assets/3f19aa7e-6a92-420b-9935-9f2e22545c24" />
(https://github.com/SunNeurotron/Aletheia/issues/102)
<h1>Aletheia v4.0</h1>
<p><strong>Plataforma de Descubrimiento Científico Guiado por IA</strong></p>
<p>Una infraestructura computacional para la epistemología y el descubrimiento en ciencias formales.</p>

<p>
<a href="Aletheia_v3/LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="Licencia"></a>
<a href="#"><img src="https://img.shields.io/badge/Python-3.9+-3776AB?logo=python" alt="Python"></a>
<a href="#"><img src="https://img.shields.io/badge/FastAPI-0.103+-009688?logo=fastapi" alt="FastAPI"></a>
<a href="#"><img src="https://img.shields.io/badge/Streamlit-1.27-FF4B4B?logo=streamlit" alt="Streamlit"></a>
<a href="#"><img src="https://img.shields.io/badge/Docker-24.0-2496ED?logo=docker" alt="Docker"></a>
<a href="#"><img src="https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql" alt="PostgreSQL"></a>
<a href="#"><img src="https://img.shields.io/badge/status-en--desarrollo-orange" alt="Estado"></a>
</p>
</div>

## Introducción

**Aletheia** es una plataforma de software diseñada para la investigación y el descubrimiento en ciencias formales, con un enfoque principal en la matemática pura y la física teórica. Su propósito es servir como un laboratorio computacional para la **epistemología asistida por IA**, donde las estructuras del conocimiento científico pueden ser representadas, sintetizadas y exploradas sistemáticamente.

La plataforma implementa el paradigma de **Modelado, Descubrimiento y Comprensión (MDU)**, materializado a través de un ecosistema de servicios interconectados. Inicialmente concebida para investigar la **Conjetura ABC**, la arquitectura de Aletheia ha evolucionado para convertirse en un sistema generalizable para la investigación en cualquier dominio formalizable.

## Fundamentos Teóricos

La plataforma integra conceptos de teoría de números, optimización, teoría de grafos, estadística y procesamiento de lenguaje natural.

### Análisis Matemático y Teoría de Números

- **Conjetura ABC**: El problema que inspiró el motor matemático de Aletheia. Dada una tripleta de enteros positivos $(a, b, c)$ coprimos tales que $a + b = c$, la conjetura establece que para todo $\varepsilon > 0$, la desigualdad $c < K_\varepsilon \cdot (\text{rad}(abc))^{1+\varepsilon}$ se cumple salvo un número finito de excepciones, donde $\text{rad}(n) = \prod_{p|n} p$ es el radical de $n$.

- **Heurística de Optimización Estructural**: Para guiar la búsqueda de tripletas interesantes, se emplea un sesgo heurístico que favorece a enteros con estructura multiplicativa simple (potencias de primos). El bono ($B$) se calcula como:
$$
B(v) = \begin{cases} S \cdot M & \text{si } v = p^k \\ S \cdot e^{-\lambda \cdot d_{\text{rel}}(v)} & \text{si } v \text{ es "cercano" a } p^k \end{cases}
$$

### Análisis Estadístico

- **Prueba t de Welch**: Para comparar dos muestras independientes sin asumir igualdad de varianzas, el servicio `aletheia_stats` utiliza la prueba t de Welch. El estadístico $t$ se calcula como:
$$
t = \frac{\bar{X}_1 - \bar{X}_2}{\sqrt{\frac{s_1^2}{N_1} + \frac{s_2^2}{N_2}}}
$$
Donde $\bar{X}$, $s^2$ y $N$ son la media, varianza y tamaño de la muestra de cada grupo.

## Arquitectura y Ecosistema de Módulos

Aletheia está diseñada como un ecosistema de microservicios que colaboran para ofrecer una funcionalidad completa, desde la ingesta de datos hasta el análisis avanzado.

```mermaid
graph TD
    subgraph "Usuario"
        U[Investigador]
    end

    subgraph "Interfaz de Usuario"
        DASH[Dashboard (Streamlit)]
    end

    subgraph "Núcleo de la Plataforma (Aletheia_v3)"
        API[API Principal (FastAPI)]
        WORKER[Worker (Celery)]
        DB[(PostgreSQL)]
        MQ[(Redis)]
        MLFLOW[MLflow Tracking Server]
    end

    subgraph "Módulos Satélite"
        STATS[aletheia_stats API]
        OMEGA[aletheia_omega API]
    end

    U -- Interacciona con --> DASH
    DASH -- Peticiones HTTP --> API

    API -- Encola Tareas --> MQ
    WORKER -- Consume Tareas --> MQ
    WORKER -- Lógica de Dominio/Síntesis --> DB
    WORKER -- Registra Experimentos --> MLFLOW

    WORKER -- Petición de Análisis Estadístico --> STATS
    STATS -- Realiza Prueba t --> STATS_DB[(DB Stats)]

    WORKER -- Petición de Optimización --> OMEGA
    OMEGA -- Registra Trayectoria --> OMEGA_DB[(DB Omega)]

    style U fill:#fff,stroke:#333,stroke-width:2px
    style DASH fill:#f9f,stroke:#333,stroke-width:2px
    style API fill:#ccf,stroke:#333,stroke-width:2px
    style WORKER fill:#fcf,stroke:#333,stroke-width:2px
    style STATS fill:#c8e6c9,stroke:#333,stroke-width:2px
    style OMEGA fill:#bbdefb,stroke:#333,stroke-width:2px

```

### Componentes del Ecosistema

-   **Núcleo de Grafo de Conocimiento y Visualización (`Aletheia_v3`)**:
    -   **Eje X (Ingesta y Ontología)**: Ingiere documentos, extrae Unidades Conceptuales Mínimas (UCM) y construye un grafo de conocimiento.
    -   **Eje Y (Síntesis de Conocimiento)**: Sintetiza conceptos de niveles superiores (clusters, proposiciones, teorías) a partir de los existentes.
    -   **Motor Matemático**: Utiliza `cypari2` para aritmética de alta precisión.
    -   **Dashboard Interactivo**: Permite la exploración visual del grafo de conocimiento.

-   **Servicio de Análisis Estadístico (`aletheia_stats`)**:
    -   Proporciona endpoints para realizar pruebas de hipótesis estadísticas (ej. Prueba t, ANOVA).
    -   Cada análisis es registrado como un experimento trazable en su propia base de datos y en MLflow.

-   **Servicio de Trayectorias de Optimización (`aletheia_omega`)**:
    -   Gestiona y persiste los resultados de ejecuciones de optimización (ej. bayesiana, genéticos).
    -   Almacena la "trayectoria" completa de cada ejecución para análisis post-hoc.

-   **Biblioteca Común (`aletheia_common`)**: Un paquete interno con utilidades compartidas (autenticación, esquemas Pydantic) para garantizar la consistencia en todo el ecosistema.

## Flujo de Demostración: De la Ingesta al Análisis

Un caso de uso típico en Aletheia podría seguir estos pasos:
1.  **Ingesta**: Un investigador sube un artículo científico en PDF sobre un nuevo material a través del **Dashboard**.
2.  **Eje X**: La **API Principal** recibe el documento y encola una tarea. Un **Worker** procesa el PDF, extrae UCMs (ej. "dureza", "composición química") y las almacena como nodos en la base de datos **PostgreSQL**.
3.  **Análisis Estadístico**: El investigador tiene datos de dos variantes del material y quiere comparar su dureza. Desde el Dashboard, envía los dos conjuntos de datos al endpoint de la **API Principal**, que a su vez llama al servicio **`aletheia_stats`**. Este último realiza una prueba t, almacena los resultados (p-valor, estadístico t) y los registra en **MLflow**.
4.  **Optimización**: Basado en los resultados, el investigador quiere encontrar la composición química óptima. Inicia una ejecución de optimización a través del Dashboard. El **Worker** llama al servicio **`aletheia_omega`** para registrar la nueva ejecución. Durante la optimización, cada nuevo punto evaluado se envía a `aletheia_omega` para ser añadido a la trayectoria.
5.  **Visualización**: El investigador explora el grafo de conocimiento actualizado, visualiza los resultados del test estadístico y monitoriza el progreso de la optimización, todo desde el **Dashboard**.

## Rendimiento y Benchmarks

La plataforma está diseñada para la eficiencia. Los benchmarks de los tests automatizados proporcionan una visión del rendimiento de los componentes clave.

*(Nota: Los siguientes datos son ilustrativos y sirven como plantilla)*.
```mermaid
graph TD
    title Tiempos de Ejecución de Suites de Pruebas (CI)

    subgraph Módulo
        A[Aletheia_v3]
        B[aletheia_stats]
        C[aletheia_omega]
    end

    subgraph "Tiempo (segundos)"
        direction LR
        P1[Unitarias: 15s]
        P2[Integración: 45s]
        P3[E2E: 90s]

        S1[Unitarias: 5s]
        S2[Integración: 12s]

        O1[Unitarias: 4s]
        O2[Integración: 10s]
    end

    A -- "Tests Unitarios" --> P1
    A -- "Tests de Integración" --> P2
    A -- "Tests End-to-End" --> P3

    B -- " " --> S1 & S2
    C -- " " --> O1 & O2
```

## Cómo Ejecutar la Plataforma

(La sección de "Cómo Ejecutar la Plataforma", "Migraciones de Base de Datos", "Documentación Avanzada" y "Licencia" se mantiene igual que en la versión anterior).

🛠️ Cómo Ejecutar la Plataforma
📋 Prerrequisitos

Docker Engine (última versión recomendada)

Docker Compose (última versión recomendada)

🚀 Pasos de Ejecución

1️⃣ Clona el Repositorio:
```bash
git clone https://github.com/SunNeurotron/Aletheia.git
cd Aletheia
```

2️⃣ Revisa la Documentación (Recomendado):
Antes de lanzar la plataforma, te sugerimos leer la [Guía de Uso End-to-End](Aletheia_v3/docs/END_TO_END_USE_CASE.md) para entender el flujo de trabajo completo.

3️⃣ Construye e Inicia los Servicios:
Desde el directorio `Aletheia_v3/`, que contiene el `docker-compose.yml`, ejecute:
```bash
docker-compose up --build
```
La primera vez puede tardar varios minutos. Los inicios posteriores serán mucho más rápidos.

4️⃣ Accede a los Servicios:
-   **Dashboard (Conjetura ABC):** `http://localhost:8501`
-   **Dashboard (Grafo de Conocimiento):** `http://localhost:8502`
-   **API (Swagger UI):** `http://localhost:8000/docs`
-   **MLflow UI:** `http://localhost:5000`

5️⃣ Ejecuta las Pruebas (Opcional):
```bash
docker-compose exec api pytest tests/
```

6️⃣ Detén la Plataforma:
Presione `Ctrl+C` y luego:
```bash
docker-compose down
```

## 🗃️ Migraciones de Base de Datos (Alembic)

Este proyecto utiliza Alembic para gestionar las migraciones del esquema de la base de datos. Al iniciar con `docker-compose up`, las migraciones se aplican automáticamente. Para generar una nueva migración, ejecute:
```bash
# Navega al directorio que contiene alembic.ini (ej. Aletheia_v3/)
alembic revision -m "descripcion_corta_de_los_cambios" --autogenerate
```

## 📚 Documentación Avanzada y Conceptos de Diseño

Para un entendimiento más profundo, consulte la documentación específica en los directorios de cada módulo y en `Aletheia_v3/docs/`.

## ⚖️ Licencia y Descargo de Responsabilidad

Distribuido bajo la Licencia Apache 2.0. Vea `LICENSE` y `NOTICE`. Consulte `Aletheia_v3/DISCLAIMER.md` para entender las limitaciones del software.

<div align="center">
<p>Autor: Alant | Año: 2025</p>
</div>
