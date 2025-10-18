from datetime import datetime
import time

from plugins.base_plugin.base_plugin import BasePlugin
from utils.image_utils import take_screenshot
from PIL import Image
from io import BytesIO
import requests
import logging

logger = logging.getLogger(__name__)

class ImmichKioskPaper(BasePlugin):
    def generate_image(self, settings, device_config):

        url = settings.get('url')
        if not url:
            raise RuntimeError("URL is required.")

        while True:
            dimensions = device_config.get_resolution()
            if device_config.get_config("orientation") == "vertical":
                dimensions = dimensions[::-1]

            logger.info(f"Taking screenshot of url: {url}")

            image = take_screenshot(url, dimensions, timeout_ms=40000)
            if not image:
                logger.error("Failed to take screenshot, please check logs.")
            else:
                logger.info("Screenshot taken successfully.")

            time.sleep(10)