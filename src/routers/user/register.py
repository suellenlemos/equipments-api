from http import HTTPStatus

from flask import request
from flask_restx import Resource
from flask_smorest import Blueprint

from src.config import db
from src.logs import logger
from src.models import User, UserSchema

from src.routers.helpers import get_response


register_blueprint = Blueprint("Register", __name__)


@register_blueprint.route('/register')
class RouteRegister(Resource):
    def post(self):
        body = request.get_json() if request.get_json() else dict()

        email: str = body.get('email')
        password: str = body.get('password')
        fullname: str = body.get('fullname')

        if not (email):
            return get_response(HTTPStatus.BAD_REQUEST, "The e-mail field must be sent")
        if not (password):
            return get_response(HTTPStatus.BAD_REQUEST, "The password field must be sent")
        if not (fullname):
            return get_response(HTTPStatus.BAD_REQUEST, "The fullname field must be sent")

        user = User(
            email=email,
            pwd=password,
            fullname=fullname,
        )

        email_already_exists = db.session.query(User) \
            .filter(User.email == user.email) \
            .filter(User.activated) \
            .first()

        if email_already_exists:
            return get_response(HTTPStatus.BAD_REQUEST, f'The email you entered is already in use. Please try logging in.')

        db.session.add(user)
        db.session.commit()
        logger.info(f'User created: {body}')
        return UserSchema().dump(user), HTTPStatus.CREATED
