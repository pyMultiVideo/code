import importlib


class CameraManager:
    """Manage one camera API instance per unique camera ID for use across the GUI.
    This class is responsible for creating, storing and closing camera API instances."""

    def __init__(self):
        self._instances = {}

    def _create(self, settings):
        _, module_name = settings.unique_id.split("-")
        camera_module = importlib.import_module(f"camera_api.{module_name}")
        return camera_module.initialise_camera_api(CameraConfig=settings)

    def get_or_create(self, settings):
        """Return an existing camera API instance, or create one for this camera ID."""
        camera_api = self._instances.get(settings.unique_id)
        if camera_api is None:
            camera_api = self._create(settings)
            self._instances[settings.unique_id] = camera_api
        return camera_api

    def get(self, unique_id):
        """Return a managed camera API instance if present."""
        return self._instances.get(unique_id)

    def close(self, unique_id):
        """Close and remove a managed camera API instance by unique ID."""
        camera_api = self._instances.pop(unique_id, None)

        if camera_api is None:
            return

        try:
            camera_api.close_api()
        except Exception:
            # Best-effort cleanup: continue closing other cameras.
            pass

    def close_all(self):
        """Close and clear all managed camera API instances."""
        camera_ids = list(self._instances.keys())

        for unique_id in camera_ids:
            self.close(unique_id)
