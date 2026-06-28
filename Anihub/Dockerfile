# Usa Python 3.12-slim por la compatibilidad con Django 5.x y 6.x
FROM python:3.12-slim

# Evita que Python genere archivos .pyc y ayuda con los logs en consola
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Directorio de trabajo dentro del contenedor
WORKDIR /code

# Instalación de dependencias del sistema necesarias para:
# 1. Psycopg2 (libpq-dev, gcc) para conectar con Postgres
# 2. Pycryptodome (herramientas de compilación)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalamos/Actualizamos pip
RUN pip install --upgrade pip

# Copiamos e instalamos las librerías de Python
COPY requirements.txt /code/
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del proyecto
COPY . /code/

# Comando para arrancar el servidor
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]