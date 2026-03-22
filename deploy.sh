#! /bin/bash
# Script de déploiement pour Albert IA Agentic

set -e

echo "🚀 Déploiement d'Albert IA Agentic"

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Vérifications
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Docker est requis${NC}"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo -e "${RED}Docker Compose est requis${NC}"; exit 1; }

# Arguments
ACTION=${1:-start}

case $ACTION in
    start)
        echo -e "${GREEN}▶ Démarrage d'Albert IA Agentic${NC}"
        
        # Vérifier le .env
        if [ ! -f .env ]; then
            echo -e "${YELLOW}⚠️ Fichier .env non trouvé. Création depuis .env.example...${NC}"
            cp .env.example .env
            echo -e "${YELLOW}⚠️ IMPORTANT: Modifiez .env avec votre ALBERT_API_KEY${NC}"
        fi
        
        docker-compose up -d --build
        echo -e "${GREEN}✅ Albert IA Agentic est démarré!${NC}"
        echo -e "   Interface: http://localhost:8090"
        echo -e "   API Docs:  http://localhost:8090/docs"
        ;;
        
    stop)
        echo -e "${YELLOW}■ Arrêt d'Albert IA Agentic${NC}"
        docker-compose down
        echo -e "${GREEN}✅ Arrêté${NC}"
        ;;
        
    restart)
        echo -e "${YELLOW}↻ Redémarrage d'Albert IA Agentic${NC}"
        docker-compose down && docker-compose up -d --build
        echo -e "${GREEN}✅ Redémarré${NC}"
        ;;
        
    logs)
        docker-compose logs -f
        ;;
        
    status)
        docker-compose ps
        ;;
        
    update)
        echo -e "${GREEN}⬆️ Mise à jour d'Albert IA Agentic${NC}"
        git pull
        docker-compose down && docker-compose up -d --build
        echo -e "${GREEN}✅ Mise à jour terminée${NC}"
        ;;
        
    clean)
        echo -e "${RED}⚠️ Nettoyage complet (y compris les données)${NC}"
        read -p "Êtes-vous sûr? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker-compose down -v --rmi local
            echo -e "${GREEN}✅ Nettoyage terminé${NC}"
        fi
        ;;
        
    *)
        echo "Usage: $0 {start|stop|restart|logs|status|update|clean}"
        exit 1
        ;;
esac
