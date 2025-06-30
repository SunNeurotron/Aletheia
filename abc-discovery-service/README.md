# ABC Discovery Service v2.2

Este proyecto es una plataforma completa y de nivel de producción para la investigación de la Conjetura abc, utilizando un enfoque de descubrimiento guiado por Inteligencia Artificial. El sistema está diseñado como un ecosistema de microservicios orquestado con Docker Compose.

## Arquitectura

El servicio sigue una arquitectura de microservicios distribuida, desacoplada y escalable:

-   **Dashboard Interactivo (`dashboard.py`):** Una interfaz de usuario web construida con **Streamlit** para enviar y monitorear trabajos de investigación.
-   **API REST (`api_server.py`):** Un punto de entrada robusto construido con **FastAPI** para la gestión programática de trabajos.
-   **Base de Datos (`database.py`, `models.py`):** Una base de datos **PostgreSQL** para la persistencia de datos, gestionada con **SQLAlchemy**.
-   **Workers Asíncronos (`celery_worker.py`, `intelligent_search.py`):** Workers de **Celery** que ejecutan las tareas de cómputo pesado, utilizando **Optimización Bayesiana** (`scikit-optimize`) para guiar la búsqueda de forma inteligente.
-   **Cola de Mensajes (`redis`):** Un broker de mensajes **Redis** que desacopla la API de los workers.
-   **Orquestación (`docker-compose.yml`, `Dockerfile`):** Todo el ecosistema está contenerizado con **Docker** para un despliegue fácil y reproducible.

## Requisitos

-   Docker
-   Docker Compose

## Cómo Ejecutar la Plataforma

1.  **Clonar el Repositorio:**
    ```bash
    git clone <URL-del-repositorio>
    cd abc-discovery-service
    ```

2.  **Construir y Levantar los Servicios:**
    Desde la raíz del proyecto, ejecute el siguiente comando. Esto construirá las imágenes de Docker, descargará las imágenes de Postgres y Redis, creará los contenedores y los iniciará.
    ```bash
    docker-compose up --build
    ```
    La primera vez que se ejecute, puede tardar varios minutos en descargar y construir todo.

3.  **Acceder a los Servicios:**
    Once que todos los contenedores estén en funcionamiento, puede acceder a los diferentes componentes del sistema:

    -   **Dashboard Interactivo:** Abra su navegador y vaya a `http://localhost:8501`
    -   **Documentación de la API:** Abra su navegador y vaya a `http://localhost:8000/docs`

4.  **Uso:**
    -   Utilice el dashboard para enviar un nuevo "Intelligent Search Job".
    -   Refresque el estado en el dashboard para monitorear el progreso del trabajo de "pending" a "processing" y finalmente a "completed".
    -   Una vez completado, los resultados se mostrarán en el dashboard.

5.  **Detener la Plataforma:**
    Para detener todos los servicios, presione `Ctrl+C` en el terminal donde ejecutó `docker-compose up`, y luego ejecute:
    ```bash
    docker-compose down
    ```
    Esto detendrá y eliminará los contenedores, pero los datos en la base de datos persistirán en un volumen de Docker.
