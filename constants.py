"""Constants for the DynamicScenes integration."""

INTEGRATION_DOMAIN = "dynamic_scenes"

# The maximum priority a scene can have (custom scene has this priority)
MAX_PRIORITY = 100


# ===== Services =====
class SERVICENAME:
    """The service names exposed by the integration."""

    SET_SCENE_CONDITION_MET = "set_scene_condition_met"
    UNSET_SCENE_CONDITION_MET = "unset_scene_condition_met"
    CONTINUE_ADJUSTMENTS = "continue_adjustments"
    STOP_ADJUSTMENTS = "stop_adjustments"
    SET_TIMESHIFT = "set_timeshift"
    SHIFT_TIME = "shift_timeshift"


class SERVICEDATA:
    """The data keys used in the service calls TO dynamic scenes services."""

    ENTITY_ID = "entity_id"
    SCENE = "scene"
    TIMESHIFT = "timeshift"
    SHIFT = "shift"


class YAMLDATA:
    """The data keys used in the YAML configuration."""

    ENTITIES = "entities"
    TIMES = "times"
    PRIORITY = "priority"

    class ATTR:
        """The attributes used in the YAML configuration."""

        BRIGHTNESS = "brightness"
        COLOR_TEMP = "color_temp"
        XY_BRIGHTNESS = "xy_brightness"
        XY_COLOR = "xy_color"
        COLOR_MODE = "color_mode"
        TRANSITION = "transition"
        DELAY = "delay"


class ENTRYDATA:
    """The data keys used in the integration configuration."""

    UPDATE_INTERVAL = "update_interval"

class HASSDATA:
    """The data keys used in the hass.data."""

    UNREGISTER_SERVICES = "unregister_services"
    UPDATE_COORDINATOR = "update_coordinator"
    CONFIG = "config"


class FILEPATH:
    """The paths to files used by the integration."""

    SCENES_FILE = "scenes.yaml"


class SCENE:
    """Built-in scenes."""

    OFF = "off"
    CUSTOM = "custom"

class SERVICECALLS:
    """Reocuting constants used in outgoing service calls."""

    ENTITY_ID = "entity_id"
