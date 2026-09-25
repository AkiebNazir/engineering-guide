# Hands-on API Gateway Lab: Kong with Rate Limiting

In this lab, you will set up a Kong API Gateway to route traffic to a backend service and apply a rate-limiting plugin.

## Setup

1. Run the `docker-compose.yml` to start Kong in DB-less mode.
2. The declarative configuration is provided in `kong.yml`.

### docker-compose.yml
```yaml
version: '3.8'
services:
  kong:
    image: kong:latest
    environment:
      KONG_DATABASE: "off"
      KONG_DECLARATIVE_CONFIG: /kong/declarative/kong.yml
      KONG_PROXY_ACCESS_LOG: /dev/stdout
      KONG_PROXY_ERROR_LOG: /dev/stderr
      KONG_PROXY_LISTEN: 0.0.0.0:8000
    ports:
      - "8000:8000"
    volumes:
      - ./kong.yml:/kong/declarative/kong.yml
```

### kong.yml
```yaml
_format_version: "2.1"
_transform: true

services:
  - name: example-service
    url: http://httpbin.org
    routes:
      - name: example-route
        paths:
          - /mock
    plugins:
      - name: rate-limiting
        config:
          minute: 5
          policy: local
```

## Instructions
1. Create the above `docker-compose.yml` and `kong.yml` in this directory.
2. Run `docker-compose up -d`.
3. Make 6 requests to `http://localhost:8000/mock/get`. The 6th request should fail with `429 Too Many Requests`.
