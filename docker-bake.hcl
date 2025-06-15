# docker-bake.hcl
# Configuration pour la construction des images avec Docker Buildx

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
  # Utilisation du cache local
  cache-to = ["type=local,dest=/tmp/docker-cache-new,mode=max"]
  cache-from = ["type=local,src=/tmp/docker-cache"]
}

# Cible pour l'image de base avec CUDA
target "base" {
  inherits = ["common"]
  context = "."
  dockerfile = "Dockerfile"
  target = "base"
  tags = ["sti-mcp-crawl4ai-base:${TAG}"]
  # Forcer la reconstruction si nécessaire
  no-cache-filter = ["base"]
}

# Cible pour l'image de builder
target "builder" {
  inherits = ["common"]
  context = "."
  dockerfile = "Dockerfile"
  target = "builder"
  tags = ["sti-mcp-crawl4ai-builder:${TAG}"]
  # Dépend de la base
  contexts = {
    base = "target:base"
  }
}

# Cible pour l'image finale de l'application
target "app" {
  inherits = ["common"]
  context = "."
  dockerfile = "Dockerfile"
  target = "app"
  tags = ["sti-mcp-crawl4ai:${TAG}"]
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
