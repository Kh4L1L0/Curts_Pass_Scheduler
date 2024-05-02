from flask_sqlalchemy import SQLAlchemy
from flask_restx import Api
from flask_apscheduler import APScheduler

api = Api()
db = SQLAlchemy()
scheduler = APScheduler()