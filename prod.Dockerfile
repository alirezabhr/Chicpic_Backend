FROM python:3.11.4-slim-buster

WORKDIR /app

# Preventing python from writing pyc to docker container
ENV PYTHONDONTWRITEBYTECODE 1

# Flushing out python buffer
ENV PYTHONUNBUFFERED 1

COPY ./requirements ./requirements
RUN pip install --no-cache-dir -r requirements/production.txt

COPY . .

RUN apt-get update
RUN apt-get install -y netcat

RUN chmod +x ./entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]