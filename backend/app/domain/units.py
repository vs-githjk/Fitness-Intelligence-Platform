from decimal import ROUND_HALF_UP, Decimal

from app.models import DistanceUnit, WeightUnit

THREE_PLACES = Decimal("0.001")
POUNDS_TO_KILOGRAMS = Decimal("0.45359237")
METERS_PER_MILE = Decimal("1609.344")


def quantize_measurement(value: Decimal) -> Decimal:
    """Store prescription measurements consistently without binary float drift."""
    return value.quantize(THREE_PLACES, rounding=ROUND_HALF_UP)


def canonical_kilograms(value: Decimal, unit: WeightUnit) -> Decimal:
    converted = value if unit == WeightUnit.KG else value * POUNDS_TO_KILOGRAMS
    return quantize_measurement(converted)


def canonical_meters(value: Decimal, unit: DistanceUnit) -> Decimal:
    multiplier = {
        DistanceUnit.METERS: Decimal("1"),
        DistanceUnit.KILOMETERS: Decimal("1000"),
        DistanceUnit.MILES: METERS_PER_MILE,
    }[unit]
    return quantize_measurement(value * multiplier)
