#!/usr/bin/env bash
set -e

echo "🦅 === HAWK INTEGRATION DEBUG REPORT ==="
echo

echo "📦 Python packages:"
docker-compose exec bot sh -c "pip freeze | grep -E 'hawkcatcher|structlog|aiogram' || true"
echo

echo "📂 Dependencies (requirements or pyproject):"
if [ -f requirements.txt ]; then
    grep hawkcatcher requirements.txt || true
elif [ -f pyproject.toml ]; then
    grep -A 2 hawkcatcher pyproject.toml || true
fi
echo

echo "⚙️ Logging setup (core/logging_setup.py):"
docker-compose exec bot sh -c "cat core/logging_setup.py | head -n 50"
echo

echo "🪶 Hawk setup (core/monitoring/hawk_setup.py):"
docker-compose exec bot sh -c "cat core/monitoring/hawk_setup.py | head -n 50"
echo

echo "🔍 Usage of Hawk across project:"
docker-compose exec bot sh -c "grep -R --color=never -n 'hawk' core/ middlewares/ services/ --exclude-dir=__pycache__ || true"
echo

echo "🚀 Main entrypoint snippet (main.py - first 50 lines):"
docker-compose exec bot sh -c "cat main.py | head -n 50"
echo

echo "🌍 Environment variables related to Hawk:"
docker-compose exec bot sh -c "printenv | grep HAWK || true"
echo

echo "✅ Done. Collected Hawk diagnostic info."
