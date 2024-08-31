import os
import jwt

from contextlib import closing
from datetime import datetime, timedelta
from dotenv import load_dotenv
from http import HTTPStatus
from flask import request, make_response, jsonify
from flask_restx import Resource
from flask_smorest import Blueprint
from pytz import timezone

from src.helpers import LogHelper
from src.logs import logger
from src.models import User, UserSchema
from src.routers.helpers import get_response, configure_session

load_dotenv()

login_blueprint = Blueprint("Login", __name__)


@login_blueprint.route('/login')
class Login(Resource):
    @staticmethod
    def post():
        body = request.get_json() if request.get_json() else dict()

        email: str = body.get('email')
        password: str = body.get('password')

        if not (email):
            return get_response(HTTPStatus.BAD_REQUEST, "The e-mail field must be sent")
        if not (password):
            return get_response(HTTPStatus.BAD_REQUEST, "The password field must be sent")

        with closing(configure_session()) as session:

            user: User = session.query(User) \
                .filter(User.email == email) \
                .filter(User.activated) \
                .first()

            if not user or not User.verify_password(user, pwd=password):
                return get_response(HTTPStatus.FORBIDDEN, "Email or password is incorrect")

            time_zone: str = 'Etc/GMT+3'

            token = jwt.encode({
                'id': user.id,
                'fullname': user.fullname,
                'exp': datetime.now(timezone(time_zone)) + timedelta(minutes=int(os.getenv('JWT_TOKEN_TIMEOUT_MINS')))
            }, os.getenv('JWT_CRYPT_KEY'),  algorithm="HS256")

            logger.info(
                f"{user.fullname} logged in successfully")

            return make_response(jsonify({
                'token': token,
                "user": UserSchema().dump(user)
            }), HTTPStatus.ACCEPTED)
