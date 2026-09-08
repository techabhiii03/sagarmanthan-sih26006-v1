#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/../backend"
if [ ! -d "venv" ]; then
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
else
  source venv/bin/activate
fi
echo "Starting SagarManthan API on http://localhost:8000"
echo "Docs: http://localhost:8000/docs"
exec uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
