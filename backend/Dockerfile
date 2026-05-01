FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN python -m compileall -q app && \
    DATABASE_URL=sqlite:// JWT_SECRET=build-secret-with-at-least-32-chars python -c "import app.main"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
