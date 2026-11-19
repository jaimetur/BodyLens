# BodyLens: imagen de producción (FastAPI + SQLite + la página de la app)

# 1) librerías de la página (sin CDN), con versiones fijadas en frontend/package-lock.json
FROM node:22-slim AS vendor
WORKDIR /w
COPY src/frontend/package.json src/frontend/package-lock.json ./
RUN npm ci --omit=dev --ignore-scripts --no-audit --no-fund \
 && mkdir /vendor \
 && cp node_modules/xlsx/dist/xlsx.full.min.js node_modules/jspdf/dist/jspdf.umd.min.js \
       node_modules/html2canvas-pro/dist/html2canvas-pro.min.js /vendor/

# 2) servidor
FROM python:3.12-slim
ARG SOURCE_REVISION=dev
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    TZ=Europe/Madrid DATA_DIR=/data \
    FRONTEND_DIR=/app/frontend BRANDING_DIR=/app/branding VENDOR_DIR=/app/frontend/vendor DOCS_DIR=/app/docs \
    PUID=1000 PGID=1000 BODYLENS_REVISION=${SOURCE_REVISION}
RUN apt-get update && apt-get install -y --no-install-recommends tzdata && rm -rf /var/lib/apt/lists/* \
 && groupadd -g 1000 bodylens && useradd -u 1000 -g 1000 -M -d /app -s /usr/sbin/nologin bodylens
WORKDIR /app/backend
RUN pip install --no-cache-dir "fastapi==0.115.6" "uvicorn[standard]==0.34.0" "httpx==0.28.1" \
      "argon2-cffi==23.1.0" "google-auth==2.37.0" "requests==2.32.3" \
      "openpyxl==3.1.5" "cryptography==44.0.0" "anthropic==2.10.0"
COPY src/backend/app ./app
COPY src/frontend /app/frontend
COPY assets/branding /app/branding
COPY help /app/docs/help
COPY README*.md CHANGELOG.md /app/docs/
COPY --from=vendor /vendor /app/frontend/vendor
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod 0755 /entrypoint.sh && python -c "import app.main"
VOLUME ["/data"]
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=4)"
ENTRYPOINT ["/entrypoint.sh"]
# un solo proceso: el planificador de cada 15 min vive dentro y no debe duplicarse
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--proxy-headers", "--forwarded-allow-ips", "*"]
