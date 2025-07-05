"""
Serveur de santé HTTP simple pour le service MCP Crawl4AI RAG.
"""
import http.server
import json
import logging
import os
import socket
import threading
from http import HTTPStatus

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,  # Niveau en majuscules
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/app/logs/health_server.log')
    ]
)
logger = logging.getLogger(__name__)

class HealthCheckHandler(http.server.BaseHTTPRequestHandler):
    """Gestionnaire de requêtes pour le point de terminaison de santé."""
    
    def do_GET(self):
        """Gère les requêtes GET sur le point de terminaison de santé."""
        if self.path == '/health' or self.path == '/health/':
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {
                'status': 'ok',
                'service': 'mcp-crawl4ai-rag',
                'version': os.getenv('APP_VERSION', '0.1.0')
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_response(HTTPStatus.NOT_FOUND)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Not Found'}).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Désactive la journalisation des requêtes HTTP par défaut."""
        return

def run_health_server(port=8052, host='0.0.0.0'):
    """Démarre le serveur de santé HTTP."""
    server_address = (host, port)
    httpd = http.server.HTTPServer(server_address, HealthCheckHandler)
    
    # Configurer le socket pour la réutilisation d'adresse
    httpd.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    logger.info(f"Serveur de santé démarré sur http://{host}:{port}")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Arrêt du serveur de santé...")
    finally:
        httpd.server_close()
        logger.info("Serveur de santé arrêté")

if __name__ == "__main__":
    # Port par défaut 8052, peut être remplacé par la variable d'environnement HEALTH_PORT
    port = int(os.getenv('HEALTH_PORT', '8052'))
    run_health_server(port=port)
