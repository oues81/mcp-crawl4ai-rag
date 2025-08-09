# docker-bake.hcl - Optimisé pour Buildx

# Variables globales
variable "TAG" {
  default = "latest"
}

# Cible pour l'image finale de l'application
target "app" {
  context = "./docker/services/mcp-crawl4ai-rag"
  dockerfile = "Dockerfile"
  tags = ["mcp-crawl4ai-optimized:${TAG}"]
  
  # Paramètres optimisés
  platforms = ["linux/amd64"]
  cache-to = ["type=inline"]
  
  # Paramètres spécifiques
  args = {
    PYTHONUNBUFFERED = "1"
    PYTHONDONTWRITEBYTECODE = "1"
  }
  
  # Cache des layers (local only en dev)
  # cache-from = ["type=local,src=.buildx-cache"]
  # cache-to   = ["type=local,dest=.buildx-cache,mode=max"]
}

# Cible par défaut
group "default" {
  targets = ["app"]
}

group "prod" {
  targets = ["app"]
}
