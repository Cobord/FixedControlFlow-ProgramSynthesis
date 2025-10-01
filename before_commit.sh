#!bin/bash
rm -rf .pytest_cache
rm -rf src/__pycache__
rm -rf src/*/__pycache__
rm -rf tests/__pycache__
uv run black src/*/*.py
uv run black tests/*.py
uv run black scripts/*.py
uv run black *.py
uv run main.py
uv run pytest tests/*.py
uv run scripts/*.py
rm -rf .pytest_cache
rm -rf src/__pycache__
rm -rf src/*/__pycache__
rm -rf tests/__pycache__