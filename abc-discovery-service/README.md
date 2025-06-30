# ABC Discovery Service v2.2: AI-Guided Research Platform

Este proyecto es una plataforma completa y de nivel de producción para la investigación de la Conjetura abc, utilizando un enfoque de descubrimiento guiado por Inteligencia Artificial. El sistema está diseñado como un ecosistema de microservicios orquestado con Docker Compose.

Esta versión representa la culminación del desarrollo, transformando un simple script en un servicio robusto, escalable e inteligente.

![ABC Conjecture Diagram](https://i.imgur.com/your-image-link-here.png)
*(Opcional: puedes subir una imagen del concepto original o un diagrama de la arquitectura a un servicio como Imgur y enlazarla aquí para un `README` más visual)*

## Arquitectura del Sistema v2.2

El servicio sigue una arquitectura de microservicios distribuida, desacoplada y escalable:

-   **Dashboard Interactivo (`dashboard.py`):** Una interfaz de usuario web construida con **Streamlit** para enviar y monitorear trabajos de investigación inteligente.
-   **API REST (`api_server.py`):** Un punto de entrada robusto construido con **FastAPI** para la gestión programática de trabajos.
-   **Base de Datos (`database.py`, `models.py`):** Una base de datos **PostgreSQL** para la persistencia de datos de trabajos y descubrimientos, gestionada con **SQLAlchemy**.
-   **Workers Asíncronos (`celery_worker.py`):** Workers de **Celery** que ejecutan las tareas de cómputo pesado.
-   **Cerebro de IA (`intelligent_search.py`):** El corazón del sistema. Utiliza **Optimización Bayesiana** (`scikit-optimize`) para guiar la búsqueda de forma inteligente, aprendiendo del espacio de soluciones para encontrar "hits" de alta calidad de manera eficiente.
-   **Cola de Mensajes (`redis`):** Un broker de mensajes **Redis** que desacopla la API de los workers, permitiendo un procesamiento asíncrono.
-   **Orquestación (`docker-compose.yml`, `Dockerfile`):** Todo el ecosistema está contenerizado con **Docker** para un despliegue de un solo comando, fácil y reproducible.

## Flujo de Trabajo del Usuario

1.  El usuario accede al **Dashboard** en su navegador.
2.  Define un "presupuesto de búsqueda" (cuántas evaluaciones realizará la IA) y envía el trabajo.
3.  El Dashboard envía una solicitud a la **API REST**.
4.  La API crea un registro del trabajo en la base de datos **PostgreSQL** y envía una tarea a la cola de **Redis**.
5.  Un **Worker de Celery** recoge la tarea de la cola.
6.  El worker invoca al **Cerebro de IA**, que comienza su bucle de Optimización Bayesiana:
    a. Sugiere un punto prometedor en el espacio de búsqueda.
    b. Evalúa la calidad `q` en ese punto.
    c. Aprende del resultado y actualiza su "mapa de probabilidad".
    d. Repite hasta que se agota el presupuesto.
7.  Los "hits" encontrados se guardan en la base de datos **PostgreSQL**, asociados al ID del trabajo.
8.  El usuario puede refrescar el **Dashboard** para ver el estado del trabajo y, una vez completado, explorar los resultados y las visualizaciones.

## Requisitos Previos

-   Docker
-   Docker Compose

## Cómo Ejecutar la Plataforma Completa

1.  **Clonar el Repositorio:**
    ```bash
    git clone https://github.com/tu-usuario/abc-discovery-service.git
    cd abc-discovery-service
    ```

2.  **Construir y Levantar los Servicios:**
    Desde la raíz del proyecto, ejecute el siguiente comando. Esto construirá las imágenes de Docker, descargará las imágenes de Postgres y Redis, creará los contenedores de red y los iniciará.
    ```bash
    docker-compose up --build
    ```
    La primera vez que se ejecute, puede tardar varios minutos en descargar todas las dependencias y construir la imagen de la aplicación.

3.  **Acceder a los Servicios:**
    Una vez que todos los contenedores estén en funcionamiento, puede acceder a los diferentes componentes del sistema:

    -   **🔬 Dashboard Interactivo:** Abra su navegador y vaya a **`http://localhost:8501`**
    -   **📄 Documentación de la API:** Abra su navegador y vaya a **`http://localhost:8000/docs`**

4.  **Uso:**
    -   Utilice el dashboard para enviar un nuevo "Intelligent Search Job".
    -   Refresque el estado en el dashboard para monitorear el progreso del trabajo de `pending` a `processing` y finalmente a `completed`.
    -   Una vez completado, los resultados se mostrarán en la tabla y el gráfico del dashboard.

5.  **Detener la Plataforma:**
    Para detener todos los servicios de forma segura, presione `Ctrl+C` en el terminal donde ejecutó `docker-compose up`, y luego ejecute:
    ```bash
    docker-compose down
    ```
    Este comando detendrá y eliminará los contenedores, pero los datos en la base de datos persistirán en un volumen de Docker (`postgres_data`), por lo que no perderá sus descubrimientos entre sesiones.

## Licencia y Descargo de Responsabilidad

Este proyecto se distribuye bajo la Licencia Apache 2.0. Puede encontrar el texto completo de la licencia en el archivo [LICENSE](LICENSE).

Por favor, revise también el archivo [DISCLAIMER.md](DISCLAIMER.md) para entender las limitaciones y responsabilidades asociadas con el uso de este software.

## Próximos Pasos y Posibles Mejoras

Este proyecto es una base sólida. Las futuras mejoras podrían incluir:

-   **Mejora de la IA:** Experimentar con diferentes modelos suplentes (además del `GaussianProcessRegressor`) o funciones de adquisición en la Optimización Bayesiana.
-   **Tests Rigurosos:** Añadir una suite completa de tests unitarios, de integración y E2E.
-   **Seguridad:** Añadir autenticación a la API y al dashboard.
-   **Monitoreo Avanzado:** Integrar herramientas como Prometheus y Grafana para monitorear el rendimiento de los servicios.
-   **CI/CD:** Configurar un pipeline con GitHub Actions para automatizar los tests y los deployments.
