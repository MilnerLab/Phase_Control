from __future__ import annotations

import threading
import time
from typing import Optional

from base_core.math.models import Angle
from elliptec.elliptec_ell14 import Rotator, StatusCode


class RotatorWorker:
    """
    Background worker around the Elliptec Rotator.

    Idea:
      - AnalysisEngine does NOT call rotator.rotate(...) directly.
      - Instead, it calls request_rotation(angle), which is non-blocking.
      - This worker runs in its own thread, performs the actual rotation
        and polls the status in the background.
      - The engine can query is_busy to decide whether it should perform
        a new analysis step or just keep plotting the latest spectrum.
    """

    def __init__(self, port: str, address: str) -> None:
        self._rotator = Rotator(port=port, address=address)

        self._request_lock = threading.Lock()
        self._requested_angle: Optional[Angle] = None

        self._stop_event = threading.Event()

        # These flags are written by the worker thread and read
        # by the analysis/UI thread.
        self._busy: bool = False
        self._status: StatusCode = StatusCode.OK

        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    # ------------------- public API ------------------- #

    def request_rotation(self, angle: Angle) -> None:
        """
        Non-blocking: remember the desired angle.

        If this is called multiple times in quick succession, only the
        most recent angle will actually be executed (intermediate
        requests are overwritten).
        """
        with self._request_lock:
            self._requested_angle = angle

    @property
    def is_busy(self) -> bool:
        """True while the rotator is working (according to StatusCode)."""
        return self._busy

    @property
    def status(self) -> StatusCode:
        """Last known status (cached, non-blocking)."""
        return self._status

    def close(self) -> None:
        """
        Stop the worker thread and clean up.

        Call this once at program shutdown.
        """
        self._stop_event.set()
        self._thread.join(timeout=2.0)
        # If your Rotator has a close() / disconnect method, call it here:
        # self._rotator.close()

    # ------------------- internal worker loop ------------------- #

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            # 1) Get the current requested angle (and clear the request)
            with self._request_lock:
                angle = self._requested_angle
                self._requested_angle = None

            if angle is None:
                # Nothing to do → short sleep to avoid a busy loop
                time.sleep(0.01)
                continue

            try:
                # We now execute this rotation request
                self._busy = True

                # a) Start the motion (may already block, depending on API)
                self._rotator.rotate(angle)

                # b) Poll the status until the rotator is no longer BUSY
                status = self._rotator.status
                self._status = status

                while (
                    status == StatusCode.BUSY
                    and not self._stop_event.is_set()
                ):
                    time.sleep(0.02)
                    status = self._rotator.status
                    self._status = status

                # Here you could handle error codes explicitly
                # e.g. OUT_OF_RANGE, MOTOR_ERROR, etc.
            except Exception:
                # Something went wrong with the connection / device
                self._status = StatusCode.COMMUNICATION_TIMEOUT
            finally:
                self._busy = False
