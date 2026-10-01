FROM python:3.13-slim


# Copy uv executable from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

ENV PYTHONUNBUFFERED=1 \
    UV_SYSTEM_PYTHON=1


WORKDIR /app

# Installation des dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*


# Copy dependency definition files first (for Docker caching)
COPY pyproject.toml /app/



# Installation des dépendances Python
RUN uv pip install --system .

# Copie ciblée des répertoires nécessaires
COPY scripts/ /app/scripts/


# Création des dossiers pour les fichiers générés
RUN mkdir -p /app/data/exports /app/data/processed /app/data/csv

