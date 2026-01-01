import threading
import time
from typing import Optional

from base_core.framework.guard.guard import Guard
from base_core.framework.services.runnable_service_base import RunnableServiceBase
from base_core.framework.concurrency.interfaces import ITaskRunner, StreamHandle
from base_core.math.models import Angle, AngleUnit
from phase_control.io.rotator.interfaces import IRotatorController


ROT_ANGLE = Angle(90, AngleUnit.DEG)             
POLL_S = 0.01                


class RandomizationEngine(RunnableServiceBase):
    def __init__(self, *, rotator_worker: IRotatorController, cpu: ITaskRunner) -> None:
        super().__init__()
        self._rotator = rotator_worker
        self._cpu = cpu
        self._handle: Optional[StreamHandle] = None
        self._rotation_speed: int = 70

        self._sign = +1
        self._stop_req = threading.Event()
        self._reset_after_stop = False

    @property
    def rotation_speed(self) -> int:
        return self._rotation_speed

    @rotation_speed.setter
    def rotation_speed(self, value: int) -> None:
        Guard.not_none(value)
        self._rotation_speed = int(value)
        self.reset()
            
    def start(self) -> None:
        self._stop_req.clear()
        self._reset_after_stop = False
        super().start()

        self._rotator.request_set_speed(self._rotation_speed)
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
        self._stop_req.set()
        super().stop()
        if self._handle:
            self._handle.stop()
            self._handle = None 

    def reset(self) -> None:
        self._reset_after_stop = True
        self.stop()

    def _producer(self, stop: threading.Event):
        while not stop.is_set() and not self._stop_req.is_set():
            while self._rotator.is_busy and not stop.is_set() and not self._stop_req.is_set():
                time.sleep(POLL_S)

            if stop.is_set() or self._stop_req.is_set():
                break

            angle = Angle(self._sign * ROT_ANGLE)  # <- sicher
            self._sign *= -1
            yield angle

        while self._rotator.is_busy:
            time.sleep(POLL_S)

    def _on_angle(self, angle: Angle) -> None:
        if self._stop_req.is_set():
            return
        self._rotator.request_rotation(angle)

    def _on_complete(self) -> None:
        self._handle = None

        if self._reset_after_stop:
            self._reset_after_stop = False
            self._sign = +1
            self._rotator.request_homing()
            self._rotator.request_set_speed(self._rotation_speed)

    def _on_error(self, e: BaseException) -> None:
        import traceback
        traceback.print_exception(type(e), e, e.__traceback__)
        self._handle = None
        super().stop()
