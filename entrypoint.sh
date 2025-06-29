#!/bin/sh
# entrypoint.sh

# Ce script sert de point d'entrée pour le conteneur.
# Il exécute la commande passée en argument (le CMD du Dockerfile).
# Cela permet d'ajouter des logiques d'initialisation ici si nécessaire à l'avenir.

set -e

# Exécute la commande passée en argument (par exemple, uvicorn...)
# Exécute la commande passée en argument (le CMD du Dockerfile) en utilisant le contexte de Poetry
exec poetry run "$@"
