# Serveur MCP Crawl4AI RAG

<p align="center">
  <em>Serveur MCP optimisé pour le crawling web et le RAG (Retrieval-Augmented Generation) fonctionnant sur CPU</em>
</p>

## 📋 Vue d'ensemble

Ce service implémente le [Model Context Protocol (MCP)](https://modelcontextprotocol.io) en utilisant [Crawl4AI](https://crawl4ai.com) et [Supabase](https://supabase.com/) pour fournir des capacités avancées de crawling web et de RAG. Il est spécialement optimisé pour fonctionner sur des environnements CPU.

## 🚀 Fonctionnalités

- **Crawling Web Avancé** : Extraction intelligente de contenu à partir de n'importe quelle URL
- **Recherche Sémantique** : Intégration avec Supabase pour la recherche vectorielle
- **Support Multi-Langue** : Prise en charge de plusieurs langues pour le traitement du texte
- **Optimisation CPU** : Conçu pour fonctionner efficacement sans GPU
- **Intégration MCP** : Compatible avec le protocole MCP pour une intégration transparente avec d'autres services
- **Gestion des Dépendances** : Utilisation de Poetry pour une gestion propre des dépendances Python
- **Conteneur Docker** : Configuration optimisée pour le déploiement en conteneur

## MCP Crawl4AI RAG Service

Ce service implémente un serveur MCP (Model Context Protocol) pour le web crawling et le RAG (Retrieval-Augmented Generation) en utilisant la bibliothèque Crawl4AI.

## Fonctionnalités

- **Crawling web** avec détection automatique du type d'URL (sitemap, fichier texte, page web)
- **RAG (Recherche Augmentée par Génération)** pour la recherche de documents
- Intégration avec **Supabase** pour le stockage vectoriel
- Support de plusieurs stratégies RAG avancées
- Intégration avec **Neo4j** pour le graphe de connaissances (optionnel)
- Détection d'hallucinations des IA
- Extraction et recherche d'exemples de code

## Prérequis

- **Python 3.12** (version recommandée)
- **Poetry** (pour la gestion des dépendances)
- **Docker** et **Docker Compose** (pour le déploiement en conteneur)
- **Compte Supabase** (pour le stockage vectoriel)
- **Clé API OpenAI** (pour les embeddings et fonctionnalités LLM)
- (Optionnel) Instance Neo4j pour les fonctionnalités de graphe de connaissances

## Démarrage Rapide

1. **Cloner le dépôt**
   ```bash
   git clone [URL_DU_REPO]
   cd docker/services/mcp-crawl4ai-rag
   ```

2. **Configurer les variables d'environnement**
   Créez un fichier `.env` à la racine du projet avec les variables requises :
   ```env
   # Configuration de base
   PORT=8002
   PYTHONPATH=/app
   
   # Configuration Supabase
   SUPABASE_URL=votre_url_supabase
   SUPABASE_SERVICE_KEY=votre_cle_service_supabase
   
   # Configuration OpenAI
   OPENAI_API_KEY=votre_cle_api_openai
   
   # Configuration du modèle
   MODEL_CHOICE=gpt-4
   
   # Fonctionnalités optionnelles
   USE_CONTEXTUAL_EMBEDDINGS=false
   USE_HYBRID_SEARCH=false
   USE_AGENTIC_RAG=false
   USE_RERANKING=false
   USE_KNOWLEDGE_GRAPH=false
   ```

3. **Construire et démarrer les services**
   ```bash
   docker-compose up --build -d
   ```

4. **Vérifier que le service est opérationnel**
   ```bash
   curl http://localhost:8002/health
   ```

## 🛠 Configuration

### Variables d'environnement

| Variable | Description | Valeur par défaut |
|----------|-------------|-------------------|
| `PORT` | Port sur lequel le service écoute | `8002` |
| `SUPABASE_URL` | URL de votre instance Supabase | - |
| `SUPABASE_SERVICE_KEY` | Clé de service Supabase | - |
| `OPENAI_API_KEY` | Clé API OpenAI | - |
| `MODEL_CHOICE` | Modèle à utiliser pour les embeddings | `gpt-4` |
| `CRAWL4_AI_BASE_DIRECTORY` | Répertoire de base pour le stockage | `/data` |

### Stratégies RAG (optionnelles)

Le service prend en charge plusieurs stratégies RAG avancées qui peuvent être activées via des variables d'environnement :

1. **Contextual Embeddings**
   ```env
   USE_CONTEXTUAL_EMBEDDINGS=true
   ```
   Améliore les embeddings en ajoutant un contexte supplémentaire.

2. **Recherche Hybride**
   ```env
   USE_HYBRID_SEARCH=true
   ```
   Combine la recherche vectorielle et par mots-clés pour de meilleurs résultats.

3. **RAG Agentique**
   ```env
   USE_AGENTIC_RAG=true
   ```
   Active les capacités RAG avancées pour les extraits de code.

## 🐛 Dépannage

### Problèmes courants

1. **Erreurs de connexion à Supabase**
   - Vérifiez que `SUPABASE_URL` et `SUPABASE_SERVICE_KEY` sont correctement définis
   - Assurez-vous que votre instance Supabase est en cours d'exécution et accessible

2. **Problèmes d'installation des dépendances**
   - Supprimez le répertoire `.venv` et le fichier `poetry.lock` puis réinstallez les dépendances
   - Vérifiez que vous utilisez Python 3.12

3. **Erreurs de démarrage**
   - Consultez les logs avec `docker-compose logs -f`
   - Vérifiez que le port 8002 n'est pas déjà utilisé

## 📜 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 🙋‍♂️ Support

Pour toute question ou problème, veuillez ouvrir une [issue](https://github.com/votre-org/sti-map-generator/issues).
