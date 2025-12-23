# your_app/app.py
from __future__ import annotations

import logging
import sys
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtWidgets import QApplication



# ---- base_qt (Qt adapters) ----
from base_core.framework.app import AppContext, Lifecycle
from base_core.framework.concurrency import ITaskRunner, TaskRunner
from base_core.framework.di import Container
from base_core.framework.events import EventBus
from base_core.framework.log import setup_logging
from base_core.framework.modules import ModuleManager
from base_qt.app.dispatcher import QtDispatcher
from phase_control.app.main_window_view import MainWindowView
from phase_control.app.module import AppModule

# from your_app.modules.spectrometer.module import SpectrometerModule
# from your_app.modules.analysis.module import AnalysisModule


def build_context() -> AppContext:
    log = setup_logging("your_app", level=logging.INFO)

    lifecycle = Lifecycle()
    events = EventBus()
    executor = ThreadPoolExecutor(max_workers=4)
    ui = QtDispatcher()
    ctx = AppContext(
        config={
            "app_name": "Your App",
        },
        log=log,
        events=events,
        executor=executor,
        lifecycle=lifecycle,
        ui=ui,
    )

    # Ensure executor is closed on shutdown
    ctx.lifecycle.add_shutdown_hook(lambda: executor.shutdown(wait=False))
    return ctx


def build_container(ctx: AppContext) -> Container:
    c = Container()

    # Core singletons / instances
    c.register_instance(AppContext, ctx)

    # One standard async entrypoint
    c.register_singleton(
        ITaskRunner,
        lambda c: TaskRunner(ctx.executor, ui_post=(ctx.ui.post if ctx.ui else None)),
    )

    return c


def get_modules():
    # Add feature modules here (hybrid approach: shell + feature modules)
    return [
        AppModule(),
        # SpectrometerModule(),
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
    ctx.lifecycle.shutdown(log=ctx.log)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
