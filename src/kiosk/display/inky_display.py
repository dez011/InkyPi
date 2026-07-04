import logging
from inky.auto import auto
from kiosk.display.abstract_display import AbstractDisplay


logger = logging.getLogger(__name__)

class InkyDisplay(AbstractDisplay):

    """
    Handles the Inky e-paper display.

    This class initializes and manages interactions with the Inky display,
    ensuring proper image rendering and configuration storage.

    The Inky display driver supports auto configuration.
    """
   
    def initialize_display(self):
        
        """
        Initializes the Inky display device.

        Sets the display border and stores the display resolution in the device configuration.

        Raises:
            ValueError: If the resolution cannot be retrieved or stored.
        """
        
        logger.info("Calling inky.auto.auto() to detect the connected board via EEPROM")
        self.inky_display = auto(verbose=True)
        logger.info(f"auto() returned {type(self.inky_display).__name__}")
        self.inky_display.set_border(self.inky_display.BLACK)
        logger.info("set_border() done")

        # cross-check the configured resolution against the panel's native one
        panel_resolution = (int(self.inky_display.width), int(self.inky_display.height))
        if self.device_config.get_resolution() != panel_resolution:
            logger.warning(
                f"Configured resolution {self.device_config.get_resolution()} does not "
                f"match panel's native resolution {panel_resolution}"
            )

    def display_image(self, image, image_settings=[]):
        
        """
        Displays the provided image on the Inky display.

        The image has been processed by adjusting orientation and resizing 
        before being sent to the display.

        Args:
            image (PIL.Image): The image to be displayed.
            image_settings (list, optional): Additional settings to modify image rendering.

        Raises:
            ValueError: If no image is provided.
        """

        logger.info("Displaying image to Inky display.")
        if not image:
            raise ValueError(f"No image provided.")

        # Display the image on the Inky display
        logger.info("Calling set_image()")
        self.inky_display.set_image(image)
        logger.info("set_image() done, calling show() - this is the slow hardware refresh step")
        self.inky_display.show()
        logger.info("show() returned - refresh complete")