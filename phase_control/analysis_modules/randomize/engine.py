import threading
import time
from typing import Optional

from base_core.framework.guard.guard import Guard
from base_core.framework.services.runnable_service_base import RunnableServiceBase
from base_core.framework.concurrency.interfaces import ITaskRunner, StreamHandle
from base_core.math.models import Angle, AngleUnit
from phase_control.io.rotator.interfaces import IRotatorController


ROT_ANGLE = Angle(90, AngleUnit.DEG)             # fixed step angle
POLL_S = 0.01                # busy polling interval


class RandomizationEngine(RunnableServiceBase):
    def __init__(self, *, rotator_worker: IRotatorController, cpu: ITaskRunner) -> None:
        super().__init__()
        self._rotator = rotator_worker
        self._cpu = cpu
        self._handle: Optional[StreamHandle] = None
        self._rotation_speed: int = None

        self._sign = +1
        self._stop_req = threading.Event()
        self._reset_after_stop = False

    def set_rotation_speed(self, percent: int) -> None:
            Guard.not_none(percent)
            self._rotation_speed = percent
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
        # graceful stop request: no new moves, but finish current one
        self._stop_req.set()
        super().stop()
        if self._handle:
            self._handle.stop()  # does NOT "join"; it just requests stop

    def reset(self) -> None:
        # request reset AFTER the graceful stop completed
        self._reset_after_stop = True
        self.stop()

    def _producer(self, stop: threading.Event):
        # normal loop: produce next angle only while not stopping
        while not stop.is_set() and not self._stop_req.is_set():
            while self._rotator.is_busy and not stop.is_set() and not self._stop_req.is_set():
                time.sleep(POLL_S)

            if stop.is_set() or self._stop_req.is_set():
                break

            angle = Angle(self._sign * ROT_ANGLE)  # <- sicher
            self._sign *= -1
            yield angle

        # drain: if a move is currently running, wait until it finishes
        while self._rotator.is_busy:
            time.sleep(POLL_S)

    def _on_angle(self, angle: Angle) -> None:
        # don't start new motion after stop was requested
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

        # Hinweis: dein RunnableServiceBase.reset() würde jetzt nichts machen,
        # weil is_running False ist. Wenn du unbedingt auf NEW willst, musst du
        # die Basisklasse anpassen (reset auch im STOPPED erlauben).

    def _on_error(self, e: BaseException) -> None:
        import traceback
        traceback.print_exception(type(e), e, e.__traceback__)
        self._handle = None
        super().stop()
