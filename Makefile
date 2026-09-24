DSA_PORT ?= 8420

.PHONY: app

app:
	@echo "Checking if port $(DSA_PORT) is in use..."
	-@lsof -ti:$(DSA_PORT) | xargs kill -9 2>/dev/null || true
	DSA_PORT=$(DSA_PORT) .venv/bin/python webapp/server.py
