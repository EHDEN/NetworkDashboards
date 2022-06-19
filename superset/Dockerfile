# Based on https://github.com/apache/superset/blob/1.5.0/Dockerfile

######################################################################
# PY stage that simply does a pip install on our requirements
######################################################################
ARG PY_VER=3.8.12
FROM python:${PY_VER} AS superset-py

RUN mkdir /app \
        && apt-get update -y \
        && apt-get install -y --no-install-recommends \
            build-essential \
            default-libmysqlclient-dev \
            libpq-dev \
            libsasl2-dev \
            libecpg-dev \
        && rm -rf /var/lib/apt/lists/*

# First, we just wanna install requirements, which will allow us to utilize the cache
# in order to only build if and only if requirements change
COPY ./repo/requirements/*.txt  /app/requirements/
COPY repo/setup.py repo/MANIFEST.in repo/README.md /app/
COPY repo/superset-frontend/package.json /app/superset-frontend/
RUN cd /app \
    && mkdir -p superset/static \
    && touch superset/static/version_info.json \
    && pip install --no-cache -r requirements/local.txt


######################################################################
# Node stage to deal with static asset construction
######################################################################
FROM node:16 AS superset-node

ARG NPM_VER=7
RUN npm install -g npm@${NPM_VER}

ARG NPM_BUILD_CMD="build"
ENV BUILD_CMD=${NPM_BUILD_CMD}

# NPM ci first, as to NOT invalidate previous steps except for when package.json changes
RUN mkdir -p /app/superset-frontend
RUN mkdir -p /app/superset/assets
COPY ./repo/docker/frontend-mem-nag.sh /
COPY ./repo/superset-frontend/ /app/superset-frontend/

# Add our boxplot
COPY ./box-plot-overrides /app/superset-frontend/plugins/plugin-chart-echarts/
RUN rm -f /app/superset-frontend/plugins/plugin-chart-echarts/src/BoxPlot/controlPanel.ts

RUN /frontend-mem-nag.sh \
        && cd /app/superset-frontend \
        && npm ci

# This seems to be the most expensive step
RUN cd /app/superset-frontend \
        && npm run ${BUILD_CMD} \
        && rm -rf node_modules


######################################################################
# Final lean image...
######################################################################
ARG PY_VER=3.8.12
FROM python:${PY_VER} AS lean

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    FLASK_ENV=production \
    FLASK_APP="superset.app:create_app()" \
    PYTHONPATH="/app/pythonpath" \
    SUPERSET_HOME="/app/superset_home" \
    SUPERSET_PORT=8088

RUN mkdir -p ${PYTHONPATH} \
        && useradd --user-group -d ${SUPERSET_HOME} -m --no-log-init --shell /bin/bash superset \
        && apt-get update -y \
        && apt-get install -y --no-install-recommends \
            build-essential \
            default-libmysqlclient-dev \
            libsasl2-modules-gssapi-mit \
            libpq-dev \
            libecpg-dev \
        && rm -rf /var/lib/apt/lists/*

# Copying configs. No need for a volume
COPY ./repo/docker/pythonpath_dev/superset_config.py ./superset_config_docker.py /app/pythonpath_docker/

COPY --from=superset-py /usr/local/lib/python3.8/site-packages/ /usr/local/lib/python3.8/site-packages/
# Copying site-packages doesn't move the CLIs, so let's copy them one by one
COPY --from=superset-py /usr/local/bin/gunicorn /usr/local/bin/celery /usr/local/bin/flask /usr/bin/
COPY --from=superset-node /app/superset/static/assets /app/superset/static/assets
COPY --from=superset-node /app/superset-frontend /app/superset-frontend

## Lastly, let's install superset itself
COPY repo/superset /app/superset
COPY repo/setup.py repo/MANIFEST.in repo/README.md /app/
RUN cd /app \
        && chown -R superset:superset * \
        && pip install -e . \
        && flask fab babel-compile --target superset/translations

COPY ./repo/docker/run-server.sh /usr/bin/
# copy scripts to start containers to avoid volumes
COPY ./repo/docker/docker-bootstrap.sh ./repo/docker/docker-init.sh /app/docker/

RUN chmod a+x /usr/bin/run-server.sh

WORKDIR /app

USER superset

HEALTHCHECK CMD curl -f "http://localhost:$SUPERSET_PORT/health"

EXPOSE ${SUPERSET_PORT}

CMD /usr/bin/run-server.sh
