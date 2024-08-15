from contextlib import closing
from datetime import datetime
from flask import request
from flask_restx import Resource
from flask_smorest import Blueprint
from flask_sqlalchemy.query import Query as BaseQuery
from http import HTTPStatus
from pandas import DataFrame, isna, read_csv
from sqlalchemy.orm import Session
from sqlalchemy.sql import and_, or_, select
from tempfile import TemporaryDirectory
from werkzeug.utils import secure_filename

from src.config import db
from src.helpers import CurrentTime, LogHelper
from src.logs import logger
from src.models import Equipment, EquipmentSchema
from src.routers.helpers import configure_session, get_response

equipment_blueprint = Blueprint("Equipment", __name__)


def normalize_timestamp(ts):
    if isinstance(ts, str):
        return datetime.fromisoformat(ts).replace(tzinfo=None)
    return ts.replace(tzinfo=None)


@equipment_blueprint.route("/equipment")
class RouteEquipment(Resource):
    def get(self):
        try:
            query = db.session.query(Equipment)

            result = get_rows_paginated(query)

            total_count = query.count()

            if not result:
                return get_response(HTTPStatus.OK, {'total': total_count,
                                                    'equipments': result,
                                                    'message': 'No equipment was found'})

            logger.info('get all equipments')

            return get_response(HTTPStatus.OK, {'total': total_count,
                                                'equipments': EquipmentSchema(many=True).dump(result),
                                                'message': 'Request happened successfully'})
        except Exception as ex:
            msg = f'Unable to get equipment list. Error: {str(ex)}'
            log_msg = LogHelper.get_log_msg(msg, request)
            logger.exception(log_msg)
            return get_response(HTTPStatus.INTERNAL_SERVER_ERROR, msg)

    def post(self):
        body = request.get_json() if request.get_json() else dict()

        equipmentId: str = body['equipmentId']
        value: float = body.get('value')

        if not (equipmentId):
            return get_response(HTTPStatus.BAD_REQUEST, "equipmentId field must be sent")

        new_equipment = Equipment(
            equipmentId=equipmentId,
            timestamp=CurrentTime.current_time(),
            value=value
        )

        db.session.add(new_equipment)
        db.session.commit()
        logger.info(f'Category created: {new_equipment}')
        return get_response(HTTPStatus.CREATED, EquipmentSchema().dump(new_equipment))


def get_rows_paginated(query: BaseQuery):
    page = int(request.args.get('page')) if request.args.get('page') else 1
    per_page = int(request.args.get('per_page')
                   ) if request.args.get('per_page') else 100

    result: Equipment = query.order_by(Equipment.equipmentId).paginate(
        page=page, per_page=per_page).items

    return result


@equipment_blueprint.route("/equipment/upload")
class RouteUploadEquipmentFile(Resource):
    def post(self):
        with closing(configure_session()) as session:
            try:
                read_file(session)
                session.commit()

                return get_response(HTTPStatus.OK, {
                    'message': 'File successfully uploaded and processed'})

            except Exception as ex:
                session.rollback()
                msg = f'Unable to upload file. Rollback executed. Error: {
                    str(ex)}'
                log_msg = LogHelper.get_log_msg(msg, request)
                logger.exception(log_msg)
                return get_response(HTTPStatus.BAD_REQUEST, msg)


def read_file(session: Session):
    if 'file' not in request.files:
        raise Exception(f"The file key 'file' must be sent")

    file_uploaded = request.files['file']

    filename = secure_filename(file_uploaded.filename)

    with TemporaryDirectory():
        temporary_path: str = f"src/temporary/{filename}"
        file_uploaded.save(temporary_path)

        try:
            workbook = read_csv(temporary_path, delimiter=';')
            add_equipment_info(session, workbook)

            logger.info(f"Extracted data from CSV file: '{
                        filename}' successfully"
                        )

        except TypeError as e:
            logger.error(f"Type error while processing file '{filename}': {e}")
            raise

        except Exception as e:
            msg = f"Error extracting data from file '{filename}': {str(e)}"
            logger.error(msg)
            raise Exception(msg)


def add_equipment_info(session: Session, workbook: DataFrame) -> None:
    header_list = {
        'equipmentId',
        'timestamp',
        'value',
    }

    relevant_columns_list, rows_by_equipment_id_and_timestamp = load_columns(
        workbook=workbook,
        header_list=header_list
    )

    modified_rows = []

    new_row = False

    for columns in relevant_columns_list:
        equipment_id = standardize_equipment_id(columns['equipmentId'])
        timestamp = normalize_timestamp(
            standardize_timestamp(columns['timestamp']))

        value: float = columns.get('value')
        if isna(value):
            value = None

        row_key = (equipment_id, timestamp)

        row: Equipment = rows_by_equipment_id_and_timestamp.get(row_key)

        if not row:
            session.add(Equipment(
                equipmentId=equipment_id,
                timestamp=timestamp,
                value=value
            ))
            new_row = True
        else:
            row.value = value
            modified_rows.append(row)

        if modified_rows or new_row:
            session.bulk_save_objects(modified_rows)
            session.commit()


def load_columns(workbook: DataFrame, header_list: set) -> list:
    logger.debug(
        f"Start time {datetime.today().strftime('%d/%m/%Y, %H:%M:%S')}")

    missing_columns = [
        col for col in header_list if col not in workbook.columns]
    if missing_columns:
        raise ValueError(f"As seguintes colunas estão faltando no arquivo: {
                         ', '.join(missing_columns)}"
                         )

    relevant_columns_df = workbook[list(header_list)].copy()

    relevant_columns_list = relevant_columns_df.to_dict(orient='records')

    equipment_ids_and_timestamps = [
        (standardize_equipment_id(row['equipmentId']),
         standardize_timestamp(row['timestamp']))
        for row in relevant_columns_list
        if row.get('equipmentId') is not None and row.get('timestamp') is not None
    ]

    with closing(configure_session()) as session:
        conditions = [
            and_(Equipment.equipmentId == equipment_id,
                 Equipment.timestamp == timestamp)
            for equipment_id, timestamp in equipment_ids_and_timestamps
        ]

        rows = session.execute(
            select(Equipment).where(or_(*conditions))
        ).scalars().all()

    rows_by_equipment_id_and_timestamp = {
        (row.equipmentId, row.timestamp): row for row in rows
    }

    logger.debug(f"End time {datetime.today().strftime('%d/%m/%Y, %H:%M:%S')}")

    return relevant_columns_list, rows_by_equipment_id_and_timestamp


def standardize_equipment_id(equipment_id: str) -> str:
    if isna(equipment_id):
        equipment_id = ''
    else:
        equipment_id = str(equipment_id)

    equipment_id = equipment_id.strip()
    if not equipment_id:
        raise ValueError(
            "A coluna equipmentId não está preenchida corretamente (existe algum valor que está em branco, por exemplo).")

    return equipment_id


def standardize_timestamp(timestamp: datetime) -> datetime:
    if isna(timestamp):
        timestamp = ''
    else:
        timestamp = timestamp

    timestamp = timestamp.strip()
    if not timestamp:
        raise ValueError(
            "A coluna timestamp não está preenchida corretamente (existe algum valor que está em branco, por exemplo).")

    return timestamp
