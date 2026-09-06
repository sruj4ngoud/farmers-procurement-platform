#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../backend"
if [ -x .venv/bin/python ]; then
  .venv/bin/python -m app.database.seed
else
  python3 -m app.database.seed
fi
