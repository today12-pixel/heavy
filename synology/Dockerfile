FROM python:3.12-slim

# Zeitzone für Zeitstempel im Log und im Dashboard
RUN apt-get update \
 && apt-get install -y --no-install-recommends tzdata \
 && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Europe/Berlin \
    HAUPTPROFIL=haupt \
    INTERVAL_HOURS=2 \
    PORT=8080

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY heavy ./heavy
COPY entrypoint.sh /app/entrypoint.sh

EXPOSE 8080
CMD ["sh", "/app/entrypoint.sh"]
