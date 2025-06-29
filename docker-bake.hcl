# docker-bake.hcl - Optimisé pour Buildx

# Variables globales
variable "TAG" {
  default = "latest"
}

# Cible pour l'image finale de l'application
target "app" {
  context = "docker/services/mcp-crawl4ai-rag"
  dockerfile = "docker/services/mcp-crawl4ai-rag/Dockerfile"
  tags = ["mcp-crawl4ai-optimized:${TAG}"]
  
  # Paramètres optimisés
  platforms = ["linux/amd64"]
  cache-to = ["type=inline"]
  
  # Paramètres spécifiques
  args = {
    PYTHONUNBUFFERED = "1"
    PYTHONDONTWRITEBYTECODE = "1"
  }
  
  # Cache des layers
  cache-from = ["type=registry,ref=ghcr.io/oues81/sti-map-generator/mcp-crawl4ai-rag:buildcache"]
}

# Cible par défaut
group "default" {
  targets = ["app"]
}

group "prod" {
  targets = ["app"]
}
