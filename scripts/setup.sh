#!/usr/bin/env bash
# setup.sh — Full AEGIS setup: deps, Qdrant, collections, skills
# Usage: ./scripts/setup.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║       AEGIS — Adaptive Evolving General Intelligence     ║"
echo "║                   System Setup Script                    ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# ── 1. Check prerequisites ────────────────────────────────────────────────────
echo "▶ Checking prerequisites..."

if ! command -v python3 &>/dev/null; then
    echo "  ✗ Python 3 not found. Please install Python 3.11+"
    exit 1
fi
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "  ✓ Python ${PYTHON_VERSION}"

if ! command -v docker &>/dev/null; then
    echo "  ✗ Docker not found. Please install Docker."
    exit 1
fi
echo "  ✓ Docker"

if ! command -v docker-compose &>/dev/null && ! docker compose version &>/dev/null 2>&1; then
    echo "  ✗ Docker Compose not found."
    exit 1
fi
echo "  ✓ Docker Compose"

# ── 2. Environment file ───────────────────────────────────────────────────────
echo ""
echo "▶ Setting up environment..."
if [ ! -f "${PROJECT_ROOT}/.env" ]; then
    cp "${PROJECT_ROOT}/.env.example" "${PROJECT_ROOT}/.env"
    echo "  ✓ Created .env from .env.example"
    echo "  ⚠ Please edit .env and add your OPENAI_API_KEY before continuing"
else
    echo "  ✓ .env already exists"
fi

# ── 3. Python virtual environment ────────────────────────────────────────────
echo ""
echo "▶ Setting up Python environment..."
if [ ! -d "${PROJECT_ROOT}/.venv" ]; then
    python3 -m venv "${PROJECT_ROOT}/.venv"
    echo "  ✓ Created virtual environment at .venv/"
fi

# Activate venv
source "${PROJECT_ROOT}/.venv/bin/activate"

echo "  ▶ Installing Python dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r "${PROJECT_ROOT}/requirements.txt"
pip install --quiet -e "${PROJECT_ROOT}/"
echo "  ✓ Python dependencies installed"

# ── 4. Start Qdrant ──────────────────────────────────────────────────────────
echo ""
echo "▶ Starting Qdrant vector database..."
cd "${PROJECT_ROOT}"

if docker compose version &>/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

${COMPOSE_CMD} up -d

echo "  ▶ Waiting for Qdrant to be ready..."
for i in {1..30}; do
    if curl -sf http://localhost:6333/health &>/dev/null; then
        echo "  ✓ Qdrant is ready at http://localhost:6333"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo "  ✗ Qdrant failed to start after 30 seconds"
        exit 1
    fi
    sleep 1
done

# ── 5. Initialize Qdrant collections ─────────────────────────────────────────
echo ""
echo "▶ Initializing Qdrant collections..."
python3 -c "
from aegis.core.qdrant_manager import QdrantManager
qm = QdrantManager()
qm.initialize_collections()
print('  ✓ All 5 collections initialized')
"

# ── 6. Install Hermes skill documents ────────────────────────────────────────
echo ""
echo "▶ Installing Hermes skill documents..."
chmod +x "${SCRIPT_DIR}/install_skills.sh"
"${SCRIPT_DIR}/install_skills.sh"

# ── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                   Setup Complete! 🚀                     ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. Edit .env with your OPENAI_API_KEY"
echo "  2. Seed demo data:    python scripts/seed_demo.py"
echo "  3. Start API:         uvicorn aegis.api.server:app --reload"
echo "  4. Start dashboard:   cd dashboard && npm install && npm run dev"
echo "  5. Open dashboard:    http://localhost:5173"
echo ""
echo "Hermes skills installed at: ~/.hermes/skills/aegis/"
echo "Copy SOUL.md:  cp hermes_config/SOUL.md ~/.hermes/SOUL.md"
