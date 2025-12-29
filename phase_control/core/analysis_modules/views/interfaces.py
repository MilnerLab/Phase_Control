from typing import Protocol, runtime_checkable

from phase_control.core.analysis_modules.view_models.interfaces import IRunnableVM

@runtime_checkable
class IRunnableView(Protocol):
    @property
    def vm(self) -> IRunnableVM: ...