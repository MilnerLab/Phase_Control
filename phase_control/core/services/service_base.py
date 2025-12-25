from abc import ABC, abstractmethod

from phase_control.core.services.enums import ServiceState


class ServiceBase(ABC):
    def __init__(self) -> None:
        self._state = ServiceState.STOPPED

    @property
    def is_running(self) -> bool:
        return self._state == ServiceState.RUNNING

    def start(self) -> None:
        if self.is_running:
            return
        self._state = ServiceState.RUNNING

    def stop(self) -> None:
        if not self.is_running:
            return
        self._state = ServiceState.STOPPED
