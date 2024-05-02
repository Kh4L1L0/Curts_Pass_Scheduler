import json

import requests
from datetime import datetime, timedelta
from skyfield.api import Topos, load, EarthSatellite
from suncalc import get_position

from ..models import Satellite, Pass, RotationSchedule
from ..extension import api, db, scheduler
from ..schedule_rotator import prepare_next_pass_rotation, scheduler_rotator


def load_ground_station_from_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        ground_station = data['ground_station']
        return ground_station


def fetch_and_update_tle(current_app, satellites_id):
    for satellite_id in satellites_id:
        url = f"https://tle.ivanstanojevic.me/api/tle/{satellite_id}"
        response = requests.get(url)
        tle_data = response.json()

        with current_app.app_context():
            satellite = Satellite.query.filter_by(id=satellite_id).first()
            if not satellite:
                satellite = Satellite(
                    id=tle_data['satelliteId'],
                    name=tle_data['name'],
                    tle_date=datetime.fromisoformat(tle_data['date']),
                    tle_line1=tle_data['line1'],
                    tle_line2=tle_data['line2']
                )
                db.session.add(satellite)
                print("Satellite tle added")
            else:
                satellite.date = datetime.fromisoformat(tle_data['date'])
                satellite.tle_line1 = tle_data['line1']
                satellite.tle_line2 = tle_data['line2']
                print("Satellite tle updated")
            db.session.commit()


def store_or_update_pass(satellite_id, aos, los, max_elevation, solar_elevation, aos_azimuth, los_azimuth):

    new_pass = Pass(satellite_id=satellite_id, aos_time=aos, los_time=los,
                    max_elevation=max_elevation, sol_elevation=solar_elevation,
                    aos_azimuth=aos_azimuth, los_azimuth=los_azimuth)
    db.session.add(new_pass)
    db.session.commit()
    return new_pass.id


def store_or_upgrade_rotation(pass_id, azimuth, elevation, time):
    new_rotation = RotationSchedule(pass_id=pass_id, azimuth=azimuth, elevation=elevation, time=time)
    db.session.add(new_rotation)
    db.session.commit()
    return new_rotation.id


def calculate_passes_for_all_satellites(current_app):
    ts = load.timescale()
    gs_data = load_ground_station_from_file(f'C:\\Users\\khali\\PycharmProjects\\CurtsPassScheduler\\app\\ground_station.json')
    ground_station = Topos(latitude_degrees=gs_data['latitude_degrees'], longitude_degrees=gs_data['longitude_degrees'],elevation_m=gs_data['elevation_m'])

    now = datetime.utcnow()
    future = now + timedelta(days=1, hours=1)

    with current_app.app_context():
        satellites = Satellite.query.all()
        for satellite in satellites:

            # Satellite loading
            sat = EarthSatellite(satellite.tle_line1, satellite.tle_line2, satellite.name, ts)
            # Calculating Pass
            t0 = ts.utc(now.year, now.month, now.day, now.hour, now.minute, now.second)

            t1 = ts.utc(future.year, future.month, future.day, future.hour, future.minute, future.second)
            t, events = sat.find_events(ground_station, t0, t1, altitude_degrees=10)

            event_names = ['aos', 'max_ele', 'los']

            passes = Pass.query.filter_by(satellite_id=satellite.id).all()
            for passage in passes:
                RotationSchedule.query.filter_by(pass_id=passage.id).delete()
            db.session.commit()

            Pass.query.filter_by(satellite_id=satellite.id).delete()
            db.session.commit()
            aos = None
            for time, event in zip(t, events):
                if event_names[event] == 'aos':
                    aos = time.utc_datetime()
                    aos_top = (sat - ground_station).at(ts.utc(aos.year, aos.month, aos.day, aos.hour, aos.minute, aos.second))
                    _, aos_azimuth, _ = aos_top.altaz()
                if event_names[event] == 'max_ele':
                    topocentric = (sat - ground_station).at(time)
                    alt, _, _ = topocentric.altaz()
                    max_ele = alt.degrees
                    solar_ele = get_position(time.utc_datetime(), gs_data['latitude_degrees'], gs_data['longitude_degrees'])['altitude']
                if event_names[event] == 'los' and aos is not None:
                    los = time.utc_datetime()
                    los_top = (sat - ground_station).at(ts.utc(los.year, los.month, los.day, los.hour, los.minute, los.second))
                    _, los_azimuth, _ = los_top.altaz()
                    pass_id = store_or_update_pass(satellite.id, aos, los, max_ele, solar_ele, aos_azimuth.degrees, los_azimuth.degrees)
                    interval = los - aos

                    for ti in range(0, int(interval.total_seconds())):
                        t = aos + timedelta(seconds=ti)
                        top = (sat - ground_station).at(ts.utc(t.year, t.month, t.day, t.hour, t.minute, t.second))
                        ele, az, _ = top.altaz()
                        store_or_upgrade_rotation(pass_id, az.degrees, ele.degrees, t)

    current_time = datetime.now()
    prepare_next_pass_rotation(current_app, current_time)
    scheduler_rotator(current_app)

