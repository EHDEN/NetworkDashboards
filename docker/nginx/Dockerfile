# https://github.com/komoot/superset-reverse-nginx-example/blob/master/nginx/Dockerfile
# source: https://testdriven.io/blog/dockerizing-django-with-postgres-gunicorn-and-nginx/

FROM nginx:1.17.2-alpine

RUN rm /etc/nginx/conf.d/default.conf

COPY nginx.conf /nginx.conf
COPY nginxSuffix.conf /nginxSuffix.conf
COPY setupURL.sh /setupURL.sh
