# Aletheia-Stats Module

Este directorio contiene el módulo **Aletheia-Stats**, un sistema de análisis estadístico diseñado según el **Marco de Desarrollo Unificado (MDU)**. Se integra como un componente dentro del repositorio principal `SunNeurotron/Aletheia`.

## Descripción General

Aletheia-Stats proporciona una API para realizar pruebas de hipótesis estadísticas (inicialmente, la prueba t de Student para muestras independientes) con un enfoque en:

- **Rigor Científico**: Uso de validaciones estadísticas (ej. prueba de normalidad de Shapiro-Wilk), documentación clara de los métodos y reproducibilidad (semillas aleatorias fijas).
- **Calidad de Producción**: Código robusto, bien probado, con tipado estático, formateo y linting consistentes.
- **Trazabilidad**: Integración con MLflow para registrar experimentos y resultados.
- **Despliegue Sencillo**: Contenerización con Docker y Docker Compose para un fácil despliegue local y en otros entornos.
- **Arquitectura Hexagonal-Científica**: Separación clara de conceptos entre dominio, aplicación e infraestructura.

## Estructura del Módulo

```
aletheia_stats/
├── alembic/                    # Configuraciones y migraciones de Alembic
├── aletheia_stats/             # Código fuente del módulo
│   ├── application/            # Casos de uso
│   ├── domain/                 # Lógica de negocio y entidades principales
│   ├── infrastructure/         # Conexiones a BD, MLflow, etc.
│   └── presentation/           # Endpoints de la API (FastAPI)
├── docs/                       # Documentación detallada (arquitectura, ecuaciones)
├── scripts/                    # Scripts útiles (ej. demo, inicialización de BD)
├── tests/                      # Pruebas automatizadas (unitarias, integración, propiedad)
├── .env.example                # Ejemplo de variables de entorno
├── Dockerfile                  # Definición del contenedor Docker para el módulo
├── docker-compose.yml          # Orquestación de servicios (API, BD, MLflow) para el módulo
├── README.md                   # Este archivo
└── requirements.txt            # Dependencias Python del módulo
```

## Configuración y Ejecución

1.  **Variables de Entorno**:
    Copie `aletheia_stats/.env.example` a `aletheia_stats/.env` y configure las variables:
    ```env
    DATABASE_URL="postgresql://user:pass@localhost:5432/aletheia_stats_db"
    MLFLOW_TRACKING_URI="http://localhost:5001" # Puerto diferente si el mlflow raíz usa 5000
    JWT_SECRET_KEY="your-super-secret-key-for-aletheia-stats"
    # Asegúrate de que los puertos no colisionen con otros servicios del proyecto principal.
    # Por ejemplo, si el proyecto raíz ya usa Postgres en 5432, cambia el puerto aquí y en docker-compose.yml.
    # Similarmente para el puerto de la API (8000) y MLflow (5001).
    ```

2.  **Construir y Levantar Contenedores**:
    Desde el directorio `aletheia_stats/`:
    ```bash
    docker-compose up --build -d
    ```
    Esto levantará la API de Aletheia-Stats, una base de datos PostgreSQL y un servidor MLflow dedicados a este módulo.

3.  **Inicializar Base de Datos (Primera Vez)**:
    Si es la primera vez o después de cambios en los modelos que requieran una nueva migración:
    ```bash
    docker-compose exec api alembic upgrade head
    ```
    (Nota: `init_db.py` podría usarse para creación inicial si no se usa Alembic desde el principio, o `scripts/run_migrations.sh` para simplificar).

4.  **Acceder a la API**:
    La documentación interactiva de la API estará disponible en [http://localhost:8000/docs](http://localhost:8000/docs) (o el puerto que hayas configurado).

5.  **Ejecutar Demo**:
    ```bash
    python scripts/demo.py
    ```
    (Asegúrate de que el script `demo.py` apunte a la URL correcta de la API).

## Desarrollo

-   **Instalar Dependencias (para desarrollo local fuera de Docker)**:
    Desde `aletheia_stats/`:
    ```bash
    python -m venv venv_stats
    source venv_stats/bin/activate  # O venv_stats\Scripts\activate en Windows
    pip install -r requirements.txt
    pip install -r ../requirements_dev.txt # Si hay un requirements_dev.txt en la raíz para pre-commit, etc.
    ```
-   **Ejecutar Pruebas**:
    Desde `aletheia_stats/`:
    ```bash
    pytest
    ```
    O desde la raíz del repositorio (asegurándose de que pytest descubra las pruebas del módulo, puede requerir configuración en `pyproject.toml` o `pytest.ini` en la raíz):
    ```bash
    pytest aletheia_stats/tests/
    ```
-   **Linters y Formateadores**:
    Se recomienda configurar `pre-commit` en la raíz del repositorio `SunNeurotron/Aletheia` para que cubra este módulo. Ejecutar manualmente desde la raíz:
    ```bash
    pre-commit run --all-files
    ```

## Contribuciones

Las contribuciones deben seguir las guías del MDU y mantener los estándares de calidad del proyecto.

## Detalles de la API

La API de Aletheia-Stats se expone bajo el prefijo `/api/v1` y sigue los estándares RESTful. La autenticación se realiza mediante tokens JWT Bearer.

### Endpoints Principales:

-   **`POST /api/v1/token`**: Obtiene un token JWT para autenticación.
    -   **Request Body**: `username` y `password` (form data).
    -   **Response**: `{ "access_token": "...", "token_type": "bearer" }`
-   **`POST /api/v1/analyze/ttest`**: Realiza un análisis de prueba t.
    -   **Request Body**: `TTestRequest` (ver `presentation/api.py` para el modelo Pydantic). Incluye `group_a`, `group_b`, `experiment_name`, `alpha`, etc.
    -   **Response**: `ExperimentResponse` con los resultados del análisis y metadatos del experimento.
    -   **Autenticación**: Requerida (rol `analyst`).
-   **`GET /api/v1/experiments/{experiment_id}`**: Obtiene un experimento por su ID.
    -   **Response**: `ExperimentResponse`.
    -   **Autenticación**: Requerida (rol `viewer` o `analyst`).
-   **`GET /api/v1/experiments`**: Lista todos los experimentos con paginación.
    -   **Query Params**: `skip`, `limit`.
    -   **Response**: Lista de `ExperimentResponse`.
    -   **Autenticación**: Requerida (rol `viewer` o `analyst`).
-   **`GET /api/v1/users/me`**: Devuelve detalles del usuario autenticado actualmente.
    -   **Response**: `User` (modelo Pydantic).
    -   **Autenticación**: Requerida.
-   **`GET /api/docs`**: Acceso a la documentación interactiva de Swagger UI.
-   **`GET /api/redoc`**: Acceso a la documentación ReDoc.
-   **`GET /health`**: Endpoint de Health Check.

### Modelos de Datos Clave (Pydantic):

-   `TTestRequest`: Define la estructura para solicitar un análisis de prueba t.
-   `TTestResultResponse`: Define la estructura de los resultados de una prueba t en las respuestas de la API.
-   `ExperimentResponse`: Define la estructura completa de un experimento en las respuestas de la API, incluyendo un resumen de los datos de entrada y los resultados.

(Consultar `aletheia_stats/aletheia_stats/presentation/api.py` para las definiciones detalladas de estos modelos).

## Lógica Científica

El núcleo del análisis estadístico reside en el `StatsService` (`domain/services.py`):

1.  **Prueba de Normalidad**: Antes de la prueba t, se realiza una prueba de normalidad de Shapiro-Wilk en cada grupo de datos.
    -   Si el p-valor de la prueba de Shapiro-Wilk es menor que el nivel alfa (ej. 0.05), se considera que el grupo podría no seguir una distribución normal, y se añade un comentario al respecto en los resultados.
    -   Ecuación y Referencia: Ver `docs/equations.md` y docstrings en `StatsService`.
2.  **Prueba t de Welch**: Se utiliza la prueba t de Welch para dos muestras independientes, que no asume varianzas iguales entre los grupos.
    -   Calcula el estadístico t, el p-valor y los grados de libertad (usando la ecuación de Welch-Satterthwaite).
    -   Calcula el intervalo de confianza del 95% para la diferencia de medias.
    -   Ecuaciones y Referencias: Ver `docs/equations.md` y docstrings en `StatsService`.

## Trazabilidad con MLflow

Cada ejecución de un análisis a través del endpoint `/analyze/ttest` es registrada como un "experimento" en MLflow (si está configurado):

-   **Parámetros Registrados**: Tamaño de los grupos, nivel alfa, y cualquier parámetro adicional proporcionado en la solicitud.
-   **Métricas Registradas**: Estadístico t, p-valor, grados de libertad, límites del intervalo de confianza, medias y varianzas de los grupos, p-valores de las pruebas de normalidad, y un indicador de significancia.
-   **Etiquetas (Tags)**: Estado de la ejecución (SUCCESS/FAILED), comentarios del análisis, ID del experimento de la base de datos.
-   El `mlflow_run_id` se almacena en la base de datos junto con los detalles del experimento para referencia cruzada.

Consultar `infrastructure/mlflow_tracker.py` para la implementación del seguimiento.

## Documentación Adicional

-   **Arquitectura del Módulo**: `docs/architecture.md`
-   **Ecuaciones y Referencias Científicas**: `docs/equations.md`

## Contribuciones

Las contribuciones deben seguir las guías del MDU y mantener los estándares de calidad del proyecto.
Asegurarse de ejecutar `pre-commit run --all-files` antes de enviar cambios y que todas las pruebas pasen.
```
