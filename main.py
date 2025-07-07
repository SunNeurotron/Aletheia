# This file serves as the entry point for Uvicorn as specified in the Dockerfile.
# It imports the FastAPI application instance from the mdu_cube_system.py file.

from mdu_cube_system import app

# To run with Uvicorn from the command line (if not using Docker CMD):
# uvicorn main:app --reload
#
# The Dockerfile CMD is:
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
# This will correctly pick up the 'app' instance imported above.

if __name__ == "__main__":
    # This block is optional and typically used for direct execution
    # (e.g., `python main.py`), which is not how Uvicorn usually runs in production.
    # However, it can be useful for local development if you want to run Uvicorn programmatically.
    import uvicorn
    print("Attempting to run Uvicorn server for MDU Cube System from main.py...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
