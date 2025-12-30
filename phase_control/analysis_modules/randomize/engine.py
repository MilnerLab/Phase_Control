import threading
import time
from typing import Optional

from base_core.framework.services.runnable_service_base import RunnableServiceBase
from base_core.framework.concurrency.interfaces import ITaskRunner, StreamHandle
from base_core.math.models import Angle, AngleUnit
from phase_control.io.rotator.interfaces import IRotatorController


ROTATION_SPEED = 40          # percent
ROT_ANGLE = Angle(90, AngleUnit.DEG)             # fixed step angle
POLL_S = 0.01                # busy polling interval


class RandomizationEngine(RunnableServiceBase):
    def __init__(
        self,
        *,
        rotator_worker: IRotatorController,
        cpu: ITaskRunner,
    ) -> None:
        super().__init__()
        self._rotator = rotator_worker
        self._cpu = cpu

        self._handle: Optional[StreamHandle] = None
        self._sign = +1  # alternates +1 / -1

    def start(self) -> None:
        super().start()

        # optional: make speed change a "busy" command in the controller
        self._rotator.request_set_speed(ROTATION_SPEED)

        self._handle = self._cpu.stream(
            self._producer,
            on_item=self._on_angle,
            on_error=self._on_error,
            on_complete=self._on_complete,
            key="cpu.randomization",
            cancel_previous=True,
            drop_outdated=True,
        )

    def stop(self) -> None:
        super().stop()
        if self._handle:
            self._handle.stop()
            self._handle = None

    def reset(self) -> None:
        self._sign = +1
        self._rotator.request_homing()
        super().reset()

    # ---------------- stream ----------------

    def _producer(self, stop: threading.Event):
        while not stop.is_set():
            # wait until the rotator is idle
            while self._rotator.is_busy and not stop.is_set():
                time.sleep(POLL_S)

            if stop.is_set():
                break

            angle = Angle(self._sign * ROT_ANGLE)
            self._sign *= -1  # alternate sign
            import threading
            print("THREAD:", threading.current_thread().name)
            yield angle

    def _on_angle(self, angle: Angle) -> None:
        # keep exceptions from killing the stream
        try:
            self._rotator.request_rotation(angle)
            import threading
            print("THREAD:", threading.current_thread().name)
        except Exception:
            import traceback
            traceback.print_exc()

    def _on_error(self, e: BaseException) -> None:
        import traceback
        traceback.print_exception(type(e), e, e.__traceback__)
        self._handle = None
        super().stop()

    def _on_complete(self) -> None:
        self._handle = None
        super().stop()
