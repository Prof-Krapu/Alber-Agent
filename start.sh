#!/bin/bash
# Script de démarrage rapide (sans Docker)

set -e

echo "🚀 Démarrage d'Albert IA Agentic"

# Vérifier Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 est requis"
    exit 1
fi

# Vérifier pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 est requis"
    exit 1
fi

# Créer l'environnement virtuel si nécessaire
if [ ! -d "venv" ]; then
    echo "📦 Création de l'environnement virtuel..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Vérifier le .env
if [ ! -f .env ]; then
    echo "⚠️ Création du fichier .env..."
    cp .env.example .env
    echo "⚠️ IMPORTANT: Modifiez .env avec votre ALBERT_API_KEY!"
fi

# Exporter les variables
export $(cat .env | grep -v '^#' | xargs)

# Lancer le serveur
echo "✅ Lancement du serveur sur http://localhost:${PORT:-8090}"
python3 albert_api.py
