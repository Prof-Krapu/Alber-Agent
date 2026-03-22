// Albert IA Agentic - JavaScript principal

// Configuration
const BOT_TOKEN = 'default-secure-token-12345';
let currentModel = 'mistralai/Ministral-3-8B-Instruct-2512';
let isProcessing = false;
let availableTools = [];

// Échapper le HTML pour la sécurité
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Ajouter un message système
function addSystemMessage(text) {
    if (typeof addMessage === 'function') {
        addMessage(text, 'system');
    } else {
        console.log("System Message:", text);
    }
}

// Initialisation au chargement
document.addEventListener('DOMContentLoaded', init);

// Initialisation
async function init() {
    try {
        await loadModels();
        await loadTools();
        await checkStatus();
        updateStatus();

        // Activer la touche Entrée pour envoyer
        document.getElementById('message').addEventListener('keydown', function (e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    } catch (error) {
        console.error('Erreur initialisation:', error);
        addSystemMessage('⚠️ Erreur de connexion au serveur');
    }
}

// Vérifier le statut du serveur
async function checkStatus() {
    try {
        const response = await fetch('/api/status', {
            headers: { 'Authorization': 'Bearer ' + BOT_TOKEN }
        });
        const data = await response.json();
        if (data.success) {
            document.getElementById('status').textContent = '🟢 Connecté';
            addSystemMessage(`Serveur connecté - ${data.tools || data.tools_count} outils disponibles`);
        }
    } catch (error) {
        document.getElementById('status').textContent = '🔴 Hors ligne';
        addSystemMessage('⚠️ Serveur non disponible');
    }
}

// Charger les modèles
async function loadModels() {
    try {
        const response = await fetch('/api/models', {
            headers: { 'Authorization': 'Bearer ' + BOT_TOKEN }
        });
        const data = await response.json();

        const selector = document.getElementById('modelSelector');
        selector.innerHTML = '';

        for (const [modelId, modelInfo] of Object.entries(data.models)) {
            const btn = document.createElement('button');
            btn.className = 'model-btn' + (modelId === currentModel ? ' active' : '');
            btn.innerHTML = `
                <span class="emoji">${modelInfo.emoji}</span>
                <span class="name">${modelInfo.name}</span>
                <span class="desc">${modelInfo.description}</span>
            `;
            btn.onclick = () => selectModel(modelId);
            selector.appendChild(btn);
        }
    } catch (error) {
        console.error('Erreur chargement modèles:', error);
        addSystemMessage('⚠️ Impossible de charger les modèles');
    }
}

// Charger les outils
async function loadTools() {
    try {
        const response = await fetch('/api/tools', {
            headers: { 'Authorization': 'Bearer ' + BOT_TOKEN }
        });
        const data = await response.json();

        availableTools = data.tools;
        const grid = document.getElementById('toolsGrid');
        grid.innerHTML = '';

        data.tools.forEach(tool => {
            const card = document.createElement('div');
            card.className = 'tool-card' + (tool.dangerous ? ' dangerous' : '');
            card.innerHTML = `
                <div class="name">${escapeHtml(tool.name)}</div>
                <div class="desc">${escapeHtml(tool.description)}</div>
                <div class="badge">${tool.dangerous ? '⚠️ Dangereux' : '✅ Sûr'}</div>
            `;
            card.onclick = () => useTool(tool.id);
            grid.appendChild(card);
        });

        document.getElementById('toolsCount').textContent = `Outils: ${data.tools.length}`;
    } catch (error) {
        console.error('Erreur chargement outils:', error);
        addSystemMessage('⚠️ Impossible de charger les outils');
    }
}

// Sélectionner un modèle
function selectModel(modelId) {
    currentModel = modelId;

    // Mettre à jour l'interface
    document.querySelectorAll('.model-btn').forEach(btn => btn.classList.remove('active'));
    event.target.closest('.model-btn').classList.add('active');

    document.getElementById('currentModel').textContent = `Modèle: ${modelId.split('/').pop()}`;
    addSystemMessage(`Modèle changé: ${modelId}`);
}

// Utiliser un outil
function useTool(toolId) {
    const input = document.getElementById('message');
    input.value = `/tool ${toolId} `;
    input.focus();
}

// Configurer marked.js pour utiliser highlight.js de manière native
if (typeof marked !== 'undefined' && typeof hljs !== 'undefined') {
    marked.setOptions({
        highlight: function (code, lang) {
            const language = hljs.getLanguage(lang) ? lang : 'plaintext';
            return hljs.highlight(code, { language }).value;
        },
        breaks: true, // Convert \n to <br>
        gfm: true     // GitHub Flavored Markdown
    });
}

// Fonction utilitaire pour protéger le LaTeX avant le parsing Markdown
let latexCache = {};
let latexCounter = 0;

function protectLatex(text) {
    latexCache = {};
    latexCounter = 0;

    function storeLatex(match, formula, isDisplay) {
        const id = `MATHREF${latexCounter++}REF`;
        latexCache[id] = { formula: formula.trim(), isDisplay };
        return id;
    }

    // 1. Display Math $$ ... $$
    let protectedText = text.replace(/\$\$([\s\S]*?)\$\$/g, (m, p1) => storeLatex(m, p1, true));
    // 2. Display Math \[ ... \]
    protectedText = protectedText.replace(/\\\[([\s\S]*?)\\\]/g, (m, p1) => storeLatex(m, p1, true));
    // 3. Inline Math \( ... \)
    protectedText = protectedText.replace(/\\\(([\s\S]*?)\\\)/g, (m, p1) => storeLatex(m, p1, false));
    // 4. Inline Math $ ... $
    protectedText = protectedText.replace(/(^|[^\\])\$([^\$\n]+?)\$/g, (m, p1, p2) => {
        if (p2.trim() === '') return m;
        return p1 + storeLatex(m, p2, false);
    });

    return protectedText;
}

function restoreLatex(html) {
    return html.replace(/MATHREF(\d+)REF/g, (match, p1) => {
        const id = `MATHREF${p1}REF`;
        if (latexCache[id]) {
            const { formula, isDisplay } = latexCache[id];
            try {
                // Version robuste de l'encodage Base64 pour UTF-8 (gère les caractères grecs littéraux)
                const utf8Bytes = new TextEncoder().encode(formula);
                const b64 = btoa(String.fromCharCode.apply(null, utf8Bytes));

                if (isDisplay) {
                    return `<div class="math-display" data-latex-b64="${b64}"></div>`;
                } else {
                    return `<span class="math-inline" data-latex-b64="${b64}"></span>`;
                }
            } catch (e) {
                return formula;
            }
        }
        return match;
    });
}

// Fonction utilitaire pour le rendu sécurisé du Markdown
function renderMarkdownSecurely(text) {
    if (typeof marked === 'undefined' || typeof DOMPurify === 'undefined') {
        return `<p>${escapeHtml(text)}</p>`;
    }

    // 1. Extraire et cacher les équations LaTeX
    const protectedText = protectLatex(text);

    // 2. Parser le Markdown brut
    const rawHtml = marked.parse(protectedText);

    // 3. Assainir avec DOMPurify (les placeholders textuels MATHREF survivent sans souci)
    const sanitizedHtml = DOMPurify.sanitize(rawHtml);

    // 4. Restaurer les balises LaTeX (data-latex-b64)
    return restoreLatex(sanitizedHtml);
}

// Appliquer KaTeX de manière explicite sur le DOM
function applyMathRendering(element) {
    if (typeof katex !== 'undefined') {
        const mathElements = element.querySelectorAll('.math-display, .math-inline');
        mathElements.forEach(el => {
            const b64 = el.getAttribute('data-latex-b64');
            if (b64) {
                try {
                    // Décodage robuste Base64 -> UTF-8
                    const binaryString = atob(b64);
                    const bytes = new Uint8Array(binaryString.length);
                    for (let i = 0; i < binaryString.length; i++) {
                        bytes[i] = binaryString.charCodeAt(i);
                    }
                    const src = new TextDecoder().decode(bytes);

                    const isDisplay = el.classList.contains('math-display');
                    katex.render(src, el, {
                        displayMode: isDisplay,
                        throwOnError: false,
                        strict: 'ignore'
                    });
                } catch (e) {
                    console.error("Erreur de rendu KaTeX:", e);
                }
            }
        });
    }
}

// Ajouter un message
function addMessage(text, sender, toolName = null) {
    const chat = document.getElementById('chat');
    // On cherche ou on crée le wrapper de contenu pour le centrage
    let wrapper = chat.querySelector('.chat-content-wrapper');
    if (!wrapper) {
        wrapper = document.createElement('div');
        wrapper.className = 'chat-content-wrapper';
        chat.appendChild(wrapper);
    }

    const messageDiv = document.createElement('div');

    if (sender === 'user') {
        messageDiv.className = 'message user-message';
        messageDiv.innerHTML = `
            <div class="meta">
                <span>👤 Vous</span>
                <span>${new Date().toLocaleTimeString()}</span>
            </div>
            <p>${escapeHtml(text)}</p>
        `;
    } else if (sender === 'assistant') {
        messageDiv.className = 'message assistant-message markdown-body';
        messageDiv.innerHTML = `
            <div class="meta">
                <span>🤖 Albert IA</span>
                <span>${new Date().toLocaleTimeString()}</span>
            </div>
            <div class="content format-guard">${renderMarkdownSecurely(text)}</div>
        `;
    } else if (sender === 'tool') {
        messageDiv.className = 'message tool-message markdown-body';
        messageDiv.innerHTML = `
            <div class="meta">
                <span>🛠️ ${escapeHtml(toolName || 'Outil')}</span>
                <span>${new Date().toLocaleTimeString()}</span>
            </div>
            <div class="content format-guard">${renderMarkdownSecurely(text)}</div>
        `;
    } else if (sender === 'system') {
        messageDiv.className = 'message assistant-message';
        messageDiv.innerHTML = `
            <div class="meta">
                <span>⚙️ Système</span>
                <span>${new Date().toLocaleTimeString()}</span>
            </div>
            <p><em>${escapeHtml(text)}</em></p>
        `;
    }

    wrapper.appendChild(messageDiv);

    // Rendu post-insertion : Mathématiques KaTeX
    if (sender === 'assistant' || sender === 'tool') {
        applyMathRendering(messageDiv);
    }

    // Scroll au bas
    setTimeout(() => {
        chat.scrollTop = chat.scrollHeight;
    }, 50);
}

// Mettre à jour le statut
function updateStatus() {
    // Mettre à jour périodiquement
    setTimeout(checkStatus, 30000);
}

// Afficher/masquer l'indicateur de frappe
function showTyping(show) {
    document.getElementById('typing').style.display = show ? 'block' : 'none';
}

// Envoyer un message
async function sendMessage() {
    if (isProcessing) return;

    const input = document.getElementById('message');
    const text = input.value.trim();

    if (!text) return;

    // Ajouter le message utilisateur
    addMessage(text, 'user');
    input.value = '';

    // Désactiver le bouton
    const sendBtn = document.getElementById('send');
    sendBtn.disabled = true;
    isProcessing = true;

    // Afficher l'indicateur de frappe
    showTyping(true);

    try {
        // Envoyer au serveur
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + BOT_TOKEN
            },
            body: JSON.stringify({
                message: text,
                model: currentModel
            })
        });

        const data = await response.json();

        if (data.success) {
            if (data.type === 'tool') {
                // Résultat d'outil
                const toolResult = JSON.stringify(data.result, null, 2);
                addMessage(`Résultat: ${toolResult}`, 'tool', data.tool_id);
            } else if (data.type === 'chat') {
                // Réponse de chat
                addMessage(data.reply, 'assistant');
            }
        } else {
            addSystemMessage(`❌ Erreur: ${data.error}`);
        }
    } catch (error) {
        console.error('Erreur envoi message:', error);
        addSystemMessage('❌ Erreur de connexion au serveur');
    } finally {
        // Réactiver le bouton
        sendBtn.disabled = false;
        isProcessing = false;
        showTyping(false);
    }
}

// Exporter les fonctions globales
window.sendMessage = sendMessage;
window.selectModel = selectModel;
window.useTool = useTool;