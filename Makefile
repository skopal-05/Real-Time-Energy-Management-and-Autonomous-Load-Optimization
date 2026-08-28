# Development entry points for the whole system.
#
# The seven modules are never built or installed - they are executed in place,
# from their own folders, by the integration layer.

PYTHON      ?= .venv/bin/python
PIP         ?= .venv/bin/pip
API_PORT    ?= 8010
UI_PORT     ?= 3010

.PHONY: help setup check run serve ui test test-guard clean

help:
	@echo "setup       create the virtual environment and install dependencies"
	@echo "check       verify modules, packages, models and data are in place"
	@echo "run         run Modules 1-7 end to end once"
	@echo "serve       start the integration API on port $(API_PORT)"
	@echo "ui          start the Next.js control centre on port $(UI_PORT)"
	@echo "test        run the full test suite"
	@echo "test-guard  run only the check that no module was modified"
	@echo "clean       remove platform run data (never touches the modules)"

setup:
	@command -v uv >/dev/null 2>&1 \
		&& uv venv --python 3.12 .venv && uv pip install --python $(PYTHON) -r requirements.txt \
		|| (python3 -m venv .venv && $(PIP) install -r requirements.txt)
	cd frontend && npm install

check:
	$(PYTHON) -m enertwin check

run:
	$(PYTHON) -m enertwin run

serve:
	$(PYTHON) -m enertwin serve --port $(API_PORT)

ui:
	cd frontend && npm run dev -- --port $(UI_PORT)

test:
	$(PYTHON) -m pytest tests/ -q

test-guard:
	$(PYTHON) -m pytest tests/test_modules_unmodified.py -v

clean:
	rm -rf enertwin_data
	find enertwin -name '__pycache__' -type d -exec rm -rf {} +
