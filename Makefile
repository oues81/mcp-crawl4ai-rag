.PHONY: install build up down logs test clean

# Variables
SERVICE_NAME := mcp-crawl4ai-rag
DOCKER_COMPOSE := docker-compose -f docker-compose.yml
PYTHON := python
PIP := pip
POETRY := poetry

# Installation des dépendances avec Poetry
install:
	@echo "Installing Python dependencies with Poetry..."
	$(POETRY) install --no-interaction --no-ansi

# Construction de l'image Docker
build:
	@echo "Building Docker image..."
	$(DOCKER_COMPOSE) build $(SERVICE_NAME)

# Démarrage des services en arrière-plan
up:
	@echo "Starting services..."
	$(DOCKER_COMPOSE) up -d $(SERVICE_NAME)

# Arrêt des services
down:
	@echo "Stopping services..."
	$(DOCKER_COMPOSE) down

# Affichage des logs en temps réel
logs:
	$(DOCKER_COMPOSE) logs -f $(SERVICE_NAME)

# Exécution des tests
test:
	@echo "Running tests..."
	$(POETRY) run pytest tests/ -v

# Nettoyage des fichiers temporaires
clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".mypy_cache" -exec rm -r {} +
	find . -type f -name "*.py[co]" -delete

# Installation des hooks git
install-hooks:
	@echo "Installing Git hooks..."
	pre-commit install

# Mise à jour des dépendances
update:
	@echo "Updating dependencies..."
	$(POETRY) update

# Lancer un shell dans le conteneur
shell:
	$(DOCKER_COMPOSE) exec $(SERVICE_NAME) /bin/bash

# Vérification de la qualité du code
lint:
	@echo "Running linters..."
	$(POETRY) run black --check src/
	$(POETRY) run isort --check-only src/
	$(POETRY) run mypy src/
	$(POETRY) run ruff check src/

# Formatage du code
format:
	@echo "Formatting code..."
	$(POETRY) run black src/
	$(POETRY) run isort src/

# Aide
default: help
help:
	@echo "\nCommandes disponibles :"
	@echo "  make install      Installer les dépendances avec Poetry"
	@echo "  make build        Construire l'image Docker"
	@echo "  make up           Démarrer les services en arrière-plan"
	@echo "  make down         Arrêter les services"
	@echo "  make logs         Afficher les logs en temps réel"
	@echo "  make test         Exécuter les tests"
	@echo "  make clean        Nettoyer les fichiers temporaires"
	@echo "  make lint         Vérifier la qualité du code"
	@echo "  make format       Formater le code automatiquement"
	@echo "  make update       Mettre à jour les dépendances"
	@echo "  make shell        Lancer un shell dans le conteneur"
	@echo "  make help         Afficher cette aide"
