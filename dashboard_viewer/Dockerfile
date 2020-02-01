FROM python:3.7.4-stretch

WORKDIR /app


COPY requirements.txt .

RUN pip install --upgrade pip setuptools \
 && pip install -r requirements.txt \
 && rm -rf /root/.cache/pip


RUN curl -sL https://deb.nodesource.com/setup_12.x | bash - && \
    apt-get update && apt-get install -y nodejs

COPY package.json .

RUN npm install


EXPOSE 8000

COPY . .

CMD ./docker-entrypoint.sh
