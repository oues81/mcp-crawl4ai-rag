"""
Configuration centralisée de la journalisation pour l'application.
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Configure la journalisation de l'application.
    
    Args:
        log_level: Niveau de journalisation (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Chemin vers le fichier de log (optionnel)
    """
    # Créer le formateur de log
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(log_format)
    
    # Configurer le niveau de log
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Niveau de log invalide: {log_level}")
    
    # Configurer le gestionnaire de console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Configuration des handlers
    handlers = [console_handler]
    
    # Configurer le fichier de log si spécifié
    if log_file:
        # Créer le répertoire des logs si nécessaire
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        # Configurer la rotation des logs (10 Mo par fichier, 5 fichiers de backup)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # Configurer le logger racine
    logging.basicConfig(
        level=numeric_level,
        handlers=handlers
    )
    
    # Désactiver les logs trop verbeux pour certaines bibliothèques
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    # Logger de test
    logger = logging.getLogger(__name__)
    logger.info("Journalisation configurée avec succès (niveau: %s)", log_level)
    if log_file:
        logger.info("Les journaux sont enregistrés dans: %s", log_file)
