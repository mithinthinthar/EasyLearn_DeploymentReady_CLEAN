FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 TRANSFORMERS_CACHE=/opt/models HF_HOME=/opt/models
WORKDIR /app
COPY requirements.deploy.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
# Cache the semantic model in the image so a final tester does not wait for a model download.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
COPY . .
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 1 --threads 4 --timeout 300 history_app_local:app"]
