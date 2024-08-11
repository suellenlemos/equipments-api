from datetime import datetime

from pytz import timezone, utc

from src.config import db, ma
from src.logs import logger


class Equipment(db.Model):
    __tablename__ = 'equipment'

    equipmentId = db.Column(db.String(255), primary_key=True)
    timestamp = db.Column(db.DateTime())
    value = db.Column(db.Float)

    def __init__(
            self,
            equipmentId: str,
            timestamp: datetime,
            value: float,
    ):
        self.equipmentId = equipmentId
        self.timestamp = timestamp
        self.value = value


class EquipmentSchema(ma.Schema):
    class Meta:
        model = Equipment
        fields = ("equipmentId", "timestamp", "value")

    timestamp = ma.Method("get_timestamp_another_timezone")

    def get_timestamp_another_timezone(self, equipment: Equipment) -> str:
        return self.convert_gmt_to_another_timezone(equipment.timestamp)

    def convert_gmt_to_another_timezone(self, equipment_field: datetime, time_zone: str = 'Etc/GMT+3') -> str:
        date_formats = ['%Y-%m-%d %H:%M:%S.%f',
                        '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f']

        equipment_field = equipment_field.replace(tzinfo=utc)

        for format in date_formats:
            try:
                return equipment_field.astimezone(timezone(time_zone)).strftime(format)
            except:
                pass

        error_message = f"date format not supported: {equipment_field}"
        logger.exception(error_message)
        raise Exception(error_message)
