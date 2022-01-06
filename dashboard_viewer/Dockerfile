FROM python:3.9.8

# Install Debian packages
RUN curl -sL https://deb.nodesource.com/setup_14.x | bash - && \
    apt-get install -y nodejs wait-for-it && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Node packages
COPY package.json .

RUN npm install

# Install Python packages
COPY requirements.txt .

RUN pip install --no-cache --upgrade pip setuptools \
 && pip install --no-cache -r requirements.txt

EXPOSE 8000

COPY . .

CMD ./docker-entrypoint.sh
