# Stage 1: Build stage (optional, but good for managing dependencies if build steps are complex)
# For this Python app, a single stage is often sufficient.

# Use an official Python runtime as a parent image
FROM python:3.10-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1  # Prevents python from writing .pyc files to disc
ENV PYTHONUNBUFFERED 1      # Prevents python from buffering stdout and stderr

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (if any)
# For example, if psycopg2 needs postgresql-client or build tools:
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     gcc \
#     libpq-dev \
# && rm -rf /var/lib/apt/lists/*

# Copy just the requirements file to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
# Using --no-cache-dir reduces image size
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
# This should copy the 'aletheia_stats' package (containing domain, app, infra, presentation)
# and potentially other necessary files like alembic.ini if needed by the running app directly
# (though alembic commands are usually run as separate steps/jobs).
COPY ./aletheia_stats ./aletheia_stats
COPY ./scripts ./scripts  # If scripts like init_db are run from within the container sometimes
COPY ./alembic.ini ./alembic.ini # if needed by entrypoint/cmd
COPY ./alembic ./alembic # if migrations run from container startup

# Application specific environment variables (can also be set in docker-compose.yml)
# ENV DATABASE_URL="postgresql://user:pass@db_host:5432/aletheia_stats_db" # Example
# ENV MLFLOW_TRACKING_URI="http://mlflow_host:5000" # Example
# ENV JWT_SECRET_KEY="your-docker-secret-key" # Example
# ENV API_PORT=8000

# Expose the port the app runs on
EXPOSE 8000
# (If using a different port, change this and the CMD instruction)

# Define the command to run the application
# This will run the FastAPI app using Uvicorn.
# The path to the app instance is 'aletheia_stats.main:app'
# which means uvicorn looks for 'app' in 'aletheia_stats/main.py'
# Ensure your main.py defines the FastAPI instance as `app`.
# Our main.py is aletheia_stats/aletheia_stats/main.py, so the module path is aletheia_stats.aletheia_stats.main:app
CMD ["uvicorn", "aletheia_stats.aletheia_stats.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Healthcheck (optional but good practice)
# HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
#   CMD curl -f http://localhost:8000/health || exit 1
