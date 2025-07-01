# Dockerfile para [Module Name]
# Este Dockerfile asume que el módulo es un servicio (ej. una API FastAPI).
# Ajustar según las necesidades del módulo (ej. si es una herramienta CLI, un worker, etc.)

# Utilizar una imagen base de Python oficial
FROM python:3.10-slim as base

# Variables de entorno para Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Directorio de trabajo en el contenedor
WORKDIR /app_module

# Copiar el archivo de requerimientos primero para aprovechar el caché de Docker
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código de la aplicación del módulo
# Esto asume que el código fuente está en un subdirectorio 'module_name'
COPY ./module_name ./module_name
# Copiar otros archivos necesarios (ej. scripts, configuraciones) si se acceden desde el contenedor
# COPY ./scripts ./scripts
# COPY ./alembic.ini ./alembic.ini # Si se usa alembic desde el CMD
# COPY ./alembic ./alembic

# Puerto en el que la aplicación del módulo escuchará (si es un servicio web)
# EXPOSE MODULE_API_PORT # Reemplazar MODULE_API_PORT con el puerto real, ej. 8001

# Comando para ejecutar la aplicación
# Ejemplo para una API FastAPI en module_name/main.py, instancia 'app'
# CMD ["uvicorn", "module_name.main:app", "--host", "0.0.0.0", "--port", "MODULE_API_PORT_INTERNAL"]

# Ejemplo para un script simple:
# CMD ["python", "module_name/main_script.py"]

# Placeholder - Definir el CMD apropiado para el módulo
CMD ["echo", "Dockerfile para [Module Name] - Reemplazar CMD con el comando de ejecución real."]
