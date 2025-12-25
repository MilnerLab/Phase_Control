from base_core.framework.modules import BaseModule
from phase_control.app.module import AppModule
from phase_control.core.concurrency.runners import IIoTaskRunner
from phase_control.io.frame_buffer import FrameBuffer
from phase_control.io.service import SpectrometerAcquisitionService
from phase_control.io.stream_client import SpectrometerStreamClient


class IOModule(BaseModule):
    requires = (AppModule,)

    def register(self, c, ctx) -> None:
        c.register_singleton(FrameBuffer, lambda c: FrameBuffer())
        c.register_singleton(SpectrometerStreamClient, lambda c: SpectrometerStreamClient())
        c.register_singleton(
            SpectrometerAcquisitionService,
            lambda c: SpectrometerAcquisitionService(
                io=c.get(IIoTaskRunner),
                bus=ctx.event_bus,                 
                buffer=c.get(FrameBuffer),
                client=c.get(SpectrometerStreamClient),
            ),
        )

    def on_startup(self, c, ctx) -> None:
        c.get(SpectrometerAcquisitionService).start()

    def on_shutdown(self, c, ctx) -> None:
        c.get(SpectrometerAcquisitionService).stop()
