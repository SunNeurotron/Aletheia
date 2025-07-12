<div align="center">
<h1>Aletheia v4.0</h1>
<p><strong>Plataforma de Descubrimiento Científico Guiado por IA</strong></p>
<p>Explorando las fronteras de la ciencia y las matemáticas con inteligencia artificial.</p>

<p>
<a href="Aletheia_v3/LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="Licencia"></a>
<a href="https://www.python.org"><img src="https://img.shields.io/badge/Python-3.9+-3776AB?logo=python" alt="Python"></a>
<a href="https://fastapi.tiangolo.com"><img src="https://img.shields.io/badge/FastAPI-0.103+-009688?logo=fastapi" alt="FastAPI"></a>
<a href="https://streamlit.io"><img src="https://img.shields.io/badge/Streamlit-1.27-FF4B4B?logo=streamlit" alt="Streamlit"></a>
<a href="https://www.docker.com"><img src="https://img.shields.io/badge/Docker-24.0-2496ED?logo=docker" alt="Docker"></a>
<a href="https://www.postgresql.org"><img src="https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql" alt="PostgreSQL"></a>
<a href="#"><img src="https://img.shields.io/badge/status-en%20desarrollo-orange" alt="Estado"></a>
</p>
</div>

Aletheia es una plataforma integral para el descubrimiento científico, diseñada para abordar problemas matemáticos complejos como la Conjetura ABC y facilitar el Modelado, Descubrimiento y Comprensión (MDC/MDU) en la investigación científica.

Esta versión avanza el marco MDC con un grafo de conocimiento funcional, síntesis guiada por IA, almacenamiento persistente y visualización interactiva. Soporta un flujo completo: ingesta de documentos, extracción de conceptos, formación de estructuras jerárquicas y exploración mediante un dashboard.

Para detalles sobre la evolución del proyecto, consulta [CHANGELOG.md](CHANGELOG.md).

## 🚀 Características Principales

### 🧠 Núcleo de Grafo de Conocimiento y Visualización
- **Entidades de Conocimiento**: Modelos `ScientificConcept` y `DirectedRelationship` forman el grafo.
- **Almacenamiento Persistente**: Repositorios SQLAlchemy con PostgreSQL, gestionados por migraciones de Alembic.
- **Eje X - Ingesta y Ontología**:
  - `IngestDocumentUseCase`: Ingesta texto, crea conceptos `DOCUMENT_SOURCE`, y extrae Unidades Conceptuales Mínimas (UCMs).
  - `ExtractUCMsUseCase`: Usa regex y análisis de palabras clave para extraer UCMs.
  - `LinkConceptsUseCase`: Permite crear relaciones manualmente.
- **Eje Y - Síntesis de Conocimiento**:
  - Pipeline (`FormClusters`, `DerivePropositions`, `MiniTheoryConstruction`) que sintetiza conceptos en niveles superiores (CLUSTER, PROPOSICIÓN, MINI_THEORY).
- **Dashboard Interactivo** (`mdu_dashboard.py`):
  - Visualización en Streamlit del grafo de conocimiento.
  - Explorador con filtros, visor de jerarquías y estadísticas.

### 🧮 Motor Matemático de Alto Rendimiento
- **Integración con PARI/GP**: Usa `cypari2` para aritmética de alta precisión y factorización de primos.
- **Cálculos Optimizados**: Caché (`lru_cache`) para reducir cálculos redundantes.

### 🌐 Computación Distribuida y Escalabilidad
- **Kubernetes**: Configuraciones en `Aletheia_v3/kubernetes/` para despliegues escalables.
- **Celery Avanzado**: Colas especializadas (ej. `math_heavy`) y autoescalado con KEDA.
- **Optimización de BD**: Particionamiento e indexación en `Aletheia_v3/infrastructure/db_optimizations.sql`.
- **HPC**: Scripts para SLURM y `mpi4py` en `Aletheia_v3/docs/HPC_ADAPTATION.md`.

### 🧩 IA Avanzada y Arquitectura de Plugins
- **Heurísticas Personalizadas**: `get_structural_bonus` en `Aletheia_v3/core/custom_acquisitions.py` guía la optimización bayesiana.
- **Plugins**: Sistema extensible para estrategias de búsqueda y evaluadores.
- **Dask**: Integración explorada en `Aletheia_v3/docs/DASK_INTEGRATION.md`.

### 🎨 Experiencia de Usuario y Colaboración
- **Visualizaciones**: Gráficos 3D en `Aletheia_v3/dashboard/dashboard.py`.
- **Colaboración**: Esquema de BD y API para múltiples investigadores.
- **Seguridad**: Diseños para RBAC y OAuth2 en `Aletheia_v3/docs/`.

## 🏗️ Diagrama de Arquitectura
```mermaid
graph TD
    User[Usuario] -->|Interactúa| Dashboard[🔬 Dashboard Streamlit]
    subgraph "Plataforma Aletheia (Docker)"
        Dashboard -->|HTTP| API[🚀 FastAPI]
        API -->|Almacena| DB[(🐘 PostgreSQL)]
        API -->|Encola| MQ[🏎️ Redis]
        Worker[⚙️ Celery Worker] -->|Toma Tarea| MQ
        Worker -->|Ejecuta| AISearch[🧠 Búsqueda IA]
        AISearch -->|Utiliza| DomainLogic[📚 Lógica de Dominio]
        Worker -->|Almacena| DB
        Worker -->|Registra| MLflowServer[📈 MLflow]
        MLflowServer -->|Metadatos| DB
        MLflowServer -->|Artefactos| ArtifactStore[(📦 S3/MinIO)]
    end
    User -->|Visualiza| MLflowUI[📈 MLflow UI]
    MLflowUI -->|Lee| MLflowServer

Nota: Copia este código en un editor Mermaid (como mermaid.live) si no se renderiza en tu visor.
```

## 🛠️ Cómo Ejecutar la Plataforma

### 📋 Prerrequisitos
- Docker Engine (última versión recomendada)
- Docker Compose (última versión recomendada)

### 🚀 Pasos de Ejecución

1️⃣ **Clona el Repositorio:**
```bash
git clone https://github.com/SunNeurotron/Aletheia.git
cd Aletheia
```

2️⃣ **Revisa la Guía de Uso (Recomendado):**
Antes de lanzar la plataforma, te sugerimos leer la [Guía de Uso End-to-End](Aletheia_v3/docs/END_TO_END_USE_CASE.md) para entender el flujo de trabajo completo.

3️⃣ **Construye e Inicia los Servicios:**
Desde el directorio que contiene `docker-compose.yml` (es decir, `Aletheia_v3/`), ejecuta:
```bash
# Si estás en la raíz del repositorio, navega a Aletheia_v3 primero:
# cd Aletheia_v3
docker-compose up --build
# Si prefieres ejecutar desde la raíz del repo:
# docker-compose -f Aletheia_v3/docker-compose.yml up --build
```
La primera vez puede tardar varios minutos. Los inicios posteriores serán mucho más rápidos.

4️⃣ **Accede a los Servicios:**
Una vez que los contenedores estén en ejecución, accede a las interfaces desde tu navegador:
-   Dashboard (Conjetura ABC): `http://localhost:8501`
-   Dashboard (Grafo): `http://localhost:8502`
-   API (Swagger): `http://localhost:8000/docs`
-   MLflow: `http://localhost:5000`

5️⃣ **Ejecuta las Pruebas (Opcional):**
Abre una nueva terminal. Si estás en la raíz del repositorio:
```bash
docker-compose -f Aletheia_v3/docker-compose.yml exec api pytest Aletheia_v3/tests/
# O, si estás en Aletheia_v3/:
# docker-compose exec api pytest tests/
```

6️⃣ **Detén la Plataforma:**
Para detener todos los servicios, presiona `Ctrl+C` en la terminal donde se ejecuta `docker-compose` y luego:
```bash
# Si estás en Aletheia_v3/:
# docker-compose down
# Si estás en la raíz del repo:
docker-compose -f Aletheia_v3/docker-compose.yml down
```
Los datos de PostgreSQL persistirán gracias a los volúmenes de Docker.

### 🗃️ Migraciones de Base de Datos (Alembic)

Este proyecto utiliza Alembic para gestionar las migraciones del esquema de la base de datos.

-   **Aplicación Automática**: Al iniciar con `docker-compose up`, las migraciones pendientes se aplicarán automáticamente antes de que la API y los workers arranquen.
-   **Generación de Nuevas Migraciones**: Si modificas los modelos en `Aletheia_v3/infrastructure/models.py`, debes generar un nuevo script de migración. Ejecuta el siguiente comando (asegúrate de estar en un entorno con las dependencias instaladas y acceso a la configuración de Alembic):
    ```bash
    # Navega al directorio que contiene alembic.ini (Aletheia_v3/)
    cd Aletheia_v3
    alembic revision -m "descripcion_corta_de_los_cambios" --autogenerate
    # O desde la raíz del proyecto:
    # (cd Aletheia_v3 && alembic revision -m "descripcion_corta_de_los_cambios" --autogenerate)
    ```
    Importante: Revisa siempre los scripts autogenerados antes de confirmarlos en el repositorio.

## 📚 Documentación Adicional

Consulta los siguientes documentos para un entendimiento más profundo:
-   Guía de Uso: [Aletheia_v3/docs/END_TO_END_USE_CASE.md](Aletheia_v3/docs/END_TO_END_USE_CASE.md)
-   Plugins: [Aletheia_v3/plugins/README.md](Aletheia_v3/plugins/README.md)
-   Adaptación a HPC: [Aletheia_v3/docs/HPC_ADAPTATION.md](Aletheia_v3/docs/HPC_ADAPTATION.md)
-   Integración con Dask: [Aletheia_v3/docs/DASK_INTEGRATION.md](Aletheia_v3/docs/DASK_INTEGRATION.md)
-   Escalado de Celery y Optimización Bayesiana Paralela: [Aletheia_v3/docs/celery_scaling_and_parallel_bayes_opt.md](Aletheia_v3/docs/celery_scaling_and_parallel_bayes_opt.md)
-   Configuraciones de Kubernetes: [Aletheia_v3/kubernetes/README.md](Aletheia_v3/kubernetes/README.md)
-   Optimizaciones de Base de Datos: [Aletheia_v3/infrastructure/db_optimizations.sql](Aletheia_v3/infrastructure/db_optimizations.sql)
-   Control de Acceso (RBAC) para MLflow: [Aletheia_v3/docs/RBAC_MLFLOW.md](Aletheia_v3/docs/RBAC_MLFLOW.md)
-   Scopes de API para Autorización Granular: [Aletheia_v3/docs/API_SCOPES.md](Aletheia_v3/docs/API_SCOPES.md)

## ⚖️ Licencia y Descargo de Responsabilidad
Licenciado bajo Apache 2.0. Copyright © 2025 Alant. Consulta [Aletheia_v3/LICENSE](Aletheia_v3/LICENSE) y [Aletheia_v3/DISCLAIMER.md](Aletheia_v3/DISCLAIMER.md). El archivo `NOTICE` se encuentra en la raíz del proyecto.

<div align="center">
<p>Autor: Alant | Año: 2025</p>
</div>
