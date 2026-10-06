# The hosted guide: sign-in with Google or an emailed one-time code, Free / Base / Pro / Pro Max
# plans enforced on the server, per-user progress. Code runs only in the separate runner
# container (Dockerfile.runner) that compose.yaml starts next to it; alone, running is off.
#
#   make up                                    web + runner, via deploy/compose.yaml
#   docker build -f deploy/Dockerfile -t engineering-guide .           (or: make docker-build)
FROM python:3.12-slim
WORKDIR /app
COPY content ./content
COPY tools/problems.tsv ./tools/problems.tsv
COPY webapp/*.py ./webapp/
COPY webapp/static ./webapp/static
RUN groupadd --system --gid 10001 guide && useradd --system --uid 10001 --gid 10001 guide \
    && mkdir /data && chown guide:guide /data
USER guide
ENV EG_AUTH=1 \
    EG_HOST=0.0.0.0 \
    DSA_PORT=8080 \
    EG_AUTH_DB=/data/auth.sqlite3 \
    EG_TRUST_PROXY=1 \
    EG_NO_BROWSER=1 \
    PYTHONUNBUFFERED=1
VOLUME /data
EXPOSE 8080
CMD ["python3", "webapp/server.py"]
