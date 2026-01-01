from base_core.framework.modules import BaseModule
from phase_control.app.module import AppModule
from phase_control.core.concurrency.runners import IIoTaskRunner
from phase_control.io.rotator.config import ELL14Config
from phase_control.io.rotator.interfaces import IRotatorController
from phase_control.io.rotator.rotator_worker import RotatorController
from phase_control.io.spectrometer.frame_buffer import FrameBuffer
from phase_control.io.spectrometer.acquisition_service import SpectrometerAcquisitionService
from phase_control.io.spectrometer.interfaces import IFrameBuffer
from phase_control.io.spectrometer.stream_client import SpectrometerStreamClient


class IOModule(BaseModule):
    requires = (AppModule,)

    def register(self, c, ctx) -> None:
        c.register_singleton(ELL14Config, lambda c: ELL14Config())
        
        c.register_singleton(IFrameBuffer, lambda c: FrameBuffer())
        c.register_singleton(SpectrometerStreamClient, lambda c: SpectrometerStreamClient())
        c.register_singleton(
            SpectrometerAcquisitionService,
            lambda c: SpectrometerAcquisitionService(
                io=c.get(IIoTaskRunner),
                bus=ctx.event_bus,                 
                buffer=c.get(IFrameBuffer),
                client=c.get(SpectrometerStreamClient),
            ),
        )
        
        c.register_singleton(
            IRotatorController,
            lambda c: RotatorController(
                port="COM6",
                io=c.get(IIoTaskRunner)))

    def on_startup(self, c, ctx) -> None:
        c.get(SpectrometerAcquisitionService).start()
        c.get(IRotatorController).open()

    def on_shutdown(self, c, ctx) -> None:
        c.get(IRotatorController).close()
        c.get(SpectrometerAcquisitionService).stop()
