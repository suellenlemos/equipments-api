from datetime import datetime


from src.config import db, ma


class Equipment(db.Model):
    __tablename__ = 'equipment'

    id = db.Column(db.Integer, primary_key=True)
    equipmentId = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime(), nullable=False)
    value = db.Column(db.Float, nullable=True)

    __table_args__ = (
        db.UniqueConstraint('equipmentId', 'timestamp',
                            name='unique_equipment_timestamp'),
    )

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
