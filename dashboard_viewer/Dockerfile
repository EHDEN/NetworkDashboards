FROM python:3.7.4-stretch

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip setuptools \
 && pip install -r requirements.txt \
 && rm -rf /root/.cache/pip

EXPOSE 8000

COPY . .

CMD ./docker-entrypoint.sh
