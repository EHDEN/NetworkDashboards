FROM python:3.7.4-stretch

RUN apt-get update \
 && apt-get -y install vim

RUN alias ll="ls -al"

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip setuptools \
 && pip install -r requirements.txt \
 && rm -rf /root/.cache/pip

EXPOSE 8000

COPY . .

CMD ./docker-entrypoint.sh
