# Exercise 03: Docker Compose Integration Testing 🐳🤝🐘

## 🎯 Objective
Create a `docker-compose.yml` file to spin up your application and a PostgreSQL database simultaneously for local CI testing.

## 📋 Prerequisites
- Knowledge of Docker Compose syntax (YAML).
- Understanding of networking between containers.

## 📝 Instructions

You are setting up local integration tests. Your app needs to connect to Postgres. 
Your app builds from the local directory (`.`).

1. Create a `docker-compose.yml` file.
2. Define a service named `api`:
   - Set it to build from the current context (`.`).
   - Map host port `8080` to container port `8080`.
   - Add an environment variable `DB_URL=postgres://user:pass@database:5432/mydb`.
   - Make it depend on the database service.
3. Define a service named `database`:
   - Use the `postgres:15-alpine` image.
   - Set environment variables to create a database (`POSTGRES_DB=mydb`), user (`POSTGRES_USER=user`), and password (`POSTGRES_PASSWORD=pass`).
   - Expose port `5432`.
   - Add a named volume called `pgdata` mapped to `/var/lib/postgresql/data`.
4. Define the named volume `pgdata` at the root level of the Compose file.

## 💡 Hints
- Services in the same docker-compose file can communicate using their service names as hostnames (e.g., the API connects to host `database`).
- The `depends_on` block ensures the database container starts before the API container.

## ✅ Expected Output / Solution

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8080:8080"
    environment:
      # Notice the hostname is 'database', matching the service name below
      - DB_URL=postgres://user:pass@database:5432/mydb
    depends_on:
      - database

  database:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=mydb
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

## 🧠 Key Takeaway
Docker Compose provides a reproducible way to stand up complex, multi-service environments. In a CI pipeline, you can run `docker-compose up -d` to start the app and database, run your integration tests against localhost:8080, and then `docker-compose down` to cleanly tear everything down.
