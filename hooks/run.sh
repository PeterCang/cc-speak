#!/usr/bin/env sh
# Detect python3 or python (must be 3.x), then run stop-speak.py

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
elif command -v python >/dev/null 2>&1; then
    # Verify it's Python 3, not Python 2
    PY_MAJOR=$(python -c "import sys; print(sys.version_info.major)" 2>/dev/null)
    if [ "$PY_MAJOR" = "3" ]; then
        PYTHON=python
    else
        exit 0
    fi
else
    exit 0
fi

exec "$PYTHON" "$SCRIPT_DIR/stop-speak.py"
