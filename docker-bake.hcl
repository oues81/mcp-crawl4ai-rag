# docker-bake.hcl
# Configuration optimisée pour la construction avec Docker Buildx

# Variables globales
variable "TAG" {
  default = "latest"
}

# Configuration commune pour toutes les cibles
target "common" {
  platforms = ["linux/amd64"]
  args = {
    BUILDKIT_INLINE_CACHE = "1"
  }
  # Optimisation du cache
  cache-from = ["type=registry,ref=registry-1.docker.io/yournamespace/mcp-crawl4ai:cache"]
  cache-to = ["type=inline"]
  # Optimisation des couches
  output = ["type=docker"]
  # Compression
  attrs = {
    "build-arg:BUILDKIT_INLINE_CACHE" = "1"
  }
}

# Cible pour l'image finale de l'application
target "app" {
  inherits = ["common"]
  context = "."
  dockerfile = "Dockerfile"
  target = "app"
  tags = ["mcp-crawl4ai:${TAG}"]
  
  # Paramètres spécifiques
  args = {
    PYTHONUNBUFFERED = "1"
    PYTHONDONTWRITEBYTECODE = "1"
    PYTHONFAULTHANDLER = "1"
  }
  
  # Labels pour l'image
  labels = {
    "org.opencontainers.image.title" = "MCP Crawl4AI RAG"
    "org.opencontainers.image.description" = "Service MCP pour le crawling et RAG"
    "org.opencontainers.image.version" = "${TAG}"
  }
  # Dépend du builder
  contexts = {
    base = "target:base",
    builder = "target:builder"
  }
}

# Groupe par défaut (construit toutes les images)
group "default" {
  targets = ["base", "builder", "app"]
}

# Groupe pour construire uniquement l'application (plus rapide)
group "app-only" {
  targets = ["app"]
}

# Groupe pour forcer la reconstruction complète
group "clean" {
  targets = ["base", "builder", "app"]
  args = {
    BUILDKIT_INLINE_CACHE = "0"
  }
}
