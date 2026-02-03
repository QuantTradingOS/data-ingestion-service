# Build from repo root: docker build -t qtos-data-service .
# Or from workspace: docker build -f data-ingestion-service/Dockerfile -t qtos-data-service data-ingestion-service

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

# Migrations run at startup via docker-compose command or entrypoint
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8001"]
