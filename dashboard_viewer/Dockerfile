FROM python:3.8.6

# Install Debian packages
RUN curl -sL https://deb.nodesource.com/setup_12.x | bash - && \
    apt-get install -y nodejs wait-for-it && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Node packages
COPY package.json .

RUN npm install

# Install Python packages
COPY requirements.txt .

RUN pip install --upgrade pip setuptools \
 && pip install -r requirements.txt \
 && rm -rf /root/.cache/pip

EXPOSE 8000

COPY . .

CMD ./docker-entrypoint.sh
