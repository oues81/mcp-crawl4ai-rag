"""
Point d'entrée principal du service MCP Crawl4AI RAG

Ce fichier est l'entrée principale pour le service MCP Crawl4AI RAG.
Il démarre le serveur FastMCP directement.
"""

import os
import sys
import asyncio
from crawl4ai_mcp import mcp, main as mcp_main

# Configuration du port depuis les variables d'environnement
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8051"))

# Point d'entrée principal
if __name__ == "__main__":
    # Afficher les informations de démarrage
    print(f"\n{'='*80}")
    print(f"{' MCP CRAWL4AI RAG SERVICE ':=^80}")
    print(f"{'='*80}")
    print(f"Host:           {HOST}")
    print(f"Port:           {PORT}")
    print(f"Environment:    {os.getenv('ENVIRONMENT', 'development')}")
    print(f"Python:         {sys.version.split()[0]}")
    print(f"Working dir:    {os.getcwd()}")
    print(f"Python path:    {os.getenv('PYTHONPATH', 'Not set')}")
    print(f"Virtual env:    {os.getenv('VIRTUAL_ENV', 'Not in a virtual environment')}")
    print(f"Installed packages:")
    
    # Afficher les packages installés (version courte)
    try:
        import pkg_resources
        installed_packages = [f"{pkg.key}=={pkg.version}" for pkg in pkg_resources.working_set]
        installed_packages.sort()
        print("  " + "\n  ".join(installed_packages))
    except Exception as e:
        print(f"  Could not list installed packages: {e}")
    
    print(f"{'='*80}\n")
    
    # Démarrer le serveur FastMCP
    asyncio.run(mcp_main())
