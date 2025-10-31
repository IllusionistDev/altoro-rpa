# Use the official Playwright image that already has browsers & deps
FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

# Speed and sanity
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONDONTWRITEBYTECODE=1

# Workdir inside container
WORKDIR /app

# Copy only reqs first for better build caching
COPY requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# (Re)install chromium in case versions drift; no-op if present
RUN playwright install chromium

# Copy the rest of the app
COPY src ./src
COPY README.md ./
# Create artifacts dir (also mountable as a volume)
RUN mkdir -p artifacts/logs artifacts/screenshots artifacts/traces artifacts/outputs

# Default command: run the full orchestrator
CMD ["python", "-m", "src.orchestration.run_all"]
