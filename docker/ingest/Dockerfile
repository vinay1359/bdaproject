FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ingest /app/src/ingest
ENV PYTHONUNBUFFERED=1
