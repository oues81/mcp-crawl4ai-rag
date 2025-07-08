"""
Module de configuration de l'application MCP Crawl4AI RAG.

Ce module charge et valide les variables d'environnement nécessaires au bon fonctionnement
du service. Il fournit également des valeurs par défaut pour les configurations optionnelles.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, BaseSettings, Field, HttpUrl, PostgresDsn, validator

# Configuration du logger
logger = logging.getLogger(__name__)

# Répertoire de base du projet
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Classe de configuration principale utilisant pydantic pour la validation."""

    # Configuration de l'application
    APP_NAME: str = "MCP Crawl4AI RAG"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    ENVIRONMENT: str = Field(default="production", env="ENV")
    SECRET_KEY: str = Field(
        default="change-this-in-production",
        description="Clé secrète utilisée pour le chiffrement et la génération de jetons.",
    )
    
    # Configuration du serveur
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8002, env="PORT")
    WORKERS: int = Field(
        default=1,
        description="Nombre de workers Uvicorn. En développement, utilisez 1 pour éviter les problèmes de concurrence.",
    )
    
    # Configuration CORS
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Configuration des logs
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[Path] = BASE_DIR / "logs" / "mcp_crawl4ai_rag.log"
    
    # Configuration de la base de données
    DATABASE_URL: Optional[PostgresDsn] = Field(
        default=None,
        env="DATABASE_URL",
        description="URL de connexion à la base de données PostgreSQL.",
    )
    
    # Configuration Supabase
    SUPABASE_URL: HttpUrl = Field(
        ...,  # Requis
        env="SUPABASE_URL",
        description="URL de votre instance Supabase.",
    )
    SUPABASE_SERVICE_ROLE_KEY: str = Field(
        ...,  # Requis
        env="SUPABASE_SERVICE_ROLE_KEY",
        description="Clé de service (secret) de votre instance Supabase.",
    )
    
    # Configuration OpenAI
    OPENAI_API_KEY: str = Field(
        ...,  # Requis
        env="OPENAI_API_KEY",
        description="Clé API pour accéder aux services d'OpenAI.",
    )
    OPENAI_MODEL: str = Field(
        default="gpt-4-turbo-preview",
        env="OPENAI_MODEL",
        description="Modèle OpenAI à utiliser pour la génération de texte.",
    )
    
    # Configuration du cache
    CACHE_DIR: Path = Field(
        default=BASE_DIR / ".cache",
        description="Répertoire de cache pour les modèles et les données temporaires.",
    )
    
    # Configuration du crawling
    CRAWL_TIMEOUT: int = Field(
        default=30,
        description="Délai d'expiration (en secondes) pour les requêtes de crawling.",
    )
    MAX_CRAWL_DEPTH: int = Field(
        default=2,
        description="Profondeur maximale de crawling pour les sites web.",
    )
    
    # Configuration RAG
    RAG_TOP_K: int = Field(
        default=5,
        description="Nombre de résultats à retourner pour les requêtes RAG.",
    )
    
    class Config:
        """Configuration Pydantic supplémentaire."""
        
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        
        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            """Ordonne les sources de configuration par priorité."""
            return (
                init_settings,
                env_settings,
                file_secret_settings,
            )
    
    def setup_logging(self) -> None:
        """Configure le système de journalisation."""
        import logging.config
        import sys
        
        # Créer le répertoire de logs s'il n'existe pas
        if self.LOG_FILE:
            self.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Configuration du logging
        logging_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": self.LOG_FORMAT,
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
            },
            "handlers": {
                "console": {
                    "level": self.LOG_LEVEL,
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                    "stream": sys.stdout,
                },
            },
            "loggers": {
                "": {  # root logger
                    "handlers": ["console"],
                    "level": self.LOG_LEVEL,
                    "propagate": True,
                },
                "mcp_crawl4ai_rag": {
                    "handlers": ["console"],
                    "level": self.LOG_LEVEL,
                    "propagate": False,
                },
                "uvicorn": {
                    "handlers": ["console"],
                    "level": self.LOG_LEVEL,
                    "propagate": False,
                },
                "fastapi": {
                    "handlers": ["console"],
                    "level": self.LOG_LEVEL,
                    "propagate": False,
                },
            },
        }
        
        # Ajouter le handler de fichier si spécifié
        if self.LOG_FILE:
            logging_config["handlers"]["file"] = {
                "level": self.LOG_LEVEL,
                "class": "logging.FileHandler",
                "filename": str(self.LOG_FILE),
                "formatter": "standard",
                "encoding": "utf-8",
            }
            
            # Ajouter le handler de fichier aux loggers
            for logger_name in ["", "mcp_crawl4ai_rag", "uvicorn", "fastapi"]:
                logging_config["loggers"][logger_name]["handlers"].append("file")
        
        # Appliquer la configuration
        logging.config.dictConfig(logging_config)
        
        # Désactiver les logs trop verbeux
        if not self.DEBUG:
            logging.getLogger("httpx").setLevel(logging.WARNING)
            logging.getLogger("httpcore").setLevel(logging.WARNING)
            logging.getLogger("urllib3").setLevel(logging.WARNING)
            logging.getLogger("asyncio").setLevel(logging.WARNING)


# Créer une instance des paramètres
settings = Settings()

# Configurer le logging au chargement du module
settings.setup_logging()

# Afficher un message de démarrage
logger.info(f"Configuration chargée pour l'environnement: {settings.ENVIRONMENT}")

# Vérifier les variables requises
if not all([settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY, settings.OPENAI_API_KEY]):
    logger.warning(
        "Certaines variables d'environnement requises sont manquantes. "
        "Assurez-vous de configurer correctement les variables d'environnement."
    )
