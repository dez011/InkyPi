import logging

from kiosk.image import take_screenshot, compute_image_hash

logger = logging.getLogger(__name__)


def run(config, display_manager, control):
    """Runs the screenshot -> display refresh loop until control.stop() is called.

    Each cycle screenshots `config.url`, and only pushes it to the display if
    it differs from the last-displayed image (avoids needless e-ink
    refreshes/wear when the kiosk slideshow hasn't advanced), unless a manual
    refresh was requested via the web UI, in which case it always pushes.
    Skips the cycle entirely outside `config.active_hours`.
    """
    last_image_hash = None

    while not control.stop_requested:
        manual = control.manual_refresh_requested
        if manual:
            control.manual_refresh_requested = False

        if not manual and not config.is_active_now():
            logger.info(f"Outside active_hours ({config.active_hours}), skipping refresh")
        else:
            try:
                dimensions = config.get_resolution()
                if config.orientation == "vertical":
                    dimensions = dimensions[::-1]

                logger.info(f"Taking screenshot of url: {config.url}")
                image = take_screenshot(config.url, dimensions, timeout_ms=40000)

                if image is None:
                    logger.error("Failed to take screenshot, will retry next cycle")
                    control.record_attempt(success=False, error="Failed to take screenshot")
                else:
                    image_hash = compute_image_hash(image)
                    if image_hash != last_image_hash or manual:
                        logger.info("Updating display")
                        display_manager.display_image(image)
                        last_image_hash = image_hash
                    else:
                        logger.info("Screenshot unchanged, skipping display refresh")
                    control.record_attempt(success=True)

            except Exception as e:
                logger.exception("Exception during refresh cycle")
                control.record_attempt(success=False, error=str(e))

        control.wait(timeout=config.refresh_interval_seconds)
