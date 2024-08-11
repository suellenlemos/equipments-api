import os

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from flask_smorest import Api

from src.routers import equipment_blueprint


basedir = os.path.dirname(os.path.realpath(__file__))

load_dotenv()


def create_app() -> Flask:
    app: Flask = Flask(__name__)

    app.config["API_TITLE"] = "Equipments REST API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

    return app


app: Flask = create_app()

api = Api(app)

api.register_blueprint(equipment_blueprint)

cors = CORS(app, resources=r'*', headers='Content-Type')
