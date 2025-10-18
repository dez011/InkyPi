from datetime import datetime

from plugins.base_plugin.base_plugin import BasePlugin
from utils.image_utils import take_screenshot
from PIL import Image
from io import BytesIO
import requests
import logging
import threading
import time
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_URL = "http://192.168.1.169:3000"
DEFAULT_INTERVAL_SEC = 900  # 15 minutes

class _ScreenshotWorker(threading.Thread):
    def __init__(self, url: str, get_dimensions, interval_sec: int, paused: bool):
        super().__init__(daemon=True)
        self._url = url
        self._get_dimensions = get_dimensions  # callable -> (w, h)
        self._interval = max(1, int(interval_sec))
        self._paused = paused
        self._running = True
        self._lock = threading.Lock()
        self._last_image: Optional[Image.Image] = None
        self._last_error: Optional[str] = None

    def update(self, url: Optional[str] = None, interval_sec: Optional[int] = None, paused: Optional[bool] = None):
        with self._lock:
            if url is not None:
                self._url = url
            if interval_sec is not None:
                try:
                    self._interval = max(1, int(interval_sec))
                except Exception:
                    pass
            if paused is not None:
                self._paused = bool(str(paused).lower() == "true") if isinstance(paused, str) else bool(paused)

    def get_last_image(self) -> Optional[Image.Image]:
        with self._lock:
            return self._last_image.copy() if self._last_image is not None else None

    def stop(self):
        self._running = False

    def run(self):
        logger.info("[Worker] Screenshot loop started")
        while self._running:
            try:
                with self._lock:
                    url = self._url
                    interval = self._interval
                    paused = self._paused
                if paused:
                    time.sleep(1)
                    continue

                dims = self._get_dimensions()
                img = take_screenshot(url, dims, timeout_ms=40000)
                if img is not None:
                    with self._lock:
                        self._last_image = img
                        self._last_error = None
                    logger.info(f"[Worker] Captured {url} at {dims}")
                else:
                    with self._lock:
                        self._last_error = "capture returned None"
                    logger.error(f"[Worker] Capture failed for {url}")
                time.sleep(interval)
            except Exception as e:
                logger.exception(f"[Worker] Loop error: {e}")
                time.sleep(2)

class ImmichKioskPaper(BasePlugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._worker: Optional[_ScreenshotWorker] = None

    def generate_image(self, settings, device_config):
        settings = settings or {}

        # Defaults + sanitize
        url = (settings.get("url") or DEFAULT_URL).strip()
        try:
            interval_sec = int(settings.get("interval", DEFAULT_INTERVAL_SEC))
        except (TypeError, ValueError):
            interval_sec = DEFAULT_INTERVAL_SEC
        if interval_sec < 1:
            interval_sec = DEFAULT_INTERVAL_SEC
        paused = str(settings.get("paused", "false")).lower() == "true"

        # dynamic dimensions callable (handles orientation each time)
        def _dims():
            dims = device_config.get_resolution()
            if device_config.get_config("orientation") == "vertical":
                dims = dims[::-1]
            return dims

        # Start or update the background worker
        if self._worker is None:
            self._worker = _ScreenshotWorker(url=url, get_dimensions=_dims, interval_sec=interval_sec, paused=paused)
            self._worker.start()
            logger.info(f"[ImmichKioskPaper] Started worker for {url} (interval={interval_sec}s, paused={paused})")
        else:
            self._worker.update(url=url, interval_sec=interval_sec, paused=paused)

        # Return the most recent image; if none yet, do a synchronous first capture
        img = self._worker.get_last_image() if self._worker else None
        if img is None and not paused:
            dims = _dims()
            logger.info(f"[ImmichKioskPaper] First run capture of {url} at {dims}")
            img = take_screenshot(url, dims, timeout_ms=40000)
            if img is not None and self._worker:
                # prime the cache
                self._worker.update()  # no-op, just ensures lock familiarity
                with self._worker._lock:
                    self._worker._last_image = img

        if img is None:
            raise RuntimeError("No screenshot available yet (still initializing or paused).")
        return img