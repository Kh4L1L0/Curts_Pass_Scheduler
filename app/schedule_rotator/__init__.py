import subprocess
from datetime import datetime, timedelta
from sqlalchemy.orm.session import make_transient

from ..models import RotationSchedule, Pass, Satellite
from ..extension import scheduler


def execute_rotator_command(azimuth, elevation):
    command = f"C:\\Workspace\\rotator\\rotatorClient.exe -azi {azimuth} -ele {elevation}"
    print(command)
    # try:
    #    subprocess.run(command, check=True, shell=True)
    # except subprocess.CalledProcessError as e:
    #    print(f"An error occurred while executing the rotator command: {e}")


def delete_rotator_schedule(current_app):
    with current_app.app_context():
        for job in scheduler.get_jobs():
            if job.id.startswith("rotator_command_"):
                scheduler.remove_job(job.id)


def rotation_direction_clockwise(aos_azimuth, los_azimuth):
    diff = (los_azimuth - aos_azimuth + 360) % 360
    return diff <= 180, (aos_azimuth < los_azimuth)


def schedule_pass_rotator_command(current_app, passage, aos_time, los_time):
    with current_app.app_context():
        rotations = RotationSchedule.query.filter_by(pass_id=passage.id).all()
        clockwise, degree_increased = rotation_direction_clockwise(passage.aos_azimuth, passage.los_azimuth)
        for rotation in rotations:
            if rotation.time > datetime.now() and aos_time <= rotation.time <= los_time:

                if clockwise and not degree_increased:
                    azimuth_value = rotation.azimuth + 360 if (
                                rotation.azimuth < passage.aos_azimuth) else rotation.azimuth
                elif not clockwise and degree_increased:
                    azimuth_value = rotation.azimuth + 360 if (
                                rotation.azimuth < passage.los_azimuth) else rotation.azimuth
                else:
                    azimuth_value = rotation.azimuth

                job_id = f'rotator_command_{rotation.id}'
                print(job_id)
                scheduler.add_job(
                    func=execute_rotator_command,
                    trigger='date',
                    id=job_id,
                    run_date=rotation.time,
                    args=[azimuth_value, rotation.elevation],
                    replace_existing=True
                )


def detect_pass_collisions(passes, current_app):
    with current_app.app_context():
        collision_details = []

        for i in range(len(passes)):
            for j in range(i + 1, len(passes)):
                pass1 = passes[i]
                pass2 = passes[j]

                if pass1.aos_time < pass2.los_time and pass1.los_time > pass2.aos_time:
                    collision_start = max(pass1.aos_time, pass2.aos_time)
                    collision_end = min(pass1.los_time, pass2.los_time)

                    midpoint_time = collision_start + (collision_end - collision_start) / 2
                    collision_details.append({
                        'pass1_id': pass1.id,
                        'pass2_id': pass2.id,
                        'collision_start': collision_start,
                        'collision_end': collision_end,
                        'midpoint_time': midpoint_time
                    })
        return collision_details


def prepare_next_pass_rotation(current_app, los_time, satellite_id=0):
    with current_app.app_context():
        sat = Satellite.query.filter_by(id=satellite_id).first()
        passes = Pass.query.all() if (sat is None) else Pass.query.filter_by(satellite_id=sat.id).all()
        current_time = los_time + timedelta(seconds=2)
        sorted_passes = sorted([passage for passage in passes if passage.aos_time > current_time], key=lambda passage: passage.aos_time)
        if sorted_passes:
            next_pass = sorted_passes[0]
            clockwise, degree_increased = rotation_direction_clockwise(next_pass.aos_azimuth, next_pass.los_azimuth)
            if not clockwise and degree_increased:
                azimuth_value = next_pass.aos_azimuth + 360
            else:
                azimuth_value = next_pass.aos_azimuth

            new_time = next_pass.aos_time - timedelta(seconds=94)
            pass_time = new_time if new_time > current_time else current_time
            job_id = f'rotator_command_pre_pass_{next_pass.id}'
            print(job_id, next_pass.aos_time, azimuth_value)
            scheduler.add_job(
                func=execute_rotator_command,
                trigger='date',
                id=job_id,
                run_date=pass_time,
                args=[azimuth_value, next_pass.max_elevation],
                replace_existing=True
            )


def scheduler_rotator(current_app, satellite_id=0):
    with current_app.app_context():
        delete_rotator_schedule(current_app)

        sat = Satellite.query.filter_by(id=satellite_id).first()
        passes = Pass.query.all() if (sat is None) else Pass.query.filter_by(satellite_id=sat.id).all()

        collision_details = detect_pass_collisions(passes, current_app)

        for passage in passes:
            make_transient(passage)

        for passage in passes:
            collision_count = 0
            last_passage = True
            for collision in collision_details:
                if collision.get('pass1_id') == passage.id or collision.get('pass2_id') == passage.id:
                    collision_count += 1
                    if passage.aos_time == collision.get('collision_start'):
                        passage.aos_time = collision.get('midpoint_time')

                    if passage.los_time == collision.get('collision_end'):
                        passage.los_time = collision.get('midpoint_time')
                        last_passage = False
            if last_passage and collision_count <= 1:
                prepare_next_pass_rotation(current_app, passage.los_time, satellite_id)

        for passage in passes:
            schedule_pass_rotator_command(current_app, passage, passage.aos_time, passage.los_time)


