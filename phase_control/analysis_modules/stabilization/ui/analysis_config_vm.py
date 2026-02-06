from PySide6.QtCore import Signal
from base_core.framework.events import EventBus
from base_qt.view_models.runnable_vm import IUiDispatcher
from base_qt.view_models.thread_safe_vm_base import ThreadSafeVMBase, ui_thread
from phase_control.analysis_modules.stabilization.config import AnalysisConfig
from phase_control.analysis_modules.stabilization.domain.events import TOPIC_NEW_ANALYSIS_CONFIG

class AnalysisConfigVM(ThreadSafeVMBase):
    config_changed = Signal()
    is_running_changed = Signal(bool)

    def __init__(self, ui: IUiDispatcher, bus: EventBus, config: AnalysisConfig) -> None:
        super().__init__(ui, bus)
        self.config = config
        self._is_running = False
        self.sub_event(TOPIC_NEW_ANALYSIS_CONFIG, self.notify_config_changed)

    def is_running(self) -> bool:
        return self._is_running

    @ui_thread
    def set_is_running(self, v: bool) -> None:
        v = bool(v)
        if self._is_running == v:
            return
        self._is_running = v
        self.is_running_changed.emit(v)

    @ui_thread
    def notify_config_changed(self, payload = None) -> None:
        self.config_changed.emit()
