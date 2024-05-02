# CURTS Pass Scheduler

The CURTS Pass Scheduler application is designed to optimize the scheduling of satellite passes and calculate the azimuth and elevation during the pass to track the satellite. It stores pass and rotation information with satellite data in a database and shares it using the application's API. The application uses the stored data to schedule antenna rotations. The API can be used to control which satellites to track.

## Application Code

Here's an overview of the application's code files:

- **app/pass_calculator/__init__.py**: This file contains the main functions for calculating satellite passes and storing rotations.

- **app/schedule_rotator/__init__.py**: This file contains functions to schedule antenna rotations based on calculated passes.

- **app/__init__.py**: This file initializes the Flask application and configures the database and API.

- **app/api_models.py**: This file contains API models used for serializing data.

- **app/extension.py**: This file initializes Flask extensions used in the application, such as SQLAlchemy, Flask-RestX, and Flask-APScheduler.

- **app/models.py**: This file defines the SQLAlchemy data models for satellites, passes, and rotations.

- **app/ground_station.json**: This file contains the coordinates of the ground station used for pass calculation.

- **app/resources.py**: This file contains Flask-RestX API endpoints for retrieving satellite and pass data.

## Using the Application

To use the application, follow these steps:

1. Install Python dependencies by running `pip install -r requirements.txt`.

2. Run the application by executing `python run.py`.

3. Use the API to retrieve satellite and pass data or to modify satellite tracking settings.

4. Consult the database to access information about passes and rotations.

Feel free to explore the source code for more details on the application's functionality. If you have any questions or feedback, don't hesitate to contact us.

Thank you for using CURTS Pass Scheduler! 🛰️📅
