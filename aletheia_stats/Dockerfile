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
# ENV STATS_API_PORT=8001 # Example, better to set in docker-compose or runtime

# Expose the port the app runs on. This should match the port Uvicorn listens to.
# This value is more for documentation and can be overridden at runtime.
# The actual port is determined by the CMD instruction and main.py's env var reading.
EXPOSE 8001 # Default port expected by main.py (STATS_API_PORT)

# Define the command to run the application
# Uvicorn will be started by main.py, which reads STATS_API_HOST and STATS_API_PORT.
# So, the command here just needs to execute main.py.
# The Dockerfile CMD should reflect how main.py's `if __name__ == "__main__":` block runs uvicorn.
# main.py's uvicorn.run expects "aletheia_stats.aletheia_stats.main:app"
# The host and port for uvicorn are read from ENV VARS by main.py itself.
CMD ["python", "-m", "aletheia_stats.aletheia_stats.main"]

# Healthcheck (optional but good practice)
# Ensure the port in the healthcheck matches the one the application actually uses (e.g. 8001 by default)
# HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
#   CMD curl -f http://localhost:8001/health || exit 1
