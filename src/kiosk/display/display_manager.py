import fnmatch
import logging

from kiosk.image import resize_image, change_orientation, apply_image_enhancement
from kiosk.display.mock_display import MockDisplay
from kiosk.display.waveshare_display import WaveshareDisplay

logger = logging.getLogger(__name__)

try:
    from kiosk.display.inky_display import InkyDisplay
except ImportError:
    InkyDisplay = None


class DisplayManager:
    """Manages the display and rendering of images.

    The concrete display driver is initialized lazily, on first use, instead
    of at construction time - so a hardware/dependency problem (missing GPIO
    library, wrong model, etc.) doesn't prevent the web UI and refresh loop
    from starting. It surfaces instead as a per-cycle refresh error the UI
    can show, and self-heals on the next cycle once the underlying issue is
    fixed (e.g. a missing pip package gets installed) - no restart needed.
    """

    def __init__(self, device_config):
        self.device_config = device_config
        self.display = None

    def _get_display(self):
        if self.display is None:
            display_type = self.device_config.display_type

            if display_type == "mock":
                logger.warning(
                    "display_type is 'mock' - screenshots will be written to disk only and "
                    "will NOT be sent to the physical panel. Set \"display_type\" in "
                    "src/kiosk/config.json to your Waveshare model (e.g. \"epd7in3f\") to "
                    "drive real hardware."
                )
                self.display = MockDisplay(self.device_config)
            elif display_type == "inky":
                if InkyDisplay is None:
                    raise ValueError(
                        "display_type is 'inky' but the 'inky' package is not installed. "
                        "Run: pip install -r install/requirements.txt"
                    )
                logger.info("Using Inky display driver (auto-detected)")
                self.display = InkyDisplay(self.device_config)
            elif fnmatch.fnmatch(display_type, "epd*in*"):
                # derived from waveshare epd - see https://github.com/waveshareteam/e-Paper
                logger.info(f"Using Waveshare display driver: {display_type}")
                self.display = WaveshareDisplay(self.device_config)
            else:
                raise ValueError(f"Unsupported display type: {display_type}")

        return self.display

    def display_image(self, image, image_settings=[]):
        """Resizes/orients/enhances the image, then delegates rendering to the concrete display."""
        display = self._get_display()

        image = change_orientation(image, self.device_config.orientation)
        image = resize_image(image, self.device_config.get_resolution(), image_settings)
        if self.device_config.inverted_image:
            image = image.rotate(180)
        image = apply_image_enhancement(image, self.device_config.image_settings)

        display.display_image(image, image_settings)
