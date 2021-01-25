# Based on https://github.com/apache/superset/blob/1.0.0rc1/Dockerfile

######################################################################
# PY stage that simply does a pip install on our requirements
######################################################################
ARG PY_VER=3.7.9
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
FROM node:12 AS superset-node

ARG NPM_BUILD_CMD="build"
ENV BUILD_CMD=${NPM_BUILD_CMD}

# NPM ci first, as to NOT invalidate previous steps except for when package.json changes
RUN mkdir -p /app/superset-frontend
RUN mkdir -p /app/superset/assets
COPY ./repo/docker/frontend-mem-nag.sh /
COPY ./repo/superset-frontend/package* /app/superset-frontend/

COPY ./plugins/plugins /app/superset-frontend/plugins

RUN /frontend-mem-nag.sh \
        && cd /app/superset-frontend \
        && for f in $(ls /app/superset-frontend/plugins) ; do npm install --save plugins/$f ; done \
        && npm ci \
        && mkdir -p package_json_files \
        && cp package*.json package_json_files

# Next, copy in the rest and let webpack do its thing
COPY ./repo/superset-frontend /app/superset-frontend

COPY ./plugins/MainPreset.js /app/superset-frontend/src/visualizations/presets/MainPreset.js

# This is BY FAR the most expensive step (thanks Terser!)
RUN cd /app/superset-frontend \
        && mv package_json_files/* . \
        && npm run ${BUILD_CMD} \
        && rm -rf node_modules \
        && rmdir package_json_files


######################################################################
# Final lean image...
######################################################################
ARG PY_VER=3.7.9
FROM python:${PY_VER} AS lean

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    FLASK_ENV=production \
    FLASK_APP="superset.app:create_app()" \
    PYTHONPATH="/app/pythonpath" \
    SUPERSET_HOME="/app/superset_home" \
    SUPERSET_PORT=8080

RUN useradd --user-group --no-create-home --no-log-init --shell /bin/bash superset \
        && mkdir -p ${SUPERSET_HOME} ${PYTHONPATH} \
        && apt-get update -y \
        && apt-get install -y --no-install-recommends \
            build-essential \
            default-libmysqlclient-dev \
            libpq-dev \
        && rm -rf /var/lib/apt/lists/*

COPY --from=superset-py /usr/local/lib/python3.7/site-packages/ /usr/local/lib/python3.7/site-packages/
# Copying site-packages doesn't move the CLIs, so let's copy them one by one
COPY --from=superset-py /usr/local/bin/gunicorn /usr/local/bin/celery /usr/local/bin/flask /usr/bin/
COPY --from=superset-node /app/superset/static/assets /app/superset/static/assets
COPY --from=superset-node /app/superset-frontend /app/superset-frontend

## Lastly, let's install superset itself
COPY repo/superset /app/superset
COPY repo/setup.py repo/MANIFEST.in repo/README.md /app/
RUN cd /app \
        && chown -R superset:superset * \
        && pip install -e .

COPY ./repo/docker/docker-entrypoint.sh /usr/bin/

WORKDIR /app

USER superset

HEALTHCHECK CMD curl -f "http://localhost:$SUPERSET_PORT/health"

EXPOSE ${SUPERSET_PORT}

ENTRYPOINT ["/usr/bin/docker-entrypoint.sh"]
