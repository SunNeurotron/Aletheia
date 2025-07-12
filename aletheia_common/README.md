# Módulo `aletheia_common`

`aletheia_common` es una biblioteca interna compartida que proporciona utilidades, esquemas y configuraciones comunes para todo el ecosistema de Aletheia. Su propósito es centralizar el código transversal para evitar la duplicación y garantizar la consistencia entre los diferentes microservicios y módulos de la plataforma.

**Este módulo no es un servicio desplegable**, sino una dependencia para otros módulos.

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

## Estructura del Módulo

-   **`auth/`**: Lógica para la gestión de tokens JWT (creación, validación, decodificación).
-   **`db/`**: Componentes de base de datos compartidos, como tipos de datos personalizados (`custom_types.py`) o modelos base de SQLAlchemy (`base.py`).
-   **`mlflow_utils/`**: Funciones de ayuda para estandarizar la interacción con el servidor de MLflow.
-   **`schemas/`**: Esquemas Pydantic comunes (ej. respuestas de error, modelos de usuario) para mantener la consistencia en las APIs.

## Uso

Este módulo se instala como una dependencia local en los entornos de desarrollo y de CI/CD de los otros módulos. Para utilizar sus componentes, simplemente impórtelos directamente.

```python
# Ejemplo de uso en otro módulo (ej. Aletheia_v3/api/auth.py)

from aletheia_common.auth import jwt_handler
from aletheia_common.schemas import UserSchema

def get_current_user(token: str) -> UserSchema:
    user_data = jwt_handler.decode_token(token)
    return UserSchema(**user_data)
```

## Desarrollo

-   **Propósito**: Añadir aquí solo código que sea genuinamente reutilizado por **dos o más** módulos.
-   **Dependencias**: Mantener las dependencias de este módulo al mínimo absoluto.
-   **Pruebas**: Las utilidades de `aletheia_common` se prueban de forma indirecta a través de las pruebas de los módulos que las consumen. Esto asegura que los componentes comunes funcionan correctamente en su contexto de uso real.
-   **Calidad de Código**: Ejecutar `pre-commit run --all-files` desde la raíz del proyecto para asegurar el cumplimiento de los estándares de formato y linting.
