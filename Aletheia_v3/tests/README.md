# Estrategia de Pruebas para Aletheia v3

Este directorio contiene el conjunto de pruebas automatizadas para el módulo `Aletheia_v3`. Nuestra filosofía de pruebas se centra en garantizar la corrección, robustez y mantenibilidad del sistema a través de múltiples niveles de verificación.

## Niveles de Pruebas

Adoptamos una estrategia de pruebas piramidal, con énfasis en pruebas unitarias rápidas y un conjunto selectivo de pruebas de mayor nivel para validar interacciones complejas.

1.  **Pruebas Unitarias (`unit/`)**:
    -   **Objetivo**: Verificar la lógica de componentes individuales (clases, métodos) en aislamiento.
    -   **Alcance**: Lógica de dominio (`core/domain_services.py`), funciones de utilidad, modelos de datos, heurísticas (`core/custom_acquisitions.py`).
    -   **Características**: Rápidas, sin dependencias externas (se usan mocks/stubs).

2.  **Pruebas de Integración (`integration/`)**:
    -   **Objetivo**: Validar la interacción entre varios componentes internos o con servicios externos (ej. base de datos, colas de mensajes).
    -   **Alcance**: Casos de uso (`application/use_cases.py`) con sus repositorios, interacciones API-Servicio, y flujos completos de conocimiento (`test_e2e_knowledge_flow.py`).

3.  **Pruebas de Sistema/Plugins**:
    -   **Objetivo**: Verificar la correcta integración y funcionamiento de sistemas transversales como el de plugins.
    -   **Ejemplo**: `test_plugin_system.py`.

4.  **Pruebas de API / End-to-End (E2E)**:
    -   **Objetivo**: Simular el comportamiento de un cliente externo, verificando el flujo completo a través de los endpoints de la API.
    -   **Ejemplo**: `test_api.py`.

## Cobertura de Pruebas por Capa Arquitectónica

El siguiente diagrama ilustra cómo nuestras pruebas cubren las distintas capas de la arquitectura del módulo:

<details>
<summary>Cobertura de Pruebas por Capa Arquitectónica</summary>

```mermaid
graph LR
    subgraph "Pruebas"
        direction TB
        T_E2E[Pruebas API/E2E]
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

    T_E2E -- Cubre --> L_API
    T_INT -- Cubre --> L_APP
    T_INT -- Cubre --> L_INFRA
    T_UNIT -- Cubre --> L_DOMAIN
    T_UNIT -- Cubre parcialmente --> L_APP

    style T_E2E fill:#f9d5e5
    style T_INT fill:#e8dff5
    style T_UNIT fill:#d5f4e6
```
</details>

## Ejecución de Pruebas

Las pruebas están escritas usando el framework `pytest`.

### 1. Desde el Entorno Docker (Recomendado)
Este método garantiza la consistencia con el entorno de CI/CD.
```bash
# Desde el directorio que contiene docker-compose.yml (ej. Aletheia_v3/)
docker-compose exec api pytest tests/
```
*(La ruta `tests/` asume que el WORKDIR en el Dockerfile está configurado en el directorio raíz del módulo `Aletheia_v3`)*.

### 2. Localmente
Requiere un entorno Python con todas las dependencias instaladas y los servicios necesarios (BD de prueba, Redis) en ejecución.
```bash
# Desde el directorio Aletheia_v3/
pytest tests/

# Desde la raíz del proyecto
pytest Aletheia_v3/tests/
```

## Informe de Cobertura

Para generar un informe de cobertura en formato HTML:
```bash
# Ajustar --cov para que apunte al directorio del código fuente del módulo
pytest --cov=Aletheia_v3 --cov-report=html Aletheia_v3/tests/
```
El informe se generará en el directorio `htmlcov/`.

## Directrices para Escribir Pruebas

-   Las nuevas características deben ir acompañadas de sus correspondientes pruebas.
-   Las correcciones de errores deben incluir pruebas de regresión.
-   Las pruebas deben ser claras, concisas y mantenibles. Utilice fixtures de `pytest` para la preparación y limpieza de datos.
-   Las pruebas deben ser independientes entre sí para permitir su ejecución en paralelo.
