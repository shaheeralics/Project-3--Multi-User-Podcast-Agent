# ---------- FRONTEND BUILD ----------
FROM node:20-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* frontend/pnpm-lock.yaml* ./
RUN if [ -f pnpm-lock.yaml ]; then npm i -g pnpm && pnpm i;     elif [ -f package-lock.json ]; then npm ci; else npm i; fi
COPY frontend ./
RUN npm run build || pnpm build

# ---------- BACKEND RUNTIME ----------
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg curl && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend ./backend
COPY --from=frontend /app/frontend/dist ./frontend_dist
ENV FLASK_ENV=production
ENV FRONTEND_DIST=/app/frontend_dist
EXPOSE 8080
WORKDIR /app/backend
CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:app"]
