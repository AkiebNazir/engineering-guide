DSA_PORT ?= 8080
PREVIEW_PORT ?= 8000
PYTHON ?= python3
OUT ?= dist
IMAGE ?= engineering-guide

.PHONY: help app serve test admin build preview clean docker-build docker-run docker-build-static

help: ## List the targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-13s %s\n", $$1, $$2}'

app: ## Run the full app locally (runs code, saves progress): http://127.0.0.1:8080, or DSA_PORT=…
	@echo "Checking if port $(DSA_PORT) is in use..."
	-@lsof -ti:$(DSA_PORT) | xargs kill -9 2>/dev/null || true
	@command -v "$(PYTHON)" >/dev/null 2>&1 || { echo "Python interpreter not found: $(PYTHON)" >&2; exit 127; }
	DSA_PORT=$(DSA_PORT) "$(PYTHON)" webapp/server.py

serve: ## Run the hosted mode locally (sign-in, plans, no code running); codes print to this console
	EG_AUTH=1 EG_OTP_CONSOLE=1 DSA_PORT=$(DSA_PORT) "$(PYTHON)" webapp/server.py

test: ## Run the sign-in / plans test suite
	"$(PYTHON)" -m unittest discover -s webapp/tests -v

admin: ## Manage accounts and plans, e.g. make admin ARGS="grant you@example.com pro --days 30"
	"$(PYTHON)" webapp/admin.py $(ARGS)

build: ## Build the static free preview into dist/ (or OUT=…); deploy that folder to any static host
	"$(PYTHON)" webapp/build_static.py --out "$(OUT)"

preview: build ## Build, then serve the static site: http://127.0.0.1:8000, or PREVIEW_PORT=…
	"$(PYTHON)" -m http.server $(PREVIEW_PORT) --bind 127.0.0.1 --directory "$(OUT)"

clean: ## Remove the static build
	rm -rf "$(OUT)"

docker-build: ## Build the hosted app image (sign-in and plans)
	docker build -f deploy/Dockerfile -t $(IMAGE) .

docker-run: ## Run that image on http://127.0.0.1:8080 (development: codes on the console, plain-HTTP cookies)
	docker run --rm -p 8080:8080 -v eg-data:/data -e EG_OTP_CONSOLE=1 -e EG_COOKIE_SECURE=0 $(IMAGE)

docker-build-static: ## Build the nginx image of the static free preview
	docker build -f deploy/Dockerfile.static -t $(IMAGE)-preview .
