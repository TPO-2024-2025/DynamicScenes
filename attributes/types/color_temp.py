"""Color temp kelvin attribute for any light entity."""

from .. import Attr  # noqa: TID252


class ColorTemp(Attr):
    """Class to represent a brightness attribute."""

    YAML_NAME: str = "color_temp"
    HASS_NAME: str = YAML_NAME
    OFF_VALUE: None = None
    DEFAULT_VALUE: int = 400

    @classmethod
    def _validate_value(cls, value: int) -> None:
        if not 153 <= value <= 500: # TODO: Unese se vrednost ki jo luč podpira
            raise ValueError(f"Invalid color_temp value: {value}")

    def _interpolate_value(self, next_val: int, ratio: float) -> int:
        return int(self.value + (next_val - self.value) * ratio)
