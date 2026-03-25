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
├── albert_agentic_ui.html # Interface moderne
├── config.py              # Configuration centralisée
├── validators.py          # Validation des entrées
├── rate_limiter.py        # Rate limiting (Token Bucket)
├── secure_executor.py     # Sandbox Python
├── tool_maker.py          # Tool engine dynamique
├── file_processor.py      # Traitement avancé des fichiers
├── tools/                 # Outils dynamiques (skills)
├── skills/                # Compétences étendues
├── tests/                 # Tests unitaires & intégration
├── Dockerfile             # Container (Déploiement)
├── docker-compose.yml     # Orchestration
├── requirements.txt       # Dépendances Python
├── start.sh               # Script de démarrage rapide
└── deploy.sh              # Script de déploiement
```

## Installation

### Prérequis

- Python 3.11+
- pip
- (Optionnel) Docker & Docker Compose

### Option 1 : Installation locale

```bash
# Cloner le projet
git clone git@forge.apps.education.fr:durieuxvincent/albert-agentic.git
cd albert-agentic

# Créer la configuration
cp .env.example .env
```

> ⚠️ **IMPORTANT** : Éditez le fichier `.env` avec vos propres clés AVANT de démarrer :
> ```bash
> # Générer un token d'accès sécurisé
> python3 -c "import secrets; print(secrets.token_urlsafe(32))"
> 
> # Éditer le .env
> nano .env
> ```

```bash
# Lancer le serveur
./start.sh
```

### Option 2 : Docker (Recommandé pour production)

```bash
cp .env.example .env
# Éditez .env avec votre ALBERT_API_KEY et BOT_ACCESS_TOKEN
./deploy.sh start
```

## Configuration

### Variables d'environnement (.env)

> ⚠️ Le fichier `.env` ne doit **JAMAIS** être commité dans le dépôt Git. Il est déjà dans le `.gitignore`.

| Variable | Description | Default |
|----------|-------------|---------|
| `ALBERT_API_KEY` | Clé API Albert (etalab.gouv.fr) | **Obligatoire** |
| `BOT_ACCESS_TOKEN` | Token d'accès à l'API | **À générer** |
| `PORT` | Port du serveur | `8090` |
| `PYTHON_EXEC_TIMEOUT` | Timeout exécution Python (s) | `30` |
| `PYTHON_MEMORY_LIMIT` | Limite mémoire Python (Mo) | `256` |
| `RATE_LIMIT_REQUESTS` | Requêtes/minute/IP | `30` |
| `MAX_CHAT_HISTORY` | Messages conservés | `100` |
| `ALLOWED_ORIGINS` | Origines CORS autorisées | `*` |

## Sécurité

### 🔐 Gestion des Clés

1. **Ne JAMAIS** commiter le fichier `.env`
2. **Toujours** utiliser des tokens générés aléatoirement :
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
3. En cas de fuite d'une clé API, la révoquer **immédiatement** sur [Albert API](https://albert.api.etalab.gouv.fr)

### Mesures de sécurité implémentées

| Mesure | Description |
|--------|-------------|
| Sandbox Python | Limites mémoire/CPU, pas d'accès réseau |
| Rate Limiting | Token Bucket par IP (30 req/min) |
| Validation | Pydantic schemas + validateurs spécialisés |
| Path Traversal | Whitelist du workspace uniquement |
| CORS | Configurable via `ALLOWED_ORIGINS` |
| Authentification | Bearer token obligatoire |

## API Endpoints

### REST API

| Méthode | Endpoint | Auth | Description |
|---------|----------|------|-------------|
| `GET` | `/api/status` | ❌ | Statut du serveur |
| `GET` | `/api/models` | ✅ | Liste des modèles |
| `GET` | `/api/tools` | ✅ | Liste des outils |
| `POST` | `/api/chat` | ✅ | Chat principal (agentique) |
| `POST` | `/api/upload` | ✅ | Upload fichiers (images, PDF, DOCX) |
| `POST` | `/api/history/clear` | ✅ | Effacer l'historique |
| `GET` | `/api/files` | ✅ | Liste des fichiers workspace |

### Documentation API

- Swagger UI: `http://localhost:8090/docs` (si `DEBUG=true`)
- ReDoc: `http://localhost:8090/redoc` (si `DEBUG=true`)

## Développement

### Lancer en mode développement

```bash
# Mode debug avec hot-reload
DEBUG=true python3 -m uvicorn albert_api:app --reload --host 0.0.0.0 --port 8090
```

### Lancer les tests

```bash
# Installer les dépendances de test
pip install -r requirements-dev.txt

# Lancer tous les tests
python3 -m pytest tests/ -v
```

### Outils Disponibles

| Outil | Description |
|-------|-------------|
| `execute_command` | Commandes shell sécurisées |
| `execute_python` | Code Python sandboxé |
| `compile_latex` | LaTeX → PDF |
| `write_file` / `read_file` | Lecture/écriture workspace |
| `list_files` | Liste des fichiers |
| `create_skill` | Crée un nouvel outil dynamique |
| `fetch_url` | Récupère le contenu d'une URL |

## Support

- **Issues**: [GitLab Forge](https://forge.apps.education.fr/durieuxvincent/albert-agentic/-/issues)
- **Documentation API**: `/docs` une fois le serveur démarré

---

Développé avec ❤️ pour l'Éducation Nationale.
