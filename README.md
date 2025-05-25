# Configuration
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

2. Copy the file from `UI/dynamic_scenes.js` to `core/config/www/dynamic_scenes.js`.
If the `www` directory is not present simply create it.