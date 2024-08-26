from datetime import datetime
from io import BytesIO
import pytz
from werkzeug.datastructures import FileStorage


from flask_testing import TestCase
from pandas import DataFrame
import pytest

from src.app import create_app
from src.config import db
from src.helpers import CurrentTime
from src.routers import standardize_equipment_id, load_columns
from src.models import Equipment


def test_standardize_equipment_id_valid():
    assert standardize_equipment_id('  ABC123  ') == 'ABC123'


def test_standardize_equipment_id_invalid():
    with pytest.raises(ValueError, match="A coluna equipmentId não está preenchida corretamente"):
        standardize_equipment_id('')


def test_load_columns_with_missing_column():
    df = DataFrame({'value': [50.55], 'timestamp': [
        '2023-02-12T01:30:00.000-05:00']})
    with pytest.raises(ValueError, match="As seguintes colunas estão faltando no arquivo: equipmentId"):
        load_columns(df, ['equipmentId', 'timestamp', 'value'])


def test_load_columns():
    df = DataFrame({
        'equipmentId': ['ABC123'],
        'timestamp': ['2023-02-12T01:30:00.000-05:00'],
        'value': [50.55]
    })
    header_list = ['equipmentId', 'timestamp', 'value']
    result, _ = load_columns(df, header_list)
    assert len(result) == 1
    assert result[0]['equipmentId'] == 'ABC123'


class TestEquipmentRoutes(TestCase):
    def create_app(self):
        app = create_app('testing')
        return app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_get_equipment_empty(self):
        response = self.client.get('/equipment')
        self.assert200(response)
        self.assertEqual(response.json['total'], 0)
        self.assertEqual(response.json['equipments'], [])
        self.assertEqual(response.json['message'], 'No equipment was found')

    def test_post_equipment_success(self):
        data = {
            'equipmentId': 'EQ-1',
            'value': 50.55
        }

        time_zone: str = 'Etc/GMT+3'

        timestamp_str = CurrentTime.current_time()

        timestamp = datetime.fromisoformat(timestamp_str)

        tz = pytz.timezone(time_zone)
        timestamp = timestamp.replace(tzinfo=pytz.utc)
        equipment_field = timestamp.astimezone(tz)

        response = self.client.post('/equipment', json=data)
        self.assertEqual(response.status_code, 201)

        equipment = db.session.get(Equipment, 'ABC123')
        self.assertIsNotNone(equipment)
        self.assertEqual(response.json['equipmentId'], 'ABC123')
        self.assertEqual(response.json['value'], 50.55)

        equipment_timestamp = equipment.timestamp.replace(
            tzinfo=pytz.utc).astimezone(tz)
        self.assertAlmostEqual(equipment_timestamp.timestamp(),
                               equipment_field.timestamp(), delta=1)

    def test_post_equipment_missing_field(self):
        data = {
            'value': 50.55
        }
        response = self.client.post('/equipment', json=data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json, {'message': 'equipmentId field must be sent'})

    def test_upload_file_success(self):
        df = DataFrame({
            'equipmentId': ['ABC123'],
            'timestamp': ['2023-02-12T01:30:00.000-05:00'],
            'value': [99.55]
        })

        file = BytesIO()
        df.to_csv(file, index=False, sep=';')
        file.seek(0)

        file_storage = FileStorage(
            stream=file, filename='test.csv', content_type='text/csv'
        )

        response = self.client.post(
            '/equipment/upload',
            content_type='multipart/form-data',
            data={'file': file_storage}
        )

        self.assertEqual(response.status_code, 200)

    def test_upload_file_missing_column(self):
        df = DataFrame({
            'timestamp': ['2023-02-12T01:30:00.000-05:00'],
            'value': [50.55]
        })
        file = BytesIO()
        df.to_csv(file, index=False, sep=';')
        file.seek(0)
        data = {
            'file': (file, 'test.csv')
        }
        response = self.client.post(
            '/equipment/upload', content_type='multipart/form-data', data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "As seguintes colunas estão faltando no arquivo: equipmentId", response.json['message'])

    def test_upload_file_with_empty_equipmentId(self):
        df = DataFrame({
            'equipmentId': None,
            'timestamp': ['2023-02-12T01:30:00.000-05:00'],
            'value': [50.55]
        })
        file = BytesIO()
        df.to_csv(file, index=False, sep=';')
        file.seek(0)
        data = {
            'file': (file, 'test.csv')
        }
        response = self.client.post(
            '/equipment/upload', content_type='multipart/form-data', data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "A coluna equipmentId não está preenchida corretamente (existe algum valor que está em branco, por exemplo).", response.json['message'])
