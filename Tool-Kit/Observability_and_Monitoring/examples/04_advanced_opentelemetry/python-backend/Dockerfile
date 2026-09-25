FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
# Install auto-instrumentation for Flask
RUN opentelemetry-bootstrap -a install
COPY app.py .
# Wrap the flask run command with opentelemetry-instrument
CMD ["opentelemetry-instrument", "flask", "run", "--host=0.0.0.0"]
