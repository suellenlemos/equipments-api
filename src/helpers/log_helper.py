from abc import ABC
from json import dumps
from os import getenv

import jwt


def get_log_request_info(request_data):
    user_agent = request_data.headers.get("User-Agent", None)
    request_info = {
        "method": request_data.method,
        "url": request_data.url,
        "user": get_request_user(request_data),
        "user_agent": user_agent,
        "remote_addr": request_data.remote_addr,
        "args": request_data.args.to_dict(),
        "form": request_data.form.to_dict(),
    }
    return request_info


def get_request_user(request_data):
    token = request_data.headers.get('Authorization', '').split(" ")[-1]

    if token:
        try:
            data = jwt.decode(token, getenv(
                'JWT_CRYPT_KEY'), algorithms=["HS256"])
            return data
        except Exception as ex:
            return {'error': "Token inválido", 'exception': f'{ex}'}
    return {'error': "Token inexistente"}


class LogHelper(ABC):

    @staticmethod
    def get_log_msg(msg, request_data=None):
        log_request_info = None
        if request_data is not None:
            log_request_info = get_log_request_info(request_data)

        log_msg = {"message": msg,
                   "request": log_request_info}
        return dumps(log_msg)
