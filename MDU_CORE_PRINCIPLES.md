# Marco de Desarrollo Unificado (MDU) - Principios Centrales para el Ecosistema Aletheia

Este documento describe los principios fundamentales del Marco de Desarrollo Unificado (MDU) que rigen el desarrollo y la evolución del proyecto Aletheia y todos sus módulos derivados (como Aletheia-Stats, futuros módulos de visualización, etc.) dentro del repositorio `SunNeurotron/Aletheia`. El MDU tiene como objetivo fusionar la robustez de la ingeniería de software de producción con el rigor y la flexibilidad necesarios para la investigación científica.

## Visión General del MDU en Aletheia

El MDU en Aletheia actúa como un **núcleo generativo**: un conjunto de directrices, arquitecturas y herramientas que facilitan la creación, integración y mantenimiento de componentes de software modulares, escalables y de alta calidad. Permite que el ecosistema Aletheia evolucione de manera coherente a medida que se incorporan nuevos aprendizajes, algoritmos y funcionalidades.

## Principios Fundamentales del MDU

Todos los componentes desarrollados dentro del ecosistema Aletheia deben adherirse a los siguientes principios:

1.  **Completitud Absoluta (Production-Grade Readiness)**:
    *   **Sin Placeholders**: Todo el código entregado debe ser funcional y completo. No se aceptan funciones vacías, comentarios "TODO" sin seguimiento, o lógica incompleta en ramas principales.
    *   **Configuración Explícita**: Las configuraciones deben ser explícitas y manejadas a través de variables de entorno (con valores por defecto seguros) y archivos de configuración versionados (`.env.example`).
    *   **Manejo de Errores Robusto**: Implementación de manejo de excepciones exhaustivo, con logging claro y respuestas de error significativas para las APIs.

2.  **Rigor Científico y Metodológico**:
    *   **Validación Intrínseca**: Incorporar validaciones estadísticas y lógicas dentro del propio código (ej. pruebas de normalidad antes de una prueba t, chequeo de precondiciones para algoritmos).
    *   **Documentación Científica**:
        *   Las funciones y módulos clave que implementan lógica científica deben incluir docstrings detallados.
        *   Estos docstrings deben explicar el "porqué" y el "cómo", incluyendo **ecuaciones LaTeX** para fórmulas matemáticas y **referencias bibliográficas** a papers o textos relevantes.
    *   **Trazabilidad y Reproducibilidad**:
        *   Uso obligatorio de **MLflow** (u otra herramienta de seguimiento de experimentos designada) para registrar parámetros, métricas, artefactos y versiones de código de todas las ejecuciones experimentales o análisis significativos.
        *   Uso de **semillas fijas** (`random_state`) en todos los procesos estocásticos para garantizar la reproducibilidad de los resultados.
    *   **Transparencia Metodológica**: La lógica detrás de cualquier análisis o algoritmo debe ser clara, bien documentada y justificable.

3.  **Calidad de Código Excepcional**:
    *   **Tipado Estático Estricto**: Uso obligatorio de type hints de Python en todo el código. Verificación con **MyPy** en modo estricto.
    *   **Linting y Formateo Automatizado**: Adhesión a un estilo de código consistente mediante **Black** para formateo y **Flake8** (con plugins como `flake8-bugbear`) para linting. Configuración gestionada centralmente a través de `pre-commit`.
    *   **Pruebas Exhaustivas**:
        *   **Cobertura de Pruebas > 90%**: Medida con `pytest-cov`.
        *   **Pruebas Unitarias**: Para componentes individuales y lógica de dominio.
        *   **Pruebas de Integración**: Para verificar la interacción entre componentes (ej. API con casos de uso y repositorios).
        *   **Pruebas de Propiedad (Hypothesis)**: Para funciones críticas o con lógica compleja, para asegurar robustez ante una amplia gama de entradas.
    *   **Código Limpio y Modular**: Seguir principios como DRY (Don't Repeat Yourself), SOLID (cuando aplique), y mantener funciones y clases concisas y enfocadas.

4.  **Arquitectura Robusta y Escalable**:
    *   **Arquitectura Hexagonal-Científica**:
        *   **Núcleo de Dominio Puro**: La lógica científica y de negocio (`domain/`) debe ser independiente de frameworks y detalles de infraestructura.
        *   **Capa de Aplicación Clara**: Orquestación de casos de uso (`application/`).
        *   **Adaptadores de Infraestructura**: Implementaciones concretas para bases de datos, APIs externas, MLflow, etc. (`infrastructure/`).
        *   **Capa de Presentación Flexible**: APIs (FastAPI), CLIs, o interfaces gráficas (`presentation/`).
    *   **Inyección de Dependencias**: Utilizar inyección de dependencias (ej. con FastAPI `Depends`) para desacoplar componentes.
    *   **Seguridad por Defecto**:
        *   Autenticación (JWT) y autorización (RBAC basada en roles/scopes) para endpoints sensibles de API.
        *   Manejo seguro de secretos y configuraciones.
    *   **Preparado para Contenerización y Orquestación**:
        *   Todos los servicios deben ser desplegables mediante **Docker**.
        *   Configuración de **Docker Compose** para desarrollo local y pruebas de integración.
        *   Considerar la preparación para **Kubernetes** para despliegues escalables (ver `README.md` de Aletheia principal).
    *   **Migraciones de Base de Datos**: Uso de **Alembic** para gestionar cambios de esquema de base de datos de forma versionada y reproducible.

5.  **Despliegue y Operaciones (DevOps)**:
    *   **Integración Continua (CI)**: Workflow de GitHub Actions (`.github/workflows/ci.yml`) que automáticamente ejecuta linters, formateadores, pruebas y builds para cada push/PR.
    *   **Despliegue Continuo (CD - Opcional pero Recomendado)**: Configuración para desplegar automáticamente a entornos de staging/producción tras pasar el CI en ramas designadas.
    *   **Logging Estructurado**: Uso de logging comprensible y estructurado en todos los servicios para facilitar la depuración y monitorización.

## Desarrollo de Módulos Derivados

Los nuevos módulos o subproyectos que se integren en el ecosistema Aletheia deben:

1.  **Seguir los Principios del MDU**: Adherirse a todos los puntos mencionados anteriormente.
2.  **Utilizar la Plantilla de Módulo**: Empezar desde `_module_template/` (si está disponible y es aplicable) para una estructura inicial consistente.
3.  **Integrarse con la Infraestructura Compartida**: Cuando sea posible y tenga sentido, los módulos deben utilizar los servicios de infraestructura compartidos (Base de Datos, MLflow, Redis, Autenticación) definidos centralmente en Aletheia (ver `aletheia_common/` y `docker-compose.yml` principal).
    *   Si un módulo requiere su propia base de datos aislada, puede ser una base de datos separada dentro de la misma instancia de PostgreSQL gestionada centralmente.
    *   Las migraciones de Alembic serán específicas del módulo pero coordinadas.
4.  **Ser Documentados Adecuadamente**: Incluir un `README.md` específico del módulo, documentación de arquitectura si es compleja, y documentación científica relevante.
5.  **Incluir un Conjunto Completo de Pruebas**: Unitarias, de integración y, si aplica, de propiedad.
6.  **Actualizar el CI/CD Principal**: Asegurar que el workflow de CI en `.github/workflows/ci.yml` se actualice para incluir la construcción y prueba del nuevo módulo.

## Evolución del MDU

El propio MDU es un framework vivo. Se espera que evolucione a medida que el proyecto Aletheia crece y se aprenden nuevas lecciones. Los cambios significativos al MDU deben ser discutidos y documentados.

---

Este documento sirve como la "constitución" para el desarrollo dentro de Aletheia. Su cumplimiento asegura un ecosistema de software científico que es a la vez innovador, robusto y sostenible.
