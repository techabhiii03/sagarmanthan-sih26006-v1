#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/../frontend"
if [ ! -d "node_modules" ]; then
  npm install
fi
echo "Starting SagarManthan UI on http://localhost:5173"
exec npm run dev -- --host 0.0.0.0 --port 5173
