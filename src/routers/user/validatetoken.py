from http import HTTPStatus
from flask import make_response, jsonify
from flask_restx import Resource
from flask_smorest import Blueprint

from src.logs import logger
from src.routers.helpers import token_required


validate_token_blueprint = Blueprint("Validate Token", __name__)


@validate_token_blueprint.route('/validatetoken')
class RouteValidateToken(Resource):
    @token_required
    def get(self):
        message = 'Token is valid'
        logger.info('check if token is valid')
        return make_response(jsonify({
            'Message': message
        }), HTTPStatus.ACCEPTED)
