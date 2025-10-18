from plugins.base_plugin.base_plugin import BasePlugin
from PIL import Image
from io import BytesIO
import requests
import logging

logger = logging.getLogger(__name__)

def grab_image(image_url, dimensions, timeout_ms=40000):
    """Grab an image from a URL and resize it to the specified dimensions."""
    try:
        response = requests.get(image_url, timeout=timeout_ms / 1000)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        img = img.resize(dimensions, Image.LANCZOS)
        return img
    except Exception as e:
        logger.error(f"Error grabbing image from {image_url}: {e}")
        return None

class ImmichKioskPaper(BasePlugin):
    def generate_image(self, settings, device_config):
        url = "http://192.168.1.169:3000" #settings.get('url')
        if not url:
            raise RuntimeError("URL is required.")

        dimensions = device_config.get_resolution()
        if device_config.get_config("orientation") == "vertical":
            dimensions = dimensions[::-1]

        logger.info(f"Grabbing image from: {url}")

        template_params = {
            # "view": view,
            # "events": events,
            # "current_dt": current_dt.replace(minute=0, second=0, microsecond=0).isoformat(),
            # "timezone": timezone,
            "plugin_settings": settings,
            # "time_format": time_format,
            # "font_scale": FONT_SIZES.get(settings.get("fontSize", "normal"))
        }

        # image = grab_image(url, dimensions, timeout_ms=40000)
        image = self.render_image(dimensions, "calendar.html", "calendar.css", template_params)

        if not image:
            raise RuntimeError("Failed to load image, please check logs.")

        return image