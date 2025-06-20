FROM python:3.10-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Descargar modelos de spaCy
RUN python -m spacy download es_core_news_sm

# Copiar código
COPY . .

# Exponer puertos
EXPOSE 8501 8000 7860

# Comando por defecto
CMD ["python", "-m", "src.interfaces.streamlit_app"]