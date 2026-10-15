FROM python:3.12-slim

LABEL org.opencontainers.image.title="foundit-backend" \
      org.opencontainers.image.description="FoundIt campus lost & found API (FastAPI)"

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Dependencies first: this layer is only rebuilt when requirements.txt changes.
COPY requirements.txt .
RUN pip install -r requirements.txt \
 && useradd --create-home --uid 10001 appuser

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app

# Never run as root: a container breakout would otherwise start as root on the node.
USER 10001
EXPOSE 8000

# python:slim has no curl, so the healthcheck uses Python itself.
HEALTHCHECK --interval=10s --timeout=3s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status == 200 else 1)"

# Bring the schema up to date, then serve. exec makes uvicorn PID 1 so it receives SIGTERM.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'"]
