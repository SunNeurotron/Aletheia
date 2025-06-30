#!/bin/sh
# Aletheia_v3/entrypoint.sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Variables (can be overridden by Docker environment variables)
DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-5432}
MAX_DB_RETRIES=${MAX_DB_RETRIES:-30} # Number of retries (e.g., 30 times with 1s sleep = 30s timeout)
DB_RETRY_INTERVAL=${DB_RETRY_INTERVAL:-1} # Sleep interval in seconds

echo "Aletheia Entrypoint Script Initialized"
echo "---------------------------------------"
echo "DB_HOST: $DB_HOST"
echo "DB_PORT: $DB_PORT"
echo "---------------------------------------"

# Function to wait for the database to be available
wait_for_db() {
    echo "Waiting for PostgreSQL database at $DB_HOST:$DB_PORT to be available..."

    retries=0
    while ! nc -z "$DB_HOST" "$DB_PORT"; do
        retries=$((retries + 1))
        if [ "$retries" -ge "$MAX_DB_RETRIES" ]; then
            echo "Error: Timed out waiting for database at $DB_HOST:$DB_PORT after $MAX_DB_RETRIES retries."
            exit 1
        fi
        echo "Database not yet available. Retrying in $DB_RETRY_INTERVAL second(s)... (Attempt $retries/$MAX_DB_RETRIES)"
        sleep "$DB_RETRY_INTERVAL"
    done

    echo "PostgreSQL database is now available at $DB_HOST:$DB_PORT."
}

# Check if the first argument is a known command or if we should prepend 'python' or 'sh'
# This allows `docker run image_name python script.py` or `docker run image_name custom_command`
# For this project, docker-compose will pass specific commands like 'uvicorn', 'celery', 'streamlit'.

# Only wait for DB and run migrations if the command seems to need it
# (e.g., running the api server or celery worker).
# The dashboard might not directly need DB init but relies on the API which does.
# Heuristic: if command is uvicorn or celery, then init DB.
if [ "$1" = "uvicorn" ] || [ "$1" = "celery" ] || [ "$1" = "pytest" ]; then # Added pytest for test runs needing DB
    wait_for_db

    echo "Running database schema initialization/check..."
    # The Python script will handle table creation (idempotent)
    # Ensure PYTHONPATH is set if this script is called from a different context,
    # though Dockerfile's WORKDIR and ENV PATH should handle it.
    # The command is run using the venv python.
    python -c 'from infrastructure.database import init_db; init_db()'
    echo "Database schema initialization/check complete."

    # For pytest, we might not want to run the main command passed ($@) if it's also pytest.
    # The `docker-compose exec api pytest tests/` command structure means $@ will be "pytest tests/"
    # So, if the first arg is pytest, we just exec "$@" directly after DB init.
    if [ "$1" = "pytest" ]; then
        echo "Executing pytest command: $@"
        exec "$@"
    fi
elif [ "$1" = "streamlit" ]; then
    echo "Skipping DB initialization for Streamlit dashboard (relies on API)."
    # Streamlit doesn't directly connect to DB, so no init_db needed here.
else
    echo "Command does not appear to require database initialization, or it's unknown."
    echo "Proceeding directly with command: $@"
fi

# Execute the main command passed to the entrypoint (e.g., uvicorn, celery, streamlit run)
# This is what `CMD` in Dockerfile or `command` in docker-compose.yml provides.
echo "Executing main command: $@"
exec "$@"
```
