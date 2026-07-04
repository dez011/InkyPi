import datetime
import json
import os
import socket


class KioskConfig:
    """Minimal, flat config for the kiosk screenshot frame.

    Replaces InkyPi's Config/PlaylistManager/PluginInstance model with a
    single JSON file since there is exactly one thing this app ever does:
    screenshot one URL and push it to one display.
    """

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(BASE_DIR, "config.json")

    def __init__(self):
        with open(self.config_file) as f:
            self.config = json.load(f)
        # runtime-only override (e.g. --dev forcing the mock display); kept
        # out of self.config so a UI save can't accidentally persist it
        self.display_type_override = None

    def save(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    @property
    def mode(self):
        """"kiosk" = screenshot config.url on an interval (the default).
        "receiver" = idle and wait for images pushed to POST /api/display
        (e.g. from Home Assistant)."""
        return self.config.get("mode", "kiosk")

    @property
    def device_id(self):
        """Identifier for this frame, so an external sender (Home Assistant)
        can tell multiple frames apart. Defaults to the hostname."""
        return self.config.get("device_id") or socket.gethostname()

    @property
    def url(self):
        return self.config["url"]

    def get_resolution(self):
        width, height = self.config["resolution"]
        return (int(width), int(height))

    @property
    def orientation(self):
        return self.config.get("orientation", "horizontal")

    @property
    def inverted_image(self):
        return self.config.get("inverted_image", False)

    @property
    def display_type(self):
        return self.display_type_override or self.config.get("display_type", "inky")

    @property
    def refresh_interval_seconds(self):
        return self.config.get("refresh_interval_seconds", 180)

    @property
    def image_settings(self):
        return self.config.get("image_settings", {})

    @property
    def active_hours(self):
        """Optional {"start": "HH:MM", "end": "HH:MM"} window during which the
        display refreshes. Omit (or set to null) to run 24/7."""
        return self.config.get("active_hours")

    def is_active_now(self, now=None):
        """Whether the current local time falls within `active_hours`.

        Always True if `active_hours` isn't set. Handles windows that span
        midnight (e.g. start "22:00", end "06:00").
        """
        active_hours = self.active_hours
        if not active_hours:
            return True

        now = (now or datetime.datetime.now()).time()
        start = datetime.time.fromisoformat(active_hours["start"])
        end = datetime.time.fromisoformat(active_hours["end"])

        if start <= end:
            return start <= now < end
        else:
            return now >= start or now < end
