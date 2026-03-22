# ALBERT AGENT - Mémoire de projet

## État actuel du projet

### 🎯 Fonctionnalités implémentées

#### Backend (FastAPI)
- [x] API FastAPI avec authentification token
- [x] Rate limiting (Token Bucket)
- [x] Validation des entrées (Pydantic)
- [x] Sandbox Python sécurisé
- [x] 4 modèles: Ministral 8B, Mistral Small 24B, GPT-OSS 120B, Qwen Coder 30B
- [x] 15 outils dynamiques (hot-reload)
- [x] Support multimodal (images, PDF, DOCX, XLSX, TXT)
- [x] Upload de fichiers avec conversion
- [x] Chat agentique avec boucle d'outils

#### Frontend (HTML/JS)
- [x] Interface moderne (dark theme)
- [x] Sélection de modèle
- [x] Rendu Markdown + KaTeX + highlight.js
- [x] Upload de fichiers avec drag & drop
- [x] Prévisualisation des images
- [x] Barre de progression d'upload
- [x] Suppression individuelle des fichiers

### 📁 Structure des fichiers

```
ALBERT AGENT/
├── albert_api.py              # Backend FastAPI (PRODUCTION)
├── config.py                  # Configuration centralisée
├── validators.py               # Validation entrées
├── rate_limiter.py             # Rate limiting
├── secure_executor.py         # Sandbox Python
├── file_processor.py           # Conversion fichiers (images, PDF, DOCX, XLSX)
├── tool_maker.py               # Tool engine
├── albert_agentic_ui.html     # Interface moderne
├── Dockerfile                  # Container production
├── docker-compose.yml          # Orchestration
├── requirements.txt            # Dépendances Python
├── .env / .env.example        # Configuration
├── deploy.sh / start.sh       # Scripts déploiement
└── tools/                     # Outils dynamiques
```

### 🔧 Technologies utilisées

| Composant | Tech |
|-----------|------|
| Backend | FastAPI + Uvicorn |
| Validation | Pydantic |
| HTTP Client | httpx |
| File Processing | Pillow, PyMuPDF, python-docx, openpyxl |
| Frontend | HTML/CSS/JS vanilla |
| Math Rendering | KaTeX |
| Markdown | marked.js + highlight.js |
| Sanitization | DOMPurify |

### 📋 Configuration (.env)

```env
ALBERT_API_KEY=<clé API Albert>
BOT_ACCESS_TOKEN=<token accès>
PORT=8090
PYTHON_EXEC_TIMEOUT=30
PYTHON_MEMORY_LIMIT=256
RATE_LIMIT_REQUESTS=30
MAX_CHAT_HISTORY=100
```

### 🚀 Démarrage

```bash
# Mode développement
./start.sh

# Mode Docker production
./deploy.sh start
```

### 🐛 Bugs connus / Limitaciones

1. Upload parfois lent (dépend de la taille du fichier)
2. Conversion PDF → images peut être lourde
3. Pas de persistence des fichiers (RAM, TTL ~1h)

### 📌 Prochaines étapes possibles

1. [ ] WebSocket pour streaming temps réel
2. [ ] Persistence Redis pour les fichiers uploadés
3. [ ] Mode streaming SSE pour les réponses
4. [ ] Historique de chat persisté (SQLite)
5. [ ] Interface React/Vue.js
6. [ ] Mode collaboration multi-utilisateurs
7. [ ] Cache des réponses API

---

*Dernière mise à jour: 18 mars 2026*
