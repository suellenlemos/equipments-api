import os
from functools import wraps
from http import HTTPStatus

import jwt
from flask import request

from src.routers.helpers.responser import get_response
from src.logs import logger

PREFIX = 'Bearer'


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = read_token()
        if type(token) is not dict:
            return token
        return f(*args, **kwargs)

    return decorated


def read_token():
    token = None
    if 'Authorization' in request.headers:
        try:
            token = get_token(request.headers['Authorization'])
        except:
            return get_response(HTTPStatus.UNAUTHORIZED, "Token is invalid, please refresh it")

    if not token:
        return get_response(HTTPStatus.UNAUTHORIZED, "Token is missing.")

    try:
        data = jwt.decode(token, os.getenv(
            'JWT_CRYPT_KEY'), algorithms=["HS256"])
        logger.info(
            f"User id: {data['id']}, name: {data['fullname']}, action: {request.full_path}")
        return data

    except:
        return get_response(HTTPStatus.UNAUTHORIZED, "Token is invalid, please refresh it")


def get_token(header):
    bearer, _, token = header.partition(' ')
    if bearer != PREFIX:
        raise ValueError('Token is invalid, missing prefix Bearer')
    return token
