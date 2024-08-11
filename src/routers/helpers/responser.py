from flask import jsonify, make_response, Response


def get_response(status_code: int, content: str | dict | list = None) -> Response:
    if isinstance(content, str):
        content = {"message": content}
    elif isinstance(content, Response):
        return make_response(content, status_code)

    return make_response(jsonify(content), status_code)
