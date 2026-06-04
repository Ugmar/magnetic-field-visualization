# ---------- Settings ----------
PYTHON := python3
PYTHON_REQUIRED := 3.12
VENV := .venv
ACTIVATE := source $(VENV)/bin/activate
REQ := requirements.txt
SHELL := /bin/bash
SHELL := /bin/bash

# ---------- Targets ----------

.PHONY: default
default: run

# Check python version
.PHONY: check-python
check-python:
	@version=$$($(PYTHON) -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"); \
	required_major=$$(echo "$(PYTHON_REQUIRED)" | cut -d. -f1); \
	required_minor=$$(echo "$(PYTHON_REQUIRED)" | cut -d. -f2); \
	current_major=$$(echo "$$version" | cut -d. -f1); \
	current_minor=$$(echo "$$version" | cut -d. -f2); \
	if [ "$$current_major" -ne "$$required_major" ]; then \
		echo "❌ Detected Python version $$version. This project requires Python $(PYTHON_REQUIRED) or newer (same major version)."; \
		exit 1; \
	elif [ "$$current_minor" -lt "$$required_minor" ]; then \
		echo "❌ Detected Python version $$version. This project requires Python $(PYTHON_REQUIRED) or newer."; \
		exit 1; \
	else \
		echo "✅ Python version $$version OK (required: $(PYTHON_REQUIRED)+)."; \
	fi

# Create python virtual environment
$(VENV)/bin/activate:
	@echo "📦 Creating virtual environment..."
	@$(PYTHON) -m venv $(VENV)
	@echo "✅ Virtual environment created."

# Install dependencies
.PHONY: install
install: check-python $(VENV)/bin/activate install-pre-commit
	@echo "📥 Installing dependencies..."
	@$(ACTIVATE) && pip install --upgrade pip
	@$(ACTIVATE) && pip install -r $(REQ)
	@echo "✅ Dependencies installed."

# Run program
.PHONY: run
run:
	@if [ ! -d "$(VENV)" ]; then \
		echo "⚙️ No virtual environment found, creating and installing dependencies..."; \
		$(MAKE) install; \
	fi
	@$(ACTIVATE) && $(PYTHON) main.py

# Code formatting
.PHONY: fmt
fmt:
	@$(ACTIVATE) && black . && isort . && flake8 .

# Clear cache (venv will not be removed)
.PHONY: clean
clean:
	@echo "🧹 Cleaning cache..."
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete
	@rm -rf build/ dist/
	@echo "✅ Cache cleaned."

# Help
.PHONY: help
help:
	@echo "Available make targets:"
	@echo -e "\tmake install   - create virtual environment and install dependencies"
	@echo -e "\tmake run       - run app (create venv if required)"
	@echo -e "\tmake fmt       - code formatting (black + isort + flake8)"
	@echo -e "\tmake clean     - clear python cache (.pyc, __pycache__, .pytest_cache)"
	@echo -e "\tmake build     - build executable program"

# Install git hook using core.hooksPath
.PHONY: install-pre-commit
install-pre-commit:
	@echo "📝 Configuring git to use external hooks directory..."
	@git config core.hooksPath hooks/
	@chmod +x hooks/pre-commit
	@echo "✅ Git hooks configured to use hooks/ directory!"
	@echo "💡 Git will now automatically use hooks/pre-commit as pre-commit hook"

.PHONY: build
build: install
	@$(ACTIVATE) && pyinstaller --onefile --name "Magnetic_field_visualisation.exe" main.py
	@echo "DONE: executable file is in dist/"
