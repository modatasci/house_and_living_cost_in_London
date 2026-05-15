FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Build context must be the repo root (see fly.toml).
COPY v2/api/pyproject.toml ./
RUN pip install --upgrade pip && pip install .

COPY v2/api/app ./app
COPY data /srv/data
ENV DATA_DIR=/srv/data

EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
