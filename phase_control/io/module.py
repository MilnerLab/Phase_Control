from cProfile import label
from base_core.framework.json.json_endpoint import JsonlSubprocessEndpoint
from base_core.framework.modules import BaseModule
from base_qt.views.registry.enums import ViewKind
from base_qt.views.registry.interfaces import IViewRegistry
from base_qt.views.registry.models import ViewSpec
from phase_control.app.module import AppModule
from phase_control.core.concurrency.runners import IRotatorTaskRunner, ISpectrometerTaskRunner
from phase_control.io.rotator.interfaces import IRotatorController
from phase_control.io.rotator.rotator_worker import RotatorController
from phase_control.io.rotator.ui.rotator_settings_view import RotatorSettingsView
from phase_control.io.rotator.ui.rotator_settings_vm import ELL14Config, RotatorSettingsViewModel
from phase_control.io.spectrometer.frame_buffer import FrameBuffer
from phase_control.io.spectrometer.interfaces import IFrameBuffer
from phase_control.io.spectrometer.spectrometer_service import SpectrometerService
from phase_control.io.spectrometer.ui.spectrometer_settings_view import SpectrometerSettingsView
from phase_control.io.spectrometer.ui.spectrometer_settings_vm import SpectrometerSettingsViewModel
from spm_002.config import PYTHON32_PATH, SpectrometerConfig
from base_core.framework.app.enums import AppStatus



class IOModule(BaseModule):
    requires = (AppModule,)

    def register(self, c, ctx) -> None:
        
        c.register_singleton(IFrameBuffer, lambda c: FrameBuffer())
        
        c.register_singleton(JsonlSubprocessEndpoint, lambda c: JsonlSubprocessEndpoint(argv=[PYTHON32_PATH, "-u", "-m", "spm_002.spectrometer_server"],))
        c.register_singleton(SpectrometerService, lambda c: SpectrometerService(
                io=c.get(ISpectrometerTaskRunner),
                endpoint=c.get(JsonlSubprocessEndpoint),
                bus=ctx.event_bus,                 
                buffer=c.get(IFrameBuffer)))
        
        c.register_factory(RotatorSettingsViewModel, lambda c: RotatorSettingsViewModel(c.get(IRotatorController)))
        c.register_factory(RotatorSettingsView, lambda c: RotatorSettingsView(RotatorSettingsViewModel))
        
        c.register_singleton(ELL14Config, lambda c: ELL14Config())
        c.register_singleton(
            IRotatorController,
            lambda c: RotatorController(
                port="COM6",
                io=c.get(IRotatorTaskRunner),
                config=c.get(ELL14Config)))
        
        c.register_factory(SpectrometerSettingsViewModel, lambda c: SpectrometerSettingsViewModel(c.get(SpectrometerService)))
        c.register_factory(SpectrometerSettingsView, lambda c: SpectrometerSettingsView(c.get(SpectrometerSettingsViewModel)))
        
        reg = c.get(IViewRegistry)
        reg.register(
            ViewSpec(
                id=RotatorSettingsView.id(),
                title="Rotator Settings",
                kind=ViewKind.POPOUT,
                factory=lambda: c.get(RotatorSettingsView),
                order=0,
            ))
        reg.register(
            ViewSpec(
                id=SpectrometerSettingsView.id(),
                title="Rotator Settings",
                kind=ViewKind.POPOUT,
                factory=lambda: c.get(SpectrometerSettingsView),
                order=0,
            )
        )

    def on_startup(self, c, ctx) -> None:
        if ctx.status is AppStatus.OFFLINE:
            return
        spectrometer: SpectrometerService = c.get(SpectrometerService)
        spectrometer.start()
        spectrometer.set_config_async()
        c.get(IRotatorController).open()

    def on_shutdown(self, c, ctx) -> None:
        c.get(IRotatorController).close()
        c.get(SpectrometerService).stop()
