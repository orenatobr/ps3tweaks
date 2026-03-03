#!/bin/bash
# PS3 Tweaks - Environment Setup Script
# Use: source tools/dev_env.sh

# Resolve project root from tools/
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"

if [ -d "$PROJECT_ROOT/.venv" ]; then
    # shellcheck source=/dev/null
    source "$PROJECT_ROOT/.venv/bin/activate"
    echo "✅ Virtual environment activated"
    echo "   Python: $(python --version)"
    echo "   Location: $VIRTUAL_ENV"
    echo ""
    echo "Installed packages:"
    echo "   - paramiko (SSH/SCP)"
    echo "   - requests (HTTP requests)"
    echo "   - pillow (Image processing)"
    echo "   - pytest (Testing)"
    echo "   - black (Code formatter)"
    echo "   - flake8 (Linter)"
else
    echo "❌ Virtual environment not found. Run:"
    echo "   cd $PROJECT_ROOT"
    echo "   uv venv"
    echo "   source .venv/bin/activate"
    echo "   uv pip install -e .[dev]"
fi
