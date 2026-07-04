import datetime
import threading


class RunnerControl:
    """Coordinates the background refresh loop with the web UI.

    Lets the UI request an immediate refresh or wake the loop early after a
    config change, and exposes the loop's latest status back to the UI.
    """

    def __init__(self):
        self._wake_event = threading.Event()
        self._lock = threading.Lock()
        self.stop_requested = False
        self.manual_refresh_requested = False

        self.last_attempt_at = None
        self.last_success_at = None
        self.last_error = None

    def stop(self):
        self.stop_requested = True
        self._wake_event.set()

    def request_refresh(self):
        self.manual_refresh_requested = True
        self._wake_event.set()

    def notify_config_changed(self):
        self._wake_event.set()

    def wait(self, timeout):
        """Sleeps until timeout or until woken early; clears the wake flag."""
        if self._wake_event.wait(timeout=timeout):
            self._wake_event.clear()

    def record_attempt(self, success, error=None):
        with self._lock:
            self.last_attempt_at = datetime.datetime.now()
            if success:
                self.last_success_at = self.last_attempt_at
                self.last_error = None
            else:
                self.last_error = error

    def snapshot(self):
        with self._lock:
            return {
                "last_attempt_at": self.last_attempt_at,
                "last_success_at": self.last_success_at,
                "last_error": self.last_error,
            }
