FROM node:24-bookworm-slim AS frontend
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim-bookworm AS runtime
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEALCOMPASS_ENGINE_MODE=rules \
    TYPESAFE_USAGE_DB=/data/typesafe-usage.sqlite3 \
    DEALCOMPASS_ANALYSIS_CACHE_DB=/data/analysis-cache.sqlite3
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend/
COPY dataset_kasirnusa/ ./dataset_kasirnusa/
COPY --from=frontend /build/frontend/dist ./frontend/dist
# Railway mounts volumes as root. /data must be a Railway volume, not image storage.
# No credentials or usage database are baked into the image.
EXPOSE 8080
CMD ["python", "-m", "backend.deployment"]
