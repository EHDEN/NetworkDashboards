FROM python:3.7.4-stretch

WORKDIR /app

COPY . /app

RUN pip install --upgrade pip setuptools \
 && pip install -r requirements.txt

EXPOSE 8000

CMD python manage.py runserver 0.0.0.0:8000
