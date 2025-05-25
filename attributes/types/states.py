"""Light state attribute for any light entity."""

from .. import Attr  # noqa: TID252


class State(Attr):
    """Represents home assistnat state."""

    YAML_NAME: str = "state"
    HASS_NAME: str = "state"
    OFF_VALUE: str = ""
    DEFAULT_VALUE: str = OFF_VALUE

    SUPPORTED_VALUES: set[str] = set()

    @classmethod
    def _validate_value(cls, value: str) -> None:
        if value not in cls.SUPPORTED_VALUES:
            raise ValueError(f"Invalid state value: {value}")

    def _interpolate_value(self, next_val: int, ratio: float) -> int:
        return self.value


class LightState(State):
    """Class to represent a brightness attribute."""

    YAML_NAME: str = "light_state"
    HASS_NAME: str = "state"
    OFF_VALUE: str = "off"
    DEFAULT_VALUE: str = OFF_VALUE

    SUPPORTED_VALUES = {"on", "off"}
