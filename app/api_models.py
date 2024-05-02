from flask_restx import fields, Namespace

from .extension import api


rotation_model = api.model('Rotation', {
    'id': fields.Integer(),
    'azimuth': fields.Float(),
    'elevation': fields.Float(),
    'time': fields.DateTime()
})

pass_model = api.model('Pass', {
    'id': fields.Integer(),
    'aos_time': fields.DateTime(),
    'los_time': fields.DateTime(),
    'max_elevation': fields.Float(),
    'sol_elevation': fields.Float(),
    'aos_azimuth': fields.Float(),
    'los_azimuth': fields.Float(),
    'rotations': fields.List(fields.Nested(rotation_model))
})

satellite_model = api.model('Satellite', {
    'id': fields.Integer(),
    'name': fields.String(),
    'tle_date': fields.DateTime(),
    'tle_line1': fields.String(),
    'tle_line2': fields.String(),
    'passes': fields.List(fields.Nested(pass_model)),
})