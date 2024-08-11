from http import HTTPStatus

from contextlib import closing
from flask import request
from flask_restx import Resource
from flask_smorest import Blueprint

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
                    .order_by(Equipment.timestamp) \
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
