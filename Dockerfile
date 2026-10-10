FROM node:22-bookworm-slim AS frontend
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY tsconfig.json vite.config.ts capacitor.config.ts index.html ./
COPY src ./src
COPY public ./public
RUN npm run build

FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DATABASE_PATH=/data/pesteyar.sqlite3 UPLOAD_DIR=/data/uploads DEMO_MODE=false
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home app && mkdir /data && chown app:app /data
COPY main.py ./
COPY server ./server
COPY --from=frontend /app/dist ./dist
USER app
VOLUME ["/data"]
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')"
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--proxy-headers"]
