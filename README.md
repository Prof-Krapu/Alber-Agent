# Albert IA Agentic 🤖

Assistant IA agentique nouvelle génération avec sécurité renforcée et architecture moderne.

## Fonctionnalités

- **Sécurité Avancée** : Sandbox Python, rate limiting, validation des entrées
- **Architecture FastAPI** : API moderne async, WebSocket, streaming SSE
- **Multi-Modèles** : Ministral, Mistral Small, GPT-OSS, Qwen Coder
- **Tool-Making** : Création dynamique d'outils Python
- **Rendu LaTeX** : Compilation PDF avec support circuitikz, mhchem, pgfplots
- **Interface Moderne** : Design responsive avec rendu mathématique KaTeX
- **Docker Ready** : Déploiement containerisé en une commande

## Architecture

```
albert-agentic/
├── albert_api.py          # Backend FastAPI (PRODUCTION)
├── albert_api_flask.py    # Backend Flask (LEGACY)
├── albert_agentic_ui.html # Interface moderne
├── config.py              # Configuration centralisée
├── validators.py          # Validation des entrées
├── rate_limiter.py        # Rate limiting
├── secure_executor.py     # Sandbox Python
├── tool_maker.py          # Tool engine
├── Dockerfile             # Container
├── docker-compose.yml      # Orchestration
├── requirements.txt        # Dépendances Python
└── deploy.sh              # Script de déploiement
```

## Installation Rapide

### Option 1: Script de déploiement

```bash
# Cloner le projet
git clone git@forge.apps.education.fr:durieuxvincent/albert-agentic.git
cd albert-agentic

# Lancer
./start.sh
```

### Option 2: Docker (Recommandé pour production)

```bash
# Configuration
cp .env.example .env
# Éditez .env avec votre ALBERT_API_KEY

# Déploiement
./deploy.sh start
```

## Configuration

### Variables d'environnement (.env)

| Variable | Description | Default |
|----------|-------------|---------|
| `ALBERT_API_KEY` | Clé API Albert | **Obligatoire** |
| `BOT_ACCESS_TOKEN` | Token d'accès | `change-me-in-production` |
| `PORT` | Port du serveur | `8090` |
| `PYTHON_EXEC_TIMEOUT` | Timeout exécution Python (s) | `30` |
| `PYTHON_MEMORY_LIMIT` | Limite mémoire Python (Mo) | `256` |
| `RATE_LIMIT_REQUESTS` | Requêtes/minute/IP | `30` |
| `MAX_CHAT_HISTORY` | Messages conservés | `100` |

### Générer un token sécurisé

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## API Endpoints

### REST API

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/status` | Statut du serveur |
| `GET` | `/api/models` | Liste des modèles |
| `GET` | `/api/tools` | Liste des outils |
| `POST` | `/api/chat` | Chat principal |
| `POST` | `/api/chat/stream` | Chat avec streaming SSE |
| `POST` | `/api/history/clear` | Effacer l'historique |
| `GET` | `/api/files` | Liste des fichiers |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| `/ws/chat` | Communication temps réel |

### Documentation API

- Swagger UI: `http://localhost:8090/docs` (si DEBUG=true)
- ReDoc: `http://localhost:8090/redoc` (si DEBUG=true)

## Sécurité

### Mesures implémentées

1. **Sandbox Python** : Limites mémoire/CPU, pas d'accès réseau
2. **Rate Limiting** : Token Bucket par IP (30 req/min)
3. **Validation** : Pydantic schemas + validateurs spécialisés
4. **Path Traversal** : Whitelist du workspace uniquement
5. **Secrets** : Variables d'environnement, jamais en dur
6. **CORS** : Configurable pour la production

### Bonnes pratiques

```bash
# Jamais commiter le .env
echo ".env" >> .gitignore

# Utiliser des tokens sécurisés
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Développement

### Lancer en mode développement

```bash
# Mode debug avec hot-reload
DEBUG=true python3 -m uvicorn albert_api:app --reload --host 0.0.0.0 --port 8090

# Avec logs détaillés
DEBUG=true LOG_LEVEL=debug python3 albert_api.py
```

### Tests

```bash
# Test de l'API
curl -X GET http://localhost:8090/api/status \
  -H "Authorization: Bearer votre_token"

# Test du chat
curl -X POST http://localhost:8090/api/chat \
  -H "Authorization: Bearer votre_token" \
  -H "Content-Type: application/json" \
  -d '{"message": "Bonjour!", "model": "mistralai/Ministral-3-8B-Instruct-2512"}'
```

## Outils Disponibles

| Outil | Description |
|-------|-------------|
| `execute_command` | Exécute des commandes shell (sécurisées) |
| `execute_python` | Exécute du code Python sandboxé |
| `compile_latex` | Compile LaTeX → PDF |
| `write_file` | Écrit dans le workspace |
| `read_file` | Lit depuis le workspace |
| `list_files` | Liste les fichiers |
| `create_skill` | Crée un nouvel outil |
| `fetch_url` | Récupère le contenu d'une URL |

## Gestion des erreurs

| Code | Signification |
|------|---------------|
| `200` | Succès |
| `401` | Token invalide |
| `429` | Rate limit atteint |
| `500` | Erreur serveur |

## Support

- **Issues**: [GitLab Forge](https://forge.apps.education.fr/durieuxvincent/albert-agentic/-/issues)
- **Documentation API**: `/docs` une fois le serveur démarré

---

Développé avec ❤️ pour l'Éducation Nationale.
