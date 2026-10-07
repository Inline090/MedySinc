FROM python:3.13-slim

# System libraries PaddleOCR and PDF handling need at runtime. libgomp1 is used by
# PyTorch and SentenceTransformers on CPU.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Manifests first, so Docker caches the installed packages across code changes.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app ./app

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Bake the embedding model into the image. The build gets slower and the image gets
# about 2.3 GB bigger, and in exchange a container restart is instant instead of
# downloading a model before it can serve anything.
ARG EMBEDDING_MODEL=BAAI/bge-m3
ENV MODEL_CACHE_DIR=/models
RUN python -c "\
from sentence_transformers import SentenceTransformer; \
SentenceTransformer('${EMBEDDING_MODEL}', cache_folder='/models')"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
