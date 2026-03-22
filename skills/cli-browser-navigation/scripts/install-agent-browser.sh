#!/bin/bash
# Script d'installation de l'Agent Browser de Vercel
# Usage: ./install-agent-browser.sh [--global] [--dev]

set -e

GLOBAL=false
DEV=false
INSTALL_DIR="$HOME/agent-browser"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --global)
            GLOBAL=true
            shift
            ;;
        --dev)
            DEV=true
            shift
            ;;
        *)
            INSTALL_DIR="$1"
            shift
            ;;
    esac
done

echo "🔧 Installation de l'Agent Browser de Vercel"
echo "=========================================="

# Check prerequisites
echo "📋 Vérification des prérequis..."

if ! command -v node &> /dev/null; then
    echo "❌ Node.js n'est pas installé"
    echo "   Installez Node.js >= 18.0.0: https://nodejs.org/"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ npm n'est pas installé"
    exit 1
fi

if ! command -v git &> /dev/null; then
    echo "❌ Git n'est pas installé"
    echo "   Installez Git: https://git-scm.com/"
    exit 1
fi

NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js version $NODE_VERSION est trop ancienne"
    echo "   Mettez à jour vers Node.js >= 18.0.0"
    exit 1
fi

echo "✅ Prérequis vérifiés:"
echo "   Node.js: $(node --version)"
echo "   npm: $(npm --version)"
echo "   Git: $(git --version)"

# Clone repository
echo ""
echo "📥 Clonage du dépôt..."
if [ -d "$INSTALL_DIR" ]; then
    echo "⚠️  Le répertoire $INSTALL_DIR existe déjà"
    read -p "Voulez-vous le mettre à jour? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd "$INSTALL_DIR"
        git pull origin main
    else
        echo "❌ Installation annulée"
        exit 1
    fi
else
    git clone https://github.com/vercel-labs/agent-browser.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# Install dependencies
echo ""
echo "📦 Installation des dépendances..."
npm install

# Build project
echo ""
echo "🔨 Construction du projet..."
npm run build

# Global installation
if [ "$GLOBAL" = true ]; then
    echo ""
    echo "🌍 Installation globale..."
    npm install -g .
    
    # Create symlink for easier access
    if [ ! -f "/usr/local/bin/agent-browser" ]; then
        sudo ln -sf "$(which agent-browser)" /usr/local/bin/agent-browser
    fi
fi

# Development setup
if [ "$DEV" = true ]; then
    echo ""
    echo "💻 Configuration développement..."
    npm run dev:setup
    
    # Install dev dependencies
    npm install --save-dev @types/node @types/jest
    
    # Create test directory
    mkdir -p tests
    cat > tests/basic.test.js << 'EOF'
const { execSync } = require('child_process');

test('agent-browser version', () => {
    const output = execSync('node bin/agent-browser.js --version').toString();
    expect(output).toMatch(/\d+\.\d+\.\d+/);
});

test('agent-browser help', () => {
    const output = execSync('node bin/agent-browser.js --help').toString();
    expect(output).toContain('Usage:');
});
EOF
fi

# Create configuration
echo ""
echo "⚙️  Création de la configuration..."
CONFIG_DIR="$HOME/.config/agent-browser"
mkdir -p "$CONFIG_DIR"

cat > "$CONFIG_DIR/config.json" << EOF
{
  "headless": true,
  "timeout": 30000,
  "maxTokens": 1000,
  "extractMode": "relevant",
  "cacheEnabled": true,
  "cacheTTL": 3600,
  "userAgent": "Agent-Browser/1.0 (+https://github.com/vercel-labs/agent-browser)",
  "language": "fr",
  "outputFormat": "markdown",
  "concurrentRequests": 2,
  "retryAttempts": 3,
  "retryDelay": 1000
}
EOF

# Create cache directory
CACHE_DIR="$HOME/.cache/agent-browser"
mkdir -p "$CACHE_DIR"

# Create examples
echo ""
echo "📚 Création d'exemples..."
EXAMPLES_DIR="$INSTALL_DIR/examples"
mkdir -p "$EXAMPLES_DIR"

cat > "$EXAMPLES_DIR/basic-search.sh" << 'EOF'
#!/bin/bash
# Exemple: Recherche basique
echo "🔍 Recherche basique..."
node bin/agent-browser.js search "physique quantique" --limit 3 --format markdown

echo ""
echo "📄 Extraction de contenu..."
node bin/agent-browser.js extract "https://fr.wikipedia.org/wiki/Physique_quantique" --max-chars 1000
EOF

chmod +x "$EXAMPLES_DIR/basic-search.sh"

cat > "$EXAMPLES_DIR/advanced-extraction.sh" << 'EOF'
#!/bin/bash
# Exemple: Extraction avancée
echo "🎯 Extraction ciblée..."
node bin/agent-browser.js extract "https://example.com" \
  --select "article.main-content" \
  --exclude "sidebar,footer,comments" \
  --output json \
  --pretty

echo ""
echo "📊 Statistiques..."
node bin/agent-browser.js stats --tokens --time
EOF

chmod +x "$EXAMPLES_DIR/advanced-extraction.sh"

# Create wrapper script
echo ""
echo "📝 Création du script wrapper..."
cat > "$INSTALL_DIR/agent-browser-wrapper.sh" << 'EOF'
#!/bin/bash
# Wrapper pour agent-browser avec configuration automatique

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$HOME/.config/agent-browser/config.json"

# Load configuration
if [ -f "$CONFIG_FILE" ]; then
    export AGENT_BROWSER_CONFIG="$CONFIG_FILE"
fi

# Set cache directory
export AGENT_BROWSER_CACHE_DIR="$HOME/.cache/agent-browser"

# Run agent-browser
if [ -f "$SCRIPT_DIR/bin/agent-browser.js" ]; then
    node "$SCRIPT_DIR/bin/agent-browser.js" "$@"
elif command -v agent-browser &> /dev/null; then
    agent-browser "$@"
else
    echo "❌ agent-browser n'est pas installé"
    echo "   Exécutez: $SCRIPT_DIR/install-agent-browser.sh"
    exit 1
fi
EOF

chmod +x "$INSTALL_DIR/agent-browser-wrapper.sh"

# Create alias in bashrc/zshrc
echo ""
echo "🔗 Configuration des alias..."
SHELL_RC="$HOME/.bashrc"
if [ -n "$ZSH_VERSION" ]; then
    SHELL_RC="$HOME/.zshrc"
fi

if ! grep -q "agent-browser" "$SHELL_RC"; then
    cat >> "$SHELL_RC" << EOF

# Agent Browser aliases
alias ab='$INSTALL_DIR/agent-browser-wrapper.sh'
alias agent-browser='$INSTALL_DIR/agent-browser-wrapper.sh'
export PATH="\$PATH:$INSTALL_DIR/bin"
EOF
    echo "✅ Alias ajoutés à $SHELL_RC"
    echo "   Redémarrez votre terminal ou exécutez: source $SHELL_RC"
fi

# Summary
echo ""
echo "🎉 Installation terminée!"
echo "========================"
echo ""
echo "📁 Répertoire d'installation: $INSTALL_DIR"
echo "⚙️  Configuration: $HOME/.config/agent-browser/config.json"
echo "💾 Cache: $HOME/.cache/agent-browser"
echo ""
echo "🚀 Commandes disponibles:"
echo "   $INSTALL_DIR/agent-browser-wrapper.sh [command]"
echo "   ab [command] (après redémarrage du terminal)"
echo ""
echo "📚 Exemples:"
echo "   cd $INSTALL_DIR/examples"
echo "   ./basic-search.sh"
echo "   ./advanced-extraction.sh"
echo ""
echo "❓ Aide:"
echo "   $INSTALL_DIR/agent-browser-wrapper.sh --help"
echo ""
echo "🔧 Pour une installation globale, exécutez:"
echo "   cd $INSTALL_DIR && npm install -g ."
echo ""
echo "💡 Astuce: Utilisez 'ab' comme alias rapide après redémarrage du terminal"