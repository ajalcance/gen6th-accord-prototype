"""Production reference process: uvicorn accord.reference:app on configured port 8000."""

from accord.personas.reference_app import create_reference_app

app = create_reference_app()
