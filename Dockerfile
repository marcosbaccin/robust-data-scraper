# Imagem base leve do Python
FROM python:3.11-slim

# Evita arquivos .pyc e buffer de logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instala as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código fonte
COPY src/ src/

# Comando padrão ao rodar o container
CMD ["python", "src/scraper.py"]