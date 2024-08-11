import os

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from flask_smorest import Api

from src.config import Db_config, db, ma
import src.models
from src.helpers import EnvVarsTranslater
from src.routers import equipment_blueprint


basedir = os.path.dirname(os.path.realpath(__file__))

load_dotenv()

cors = CORS()


def create_app() -> Flask:
    app: Flask = Flask(__name__)

    app.config["API_TITLE"] = "Equipments REST API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

    app.config['SQLALCHEMY_DATABASE_URI'] = Db_config.get_db_con_uri()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv(
        'SQLALCHEMY_TRACK_MODIFICATIONS')
    app.config['SQLALCHEMY_ECHO'] = EnvVarsTranslater.get_bool(
        'SQLALCHEMY_SHOW_QUERY_LOGS')

    db.init_app(app)
    ma.init_app(app)

    api = Api(app)

    cors.init_app(app, resources=r'*', headers='Content-Type')

    with app.app_context():
        if EnvVarsTranslater.get_bool("SQLALCHEMY_AUTO_CREATE_TABLES"):
            db.create_all()
            db.session.commit()

    api.register_blueprint(equipment_blueprint)

    return app


app: Flask = create_app()
