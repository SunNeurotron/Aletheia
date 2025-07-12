# Estrategia de Pruebas para `Aletheia_v3`

Este directorio contiene el conjunto de pruebas automatizadas para el módulo `Aletheia_v3`, enfocadas en garantizar la corrección, robustez y mantenibilidad del sistema.

## Niveles de Pruebas y Cobertura

Adoptamos una estrategia de pruebas piramidal, donde la cobertura de cada capa de la arquitectura es fundamental.

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

-   **Pruebas Unitarias (`unit/`)**: Verifican componentes en aislamiento (lógica de dominio, utilidades). Son rápidas y no tienen dependencias externas.
-   **Pruebas de Integración (`integration/`)**: Validan la interacción entre componentes (ej. casos de uso con repositorios) y con servicios como la base de datos.
-   **Pruebas de API / E2E**: Simulan el comportamiento de un cliente, verificando el flujo completo a través de los endpoints de la API.

## Ejecución de Pruebas

Las pruebas utilizan el framework `pytest`.

### 1. Entorno Docker (Recomendado)
Garantiza la consistencia con el entorno de CI/CD.
```bash
# Desde el directorio que contiene docker-compose.yml (ej. Aletheia_v3/)
docker-compose exec api pytest tests/
```

### 2. Localmente
Requiere un entorno Python con todas las dependencias y servicios necesarios (BD, Redis) en ejecución.
```bash
# Desde el directorio Aletheia_v3/
pytest tests/
```

### Informe de Cobertura
Para generar un informe de cobertura en formato HTML:
```bash
pytest --cov=Aletheia_v3 --cov-report=html Aletheia_v3/tests/
```
El informe se generará en el directorio `htmlcov/`.

## Directrices
-   Nuevas características deben ir acompañadas de sus pruebas.
-   Correcciones de errores deben incluir pruebas de regresión.
-   Las pruebas deben ser claras, concisas y mantenibles.
