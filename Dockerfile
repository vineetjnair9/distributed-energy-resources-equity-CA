# syntax=docker/dockerfile:1

# 1. Frontend: typecheck, test, and build the React app.
FROM node:25-alpine AS frontend
WORKDIR /app
COPY docs/openapi.json docs/openapi.json
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm test && npm run build

# 2. Database: build the synthetic fixture through the production loaders.
#    pandas is needed here only, so it stays out of the runtime image.
FROM python:3.11-slim AS database
WORKDIR /app
RUN pip install --no-cache-dir pandas==2.3.3 numpy==1.26.4 openai==3.0.0 \
        python-dotenv==1.2.2 pydantic==2.13.5
COPY backend/ backend/
RUN python -m backend.fixtures.build_fixture_db --database /app/data/der.db

# 3. Runtime: FastAPI serves the API and the built frontend on one port.
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DER_DB_PATH=/app/data/der.db \
    PORT=8000
WORKDIR /app
COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt \
    && useradd --create-home --uid 10001 app
COPY backend/ backend/
COPY --from=frontend /app/frontend/dist frontend/dist
COPY --from=database --chown=app:app /app/data data
RUN chown app:app /app/data
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD python -c "import os,urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/health', timeout=4)"
CMD ["python", "-m", "backend.serve"]
