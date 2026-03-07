FROM python:3.11-slim
WORKDIR /app
RUN echo "RAILWAY_PYTHON_DOCKERFILE_MARKER_20260307"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
