import os
from abc import ABC
from http import HTTPStatus
from flask import jsonify, make_response, Response

from dotenv import load_dotenv
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import NullPool

from src.logs import logger

load_dotenv()

db = SQLAlchemy()
ma = Marshmallow()


class Db_config(ABC):
    @staticmethod
    def get_db_con_uri():
        try:
            user: str = os.getenv('POSTGRES_USER')
            password: str = os.getenv('POSTGRES_PASSWORD')
            host: str = os.getenv('POSTGRES_HOST')
            port: str = os.getenv('POSTGRES_PORT')
            database: str = os.getenv('POSTGRES_DB')

            return f'postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}'
        except Exception as ex:
            msg = f'Error retrieving database connection URI: {str(ex)}'
            logger.exception(msg)
            return get_response(HTTPStatus.INTERNAL_SERVER_ERROR, msg)

    @staticmethod
    def create_default_db_engine(database_uri: str | None = None):
        try:
            if not database_uri:
                database_uri = Db_config.get_db_con_uri()
            return create_engine(database_uri, client_encoding='utf8', poolclass=NullPool)
        except SQLAlchemyError as ex:
            msg = f'Error creating database engine:  {str(ex)}'
            logger.exception(msg)
            return get_response(HTTPStatus.INTERNAL_SERVER_ERROR, msg)


def get_response(status_code: int, content: str | dict | list = None) -> Response:
    if isinstance(content, str):
        logger.info(content)
        content = {"message": content}

    return make_response(jsonify(content), status_code)
