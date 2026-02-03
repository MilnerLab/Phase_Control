# your_app/app.py
from __future__ import annotations

import logging
import sys
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtWidgets import QApplication



# ---- base_qt (Qt adapters) ----
from base_core.framework.app import AppContext
from base_core.framework.concurrency.task_runner import TaskRunner
from base_core.framework.di import Container
from base_core.framework.events import EventBus
from base_core.framework.lifecycle.cleanup_collection import CleanupCollection
from base_core.framework.log import setup_logging
from base_core.framework.modules import ModuleManager
from base_qt.app.dispatcher import QtDispatcher
from phase_control.analysis_modules.envelope.module import EnvelopeModule
from phase_control.analysis_modules.randomize.module import RandomizationModule
from phase_control.analysis_modules.stabilization.module import StabilizationModule
from phase_control.app.module import AppModule
from phase_control.app.ui.main_window_view import MainWindowView
from phase_control.core.concurrency.runners import ICpuTaskRunner, IIoTaskRunner
from phase_control.core.module import CoreModule
from phase_control.io.module import IOModule
from base_qt.app.interfaces import IUiDispatcher




def build_context() -> AppContext:
    log = setup_logging("your_app", level=logging.INFO)

    lifecycle = CleanupCollection()
    bus = EventBus()
    ctx = AppContext(
        config={
            "app_name": "Your App",
            "rotator_port": "COM6",
        },
        log=log,
        event_bus=bus,
        lifecycle=lifecycle,
    )

    return ctx


def build_container(ctx: AppContext) -> Container:
    c = Container()

    c.register_instance(AppContext, ctx)

    io_exec = ThreadPoolExecutor(max_workers=2, thread_name_prefix="io")
    cpu_exec = ThreadPoolExecutor(max_workers=1, thread_name_prefix="cpu") 

    c.register_singleton(IIoTaskRunner, lambda c: TaskRunner(io_exec))
    c.register_singleton(ICpuTaskRunner, lambda c: TaskRunner(cpu_exec))
    
    c.register_singleton(IUiDispatcher, lambda c: QtDispatcher())

    ctx.lifecycle.add(lambda: io_exec.shutdown(wait=False))
    ctx.lifecycle.add(lambda: cpu_exec.shutdown(wait=False))

    return c


def get_modules():
    # Add feature modules here (hybrid approach: shell + feature modules)
    return [
        AppModule(),
        CoreModule(),
        IOModule(),
        StabilizationModule(),
        RandomizationModule(),
        EnvelopeModule(),
        # AnalysisModule(),
    ]


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv

    app = QApplication(argv)

    ctx = build_context()
    c = build_container(ctx)

    # Bootstrap modules (register + start; stop happens via lifecycle shutdown)
    ModuleManager(get_modules()).bootstrap(c, ctx)

    # Resolve and show main window (ShellModule should register AppMainWindowView as factory)
    win = c.get(MainWindowView)
    win.show()

    rc = app.exec()

    # Stop modules + cleanup
    ctx.lifecycle.clear()
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
