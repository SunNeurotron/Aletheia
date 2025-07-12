# Módulo `aletheia_common`: Fundamentos Compartidos

`aletheia_common` es una biblioteca interna esencial que proporciona utilidades, esquemas Pydantic y configuraciones comunes para todo el ecosistema Aletheia. Su objetivo principal es centralizar el código transversal, promoviendo la reutilización, la consistencia y reduciendo la duplicación entre los diversos microservicios.

**Este módulo no es un servicio desplegable**, sino una dependencia fundamental para otros módulos de la plataforma.

## Rol en el Ecosistema Aletheia

Este módulo sirve como la base sobre la cual se construyen otros servicios, proporcionando funcionalidades reutilizables.

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

    subgraph "Funcionalidades Comunes Provistas"
        direction LR
        AUTH[Auth (JWT)]
        DB_UTILS[DB (Tipos, Base SQLAlchemy)]
        ML_UTILS[MLflow Utils]
        SCHEMAS[Schemas Pydantic]
    end

    A -- Importa --> C
    O -- Importa --> C
    S -- Importa --> C

    C -- Provee --> AUTH
    C -- Provee --> DB_UTILS
    C -- Provee --> ML_UTILS
    C -- Provee --> SCHEMAS

    style C fill:#d5e8d4,stroke:#333,stroke-width:2px
    style A fill:#d2eaff
    style O fill:#e8dff5
    style S fill:#fcf6bd
```

## Componentes Clave

-   **`auth/`**: Lógica para la gestión de tokens JWT (creación, validación, decodificación).
-   **`db/`**: Componentes de base de datos compartidos, como tipos de datos personalizados (`custom_types.py`) o modelos base de SQLAlchemy (`base.py`).
-   **`mlflow_utils/`**: Funciones de ayuda para estandarizar la interacción con el servidor de MLflow.
-   **`schemas/`**: Esquemas Pydantic comunes (ej. respuestas de error, modelos de usuario) para mantener la consistencia en las APIs.

## Uso e Integración
Este módulo se instala como una dependencia en los entornos de desarrollo de los otros módulos. Para utilizar sus componentes:
```python
# Ejemplo de uso en Aletheia_v3/api/auth.py
from aletheia_common.auth import jwt_handler
from aletheia_common.schemas import UserSchema # Suponiendo que UserSchema está en aletheia_common

def get_current_user_example(token: str) -> UserSchema:
    user_data = jwt_handler.decode_token(token)
    # ... lógica adicional ...
    return UserSchema(**user_data)
```

## Directrices de Desarrollo
-   **Propósito**: Añadir aquí solo código que sea genuinamente reutilizado por **dos o más** módulos.
-   **Dependencias**: Mantener las dependencias de este módulo al mínimo absoluto.
-   **Pruebas**: Las utilidades se prueban indirectamente a través de los tests de los módulos consumidores.
