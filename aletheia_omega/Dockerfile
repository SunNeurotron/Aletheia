# aletheia_omega/Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# Configurar el PYTHONPATH para incluir el directorio de la aplicación y cualquier módulo común montado.
# Si aletheia_common se monta en /app/aletheia_common, entonces /app debe estar en PYTHONPATH.
ENV PYTHONPATH /app

WORKDIR /app

# Instalar dependencias del sistema si fueran necesarias en el futuro
# Ejemplo: RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Copiar solo requirements.txt primero para aprovechar el cache de Docker si no cambia
COPY ./aletheia_omega/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# Copiar el código del módulo aletheia_omega y los archivos de Alembic.
# Estos paths asumen que el contexto del build de Docker es el directorio PADRE de aletheia_omega.
# Si el contexto es el propio directorio aletheia_omega, los paths serían:
# COPY ./requirements.txt ./
# COPY ./aletheia_omega ./aletheia_omega (o COPY . .) si todo está en el raíz del contexto
# Por ahora, seguimos la asunción de que el contexto es el padre,
# y los archivos de este módulo están en un subdirectorio aletheia_omega.

COPY ./aletheia_omega /app/aletheia_omega
COPY ./aletheia_omega/alembic.ini /app/alembic.ini
COPY ./aletheia_omega/alembic /app/alembic

# Si aletheia_common se copia como parte de la imagen (en lugar de montarse como volumen):
# COPY ./aletheia_common /app/aletheia_common

# Exponer el puerto en el que la API se ejecutará dentro del contenedor
EXPOSE 8002

# Comando por defecto para ejecutar la aplicación.
# Puede ser sobreescrito por docker-compose.yml (ej. para añadir --reload).
# Asegurarse de que el path al módulo de la API sea correcto.
CMD ["uvicorn", "aletheia_omega.presentation.api:app", "--host", "0.0.0.0", "--port", "8002"]
