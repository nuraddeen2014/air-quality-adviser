import re
from datetime import datetime, timedelta


def validate_latitude(latitude):
    try:
        latitude = float(latitude)
        return -90 <= latitude <= 90
    except (TypeError, ValueError):
        return False


def validate_longitude(longitude):
    try:
        longitude = float(longitude)
        return -180 <= longitude <= 180
    except (TypeError, ValueError):
        return False


def validate_location(location):
    if not isinstance(location, str):
        return False

    location = location.strip()

    if not location:
        return False

    return len(location) <= 100


def validate_coordinates(coordinates):
    pattern = r"^\s*-?\d+(\.\d+)?\s*,\s*-?\d+(\.\d+)?\s*$"

    if not isinstance(coordinates, str):
        return False

    if not re.match(pattern, coordinates):
        return False

    latitude, longitude = coordinates.split(",")

    return validate_latitude(latitude) and validate_longitude(longitude)


def get_current_time():
    return datetime.now()


def get_tomorrow():
    return datetime.now() + timedelta(days=1)


def get_forecast_date(days_ahead=0):
    date = datetime.now() + timedelta(days=days_ahead)
    return date.strftime("%Y-%m-%d")