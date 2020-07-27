# Based on https://github.com/apache/incubator-superset/blob/0.37.0rc3/Dockerfile

######################################################################
# PY stage that simply does a pip install on our requirements
######################################################################
ARG PY_VER=3.6.9
FROM python:${PY_VER} AS superset-py

RUN mkdir /app \
        && apt-get update -y \
        && apt-get install -y --no-install-recommends \
            build-essential \
            default-libmysqlclient-dev \
            libpq-dev \
        && rm -rf /var/lib/apt/lists/*

# First, we just wanna install requirements, which will allow us to utilize the cache
# in order to only build if and only if requirements change
COPY ./requirements.txt ./docker/requirements-extra.txt /app/
RUN cd /app \
        && pip install --upgrade pip setuptools \
        && pip install --no-cache -r requirements.txt -r requirements-extra.txt


######################################################################
# Node stage to deal with static asset construction
######################################################################
FROM node:10-jessie AS superset-node

ARG NPM_BUILD_CMD="build"
ENV BUILD_CMD=${NPM_BUILD_CMD}

# NPM ci first, as to NOT invalidate previous steps except for when package.json changes
RUN mkdir -p /app/superset-frontend
RUN mkdir -p /app/superset/assets
COPY ./docker/frontend-mem-nag.sh /
COPY ./superset-frontend/package* /app/superset-frontend/
RUN /frontend-mem-nag.sh \
        && cd /app/superset-frontend \
        && npm ci

# Next, copy in the rest and let webpack do its thing
COPY ./superset-frontend /app/superset-frontend
# This is BY FAR the most expensive step (thanks Terser!)
RUN cd /app/superset-frontend \
        && npm run ${BUILD_CMD} \
        && rm -rf node_modules


######################################################################
# Final lean image...
######################################################################
ARG PY_VER=3.6.9
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

COPY --from=superset-py /usr/local/lib/python3.6/site-packages/ /usr/local/lib/python3.6/site-packages/
# Copying site-packages doesn't move the CLIs, so let's copy them one by one
COPY --from=superset-py /usr/local/bin/gunicorn /usr/local/bin/celery /usr/local/bin/flask /usr/bin/
COPY --from=superset-node /app/superset/static/assets /app/superset/static/assets
COPY --from=superset-node /app/superset-frontend /app/superset-frontend

## Lastly, let's install superset itself
COPY superset /app/superset
COPY setup.py MANIFEST.in README.md /app/
RUN cd /app \
        && chown -R superset:superset * \
        && pip install -e .

COPY ./docker/docker-entrypoint.sh /usr/bin/

WORKDIR /app

USER superset

HEALTHCHECK CMD ["curl", "-f", "http://localhost:8088/health"]

EXPOSE ${SUPERSET_PORT}

ENTRYPOINT ["/usr/bin/docker-entrypoint.sh"]
