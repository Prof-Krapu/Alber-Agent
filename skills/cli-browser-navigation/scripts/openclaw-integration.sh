#!/bin/bash
# Intégration d'Agent Browser avec OpenClaw
# Permet une navigation web économe en tokens depuis OpenClaw

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$HOME/.openclaw/agent-browser.json"

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérifier si agent-browser est installé
check_agent_browser() {
    if command -v agent-browser &> /dev/null; then
        AGENT_BROWSER_CMD="agent-browser"
        return 0
    elif [ -f "$HOME/agent-browser/bin/agent-browser.js" ]; then
        AGENT_BROWSER_CMD="node $HOME/agent-browser/bin/agent-browser.js"
        return 0
    else
        log_error "Agent Browser n'est pas installé"
        log_info "Pour installer: $SKILL_DIR/scripts/install-agent-browser.sh"
        return 1
    fi
}

# Charger la configuration
load_config() {
    if [ -f "$CONFIG_FILE" ]; then
        log_info "Chargement de la configuration: $CONFIG_FILE"
        MAX_TOKENS=$(jq -r '.max_tokens // 1000' "$CONFIG_FILE")
        TIMEOUT=$(jq -r '.timeout // 30000' "$CONFIG_FILE")
        OUTPUT_FORMAT=$(jq -r '.output_format // "markdown"' "$CONFIG_FILE")
        CACHE_ENABLED=$(jq -r '.cache_enabled // true' "$CONFIG_FILE")
    else
        log_warning "Configuration non trouvée, utilisation des valeurs par défaut"
        MAX_TOKENS=1000
        TIMEOUT=30000
        OUTPUT_FORMAT="markdown"
        CACHE_ENABLED=true
        
        # Créer la configuration par défaut
        mkdir -p "$(dirname "$CONFIG_FILE")"
        cat > "$CONFIG_FILE" << EOF
{
  "max_tokens": $MAX_TOKENS,
  "timeout": $TIMEOUT,
  "output_format": "$OUTPUT_FORMAT",
  "cache_enabled": $CACHE_ENABLED,
  "openclaw_integration": true,
  "optimize_for_tokens": true,
  "default_limit": 5,
  "language": "fr"
}
EOF
        log_success "Configuration créée: $CONFIG_FILE"
    fi
}

# Recherche web optimisée
web_search() {
    local query="$1"
    local limit="${2:-5}"
    
    log_info "Recherche: '$query' (limite: $limit)"
    
    local cache_flag=""
    if [ "$CACHE_ENABLED" = "true" ]; then
        cache_flag="--cache"
    fi
    
    # Construire la commande
    local cmd="$AGENT_BROWSER_CMD search \"$query\" \
        --limit $limit \
        --format $OUTPUT_FORMAT \
        --timeout $TIMEOUT \
        $cache_flag"
    
    log_info "Exécution: $cmd"
    
    # Exécuter et capturer la sortie
    local output
    if output=$(eval "$cmd" 2>&1); then
        echo "$output"
        
        # Analyser l'utilisation de tokens
        local token_count=$(echo "$output" | wc -w)
        log_info "Tokens estimés: $token_count / $MAX_TOKENS"
        
        if [ "$token_count" -gt "$MAX_TOKENS" ]; then
            log_warning "Attention: Sortie dépasse la limite de tokens"
            log_info "Utilisez --max-chars pour limiter la sortie"
        fi
    else
        log_error "Échec de la recherche: $output"
        return 1
    fi
}

# Extraction de contenu optimisée
extract_content() {
    local url="$1"
    local max_chars="${2:-2000}"
    
    log_info "Extraction: $url (max: ${max_chars} caractères)"
    
    # Construire la commande
    local cmd="$AGENT_BROWSER_CMD extract \"$url\" \
        --max-chars $max_chars \
        --format $OUTPUT_FORMAT \
        --timeout $TIMEOUT \
        --optimize"
    
    log_info "Exécution: $cmd"
    
    # Exécuter et capturer la sortie
    local output
    if output=$(eval "$cmd" 2>&1); then
        echo "$output"
        
        # Calculer les statistiques
        local char_count=${#output}
        local token_estimate=$((char_count / 4))
        log_info "Statistiques: ${char_count} caractères, ~${token_estimate} tokens"
        
        if [ "$token_estimate" -gt "$MAX_TOKENS" ]; then
            log_warning "Contenu tronqué pour respecter la limite de tokens"
            log_info "Utilisez une valeur plus petite pour --max-chars"
        fi
    else
        log_error "Échec de l'extraction: $output"
        return 1
    fi
}

# Recherche académique spécialisée
academic_search() {
    local query="$1"
    local sources="${2:-arxiv.org,researchgate.net,pubmed.ncbi.nlm.nih.gov}"
    
    log_info "Recherche académique: '$query'"
    log_info "Sources: $sources"
    
    # Diviser les sources
    IFS=',' read -ra SOURCE_ARRAY <<< "$sources"
    
    local results=""
    for source in "${SOURCE_ARRAY[@]}"; do
        log_info "Recherche sur: $source"
        
        local search_cmd="$AGENT_BROWSER_CMD search \"site:$source $query\" \
            --limit 3 \
            --format brief \
            --timeout 15000"
        
        if source_results=$(eval "$search_cmd" 2>&1); then
            results+="\n=== $source ===\n$source_results\n"
        else
            log_warning "Échec sur $source"
        fi
    done
    
    echo -e "$results"
}

# Surveillance de page avec diff
monitor_page() {
    local url="$1"
    local interval="${2:-3600}"
    
    log_info "Surveillance: $url (intervalle: ${interval}s)"
    
    # Créer un hash de la page actuelle
    local current_hash
    if current_hash=$(extract_content "$url" 1000 | md5sum | cut -d' ' -f1); then
        local cache_file="/tmp/agent-browser-monitor-$(echo "$url" | md5sum | cut -d' ' -f1)"
        
        if [ -f "$cache_file" ]; then
            local previous_hash=$(cat "$cache_file")
            
            if [ "$current_hash" != "$previous_hash" ]; then
                log_success "Changement détecté sur: $url"
                echo "La page a été modifiée depuis la dernière vérification."
                
                # Extraire et comparer le contenu
                local current_content=$(extract_content "$url" 5000)
                local previous_content=$(cat "${cache_file}.content" 2>/dev/null || echo "")
                
                if [ -n "$previous_content" ]; then
                    echo ""
                    echo "=== DIFF ==="
                    diff -u <(echo "$previous_content") <(echo "$current_content") | head -50
                fi
            else
                log_info "Aucun changement détecté"
            fi
        else
            log_info "Première surveillance de la page"
        fi
        
        # Sauvegarder le hash et le contenu
        echo "$current_hash" > "$cache_file"
        extract_content "$url" 5000 > "${cache_file}.content"
        
    else
        log_error "Impossible de surveiller la page"
        return 1
    fi
}

# Mode batch pour plusieurs URLs
batch_process() {
    local urls_file="$1"
    local output_dir="${2:-./output}"
    
    if [ ! -f "$urls_file" ]; then
        log_error "Fichier non trouvé: $urls_file"
        return 1
    fi
    
    mkdir -p "$output_dir"
    local count=0
    
    log_info "Traitement batch: $urls_file"
    log_info "Sortie: $output_dir"
    
    while IFS= read -r url || [ -n "$url" ]; do
        url=$(echo "$url" | xargs)  # Trim
        [ -z "$url" ] && continue
        
        count=$((count + 1))
        log_info "Traitement [$count]: $url"
        
        local safe_filename=$(echo "$url" | sed 's/[^a-zA-Z0-9]/_/g' | cut -c1-50)
        local output_file="$output_dir/${safe_filename}.md"
        
        if extract_content "$url" 3000 > "$output_file" 2>/dev/null; then
            log_success "  ✓ Sauvegardé: $output_file"
        else
            log_warning "  ✗ Échec: $url"
        fi
        
        # Pause pour éviter le rate limiting
        sleep 2
    done < "$urls_file"
    
    log_success "Traitement terminé: $count URLs traitées"
}

# Générer un rapport d'utilisation
generate_report() {
    log_info "Génération du rapport d'utilisation..."
    
    local report_file="/tmp/agent-browser-report-$(date +%Y%m%d-%H%M%S).txt"
    
    cat > "$report_file" << EOF
📊 RAPPORT D'UTILISATION AGENT BROWSER
====================================
Date: $(date)
Utilisateur: $(whoami)
OpenClaw Skill: cli-browser-navigation

CONFIGURATION:
-------------
Max tokens: $MAX_TOKENS
Timeout: $TIMEOUT ms
Format de sortie: $OUTPUT_FORMAT
Cache: $CACHE_ENABLED

COMMANDES DISPONIBLES:
---------------------
1. web_search <query> [limit]     - Recherche web optimisée
2. extract_content <url> [max_chars] - Extraction de contenu
3. academic_search <query> [sources] - Recherche académique
4. monitor_page <url> [interval]  - Surveillance de page
5. batch_process <file> [output_dir] - Traitement batch

STATISTIQUES DE PERFORMANCE:
---------------------------
- Tokens par requête: ≤ $MAX_TOKENS
- Timeout par requête: ${TIMEOUT}ms
- Format optimisé: $OUTPUT_FORMAT
- Cache activé: $CACHE_ENABLED

CONSEILS D'OPTIMISATION:
-----------------------
1. Utilisez des requêtes spécifiques
2. Limitez la longueur avec max_chars
3. Activez le cache pour les recherches répétées
4. Utilisez le format 'brief' pour les aperçus
5. Divisez les recherches complexes en plusieurs requêtes

EXEMPLES:
--------
# Recherche simple
web_search "physique quantique principes" 5

# Extraction limitée
extract_content "https://example.com" 1500

# Recherche académique
academic_search "deep learning chemistry"

# Surveillance
monitor_page "https://news.com" 1800

EOF
    
    log_success "Rapport généré: $report_file"
    cat "$report_file"
}

# Afficher l'aide
show_help() {
    cat << EOF
🌐 Agent Browser - Intégration OpenClaw
====================================

Usage: $0 <commande> [arguments]

Commandes:
  search <query> [limit]      - Recherche web
  extract <url> [max_chars]   - Extraire du contenu
  academic <query> [sources]  - Recherche académique
  monitor <url> [interval]    - Surveiller une page
  batch <file> [output_dir]   - Traitement batch
  report                      - Générer un rapport
  help                        - Afficher cette aide

Exemples:
  $0 search "IA générative" 3
  $0 extract "https://wikipedia.org" 2000
  $0 academic "machine learning" 
  $0 monitor "https://news.com" 3600
  $0 batch urls.txt ./results
  $0 report

Configuration: $CONFIG_FILE
Skill: $SKILL_DIR

EOF
}

# Point d'entrée principal
main() {
    log_info "🌐 Agent Browser - Intégration OpenClaw"
    log_info "Skill: cli-browser-navigation"
    
    # Vérifications initiales
    if ! check_agent_browser; then
        exit 1
    fi
    
    load_config
    
    # Traitement des commandes
    case "${1:-help}" in
        search|web_search)
            web_search "${2}" "${3:-5}"
            ;;
        extract|extract_content)
            extract_content "${2}" "${3:-2000}"
            ;;
        academic|academic_search)
            academic_search "${2}" "${3:-arxiv.org,researchgate.net,pubmed.ncbi.nlm.nih.gov}"
            ;;
        monitor|monitor_page)
            monitor_page "${2}" "${3:-3600}"
            ;;
        batch|batch_process)
            batch_process "${2}" "${3:-./output}"
            ;;
        report)
            generate_report
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Commande inconnue: $1"
            show_help
            exit 1
            ;;
    esac
}

# Exécuter le script
main "$@"