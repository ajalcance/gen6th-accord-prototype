# Multi-stage, non-root runtime image.
FROM python:3.12-slim@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1 AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first (better layer caching).
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# App code.
COPY . .

# Run as a non-root user, named by its numeric id so a runtime (Kubernetes runAsNonRoot, Cloud
# Run) can verify it is not root without resolving a name (hadolint DL3066).
RUN useradd --create-home --uid 10001 appuser
USER 10001

EXPOSE 8000
# Exec (JSON) form: no shell wraps the check, so signals and exit codes are the check's own
# (hadolint DL3025).
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health').status==200 else 1)"]

CMD ["uvicorn", "accord.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
