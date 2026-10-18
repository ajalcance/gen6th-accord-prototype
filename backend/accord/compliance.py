"""Worker-pool process: uvicorn accord.compliance:app; private health only."""

from accord.command.compliance_app import create_compliance_app

app = create_compliance_app()
