from datetime import datetime
from pytz import timezone


class CurrentTime():

    @staticmethod
    def current_time(tmz: str = 'Etc/GMT+0') -> datetime:
        format = "%Y-%m-%d %H:%M:%S.%f"
        return datetime.now(timezone(tmz)).strftime(format)

    @staticmethod
    def current_time_concatenated(tmz: str = 'Etc/GMT+0') -> str:
        format = "%d-%m-%Y-%H-%M-%S"
        return datetime.now(timezone(tmz)).strftime(format)

    @staticmethod
    def get_time(date: datetime, tmz: str = 'Etc/GMT+0') -> datetime:
        format = "%Y-%m-%d %H:%M:%S.%f"
        return date.astimezone(timezone(tmz)).strftime(format)

    @staticmethod
    def current_year() -> int:
        return int(datetime.today().strftime("%Y"))

    @staticmethod
    def get_today_as_datetime() -> datetime:
        return datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
