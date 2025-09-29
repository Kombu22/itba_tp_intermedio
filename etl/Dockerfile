# Base mínima con Python
FROM python:3.11-slim
WORKDIR /app                   # Carpeta de trabajo dentro del contenedor

# Instala dependencias de Python
COPY etl/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el script
COPY etl/main.py .

# Comando por defecto del contenedor
CMD ["python", "main.py"]
