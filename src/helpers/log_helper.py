from abc import ABC
from json import dumps


def get_log_request_info(request_data):
    user_agent = request_data.headers.get("User-Agent", None)
    request_info = {
        "method": request_data.method,
        "url": request_data.url,
        "user_agent": user_agent,
        "remote_addr": request_data.remote_addr,
        "args": request_data.args.to_dict(),
        "form": request_data.form.to_dict(),
    }
    return request_info


class LogHelper(ABC):

    @staticmethod
    def get_log_msg(msg, request_data=None):
        log_request_info = None
        if request_data is not None:
            log_request_info = get_log_request_info(request_data)

        log_msg = {"message": msg,
                   "request": log_request_info}
        return dumps(log_msg)
