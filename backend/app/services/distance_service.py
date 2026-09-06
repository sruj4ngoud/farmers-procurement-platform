"""Distance calculation service using Haversine formula."""

from decimal import Decimal
from math import atan2, cos, radians, sin, sqrt


def haversine_distance(
    lat1: Decimal, lon1: Decimal, lat2: Decimal, lon2: Decimal
) -> Decimal:
    """
    Calculate distance between two points using Haversine formula.

    Args:
        lat1: Latitude of point 1 (degrees)
        lon1: Longitude of point 1 (degrees)
        lat2: Latitude of point 2 (degrees)
        lon2: Longitude of point 2 (degrees)

    Returns:
        Distance in kilometers
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return Decimal(0)

    # Convert to float for calculation
    lat1_f = float(lat1)
    lon1_f = float(lon1)
    lat2_f = float(lat2)
    lon2_f = float(lon2)

    # Earth's radius in kilometers
    R = 6371.0

    # Convert to radians
    lat1_rad = radians(lat1_f)
    lon1_rad = radians(lon1_f)
    lat2_rad = radians(lat2_f)
    lon2_rad = radians(lon2_f)

    # Differences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Haversine formula
    a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c

    return Decimal(str(round(distance, 2)))
