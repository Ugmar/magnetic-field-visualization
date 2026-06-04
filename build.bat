@echo off
echo Building Magnetic Field Visualization...

python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m PyInstaller --onefile --name "MagneticFieldVisualization" main.py

powershell -NoProfile -Command "Write-Host 'Build complete! Check dist/ folder.' -ForegroundColor Green"
