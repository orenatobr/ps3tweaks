.PHONY: help install dev test lint format clean venv setup install-ps3

help:
	@echo "PS3 Tweaks - Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  make venv          - Create uv virtual environment"
	@echo "  make setup         - Full setup (venv + dependencies)"
	@echo "  make install       - Install project with dev dependencies"
	@echo "  make test          - Run tests"
	@echo "  make isort         - Sort imports with isort"
	@echo "  make lint          - Run flake8"
	@echo "  make ruff          - Run ruff checks"
	@echo "  make format        - Format code with black"
	@echo "  make clean         - Clean temporary files"
	@echo "  make install-ps3   - Install scripts to PS3 (requires IP)"
	@echo ""

venv:
	uv venv
	. .venv/bin/activate && uv pip install -e .

setup: venv install

install:
	. .venv/bin/activate && uv pip install -e ".[dev]"

test:
	. .venv/bin/activate && pytest tests/ -v --cov=src/ps3tweaks --cov-report=term-missing --cov-fail-under=80

isort:
	. .venv/bin/activate && isort src/ tests/

lint:
	. .venv/bin/activate && flake8 src/ tests/

ruff:
	. .venv/bin/activate && ruff check src/ tests/

format:
	. .venv/bin/activate && black src/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/

install-ps3:
	@read -p "PS3 IP: " PS3_IP; \
	if [ -z "$$PS3_IP" ]; then \
		echo "IP not provided"; \
		exit 1; \
	fi; \
	bash scripts/install.sh $$PS3_IP

# Quick alias for environment activation
activate:
	@echo "To activate the environment, run:"
	@echo "  source tools/dev_env.sh"
