# Albert IA Agentic - Dockerfile
# Multi-stage build pour optimiser la taille de l'image

FROM python:3.11-slim as builder

WORKDIR /app

# Dépendances système pour LaTeX et compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage final
FROM python:3.11-slim

WORKDIR /app

# Dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-pictures \
    texlive-science \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Utilisateur non-root pour la sécurité
RUN useradd -m -u 1000 albert && chown -R albert:albert /app
USER albert

# Copier les dépendances Python
COPY --from=builder /root/.local /home/albert/.local
ENV PATH=/home/albert/.local/bin:$PATH

# Copier le code
COPY --chown=albert:albert . .

# Créer les répertoires
RUN mkdir -p workspace/output tools skills

# Exposer le port
EXPOSE 8090

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8090/api/status || exit 1

# Lancer l'application
CMD ["python", "albert_api.py"]
