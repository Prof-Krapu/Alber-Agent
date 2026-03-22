---
name: cli-browser-navigation
description: Navigation internet économe en tokens en CLI utilisant Agent Browser de Vercel. Use when: user needs to browse the web, search information, or extract content from websites with minimal token usage and maximum efficiency via command-line interface. NOT for: GUI browser automation, heavy JavaScript websites requiring full browser rendering, or complex interactive web applications.
---

# CLI Browser Navigation - Navigation internet économe en tokens

Ce skill permet la navigation internet via ligne de commande en utilisant l'Agent Browser de Vercel, optimisé pour une utilisation minimale de tokens et une efficacité maximale.

## 🎯 Pourquoi ce skill ?

### Problèmes des approches traditionnelles :
- **Navigateurs GUI** : Consommation élevée de tokens pour le rendu
- **Web scraping classique** : Complexe, fragile, nécessite beaucoup de code
- **APIs REST** : Limitées, souvent payantes, pas toujours disponibles

### Solutions offertes par ce skill :
- ✅ **Économie de tokens** : Interface CLI légère
- ✅ **Extraction précise** : Ciblage du contenu pertinent
- ✅ **Navigation intelligente** : Recherche et exploration efficaces
- ✅ **Intégration facile** : Installation simple, utilisation rapide

## 📦 Installation

### 1. Prérequis
```bash
# Vérifier Node.js et npm
node --version  # >= 18.0.0
npm --version   # >= 9.0.0

# Vérifier Git
git --version
```

### 2. Installation de l'Agent Browser
```bash
# Cloner le dépôt
git clone https://github.com/vercel-labs/agent-browser.git
cd agent-browser

# Installer les dépendances
npm install

# Construire le projet
npm run build

# Installer globalement (optionnel)
npm install -g .
```

### 3. Configuration
```bash
# Créer un fichier de configuration
cat > ~/.agent-browser-config.json << EOF
{
  "headless": true,
  "timeout": 30000,
  "maxTokens": 1000,
  "extractMode": "relevant",
  "cacheEnabled": true,
  "cacheTTL": 3600
}
EOF
```

## 🚀 Utilisation de base

### 1. Recherche web
```bash
# Recherche simple
agent-browser search "physique quantique principes fondamentaux"

# Recherche avec options
agent-browser search "loi de Faraday" --limit 5 --format markdown

# Recherche avancée
agent-browser search "site:wikipedia.org équation de Schrödinger" --extract math
```

### 2. Extraction de contenu
```bash
# Extraire le contenu principal
agent-browser extract https://fr.wikipedia.org/wiki/Physique_quantique

# Extraire des sections spécifiques
agent-browser extract https://example.com --sections "introduction,methodologie,conclusion"

# Extraire avec filtrage
agent-browser extract https://news.com --filter "date>2024-01-01 category=science"
```

### 3. Navigation interactive
```bash
# Mode interactif
agent-browser interactive

# Commandes en mode interactif :
#   search <query>      - Recherche web
#   extract <url>       - Extraire contenu
#   follow <selector>   - Suivre un lien
#   back               - Retour en arrière
#   history            - Voir l'historique
#   save <filename>    - Sauvegarder le contenu
#   exit               - Quitter
```

## 🔧 Commandes avancées

### Recherche ciblée
```bash
# Recherche académique
agent-browser search "machine learning applications chemistry" \
  --sources "arxiv.org,researchgate.net,pubmed.ncbi.nlm.nih.gov" \
  --years "2020-2024" \
  --format bibtex

# Recherche technique
agent-browser search "python async web scraping" \
  --tags "tutorial,code,examples" \
  --language python \
  --codeblocks
```

### Extraction optimisée
```bash
# Extraire seulement le texte pertinent
agent-browser extract https://tutorial.com \
  --strategy "content-focused" \
  --remove "ads,comments,navigation" \
  --compress

# Extraire des données structurées
agent-browser extract https://dataset.org \
  --output json \
  --schema "title,description,url,date,authors" \
  --validate
```

### Batch processing
```bash
# Traiter plusieurs URLs
cat urls.txt | xargs -I {} agent-browser extract {} --output markdown

# Recherche en parallèle
parallel -j 4 'agent-browser search "{}" --limit 3' ::: "topic1" "topic2" "topic3" "topic4"
```

## 🎯 Stratégies d'économie de tokens

### 1. Filtrage intelligent
```bash
# Avant (coûteux)
agent-browser extract https://page.com

# Après (économique)
agent-browser extract https://page.com \
  --select "article.main-content" \
  --exclude "sidebar,footer,comments" \
  --truncate 2000
```

### 2. Extraction ciblée
```bash
# Extraire seulement ce qui est nécessaire
agent-browser extract https://paper.edu \
  --target "abstract,methods,results,conclusion" \
  --max-sentences 50 \
  --min-relevance 0.7
```

### 3. Cache et réutilisation
```bash
# Utiliser le cache
agent-browser search "quantum physics" --cache

# Forcer la mise à jour
agent-browser search "latest news" --no-cache

# Gérer le cache
agent-browser cache --list
agent-browser cache --clear
agent-browser cache --stats
```

## 📊 Monitoring et optimisation

### Vérifier l'utilisation
```bash
# Statistiques d'utilisation
agent-browser stats --tokens --time --requests

# Profiler une session
agent-browser profile "search 'AI research' --limit 10"

# Optimiser les paramètres
agent-browser optimize --config ~/.agent-browser-config.json
```

### Journalisation
```bash
# Activer les logs détaillés
export AGENT_BROWSER_LOG_LEVEL=debug

# Journaliser dans un fichier
agent-browser search "topic" --log-file search.log

# Analyser les logs
agent-browser analyze-logs search.log --report
```

## 🔗 Intégration avec d'autres outils

### Avec curl et jq
```bash
# API-like usage
agent-browser search "query" --output json | jq '.results[].title'

# Pipeline processing
agent-browser extract $URL --output text | grep -i "keyword" | head -5
```

### Avec Python
```python
import subprocess
import json

def agent_browser_search(query, limit=5):
    cmd = ["agent-browser", "search", query, "--limit", str(limit), "--output", "json"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)

# Utilisation
results = agent_browser_search("quantum computing", limit=3)
for item in results:
    print(f"Title: {item['title']}")
    print(f"URL: {item['url']}")
    print(f"Snippet: {item['snippet'][:100]}...")
```

### Avec OpenClaw
```bash
# Dans un script OpenClaw
#!/bin/bash
QUERY="$1"
RESULTS=$(agent-browser search "$QUERY" --limit 3 --format brief)

echo "Résultats pour: $QUERY"
echo "$RESULTS"
```

## 🛠️ Dépannage

### Problèmes courants

#### 1. Installation échouée
```bash
# Vérifier les permissions
sudo chown -R $USER:$USER /usr/local/lib/node_modules

# Réinstaller
npm uninstall -g agent-browser
npm cache clean --force
npm install -g .
```

#### 2. Erreurs de réseau
```bash
# Vérifier la connectivité
agent-browser check-connection

# Configurer le proxy
export HTTP_PROXY="http://proxy:port"
export HTTPS_PROXY="http://proxy:port"

# Désactiver SSL verification (développement seulement)
export NODE_TLS_REJECT_UNAUTHORIZED=0
```

#### 3. Performances lentes
```bash
# Optimiser les paramètres
agent-browser config --set timeout=15000
agent-browser config --set headless=true
agent-browser config --set concurrent=2

# Nettoyer le cache
agent-browser cache --clear
```

## 📚 Exemples pratiques

### Recherche académique
```bash
# Recherche de publications
agent-browser search "\"deep learning\" chemistry" \
  --sources "pubs.acs.org,rsc.org,springer.com" \
  --years "2023-2024" \
  --type "article" \
  --output bibtex > references.bib

# Extraire les abstracts
for url in $(cat paper_urls.txt); do
  agent-browser extract "$url" \
    --target abstract \
    --output text \
    >> abstracts.txt
done
```

### Surveillance de contenu
```bash
# Surveiller les mises à jour
agent-browser monitor https://blog.example.com/feed \
  --interval 3600 \
  --diff \
  --notify

# Comparer les versions
agent-browser diff https://page.com/v1 https://page.com/v2 \
  --output html > changes.html
```

### Extraction de données
```bash
# Scraper un tableau
agent-browser extract https://data.gov/dataset \
  --table "main" \
  --output csv > data.csv

# Extraire des images
agent-browser extract https://gallery.com \
  --media images \
  --download-dir ./images \
  --limit 20
```

## 🎯 Bonnes pratiques

### 1. Toujours spécifier des limites
```bash
# ❌ Mauvais (peut extraire trop)
agent-browser extract https://long-article.com

# ✅ Bon (contrôlé)
agent-browser extract https://long-article.com \
  --max-chars 5000 \
  --max-elements 20
```

### 2. Utiliser le format approprié
```bash
# Pour l'analyse
agent-browser search "topic" --output json

# Pour la lecture
agent-browser extract $URL --output markdown

# Pour le traitement
agent-browser extract $URL --output text
```

### 3. Profiter du cache
```bash
# Recherches répétées
agent-browser search "daily news" --cache --ttl 3600

# Contenu stable
agent-browser extract https://reference.com --cache --ttl 86400
```

### 4. Valider les résultats
```bash
# Vérifier la qualité
agent-browser validate https://page.com \
  --min-length 100 \
  --required-tags "h1,p" \
  --language fr

# Filtrer le bruit
agent-browser filter results.json \
  --min-relevance 0.6 \
  --max-age 30 \
  --source-reputation high
```

## 🔮 Évolution future

### Améliorations prévues
1. **Support multi-langues** amélioré
2. **Extraction d'images et PDF**
3. **API REST complète**
4. **Plugins pour navigateurs**
5. **Intégration LLM native**

### Roadmap
- **Q1 2024** : Support Markdown avancé
- **Q2 2024** : Extraction de données structurées
- **Q3 2024** : API GraphQL
- **Q4 2024** : Interface web

## 📞 Support

### Documentation
- [GitHub Repository](https://github.com/vercel-labs/agent-browser)
- [API Documentation](https://agent-browser-docs.vercel.app)
- [Examples Gallery](https://agent-browser-examples.vercel.app)

### Communauté
- [Discussions GitHub](https://github.com/vercel-labs/agent-browser/discussions)
- [Twitter @AgentBrowser](https://twitter.com/AgentBrowser)
- [Discord Community](https://discord.gg/agent-browser)

### Rapporter des bugs
```bash
# Générer un rapport de bug
agent-browser bug-report --include-logs --include-config

# Ou via GitHub
gh issue create --repo vercel-labs/agent-browser --title "Bug report"
```

---

**Note** : Ce skill est optimisé pour OpenClaw et les assistants IA. Il minimise l'utilisation de tokens tout en maximisant l'efficacité de la navigation web via CLI.