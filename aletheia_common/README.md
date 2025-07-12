# Aletheia-Common Module

## Propósito

El módulo `aletheia_common` sirve como una biblioteca compartida de utilidades y definiciones comunes utilizadas por varios módulos dentro del ecosistema Aletheia. Su objetivo es promover la reutilización de código, la consistencia y reducir la duplicación entre diferentes componentes de la plataforma.

Este módulo **no** está diseñado para ser un servicio independiente, sino una colección de herramientas y bloques de construcción importables.

## Rol en el Ecosistema Aletheia

Este módulo sirve como la base sobre la cual se construyen otros servicios, proporcionando funcionalidades reutilizables en dominios como la autenticación, el acceso a la base de datos y la interacción con MLflow.

```mermaid
graph TD
    subgraph "Ecosistema Aletheia"
        A[Aletheia_v3 (Servicio Principal)]
        O[aletheia_omega (Servicio de Optimización)]
        S[aletheia_stats (Servicio de Estadísticas)]
    end

    subgraph "Biblioteca Central"
        C(aletheia_common)
    end

    subgraph "Funcionalidades Comunes"
        direction LR
        AUTH[Auth (JWT)]
        DB[DB (Tipos, Base)]
        ML[MLflow Utils]
        SCH[Schemas (Pydantic)]
    end

    A -- Importa --> C
    O -- Importa --> C
    S -- Importa --> C

    C -- Provee --> AUTH
    C -- Provee --> DB
    C -- Provee --> ML
    C -- Provee --> SCH

    style C fill:#d5e8d4,stroke:#333,stroke-width:2px
    style A fill:#d2eaff
    style O fill:#e8dff5
    style S fill:#fcf6bd
```

## Cumplimiento del MDU

Este módulo se adhiere a los principios del **Marco de Desarrollo Unificado (MDU)**, especialmente en lo referente a:
- **Modularidad:** Proporciona componentes bien definidos y reutilizables.
- **Calidad de Producción:** Incluye código robusto con tipado estático y se espera que tenga pruebas asociadas (aunque las pruebas de los componentes comunes pueden residir en los módulos que los utilizan o en una suite de pruebas dedicada si es necesario).
- **Claridad:** Busca ofrecer interfaces claras y bien documentadas para sus utilidades.

## Estructura del Módulo

```
aletheia_common/
├── auth/                     # Utilidades de autenticación (ej. manejo de JWT)
│   └── jwt_handler.py
├── db/                       # Utilidades de base de datos (ej. sesiones, base models - si aplica)
├── mlflow_utils/             # Funciones de ayuda para interactuar con MLflow
├── schemas/                  # Esquemas Pydantic comunes (ej. respuestas de error estándar)
└── README.md                 # Este archivo
```
*(Nota: La estructura real puede variar y expandirse según las necesidades. No se espera que este módulo tenga su propio `Dockerfile` o `docker-compose.yml` ya que no es un servicio desplegable por sí mismo.)*

## Componentes Clave

-   **`auth/jwt_handler.py`**: Podría contener funciones para crear, decodificar y validar tokens JWT, utilizando una configuración centralizada de secretos.
-   **`db/`**: Podría incluir configuraciones de base de datos reutilizables, clases base para modelos SQLAlchemy, o helpers para la gestión de sesiones.
-   **`mlflow_utils/`**: Funciones para simplificar el logging de parámetros, métricas o artefactos a MLflow de una manera estandarizada.
-   **`schemas/`**: Definiciones Pydantic para estructuras de datos comunes, como mensajes de error estándar, respuestas paginadas genéricas, etc., que pueden ser reutilizadas por las APIs de diferentes módulos.

## Configuración y Uso

Este módulo está destinado a ser importado por otros módulos de Aletheia.

1.  **Instalación (como parte de otro módulo):**
    Las dependencias de `aletheia_common` deberían ser mínimas y, idealmente, estar cubiertas por las dependencias de los módulos que lo utilizan. Si tuviera dependencias únicas, estas deberían gestionarse en el contexto del proyecto global o del módulo consumidor.

2.  **Uso:**
    Simplemente importe las utilidades necesarias en otros módulos:
    ```python
    # Ejemplo en otro módulo:
    # from aletheia_common.auth import jwt_handler
    # from aletheia_common.schemas import ErrorResponse
    #
    # token_data = jwt_handler.decode_token(token, secret_key)
    # return ErrorResponse(detail="Ocurrió un error")
    ```

## Desarrollo y Pruebas

-   **Linters/Formateadores**: Ejecutar `pre-commit run --all-files` desde la raíz del repositorio Aletheia.
-   **Pruebas**:
    Las pruebas para las utilidades en `aletheia_common` pueden ser incluidas en los módulos que las utilizan para asegurar que se comportan como se espera en ese contexto. Alternativamente, si el módulo crece en complejidad, podría tener su propio directorio `tests/` dentro de `aletheia_common/`.

## Contribuciones

Las contribuciones deben enfocarse en funcionalidades que sean verdaderamente comunes a múltiples módulos. Evitar añadir lógica específica de un solo módulo aquí. Mantener las dependencias al mínimo.
```
