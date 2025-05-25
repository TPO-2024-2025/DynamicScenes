"""HTTP API for dynamic scenes."""
from pathlib import Path

import yaml

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .config import Config
from .constants import FILEPATH


class DynamicScenesDataView(HomeAssistantView):
    url = "/api/dynamic_scenes/data"
    name = "api:dynamic_scenes:data"
    requires_auth = True

    def __init__(self, hass: HomeAssistant, config: Config) -> None:
        self.hass = hass
        self.config = config
        self.scene_file_path = Path(__file__).parent / FILEPATH.SCENES_FILE

    async def get(self, request):
        """Read and return the contents of scene.yaml."""
        try:

            def load_yaml():
                with self.scene_file_path.open("r") as f:
                    return yaml.safe_load(f)

            data = await self.hass.async_add_executor_job(load_yaml)

        except FileNotFoundError:
            return self.json_message("Scene file not found", status_code=404)
        except yaml.YAMLError as err:
            return self.json_message(f"Invalid YAML: {err}", status_code=500)

        return self.json(data)

    async def post(self, request):
        try:
            data = await request.json()

            def save_yaml():
                with self.scene_file_path.open("w") as f:
                    yaml.safe_dump(data, f, default_flow_style=False)

            await self.hass.async_add_executor_job(save_yaml)
            await self.config.async_load_entities()

        except yaml.YAMLError as err:
            return self.json_message(f"Invalid YAML: {err}", status_code=500)
        except Exception as err:
            return self.json_message(f"Failed to write file: {err}", status_code=500)

        return self.json_message("Scene data saved successfully")
