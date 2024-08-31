FROM python:3.12.5-alpine

ENV APP_PATH=/app
ENV APP_SRC_PATH=$APP_PATH/src
ENV VIRTUAL_ENV=$APP_PATH/venv

RUN apk update && apk upgrade

RUN apk update && apk add --no-cache \
    linux-headers g++ postgresql-dev gcc build-base ca-certificates \
    python3-dev libffi-dev openssl-dev libxslt-dev

RUN pip install --upgrade pip

RUN pip wheel --wheel-dir=/root/wheels psycopg2

RUN pip wheel --wheel-dir=/root/wheels cryptography

RUN mkdir -p $APP_PATH
RUN mkdir -p $APP_SRC_PATH

RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY /src $APP_SRC_PATH
COPY /main.py $APP_PATH

RUN pip install --no-cache-dir -r $APP_SRC_PATH/requirements.txt

WORKDIR $APP_PATH

EXPOSE 8080

CMD uwsgi --ini $APP_SRC_PATH/config/app.ini
