import fnmatch
import logging

from kiosk.image import resize_image, change_orientation, apply_image_enhancement
from kiosk.display.mock_display import MockDisplay
from kiosk.display.waveshare_display import WaveshareDisplay

logger = logging.getLogger(__name__)


class DisplayManager:
    """Manages the display and rendering of images."""

    def __init__(self, device_config):
        self.device_config = device_config

        display_type = device_config.display_type

        if display_type == "mock":
            self.display = MockDisplay(device_config)
        elif fnmatch.fnmatch(display_type, "epd*in*"):
            # derived from waveshare epd - see https://github.com/waveshareteam/e-Paper
            self.display = WaveshareDisplay(device_config)
        else:
            raise ValueError(f"Unsupported display type: {display_type}")

    def display_image(self, image, image_settings=[]):
        """Resizes/orients/enhances the image, then delegates rendering to the concrete display."""
        image = change_orientation(image, self.device_config.orientation)
        image = resize_image(image, self.device_config.get_resolution(), image_settings)
        if self.device_config.inverted_image:
            image = image.rotate(180)
        image = apply_image_enhancement(image, self.device_config.image_settings)

        self.display.display_image(image, image_settings)
