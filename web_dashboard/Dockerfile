FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080 8443
# Inicia simultaneamente as duas versões do painel (para o teste antes/depois)
CMD ["sh", "-c", "python app_vulneravel.py & python app_seguro.py"]