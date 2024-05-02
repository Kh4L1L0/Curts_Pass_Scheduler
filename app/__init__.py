from flask import Flask
from .pass_calculator import fetch_and_update_tle, calculate_passes_for_all_satellites
from datetime import datetime, timedelta

from .extension import api, db, scheduler
from .resources import ns
from .models import Satellite


def create_app():
    app = Flask(__name__)

    # Config DataBase instance
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///passScheduler.sqlite3'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SCHEDULER_API_ENABLED'] = False

    api.init_app(app)
    db.init_app(app)
    api.add_namespace(ns)
    scheduler.init_app(app)
    scheduler.start()

    #scheduler.add_job(id='Fetch and Update TLE', func=fetch_and_update_tle, args=[app, [25544, 42828]], trigger='date', run_date=datetime.utcnow() + timedelta(hours=1, seconds=5))
    scheduler.add_job(id='Calculate Passes', func=calculate_passes_for_all_satellites, args=[app], trigger='date', run_date=datetime.utcnow() + timedelta(hours=1, seconds=10))

    return app
