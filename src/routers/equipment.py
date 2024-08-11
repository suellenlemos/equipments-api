from contextlib import closing
from flask import request
from flask_restx import Resource
from flask_smorest import Blueprint
from http import HTTPStatus

from src.config import db
from src.helpers import LogHelper
from src.logs import logger
from src.models import Equipment, EquipmentSchema
from src.routers.helpers import configure_session, get_response

equipment_blueprint = Blueprint("Equipment", __name__)


@equipment_blueprint.route("/equipment")
class RouteEquipment(Resource):
    def get(self):
        with closing(configure_session()) as session:
            try:
                result = session.query(Equipment)\
                    .order_by(Equipment.equipmentId) \
                    .all()

                total_count = len(result)

                if not result:
                    return get_response(HTTPStatus.OK, {'total': total_count,
                                                        'equipments': result,
                                                        'message': 'No equipment was found'})

                logger.info('get all equipments')

                return get_response(HTTPStatus.OK, {'total': total_count,
                                                    'equipments': EquipmentSchema(many=True).dump(result),
                                                    'message': 'Request happened successfully'})
            except Exception as ex:
                session.rollback()
                msg = f'Unable to get equipment list. Error: {str(ex)}'
                log_msg = LogHelper.get_log_msg(msg, request)
                logger.exception(log_msg)
                return get_response(HTTPStatus.INTERNAL_SERVER_ERROR, msg)

    def post(self):
        body = request.get_json() if request.get_json() else dict()

        equipmentId: str = body.get('equipmentId')
        value: float = body.get('value')

        if not (equipmentId):
            return get_response(HTTPStatus.BAD_REQUEST, "equipmentId field must be sent")

        new_equipment = Equipment(
            equipmentId=equipmentId,
            value=value
        )

        equipment_already_exists = db.session.query(
            Equipment).filter(Equipment.equipmentId == new_equipment.equipmentId).first()

        if equipment_already_exists:
            return get_response(HTTPStatus.BAD_REQUEST, f"This equipment {equipment_already_exists.equipmentId.capitalize()} already exists")

        db.session.add(new_equipment)
        db.session.commit()
        logger.info(f'Category created: {new_equipment}')
        return get_response(HTTPStatus.CREATED, EquipmentSchema().dump(new_equipment))
