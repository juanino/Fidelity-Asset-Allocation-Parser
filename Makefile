.PHONY: help install run clean lint

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PYLINT := $(VENV)/bin/pylint

help:
	@echo "Available targets:"
	@echo "  make install  - Create virtual environment and install dependencies"
	@echo "  make run      - Run the asset allocation analysis"
	@echo "  make clean    - Remove generated PDF reports"
	@echo "  make lint     - Run pylint on the code"

install:
	@echo "Creating virtual environment..."
	python3 -m venv $(VENV)
	@echo "Installing dependencies..."
	$(PIP) install -r requirements.txt
	@echo "Installation complete!"

run:
	@echo "Running asset allocation analysis..."
	$(PYTHON) check_allocation.py

clean:
	@echo "Cleaning up PDF reports..."
	rm -f asset_allocation_report_*.pdf
	@echo "PDF reports removed."

lint:
	@echo "Running pylint..."
	$(PYLINT) ./check_allocation.py
