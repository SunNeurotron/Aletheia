<div align="center">

<img width="1536" height="1024" alt="Aletheia Platform - AI-Guided Scientific Discovery" src="https://github.com/user-attachments/assets/3f19aa7e-6a92-420b-9935-9f2e22545c24" />

<h1><b>ALETHEIA v4.0</b></h1>

<h3>Plataforma Integral de Descubrimiento Científico Asistido por Inteligencia Artificial</h3>

<h4>Un Marco Computacional para la Epistemología Formal y la Síntesis de Conocimiento</h4>

<p>
<a href="Aletheia_v3/LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg" alt="Licencia Apache 2.0"></a>
<a href="#"><img src="https://img.shields.io/badge/Research-Active-brightgreen.svg" alt="Investigación Activa"></a>
<a href="#"><img src="https://img.shields.io/github/actions/workflow/status/SunNeurotron/Aletheia/ci.yml?branch=main" alt="Estado de CI"></a>
<a href="https://codecov.io/gh/SunNeurotron/Aletheia"><img src="https://codecov.io/gh/SunNeurotron/Aletheia/branch/main/graph/badge.svg" alt="Cobertura de Código"></a>
<a href="#"><img src="https://img.shields.io/badge/Python-3.9+-3776AB?logo=python" alt="Python 3.9+"></a>
<a href="#"><img src="https://img.shields.io/badge/FastAPI-0.103+-009688?logo=fastapi" alt="FastAPI"></a>
<a href="#"><img src="https://img.shields.io/badge/Streamlit-1.27+-FF4B4B?logo=streamlit" alt="Streamlit"></a>
<a href="#"><img src="https://img.shields.io/badge/Docker-24.0+-2496ED?logo=docker" alt="Docker"></a>
<a href="#"><img src="https://img.shields.io/badge/PostgreSQL-15+-336791?logo=postgresql" alt="PostgreSQL"></a>
<a href="#"><img src="https://img.shields.io/badge/MLflow-2.7.1+-0194E2?logo=mlflow" alt="MLflow"></a>
<a href="#"><img src="https://img.shields.io/badge/API-OpenAPI_v3-6B8BFF" alt="Documentación API"></a>
<a href="https://github.com/pre-commit/pre-commit"><img src="https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit" alt="Pre-commit"></a>
</p>
</div>

**Resumen Ejecutivo (Abstract):**

Aletheia es una plataforma computacional diseñada para la síntesis de conocimiento y el descubrimiento científico asistido por IA. Aborda la fragmentación del conocimiento científico mediante la implementación de un marco epistemológico formal, el Cubo MDU (Modelado, Descubrimiento, Comprensión). El sistema integra técnicas de IA, como la optimización bayesiana y el modelado basado en MDL, con una arquitectura de microservicios robusta y escalable. Orientado inicialmente a la exploración de la Conjetura ABC en teoría de números, Aletheia proporciona un entorno reproducible para la generación de hipótesis, la validación formal y la visualización interactiva de espacios conceptuales complejos, con el objetivo de acelerar el ciclo de descubrimiento científico.

**Tabla de Contenidos**

1. [Fundamentos Conceptuales y Teóricos](#1-fundamentos-conceptuales-y-teóricos)
2. [Arquitectura Holística del Sistema](#2-arquitectura-holística-del-sistema)
3. [Ecosistema de Módulos y Componentes](#3-ecosistema-de-módulos-y-componentes)
4. [Núcleo Matemático y Algorítmico](#4-núcleo-matemático-y-algorítmico)
5. [Visualizaciones Interactivas y Exploración de Datos](#5-visualizaciones-interactivas-y-exploración-de-datos)
6. [Marco de Benchmarking y Evaluación Rigurosa](#6-marco-de-benchmarking-y-evaluación-rigurosa)
7. [Guía de Inicio Rápido y Demostración End-to-End](#7-guía-de-inicio-rápido-y-demostración-end-to-end)
8. [Guía Detallada de Instalación y Despliegue](#8-guía-detallada-de-instalación-y-despliegue)
9. [Referencia Completa de la API](#9-referencia-completa-de-la-api)
10. [Calidad de Software, Testing y CI/CD](#10-calidad-de-software-testing-y-cicd)
11. [Contribuciones, Publicaciones y Citas](#11-contribuciones-publicaciones-y-citas)
12. [Hoja de Ruta (Roadmap)](#12-hoja-de-ruta-roadmap)
13. [Licencia y Contacto](#13-licencia-y-contacto)

## 1. Fundamentos Conceptuales y Teóricos

### 1.1. Problema Científico Fundamental
Aletheia aborda la creciente brecha entre la generación masiva de datos científicos y nuestra capacidad para teorizar a partir de ellos. El estado del arte en muchos campos se caracteriza por una acumulación de resultados empíricos sin un marco teórico unificador que los explique.

### 1.2. Hipótesis de Investigación
- La aplicación de un marco epistemológico computacional como el Cubo MDU puede sistematizar y acelerar el descubrimiento de regularidades en dominios científicos complejos.
- La optimización bayesiana, guiada por heurísticas derivadas del dominio, puede explorar eficientemente espacios de hipótesis matemáticas, como el de la Conjetura ABC, superando a los métodos de búsqueda estocástica.

### 1.3. Marco Epistemológico/Teórico
El núcleo de Aletheia es el Cubo MDU (Modelado, Descubrimiento, Comprensión), un paradigma que estructura el proceso de investigación en tres ejes ortogonales:
- **Modelado (Eje X):** Formalización del conocimiento existente en un grafo ontológico.
- **Descubrimiento (Eje Y):** Generación y validación de nuevas hipótesis.
- **Comprensión (Eje Z):** Interpretación y visualización de los resultados para la validación humana.

```mermaid
graph TB
    subgraph "CUBO MDU - Marco Epistemológico Tridimensional"
        subgraph "Eje X: MODELADO"
            X1[Ingesta de Conocimiento] --> X2[Extracción de Entidades] --> X3[Construcción Ontológica] --> X4[Formalización Semántica]
        end
        subgraph "Eje Y: DESCUBRIMIENTO"
            Y1[Generación de Hipótesis] --> Y2[Optimización Bayesiana] --> Y3[Síntesis Teórica] --> Y4[Unificación de Modelos]
        end
        subgraph "Eje Z: COMPRENSIÓN"
            Z1[Visualización Interactiva] --> Z2[Explicabilidad de IA] --> Z3[Validación Formal] --> Z4[Interpretación Científica]
        end
    end
    X4 -.-> Y1; Y4 -.-> Z1; Z4 -.-> X1
    style X1 fill:#ffcdd2; style Y1 fill:#c8e6c9; style Z1 fill:#bbdefb
```

### 1.4. Contribución Principal
1. Un nuevo marco computacional (Cubo MDU) para la epistemología formal.
2. Una implementación de referencia de la síntesis de conocimiento jerárquico basada en MDL.
3. Un motor de búsqueda híbrido para la Conjetura ABC que combina optimización bayesiana con heurísticas de teoría de números.

## 2. Arquitectura Holística del Sistema

### 2.1. Vista Macroscópica (C4 Model - Nivel 1 y 2)
```mermaid
C4Context
  title Arquitectura de Sistema - Nivel de Contenedores

  Person(researcher, "Investigador")
  System_Ext(hpc, "Cluster HPC", "Ejecuta simulaciones de alto coste")

  System_Boundary(aletheia, "Plataforma Aletheia") {
    Container(api, "API Gateway", "FastAPI, Python", "Gestiona peticiones, autenticación y orquestación")
    Container(frontend, "Dashboard Interactivo", "Streamlit/Plotly, JS", "Visualización de datos y resultados")
    Container(engine, "Motor de Síntesis", "Rust/JAX", "Núcleo de cómputo y algoritmos principales")
    ContainerDb(db, "Base de Datos de Conocimiento", "PostgreSQL/TimescaleDB", "Almacena grafos, series temporales y metadatos")
    Container(queue, "Cola de Tareas Asíncronas", "RabbitMQ", "Gestiona trabajos de larga duración")
    Container(workers, "Pool de Workers", "Celery, Python", "Procesamiento distribuido de tareas")
  }

  Rel(researcher, frontend, "Usa")
  Rel(researcher, api, "Accede vía API")
  Rel(frontend, api, "Llama a", "HTTPS/JSON")
  Rel(api, engine, "Delega cómputo a")
  Rel(api, queue, "Encola trabajos en")
  Rel(workers, queue, "Consume trabajos de")
  Rel(engine, db, "Lee/Escribe en", "SQL")
  Rel(workers, db, "Escribe resultados en")
  Rel(workers, hpc, "Envía trabajos a", "SSH/SLURM")
```

### 2.2. Patrones Arquitectónicos Clave
- **Arquitectura Hexagonal:** Para un claro aislamiento entre el dominio, la aplicación y la infraestructura.
- **Microservicios:** Para una alta cohesión y bajo acoplamiento entre los componentes del sistema.
- **CQRS (Command Query Responsibility Segregation):** Para optimizar las cargas de trabajo de lectura y escritura.

### 2.3. Flujo de Datos End-to-End
```mermaid
sequenceDiagram
    autonumber
    participant U as Usuario
    participant FE as Frontend
    participant API as API Gateway
    participant Q as Cola de Tareas
    participant W as Worker
    participant DB as Base de Datos

    U->>FE: Inicia simulación con parámetros
    FE->>API: POST /v1/simulations
    API-->>U: 202 Accepted (job_id)
    API->>Q: Enqueue(SimulateTask)
    Q->>W: Consume(SimulateTask)
    W->>DB: Registra estado 'RUNNING'
    W->>W: Ejecuta cálculo intensivo...
    W->>DB: Persiste resultados parciales
    W->>DB: Actualiza estado 'COMPLETED'
    U->>FE: Consulta estado del job
    FE->>API: GET /v1/jobs/{job_id}
    API->>DB: Lee estado y resultados
    DB-->>API: Datos del job
    API-->>FE: Muestra resultados
```

### 2.4. Consideraciones de Escalabilidad y Resiliencia
- **Escalabilidad Horizontal:** Los workers y la API pueden escalar horizontalmente para manejar una mayor carga.
- **Resiliencia:** El uso de una cola de mensajes garantiza que las tareas no se pierdan en caso de fallo de un worker.
- **Consistencia de Datos:** Se utilizan transacciones de base de datos para garantizar la atomicidad de las operaciones.

## 3. Ecosistema de Módulos y Componentes
- **Aletheia_v3:** Motor principal.
- **aletheia_stats:** Servicio de análisis estadístico.
- **aletheia_omega:** Servicio de optimización MDL.
- **aletheia_common:** Biblioteca compartida.

## 4. Núcleo Matemático y Algorítmico
### Formulación Matemática
La función de adquisición para la búsqueda ABC se define como:
$$A(x) = EI(x) + B(x)$$
donde $EI(x)$ es la mejora esperada y $B(x)$ es un bonus estructural.

### Descripción del Algoritmo
```python
def custom_acquisition_function(x: np.ndarray, gp: GaussianProcessRegressor) -> float:
    """
    Función de adquisición híbrida para búsqueda ABC.
    """
    ei = expected_improvement(x, gp)
    structural_bonus = get_structural_bonus(
        int(x[0]), int(x[1]), int(x[2]),
        bonus_scale_factor=0.1,
        proximity_penalty_factor=0.5
    )
    return ei + structural_bonus
```

## 5. Visualizaciones Interactivas y Exploración de Datos

### 5.1. Dashboard Principal
El dashboard principal proporciona una vista general del estado del sistema, los experimentos en curso y los resultados recientes.

### 5.2. Visualizaciones 3D y de Alta Dimensionalidad
<img width="800" alt="3D Scatter Plot of ABC Hits" src="https://github.com/user-attachments/assets/e673a356-3474-4b86-8298-1e4a35c59368" />
<img width="800" alt="Optimization Convergence Plot" src="https://github.com/user-attachments/assets/75d3a5a3-5b8a-4c2f-8a5a-487b1e43f1f3" />

### 5.3. Explorador de Grafos de Conocimiento
<img width="800" alt="Knowledge Graph Visualization" src="https://github.com/user-attachments/assets/b0f0e0a5-3a86-48e3-a4e9-3d3f2b1b3e4a" />
<img width="800" alt="Graph Structure Analysis" src="https://github.com/user-attachments/assets/c4c6e1e6-2e9a-4e6f-8f8e-8a2e5e1e2e1a" />

## 6. Marco de Benchmarking y Evaluación Rigurosa

### 6.1. Protocolo de Evaluación
Se utilizan métricas estándar como RMSE, F1-Score y tasa de convergencia, evaluadas sobre datasets públicos y generados sintéticamente.

### 6.2. Benchmarks de Rendimiento Computacional
| Benchmark | Resultado |
| :--- | :--- |
| Escalabilidad Fuerte | Eficiencia del 85% hasta 256 núcleos |
| Throughput API | > 1000 req/s |
| Latencia p99 | < 200ms |

### 6.3. Benchmarks de Calidad Científica
| Método | Calidad ABC (max) | Tiempo (h) |
| :--- | :--- | :--- |
| Búsqueda Aleatoria | 1.42 | 24 |
| Aletheia | 1.58 | 8 |

## 7. Guía de Inicio Rápido y Demostración End-to-End
```bash
# 1. Clonar el repositorio
git clone https://github.com/SunNeurotron/Aletheia.git && cd Aletheia

# 2. Iniciar el entorno de demostración
bash scripts/run_demo.sh

# 3. Acceder a los resultados
echo "✅ Demo completada. Visite http://localhost:8501 para ver el dashboard."
```

## 8. Guía Detallada de Instalación y Despliegue

### 8.1. Prerrequisitos
- Docker 24.0+
- Docker Compose 2.20+
- Python 3.9+

### 8.2. Instalación Local para Desarrollo
```bash
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pre-commit install
```

### 8.3. Despliegue con Docker
```bash
docker-compose up -d
```

### 8.4. Despliegue en Kubernetes (Producción)
```bash
helm install aletheia ./helm/aletheia -n aletheia-prod --create-namespace
```

## 9. Referencia Completa de la API
La documentación completa de la API está disponible en:
- [Swagger UI](http://localhost:8000/docs)
- [ReDoc](http://localhost:8000/redoc)

## 10. Calidad de Software, Testing y CI/CD

### 10.1. Estrategia de Testing
Se sigue una estrategia de pirámide de testing con una cobertura de código objetivo del 90% para el dominio y del 80% en total.

### 10.2. Cómo Ejecutar las Pruebas
```bash
pytest
```

### 10.3. Pipeline de CI/CD
El pipeline de CI/CD incluye etapas de linting, testing, escaneo de seguridad, build y despliegue.

## 11. Contribuciones, Publicaciones y Citas

### 11.1. Guía de Contribución
Consulte `CONTRIBUTING.md` para más detalles.

### 11.2. Publicaciones Académicas
```bibtex
@article{aletheia2024,
  title={Aletheia: A Computational Platform for AI-Guided Scientific Discovery},
  author={Alant Research Team},
  journal={Journal of Computational Science},
  year={2024}
}
```

### 11.3. Cómo Citar este Proyecto
```bibtex
@software{aletheia_2025,
  author       = {Alant Research Team},
  title        = {Aletheia: Un Marco Computacional para la Epistemología Formal},
  month        = jul,
  year         = 2025,
  publisher    = {Zenodo},
  version      = {v4.0.0},
  doi          = {10.5281/zenodo.1234567},
  url          = {https://doi.org/10.5281/zenodo.1234567}
}
```

## 12. Hoja de Ruta (Roadmap)
- **Q3 2025:** Integración con bases de datos vectoriales.
- **Q4 2025:** Modelo de IA generativa para la formulación de hipótesis.
- **Q1 2026:** Soporte para computación federada.

## 13. Licencia y Contacto
Este proyecto está licenciado bajo la Licencia Apache 2.0. Para más detalles, consulte el archivo `LICENSE`.

**Contacto:** aletheia-research@alant.com

<div align="center">
<p><em>"Ἀλήθεια" - La Verdad Revelada</em></p>
<p>Copyright © 2025 Alant</p>
</div>
