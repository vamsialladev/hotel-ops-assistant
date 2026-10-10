# Always-on image with full hybrid search (keywords + embeddings).
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

# CPU-only PyTorch: the default Linux wheel pulls several GB of CUDA libraries this app never uses.
COPY requirements.txt requirements-hybrid.txt ./
RUN pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements-hybrid.txt

COPY . .
# Build the search index (and download the embedding model) at build time so the container starts fast.
RUN python -m src.ingest && useradd --create-home app && chown -R app /app
USER app

# Hosts like Render set $PORT; locally it defaults to 8501.
EXPOSE 8501
HEALTHCHECK CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://localhost:{os.getenv(\"PORT\", \"8501\")}/_stcore/health')"
CMD ["sh", "-c", "streamlit run app.py --server.address=0.0.0.0 --server.port=${PORT:-8501}"]
