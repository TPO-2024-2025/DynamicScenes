"""All exceptions raised by the integration."""


class InputValidationError(ValueError):
    """Exception raised when a value provided in the scene is invalid."""


class SceneNameError(ValueError):
    """Exception raised when a scene name is not found."""
