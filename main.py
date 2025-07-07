# This file serves as the entry point for Uvicorn as specified in the Dockerfile.
# It imports the FastAPI application instance from the Aletheia_v3 MDU API server.

# Assuming Aletheia_v3 is in PYTHONPATH, or this main.py is in a location
# from where Aletheia_v3 can be imported.
from Aletheia_v3.api.mdu_api_server import create_mdu_api_application

# Create the application instance
# This allows for any setup within create_mdu_api_application() to run,
# such as setting up dependencies or configurations.
app = create_mdu_api_application()

# To run with Uvicorn from the command line (if not using Docker CMD):
# uvicorn main:app --reload
#
# The Dockerfile CMD is:
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
# This will correctly pick up the 'app' instance created above.

if __name__ == "__main__":
    # This block is optional and typically used for direct execution
    # (e.g., `python main.py`), which is not how Uvicorn usually runs in production.
    # However, it can be useful for local development if you want to run Uvicorn programmatically.
    import uvicorn
    print("Attempting to run Uvicorn server for Aletheia_v3 MDU API from main.py...")
    # Pass the app instance directly to uvicorn.run if it's already created.
    # If app creation is heavy, it's better done once as above.
    # Alternatively, pass the import string "main:app" to uvicorn.run
    # uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
