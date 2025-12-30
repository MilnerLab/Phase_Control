from base_core.framework.concurrency.task_runner import ITaskRunner
from elliptec.base.enums import StatusCode
from elliptec.elliptec_ell14 import Rotator
from phase_control.io.rotator.interfaces import IRotatorController


class RotatorController(IRotatorController):
    def __init__(self, port: str, io: ITaskRunner):
        self._port = port
        self._runner = io
        self._rotator = None 
         
    @property
    def is_busy(self) -> bool:
        if (self._rotator is None or self._rotator.status == StatusCode.OK):
            return False
        return True
    
    def open(self):
        def work() -> None:
            r = self._ensure_open()
            r.home()
        self._runner.run(lambda: work, key="rotator")
        
    def close(self):
        self._runner.run(lambda: self._ensure_open().close, key="rotator")
        self._rotator = None
        
    def _ensure_open(self):
        if self._rotator is None:
            r = Rotator(port=self._port)
            r.open()
            self._rotator = r
        return self._rotator

    def request_rotation(self, angle):
        if angle != 0:
            self._runner.run(
                lambda: self._ensure_open().rotate(angle),
                key="rotator",
                cancel_previous=True,
                drop_outdated=True,
            )
