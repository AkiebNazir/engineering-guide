# The static site in an nginx container: runs on any container platform
# (Cloud Run, AWS App Runner / ECS, Azure Container Apps, Fly.io, Render, Kubernetes…).
#
#   docker build -f deploy/Dockerfile -t engineering-guide .     (or: make docker-build)
#   docker run --rm -p 8080:8080 engineering-guide               (or: make docker-run)

# 1. Build: render every page's data to static files (standard library only).
FROM python:3.12-slim AS build
WORKDIR /src
COPY . .
RUN python3 webapp/build_static.py --out /site

# 2. Serve: plain nginx, listening on 8080.
FROM nginx:1.27-alpine
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /site /usr/share/nginx/html
EXPOSE 8080
