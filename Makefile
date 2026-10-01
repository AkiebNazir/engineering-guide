DSA_PORT ?= 8080
PYTHON ?= python3

.PHONY: app

app:
	@echo "Checking if port $(DSA_PORT) is in use..."
	-@lsof -ti:$(DSA_PORT) | xargs kill -9 2>/dev/null || true
	@command -v "$(PYTHON)" >/dev/null 2>&1 || { echo "Python interpreter not found: $(PYTHON)" >&2; exit 127; }
	DSA_PORT=$(DSA_PORT) "$(PYTHON)" webapp/server.py
