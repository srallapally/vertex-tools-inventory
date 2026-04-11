FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py ./
COPY inventory ./inventory
COPY config ./config

CMD ["python3", "main.py", "--config", "/app/config/job-config.json"]
