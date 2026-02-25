Copy-Item -Path .env.example -Destination .env -ErrorAction SilentlyContinue

python -m pip install --upgrade pip
python -m pip install uv pre-commit
pip install -e .\backend[dev]

Push-Location frontend
npm install
Pop-Location

pre-commit install
Write-Host "Setup complete. Run: make up"
