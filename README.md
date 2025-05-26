# Dynamic Scenes Integration

Provides dynamic, time-based lighting control for Home Assistant with smooth interpolation between dynamic scene values throughout the day.

## Features

- **Time-Based Transitions**: Light values smoothly interpolate between defined time points
- **Priority System**: Multiple scenes can be active; highest priority scene controls the lights
- **Custom Override**: Manual adjustments automatically override automatic control
- **Time Shifting**: Adjust effective time for scene calculations

## Configuration
To add the integration simply clone the repo into /config/custom_components
### Integration config

### UI Config
To configure the side panel of the integration which allows the user to edit the scene do the following things.

1. Add the following code snippet to `configuration.yaml`:
```yaml
panel_custom:
  - name: dynamic-scenes
    url_path: redirect-server-controls
    sidebar_title: Dynamic Scenes
    sidebar_icon: mdi:server
    module_url: /local/dynamic_scenes.js
    config:
      hello: world
```

## Usage

1. Define scenes with time points and light values in the Dynamic Scenes panel in Home Assistant UI
2. Integration smoothly interpolates between time points
3. Use services exposed by the integration to activate/deactivate scenes based on conditions, shift time, or stop/resume automatic adjustments
4. Higher priority scenes override lower priority ones
5. Manual light adjustments create a temporary override until resumed


## Services

- **`set_scene_condition_met`**: Activate a scene (e.g., when TV turns on)
- **`unset_scene_condition_met`**: Deactivate a scene (e.g., when TV turns off)
- **`stop_adjustments`**: Disable automatic control for manual adjustments
- **`continue_adjustments`**: Resume automatic control
- **`set_timeshift`**: Set time offset for scenes (±12 hours)
- **`shift_timeshift`**: Adjust current timeshift
