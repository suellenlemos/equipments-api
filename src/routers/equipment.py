from contextlib import closing
from datetime import datetime
from flask import request
from flask_restx import Resource
from flask_smorest import Blueprint
from flask_sqlalchemy.query import Query as BaseQuery
from http import HTTPStatus
from os import path
from pandas import DataFrame, isna, read_csv
from sqlalchemy.orm import Session
from sqlalchemy.sql import select
from tempfile import TemporaryDirectory
from werkzeug.utils import secure_filename

from src.config import db
from src.helpers import CurrentTime, LogHelper
from src.logs import logger
from src.models import Equipment, EquipmentSchema
from src.routers.helpers import configure_session, get_response

equipment_blueprint = Blueprint("Equipment", __name__)


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

        equipmentId: str = body.get('equipmentId')
        value: float = body.get('value')

        if not (equipmentId):
            return get_response(HTTPStatus.BAD_REQUEST, "equipmentId field must be sent")

        new_equipment = Equipment(
            equipmentId=equipmentId,
            timestamp=CurrentTime.current_time(),
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

    with TemporaryDirectory() as dir_path:
        temporary_path: str = f"src/temporary/{filename}"
        file_path = path.join(dir_path, filename)
        file_uploaded.save(temporary_path)

        try:
            workbook = read_csv(temporary_path, delimiter=';')
            create_equipment(session, workbook)

            logger.info(
                logger.info(f"Extracted data from CSV file: '{filename}' successfully"))

        except TypeError as e:
            logger.error(f"Type error while processing file '{filename}': {e}")
            raise

        except Exception as e:
            msg = f"Error extracting data from file '{filename}': {str(e)}"
            logger.error(msg)
            raise Exception(msg)


def create_equipment(session: Session, workbook: DataFrame) -> None:
    header_list = {
        'equipmentId',
        'timestamp',
        'value',
    }

    relevant_columns_list, rows_by_equipment_id = load_columns(
        workbook=workbook,
        header_list=header_list,
        equipment_id='equipmentId'
    )

    modified_rows = []

    new_row = False

    for columns in relevant_columns_list:
        equipment_id = standardize_equipment_id(columns.get('equipmentId'))

        row: Equipment = rows_by_equipment_id.get(equipment_id)

        if not row:
            session.add(Equipment(
                equipmentId=equipment_id,
                timestamp=columns.get('timestamp'),
                value=columns.get('value'),
            ))
            new_row = True
        else:
            row.timestamp = columns.get('timestamp'),
            row.value = columns.get('value'),
            modified_rows.append(row)

        if modified_rows or new_row:
            session.bulk_save_objects(modified_rows)
            session.commit()


def load_columns(workbook: DataFrame, header_list: list, equipment_id: str = 'equipmentId') -> list:
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

    equipment_ids = []
    for columns in relevant_columns_list:
        if columns.get(equipment_id) is not None:
            standardized_equipment_id = standardize_equipment_id(
                columns.get(equipment_id))
            equipment_ids.append(standardized_equipment_id)
        elif all(value is None for value in columns.values()):
            break

    with closing(configure_session()) as session:
        rows = session.execute(
            select(Equipment)
            .where(Equipment.equipmentId.in_(equipment_ids))
        ).scalars().all()

    rows_by_equipment_id = {row.equipmentId: row for row in rows}

    logger.debug(f"End time {datetime.today().strftime('%d/%m/%Y, %H:%M:%S')}")

    return relevant_columns_list, rows_by_equipment_id


def standardize_equipment_id(equipment_id: str) -> str:
    if isna(equipment_id):
        equipment_id = ''
    else:
        equipment_id = str(equipment_id)

    equipment_id = equipment_id.strip()
    if not equipment_id:
        raise ValueError(
            "A coluna equipmentId não está preenchida corretamente (o valor está em branco, por exemplo).")

    return equipment_id
