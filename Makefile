DSA_PORT ?= 8080
PREVIEW_PORT ?= 8000
PYTHON ?= python3
OUT ?= dist
IMAGE ?= engineering-guide

.PHONY: help app build preview clean docker-build docker-run

help: ## List the targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-13s %s\n", $$1, $$2}'

app: ## Run the full app locally (runs code, saves progress): http://127.0.0.1:8080, or DSA_PORT=…
	@echo "Checking if port $(DSA_PORT) is in use..."
	-@lsof -ti:$(DSA_PORT) | xargs kill -9 2>/dev/null || true
	@command -v "$(PYTHON)" >/dev/null 2>&1 || { echo "Python interpreter not found: $(PYTHON)" >&2; exit 127; }
	DSA_PORT=$(DSA_PORT) "$(PYTHON)" webapp/server.py

build: ## Build the static site into dist/ (or OUT=…); deploy that folder to any static host
	"$(PYTHON)" webapp/build_static.py --out "$(OUT)"

preview: build ## Build, then serve the static site: http://127.0.0.1:8000, or PREVIEW_PORT=…
	"$(PYTHON)" -m http.server $(PREVIEW_PORT) --bind 127.0.0.1 --directory "$(OUT)"

clean: ## Remove the static build
	rm -rf "$(OUT)"

docker-build: ## Build the nginx container image of the static site
	docker build -f deploy/Dockerfile -t $(IMAGE) .

docker-run: ## Run that image on http://127.0.0.1:8080
	docker run --rm -p 8080:8080 $(IMAGE)
