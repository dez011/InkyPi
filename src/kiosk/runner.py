import logging
import threading

from kiosk.image import take_screenshot, compute_image_hash

logger = logging.getLogger(__name__)

DISPLAY_TIMEOUT_SECONDS = 90


def _display_with_timeout(display_manager, image, timeout_seconds=DISPLAY_TIMEOUT_SECONDS):
    """Runs display_manager.display_image() in a worker thread with a hard
    deadline, so a hung hardware call (e.g. a busy-pin wait that never
    resolves) can't block the refresh loop forever. If it times out, the
    worker thread is abandoned (Python can't forcibly kill a thread) and an
    error is raised so the next cycle tries again fresh.
    """
    result = {}

    def _target():
        try:
            display_manager.display_image(image)
            result["ok"] = True
        except BaseException as e:
            # BaseException, not Exception: Pimoroni's gpiodevice raises
            # SystemExit on GPIO errors, which threading swallows silently -
            # the thread just vanishes and the failure never gets logged.
            result["error"] = e

    worker = threading.Thread(target=_target, daemon=True)
    worker.start()
    worker.join(timeout=timeout_seconds)

    if worker.is_alive():
        raise TimeoutError(
            f"Display update did not finish within {timeout_seconds}s - abandoning "
            f"this attempt (possible hardware hang). The stuck worker thread is "
            f"being left running in the background."
        )
    if "error" in result:
        err = result["error"]
        if isinstance(err, Exception):
            raise err
        # convert SystemExit/KeyboardInterrupt into a normal error so the
        # refresh loop's own thread doesn't get silently killed re-raising it
        raise RuntimeError(f"Display update aborted with {type(err).__name__}: {err}")
    if "ok" not in result:
        raise RuntimeError("Display worker thread ended without success or error")


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

        pushed_image = control.take_pending_image()

        if pushed_image is not None:
            # An externally pushed image (receiver mode / POST /api/display).
            # An explicit push always displays right away - it bypasses
            # active_hours, and only the hash check is kept to spare the
            # panel if the exact same image is re-sent.
            try:
                image_hash = compute_image_hash(pushed_image)
                if image_hash != last_image_hash:
                    logger.info("Displaying pushed image")
                    _display_with_timeout(display_manager, pushed_image)
                    last_image_hash = image_hash
                else:
                    logger.info("Pushed image identical to current, skipping display refresh")
                control.record_attempt(success=True)
            except Exception as e:
                logger.exception("Exception displaying pushed image")
                control.record_attempt(success=False, error=str(e))

        elif config.mode == "receiver":
            # Nothing to do until something POSTs an image to /api/display.
            pass

        elif not manual and not config.is_active_now():
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
                        _display_with_timeout(display_manager, image)
                        last_image_hash = image_hash
                    else:
                        logger.info("Screenshot unchanged, skipping display refresh")
                    control.record_attempt(success=True)

            except Exception as e:
                logger.exception("Exception during refresh cycle")
                control.record_attempt(success=False, error=str(e))

        control.wait(timeout=config.refresh_interval_seconds)
