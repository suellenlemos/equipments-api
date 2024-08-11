from flask_restx import Resource
from flask_smorest import Blueprint
from http import HTTPStatus

from src.routers.helpers import get_response

equipment_blueprint = Blueprint("Equipment", __name__)


equipments = [
    {
        "equipmentId": "EQ-12495",
        "timestamp": "2023-02-15T01:30:00.000-05:00",
        "value": 78.42
    },
    {
        "equipmentId": "EQ-12492",
        "timestamp": "2023-01-12T01:30:00.000-05:00",
        "value": 8.8
    }
]


@equipment_blueprint.route("/equipment")
class RouteEquipment(Resource):
    def get(self):
        try:
            result = equipments

            if not result:
                return get_response(HTTPStatus.NO_CONTENT)

            return get_response(HTTPStatus.OK, {'total': len(result),
                                                'equipments': equipments,
                                                'message': 'Request happened successfully'})
        except Exception as ex:
            msg = f'Unable to get equipment list. Error: {str(ex)}'
            return get_response(HTTPStatus.INTERNAL_SERVER_ERROR, msg)
