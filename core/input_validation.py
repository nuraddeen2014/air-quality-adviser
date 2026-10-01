import re

LOCATION_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9 .,'-]*[A-Za-z0-9]$"
LOCATION_REGEX = re.compile(LOCATION_PATTERN)


def validate_location(location):
    if not isinstance(location, str):
        return False

    location = location.strip()

    if not location or len(location) > 100:
        return False

    return bool(LOCATION_REGEX.fullmatch(location))


def clean_location(location):
    if not isinstance(location, str):
        return ""

    location = location.strip()
    return re.sub(r"\s+", " ", location)


def validate_input(value):
    if value is None or not isinstance(value, str):
        return False

    return bool(value.strip())


def validate_number(value, minimum=None, maximum=None):
    try:
        number = float(value)
    except (ValueError, TypeError):
        return False

    if minimum is not None and number < minimum:
        return False

    if maximum is not None and number > maximum:
        return False

    return True


def validate_positive_number(value):
    return validate_number(value, minimum=0)


def validate_and_clean_location(location):
    location = clean_location(location)

    if validate_location(location):
        return location

    return None
