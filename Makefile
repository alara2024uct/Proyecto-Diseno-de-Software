# ==============================================================================
# Makefile para administrar el proyecto Anihub con Docker
# ==============================================================================

.PHONY: run build up down restart logs migrate createsuperuser shell bash test lint format clean help

# Comando por defecto: muestra la ayuda
.DEFAULT_GOAL := help

help:
	@echo "Comandos disponibles:"
	@echo "  make run             Levanta los contenedores en primer plano (up)"
	@echo "  make up              Levanta los contenedores en segundo plano (detached)"
	@echo "  make build           Construye o reconstruye las imágenes de Docker"
	@echo "  make down            Detiene y elimina los contenedores y redes creadas"
	@echo "  make restart         Reinicia los contenedores del proyecto"
	@echo "  make logs            Muestra los logs en tiempo real"
	@echo "  make migrate         Ejecuta las migraciones de base de datos en Django"
	@echo "  make createsuperuser Crea un usuario administrador interactivo en Django"
	@echo "  make shell           Abre el shell interactivo de Django"
	@echo "  make bash            Entra a la consola (bash) del contenedor web"
	@echo "  make test            Ejecuta las pruebas unitarias de Django"
	@echo "  make lint            Analiza la calidad del código (linter) usando Ruff"
	@echo "  make format          Formatea el código automáticamente usando Ruff"
	@echo "  make clean           Limpia contenedores, redes y volúmenes persistidos"

# Levanta el proyecto y muestra la salida en consola
run:
	cd Anihub && docker compose up

# Levanta el proyecto en segundo plano (detached mode)
up:
	cd Anihub && docker compose up -d

# Construye o reconstruye los contenedores
build:
	cd Anihub && docker compose build

# Detiene los contenedores y limpia los recursos de red del compose
down:
	cd Anihub && docker compose down

# Reinicia los servicios
restart:
	cd Anihub && docker compose restart

# Visualiza logs de los contenedores
logs:
	cd Anihub && docker compose logs -f

# Ejecuta las migraciones dentro del contenedor 'web'
migrate:
	cd Anihub && docker compose exec web python manage.py migrate

# Crea un superusuario de Django
createsuperuser:
	cd Anihub && docker compose exec web python manage.py createsuperuser

# Entra al shell interactivo de Django
shell:
	cd Anihub && docker compose exec web python manage.py shell

# Entra a la consola interactiva bash del contenedor web
bash:
	cd Anihub && docker compose exec web /bin/bash

# Ejecuta los tests de Django
test:
	cd Anihub && docker compose exec web python manage.py test

# Analiza la calidad del código (linter)
lint:
	ruff check Anihub/

# Formatea el código de manera automática
format:
	ruff format Anihub/

# Limpia los recursos incluyendo los volúmenes de base de datos
clean:
	cd Anihub && docker compose down -v