# Exercise 01: Containerizing a Python Application 🐳

## 🎯 Objective
Write a basic, optimized Dockerfile for a Python web application, demonstrating layer caching and non-root user security.

## 📋 Prerequisites
- Basic understanding of Python and pip.
- Docker concepts from the README.

## 📝 Instructions

Imagine you have a simple Flask application structure:
```text
myapp/
├── src/
│   └── app.py
└── requirements.txt
```

Your goal is to write the `Dockerfile` to containerize this app.

1. Create a `Dockerfile`.
2. Start with the `python:3.11-slim` base image.
3. Create a non-root user named `appuser`.
4. Set the working directory to `/app`.
5. Copy *only* the `requirements.txt` file first.
6. Run `pip install --no-cache-dir -r requirements.txt`.
7. Copy the rest of the application code into `/app`.
8. Ensure `appuser` owns the files.
9. Switch to `appuser` using the `USER` instruction.
10. Expose port `5000`.
11. Set the default command to run `python src/app.py`.

## 💡 Hints
- Remember that copying `requirements.txt` *before* the source code is critical for leveraging Docker's layer cache. If `app.py` changes but `requirements.txt` doesn't, Docker skips the `pip install` step on rebuild!
- Use `useradd` to create the user.

## ✅ Expected Output / Solution

```dockerfile
# 1. Base Image
FROM python:3.11-slim

# 2. Create non-root user for security
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# 3. Set Working Directory
WORKDIR /app

# 4. Cache dependencies layer! 
# We copy this BEFORE the source code.
COPY requirements.txt .

# 5. Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy application code
COPY src/ ./src/

# 7. Set ownership
RUN chown -R appuser:appgroup /app

# 8. Switch to non-root user
USER appuser

# 9. Document exposed port
EXPOSE 5000

# 10. Start command
CMD ["python", "src/app.py"]
```

## 🧠 Key Takeaway
By copying dependency files separately before the application code, you optimize the Docker layer cache, making subsequent CI builds significantly faster. Running as a non-root user drastically reduces the security risk if the container is compromised.
