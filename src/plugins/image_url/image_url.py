import this

from plugins.base_plugin.base_plugin import BasePlugin
from PIL import Image
from io import BytesIO
import requests
import logging
# from src.config import Config


# src/plugins/image_url
#/Users/miguelhernandez/Documents/GitHub/InkyPi/src/config.py
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

class ImageURL(BasePlugin):
    def generate_image(self, settings, device_config):
        url = settings.get('url')
        print("*****before")
        refresh_interval_minutes = settings.get('refresh_interval_minutes', 0)
        print(f"&&&&&&after {refresh_interval_minutes}")
        print(settings)
        print(BasePlugin)
        print(BasePlugin.config.plugins_list)
        print(BasePlugin.config.config)
        print(BasePlugin.config.get_plugins())
        print(BasePlugin.config.read_config())
        print(BasePlugin.config.get_plugin("image_url"))



        logger.debug(
            f"ImageURL refresh_interval_minutes: {refresh_interval_minutes}"
        )
        if not url:
            raise RuntimeError("URL is required.")

        print(settings)
        print("----settings ^^^^ devConfig vvv----")
        print(device_config)
        # config = Config()
        # plugin_config = config.get_plugin("image_url")
        # config.update_value("refresh_interval_minutes", refresh_interval_minutes, write=True)

        dimensions = device_config.get_resolution()
        if device_config.get_config("orientation") == "vertical":
            dimensions = dimensions[::-1]

        logger.info(f"Grabbing image from: {url}")

        image = grab_image(url, dimensions, timeout_ms=40000)

        if not image:
            raise RuntimeError("Failed to load image, please check logs.")

        return image