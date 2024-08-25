from contextlib import closing
from datetime import datetime, timedelta
from http import HTTPStatus


from flask import request
from flask_restx import Resource
from flask_smorest import Blueprint
from flask_sqlalchemy.query import Query as BaseQuery
from pandas import DataFrame, isna, read_csv
from sqlalchemy.orm import Session
from sqlalchemy.sql import and_, func, or_, select
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


def calculate_average(query: BaseQuery, time_delta: datetime):
    now = datetime.now()

    if time_delta == timedelta(hours=24):
        start_time = now - timedelta(days=1)
    elif time_delta == timedelta(hours=48):
        start_time = now - timedelta(days=2)
    elif time_delta == timedelta(weeks=1):
        start_time = now - timedelta(weeks=1)
    elif time_delta == timedelta(days=30):
        start_time = now - timedelta(days=30)
    else:
        raise ValueError("Unsupported time_delta")

    start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
    end_time = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    filtered_query = query.filter(
        Equipment.timestamp >= start_time, Equipment.timestamp <= end_time)
    avg_value = filtered_query.with_entities(
        func.avg(Equipment.value)).scalar()
    return round(avg_value, 2) if avg_value is not None else None


@equipment_blueprint.route("/equipment")
class RouteEquipment(Resource):
    def get(self):
        try:
            column_name = request.args.get('column_name')
            filter_by = request.args.getlist('filter_by')
            query = db.session.query(Equipment)

            if column_name:
                dropdown_options = query_column(column_name, query)
                total_rows = len(dropdown_options)
                return get_response(HTTPStatus.OK, {
                    'dropdown_options': sorted(dropdown_options, key=lambda item: item['value']),
                    'total': total_rows
                })

            query = add_query_filters(query, filter_by)

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


def query_column(column_name: str, query: BaseQuery):
    with closing(configure_session()) as session:
        try:
            dropdown_options = []
            if column_name == 'equipmentId':
                equipments: list[Equipment] = (
                    query.with_entities(Equipment.equipmentId)
                    .filter(Equipment.value != None)
                    .distinct()
                    .order_by(Equipment.equipmentId)
                    .all()
                )

                for equipment in equipments:
                    equipment_id = equipment.equipmentId

                    equipment_query = db.session.query(Equipment).filter(
                        Equipment.equipmentId == equipment_id,
                        Equipment.value != None
                    )

                    last_24 = calculate_average(
                        equipment_query, timedelta(hours=24))
                    last_48 = calculate_average(
                        equipment_query, timedelta(hours=48))
                    last_week = calculate_average(
                        equipment_query, timedelta(weeks=1))
                    last_month = calculate_average(
                        equipment_query, timedelta(days=30))

                    dropdown_options.append({
                        'value': equipment_id,
                        'label': equipment_id,
                        'last_24': last_24,
                        'last_48': last_48,
                        'last_week': last_week,
                        'last_month': last_month,
                    })

                return dropdown_options
            else:
                equipments = query.distinct(db.Column(column_name)).all()

                for equipment in equipments:
                    value: str | datetime = getattr(equipment, column_name)
                    if value:
                        dictionary = {'label': value, 'value': value}
                        dropdown_options.append(dictionary)

                return dropdown_options

        except:
            msg = 'No able to get dropdown options. Rollback executed'
            session.rollback()
            logger.exception(msg)
            return get_response(HTTPStatus.INTERNAL_SERVER_ERROR, msg)


def add_query_filters(query: BaseQuery, filter_by: list) -> BaseQuery:
    equipment_id = request.args.get('equipmentId')
    timestamp = request.args.get('timestamp')
    value = request.args.get('value')

    if equipment_id:
        query = query.filter(
            Equipment.equipmentId == equipment_id,
            Equipment.value != None
        )

        now = datetime.now()

        if 'last_24' in filter_by:
            start_time = now - timedelta(days=1)
            start_time = start_time.replace(
                hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(Equipment.timestamp >= start_time)

        elif 'last_48' in filter_by:
            start_time = now - timedelta(days=2)
            start_time = start_time.replace(
                hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(Equipment.timestamp >= start_time)

        elif 'last_week' in filter_by:
            start_time = now - timedelta(weeks=1)
            start_time = start_time.replace(
                hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(Equipment.timestamp >= start_time)

        elif 'last_month' in filter_by:
            start_time = now - timedelta(days=30)
            start_time = start_time.replace(
                hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(Equipment.timestamp >= start_time)

    if timestamp:
        query = query.filter(Equipment.timestamp == timestamp)

    if value:
        query = query.filter(Equipment.value == value)

    return query
