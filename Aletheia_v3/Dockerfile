# Aletheia_v3/Dockerfile

# Use an official Python runtime as a parent image
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1  # Prevents python from writing .pyc files
ENV PYTHONUNBUFFERED 1      # Prevents python from buffering stdin/stdout/stderr

# Set the working directory in the container
WORKDIR /opt/aletheia

# Install system dependencies that might be needed by Python packages
# For example, build-essential for packages that compile C extensions,
# libpq-dev for psycopg2 if not using psycopg2-binary.
# Since we use psycopg2-binary and scikit-optimize often bundles its deps,
# this might be minimal. netcat-openbsd is for the entrypoint script's DB check.
# For cypari2 (PARI/GP), we need libgmp-dev, libmpfr-dev, libmpc-dev.
# Numba often needs llvm and tbb, but pip wheels might handle this. Let's add build-essentials.
# Added libpari-dev for cypari2 compilation and reordered for clarity
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpari-dev \
    libgmp-dev \
    libmpfr-dev \
    libmpc-dev \
    netcat-openbsd \
    postgresql-client && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install pipenv if you were to use Pipfile (optional, sticking to requirements.txt for now)
# RUN pip install pipenv

# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
# Using --no-cache-dir reduces image size
# Using a virtual environment within the Docker image is a good practice
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt && \
    /opt/venv/bin/python -m spacy download en_core_web_sm

# Now copy the entire project's source code into the container
# This includes all subdirectories (api, core, infrastructure, dashboard, tests)
COPY . /opt/aletheia/

# Make the entrypoint script executable
COPY entrypoint.sh /opt/aletheia/entrypoint.sh
RUN chmod +x /opt/aletheia/entrypoint.sh

# --- Final Stage ---
# For a smaller final image, could use a new slim stage and copy only the venv and app code
# FROM python:3.11-slim as final
# WORKDIR /opt/aletheia
# COPY --from=builder /opt/venv /opt/venv
# COPY --from=builder /opt/aletheia /opt/aletheia
# RUN chmod +x /opt/aletheia/entrypoint.sh
# ENV PATH="/opt/venv/bin:$PATH"
# ENTRYPOINT ["/opt/aletheia/entrypoint.sh"]
# CMD instruction will be provided by docker-compose.yml for each service (api, worker, dashboard)

# For simplicity, we'll use the builder stage directly if multi-stage isn't strictly needed yet.
# The main benefit of multi-stage here would be if the build process pulled in lots of build-only deps.

# Ensure the PATH includes the virtual environment's bin directory
ENV PATH="/opt/venv/bin:$PATH"

# The ENTRYPOINT will execute the entrypoint.sh script.
# The CMD will be passed from the docker-compose.yml file to specify what command
# the entrypoint.sh script should finally execute (e.g., uvicorn, celery, streamlit).
ENTRYPOINT ["/opt/aletheia/entrypoint.sh"]

# Expose ports (optional, as docker-compose handles port mapping, but good for documentation)
# FastAPI app typically runs on 8000
EXPOSE 8000
# Streamlit dashboard typically runs on 8501
EXPOSE 8501
# MLflow UI typically runs on 5000 (this Dockerfile isn't for MLflow server itself, but for app components)

# Default CMD (can be overridden by docker-compose.yml)
# This is just a placeholder if someone runs `docker run <image_name>` without a command.
# It's not strictly necessary as docker-compose defines the commands.
# CMD ["uvicorn", "Aletheia_v3.api.api_server:app", "--host", "0.0.0.0", "--port", "8000"]
# The actual commands for api, worker, dashboard are set in docker-compose.yml
# and passed to entrypoint.sh.
CMD ["--help"] # Or some other default action if run directly.
```
