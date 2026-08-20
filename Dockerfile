FROM python:3.12-slim@sha256:2c941e860699f878900b0edc2403613c234d4b32eda3cc9fa7036991a2a63c4a

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 qazfund \
    && useradd --uid 10001 --gid qazfund --create-home --shell /usr/sbin/nologin qazfund

COPY requirements.txt requirements-prod.txt ./
COPY vendor/qazstack-1.41.2-py3-none-any.whl vendor/qazstack-1.41.2-py3-none-any.whl
COPY vendor/qazstack-1.41.2.sha256 vendor/qazstack-1.41.2.sha256
RUN sha256sum -c vendor/qazstack-1.41.2.sha256 \
    && pip install --upgrade pip \
    && pip install -r requirements.txt

COPY --chown=qazfund:qazfund . .

EXPOSE 8000

USER 10001:10001

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
