FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Inicia a reconciliação (buffer) e a IA Defensiva em paralelo
CMD ["sh", "-c", "python store_and_forward.py & python anomaly_detection.py"]