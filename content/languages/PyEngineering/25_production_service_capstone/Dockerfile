# Multi-stage build for the problem-25 capstone service.
#
# Build (run from this directory):
#   docker build -t task-service .
# Run:
#   docker run --rm -p 8000:8000 task-service
#
# Not built/run by this curriculum's verification loop (no Docker daemon
# in the pytest/mypy/ruff/black checks) - read this as you would a
# colleague's PR touching deploy config, not by executing it here.

# ---------------------------------------------------------------------------
# Stage 1: builder - installs dependencies into an isolated venv.
# Ships none of this stage's layers (compilers, pip's cache, build
# artifacts) into the final image.
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /build

# A venv (not a global site-packages install) makes "copy the installed
# packages into the final stage" a single, self-contained directory copy.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

# Only the runtime deps this service actually needs - not the whole
# curriculum's requirements.txt (mypy/black/ruff/hypothesis/pytest have no
# business in a production image).
RUN pip install --no-cache-dir \
    "fastapi==0.115.*" \
    "uvicorn[standard]==0.32.*" \
    "prometheus_client==0.21.*"

# ---------------------------------------------------------------------------
# Stage 2: final - slim runtime image, non-root user, just the venv + app.
# ---------------------------------------------------------------------------
FROM python:3.12-slim

# A dedicated, unprivileged user - never run the service process as root
# inside the container. Fixed uid/gid makes the image reproducible and
# lets an orchestrator's securityContext (e.g. Kubernetes runAsNonRoot,
# runAsUser) pin against a known value instead of guessing.
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid appuser --create-home --shell /usr/sbin/nologin appuser

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# The solution file's module name starts with a digit ("25_..."), which
# isn't a valid Python import target - copied in as app.py so the
# uvicorn entrypoint below can import it as a normal module, the same way
# the test suite works around the same constraint via importlib.
COPY 25_production_service_capstone_solution.py ./app.py

USER appuser

EXPOSE 8000

# create_app() is a factory (not a bare module-level `app`), so uvicorn's
# CLI needs the "module:factory()" form via --factory.
ENTRYPOINT ["uvicorn", "app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
