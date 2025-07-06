# Módulo Aletheia v3

Este es el módulo principal de la plataforma Aletheia.

Para la documentación completa del proyecto Aletheia v4.0, incluyendo la arquitectura general, configuración, cómo ejecutar la plataforma, detalles de migración de base de datos, y más, por favor consulte el **[README principal del proyecto](../../README.md)**.

Este directorio (`Aletheia_v3`) contiene los componentes centrales de la aplicación, como:
-   `api/`: El servidor FastAPI.
-   `core/`: La lógica de dominio y casos de uso.
-   `infrastructure/`: Componentes de infraestructura como la configuración de base de datos, Celery, etc.
-   `tests/`: Pruebas para el módulo.
-   `alembic/`: Configuraciones y versiones de migración de base de datos Alembic.
-   `docker-compose.yml`: Para ejecutar los servicios de este módulo.
-   `Dockerfile`: Para construir la imagen Docker del servicio principal de este módulo.

Cualquier documentación específica de los sub-componentes dentro de `Aletheia_v3` que no sea de interés general para la plataforma se puede encontrar en sus respectivos subdirectorios si es necesario.
