from flask_restx import Resource, Namespace, fields
from flask import current_app
from datetime import datetime

from .api_models import satellite_model, pass_model, rotation_model
from .models import Satellite, Pass, RotationSchedule
from .schedule_rotator import prepare_next_pass_rotation, scheduler_rotator

ns = Namespace('api')


@ns.route('/hello')
class HelloWorld(Resource):
    def get(self):
        return {'hello': 'hey'}


@ns.route('/Satellites')
class SatellitesListAPI(Resource):
    @ns.marshal_list_with(satellite_model)
    def get(self):
        return Satellite.query.all()

@ns.route('/Satellites/<int:id>')
class SatellitesAPI(Resource):
    def post(self, id):
        current_time = datetime.now()
        prepare_next_pass_rotation(current_app, current_time, id)
        scheduler_rotator(current_app, id)
        return {'message': 'schedule change to {}'.format(id)}

@ns.route('/Passes')
class SatellitesListAPI(Resource):
    @ns.marshal_list_with(pass_model)
    def get(self):
        return Pass.query.all()
