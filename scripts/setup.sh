#!/usr/bin/env bash
set -euo pipefail

cp -n .env.example .env || true

python -m pip install --upgrade pip
python -m pip install uv pre-commit
pip install -e ./backend[dev]

cd frontend
npm install
cd ..

pre-commit install

echo "Setup complete. Run: make up"
