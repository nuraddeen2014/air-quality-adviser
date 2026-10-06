import re

LOCATION_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9 .,'-]*[A-Za-z0-9]$"


def validate_location(location):
    if not isinstance(location, str):
        return False

    location = location.strip()

    if not location or len(location) > 100:
        return False

    return bool(re.fullmatch(LOCATION_PATTERN, location))


def clean_location(location):
    if not isinstance(location, str):
        return ""

    return re.sub(r"\s+", " ", location.strip())


def validate_and_clean_location(location):
    location = clean_location(location)

    if validate_location(location):
        return location

    return None