# Import a lighter version of python
FROM python:3.9-slim

WORKDIR /app

ENV PYTHONUNBUFFERED True

RUN apt-get update \
    && apt-get -y install libpq-dev gcc 
RUN mkdir -p src/category_crypto
RUN mkdir -p src/global_crypto
RUN mkdir -p src/defillama

COPY src/category_crypto ./src/category_crypto
COPY src/global_crypto ./src/global_crypto
COPY src/db_credentials.py ./src
copy src/defillama ./src/defillama

COPY app.py .
COPY requirements_prod.txt .

RUN pip install -r requirements_prod.txt 

# ENTRYPOINT ["python", "app.py"]
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app 
# app:app
# first app is app.py
# second app the name of the flask function