from base_core.framework.concurrency.task_runner import ITaskRunner
from base_core.math.models import Angle
from elliptec.base.enums import StatusCode
from elliptec.elliptec_ell14 import Rotator
from phase_control.io.rotator.interfaces import IRotatorController


class RotatorController(IRotatorController):
    def __init__(self, port: str, io: ITaskRunner):
        self._port = port
        self._runner = io
        self._rotator: Rotator | None = None

    @property
    def is_busy(self) -> bool:
        r = self._rotator
        if r is None:
            return False
        return r.status != StatusCode.OK

    def open(self) -> None:
        def work() -> None:
            r = self._ensure_open()
            r.home()
        self._runner.run(work, key="rotator.open", cancel_previous=True)

    def close(self) -> None:
        def work() -> None:
            if self._rotator is not None:
                self._rotator.close()
        self._runner.run(work, key="rotator.close", cancel_previous=True)
        import threading
        print("THREAD:", threading.current_thread().name)
        self._rotator = None

    def request_rotation(self, angle: Angle) -> None:
        if angle == 0:
            return

        self._runner.run(
            lambda: self._ensure_open().rotate(angle),
            key="rotator.rotate",
            cancel_previous=True,
            drop_outdated=True,
        )
    
    def request_homing(self) -> None:
        self._runner.run(
            lambda: self._ensure_open().home(),
            key="rotator.home",
            cancel_previous=True,
            drop_outdated=True,
        )
        
    def request_set_speed(self, percent: int) -> None:
        self._runner.run(
            lambda: self._ensure_open().set_speed(percent),
            key="rotator.set_speed",
            cancel_previous=True,
            drop_outdated=True,
        )

    def _ensure_open(self) -> Rotator:
        if self._rotator is None:
            r = Rotator()
            r.open(port=self._port)
            self._rotator = r
        return self._rotator