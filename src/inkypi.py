#!/usr/bin/env python3

# set up logging
import os, logging.config
logging.config.fileConfig(os.path.join(os.path.dirname(__file__), 'config', 'logging.conf'))

import argparse
import logging
import threading
import warnings

from waitress import serve

# surface every warning (e.g. the inky library's "Busy Wait: Timed out")
# in the log every time it happens, not just once per call site
logging.captureWarnings(True)
warnings.simplefilter("always")

from kiosk.config import KioskConfig
from kiosk.control import RunnerControl
from kiosk.display.display_manager import DisplayManager
from kiosk.runner import run
from kiosk.web import create_app

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(description='InkyPi Kiosk Display')
parser.add_argument('--dev', action='store_true', help='Force the mock display and serve on port 8080')
args = parser.parse_args()

PORT = 8080 if args.dev else 80

if __name__ == '__main__':
    config = KioskConfig()
    if args.dev:
        config.display_type_override = "mock"

    display_manager = DisplayManager(config)
    control = RunnerControl()

    refresh_thread = threading.Thread(target=run, args=(config, display_manager, control), daemon=True)
    refresh_thread.start()

    app = create_app(config, control)

    try:
        logger.info(f"Serving kiosk UI on port {PORT}")
        serve(app, host="0.0.0.0", port=PORT, threads=2)
    finally:
        control.stop()
        refresh_thread.join()
