from abc import ABC


class ContextHelper(ABC):

    @staticmethod
    def is_running_inside_wsgi() -> bool:
        try:
            import uwsgi
            return True
        except ImportError:
            return False
