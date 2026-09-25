FROM python:3.9-alpine
WORKDIR /code
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY app.py app.py
CMD ["flask", "run", "--host=0.0.0.0"]
