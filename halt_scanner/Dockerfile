FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Create data directory
RUN mkdir -p data logs

# Health check
HEALTHCHECK --interval=5m --timeout=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=5)" || exit 1

# Environment variables (override in deployment)
ENV ANTHROPIC_API_KEY=""
ENV TELEGRAM_BOT_TOKEN=""
ENV TELEGRAM_CHAT_ID=""
ENV EMAIL_ENABLED="false"

EXPOSE 8080

CMD ["python", "main.py"]
