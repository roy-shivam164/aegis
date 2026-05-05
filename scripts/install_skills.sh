#!/usr/bin/env bash
# install_skills.sh — Copy AEGIS skill documents to ~/.hermes/skills/aegis/
# Usage: ./scripts/install_skills.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SKILLS_SRC="${PROJECT_ROOT}/hermes_skills"
HERMES_SKILLS_DIR="${HERMES_SKILLS_DIR:-${HOME}/.hermes/skills/aegis}"

echo "Installing AEGIS skills to ${HERMES_SKILLS_DIR}..."

mkdir -p "${HERMES_SKILLS_DIR}"

INSTALLED=0
for skill_file in "${SKILLS_SRC}"/*.md; do
    if [ -f "${skill_file}" ]; then
        filename=$(basename "${skill_file}")
        cp "${skill_file}" "${HERMES_SKILLS_DIR}/${filename}"
        echo "  ✓ ${filename}"
        INSTALLED=$((INSTALLED + 1))
    fi
done

echo ""
echo "✓ Installed ${INSTALLED} AEGIS skill documents"
echo "  Skills directory: ${HERMES_SKILLS_DIR}"
echo ""
echo "Available skills in Hermes:"
echo "  /aegis-skillforge — Brain 1: failure tracing & skill evolution"
echo "  /aegis-mirror     — Brain 2: life logging & proactive JARVIS"
echo "  /aegis-shadow     — Brain 3: person profiling & motive analysis"
echo "  /aegis-heartbeat  — Run proactive heartbeat cycle"
echo "  /aegis-status     — System health & metrics"
