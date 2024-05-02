from .extension import db


class Satellite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(12), unique=True)
    tle_date = db.Column(db.DateTime)
    tle_line1 = db.Column(db.String)
    tle_line2 = db.Column(db.String)

    passes = db.relationship('Pass', back_populates='satellite')


class Pass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    satellite_id = db.Column(db.Integer, db.ForeignKey('satellite.id'), nullable=False)

    satellite = db.relationship('Satellite', back_populates='passes')
    aos_time = db.Column(db.DateTime)
    los_time = db.Column(db.DateTime)
    max_elevation = db.Column(db.Float)
    sol_elevation = db.Column(db.Float)
    aos_azimuth = db.Column(db.Float)
    los_azimuth = db.Column(db.Float)
    rotations = db.relationship('RotationSchedule', back_populates='passage')


class RotationSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pass_id = db.Column(db.Integer, db.ForeignKey('pass.id'), nullable=False)

    azimuth = db.Column(db.Float)
    elevation = db.Column(db.Float)
    time = db.Column(db.DateTime)

    passage = db.relationship('Pass', back_populates='rotations')
