# Estrategia de Pruebas para Aletheia v3

Este directorio contiene el conjunto de pruebas automatizadas para el módulo `Aletheia_v3`. Nuestra filosofía de pruebas se centra en garantizar la corrección, robustez y mantenibilidad del sistema a través de múltiples niveles de verificación.

## Niveles de Pruebas

Adoptamos una estrategia de pruebas piramidal, con énfasis en pruebas unitarias rápidas y un conjunto selectivo de pruebas de mayor nivel para validar interacciones complejas.

1.  **Pruebas Unitarias (`unit/`)**:
    -   **Objetivo**: Verificar la lógica de componentes individuales (clases, métodos) en aislamiento.
    -   **Alcance**: Lógica de dominio (`core/domain_services.py`), funciones de utilidad, modelos de datos.
    -   **Características**: Rápidas, sin dependencias externas (se usan mocks/stubs).
    -   **Ejemplos**: `tests/unit/test_domain_services.py`.

2.  **Pruebas de Integración (`integration/`)**:
    -   **Objetivo**: Validar la interacción entre varios componentes internos o con servicios externos (ej. base de datos, colas de mensajes).
    -   **Alcance**: Casos de uso (`application/use_cases.py`) con sus repositorios, interacciones API-Servicio.
    -   **Características**: Pueden requerir una base de datos de prueba o un broker de mensajes. Más lentas que las unitarias.
    -   **Ejemplos**: `tests/integration/test_e2e_knowledge_flow.py`, `tests/integration/test_mdu_cubic_pipeline.py`.

3.  **Pruebas de API / End-to-End (E2E)**:
    -   **Objetivo**: Simular el comportamiento del usuario o de un cliente externo, verificando el flujo completo a través de la API hasta la base de datos y de vuelta.
    -   **Alcance**: Endpoints de la API (`api/routers/`), incluyendo serialización, autenticación y respuesta.
    -   **Características**: Las más lentas; requieren que la aplicación (o una parte significativa) esté en ejecución.
    -   **Ejemplos**: `tests/test_api.py` (si prueba los endpoints completos).

4.  **Pruebas de Propiedad (Opcional/Conceptual - `property/`)**:
    -   **Objetivo**: Verificar que el código satisface ciertas propiedades o invariantes para un amplio rango de entradas generadas automáticamente.
    -   **Alcance**: Funciones con lógica matemática compleja, algoritmos.
    -   **Herramientas**: [Hypothesis](https://hypothesis.readthedocs.io/).

## Cobertura de Pruebas por Capa Arquitectónica

El siguiente diagrama ilustra cómo nuestras pruebas cubren las distintas capas de la arquitectura del módulo:

```mermaid
graph LR
    subgraph "Pruebas"
        direction TB
        T_API[Pruebas API/E2E]
        T_INT[Pruebas de Integración]
        T_UNIT[Pruebas Unitarias]
    end

    subgraph "Arquitectura Aletheia_v3"
        direction TB
        L_API[API (FastAPI Routers)]
        L_APP[Aplicación (Casos de Uso, Puertos)]
        L_INFRA[Infraestructura (Repositorios, BD, Celery)]
        L_DOMAIN[Dominio (Modelos, Servicios de Dominio)]
    end

    T_API -- Cubre --> L_API
    T_INT -- Cubre --> L_APP
    T_INT -- Cubre --> L_INFRA
    T_UNIT -- Cubre --> L_DOMAIN
    T_UNIT -- Cubre parcialmente --> L_APP

    style T_API fill:#f9d5e5
    style T_INT fill:#e8dff5
    style T_UNIT fill:#d5f4e6
```

## Ejecución de Pruebas

Las pruebas se desarrollan utilizando el framework `pytest`.

### 1. Entorno Docker (Recomendado)
Para consistencia y facilidad, especialmente en CI/CD:
```bash
# Asegúrate de estar en el directorio Aletheia_v3/ o el raíz del proyecto
# si docker-compose.yml está allí.
docker-compose exec api pytest /opt/aletheia/Aletheia_v3/tests/
# o simplemente 'pytest tests/' si el WORKDIR en el Dockerfile es /opt/aletheia/Aletheia_v3/
# o 'pytest Aletheia_v3/tests/' si el WORKDIR es /opt/aletheia/
```
Ajuste la ruta según la configuración de `WORKDIR` en su `Dockerfile` y la ubicación de los tests.

### 2. Localmente
Requiere un entorno Python con todas las dependencias (`Aletheia_v3/requirements.txt`) y servicios (BD de prueba, Redis) configurados y accesibles.
```bash
# Desde el directorio Aletheia_v3/
pytest tests/

# Desde la raíz del proyecto
pytest Aletheia_v3/tests/
```

## Informe de Cobertura

Para generar un informe de cobertura (HTML):
```bash
# Asegúrate de ajustar --cov para que apunte al directorio del código fuente del módulo
pytest --cov=aletheia_v3 --cov-report=html Aletheia_v3/tests/
```
Esto asumirá que tu código fuente principal para el módulo `Aletheia_v3` está en una carpeta llamada `aletheia_v3` (por ejemplo, `Aletheia_v3/aletheia_v3/...`). Si la estructura es `Aletheia_v3/api/`, `Aletheia_v3/core/`, etc., podrías necesitar listar múltiples rutas o una ruta padre: `--cov=Aletheia_v3`.

El informe se generará en el directorio `htmlcov/`.

## Directrices para Escribir Pruebas

-   **Nuevas Características**: Deben ir acompañadas de pruebas que cubran su funcionalidad.
-   **Corrección de Errores**: Incluir pruebas de regresión para evitar que el error reaparezca.
-   **Claridad**: Las pruebas deben ser fáciles de entender y mantener.
-   **Independencia**: Las pruebas deben ser independientes entre sí para poder ejecutarse en cualquier orden y en paralelo.
-   **Preparación y Limpieza**: Utilice fixtures de `pytest` (`conftest.py`) para gestionar el estado de las pruebas (ej. datos de prueba en la BD).
