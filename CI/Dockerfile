FROM python:3.9.13-alpine
RUN apk update && apk add alpine-conf
RUN setup-timezone -z Canada/Pacific

EXPOSE 8000

EXPOSE 5432

RUN apk add postgresql

WORKDIR /src/app
COPY requirements.txt requirements.txt
COPY jobs jobs
COPY jobs_site jobs_site
COPY manage.py manage.py
COPY CI/run_docker.sh run_docker.sh
COPY CI/wait-for-postgres.sh wait-for-postgres.sh

RUN apk update && apk add python3-dev gcc libc-dev

RUN pip install --no-cache-dir -r requirements.txt


CMD ["./wait-for-postgres.sh", "./run_docker.sh"]
#CMD ["sh"]
