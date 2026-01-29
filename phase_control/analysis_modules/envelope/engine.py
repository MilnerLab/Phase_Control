from __future__ import annotations

from typing import Callable, Optional

import threading
import time

from base_core.framework.services.runnable_service_base import RunnableServiceBase
from base_core.framework.concurrency.interfaces import ITaskRunner, StreamHandle
from base_core.framework.events.event_bus import EventBus

from phase_control.core.models import Spectrum
from phase_control.io.events import TOPIC_NEW_SPECTRUM
from phase_control.io.rotator.interfaces import IRotatorController
from phase_control.io.spectrometer.interfaces import IFrameBuffer

from phase_control.analysis_modules.envelope.domain.envelope_signal_generator import (
    EnvelopeSignalGenerator,
    EnvelopeSignalGeneratorConfig,
)


class EnvelopeEngine(RunnableServiceBase):
    """
    Same stream/pending concept as AnalysisEngine:
      - subscribe to TOPIC_NEW_SPECTRUM
      - coalesce latest spectrum
      - wait until rotator idle
      - step(): ask generator for correction angle
      - rotator.request_rotation(correction)
      - call _on_result with debug curves
    """

    def __init__(
        self,
        *,
        config: EnvelopeSignalGeneratorConfig,
        buffer: IFrameBuffer,
        rotator_worker: IRotatorController,
        bus: EventBus,
        cpu: ITaskRunner,
    ) -> None:
        super().__init__()
        self._buffer = buffer
        self._rotator = rotator_worker
        self._bus = bus
        self._cpu = cpu

        self._generator = EnvelopeSignalGenerator(config)

        # result callback (VM sets/unsets in bind/unbind)
        self._on_result: Optional[Callable[[dict[str, Spectrum]], None]] = None
        self._cb_lock = threading.Lock()

        # lifecycle / concurrency
        self._lock = threading.RLock()
        self._handle: Optional[StreamHandle] = None
        self._unsub: Optional[Callable[[], None]] = None

        # gating: “new spectrum pending”
        self._pending_event = threading.Event()
        self._pending_lock = threading.Lock()
        self._latest: Optional[Spectrum] = None

    # -------------------------------------------------------------- #
    # public API
    # -------------------------------------------------------------- #
    def set_on_result(self, cb: Optional[Callable[[dict[str, Spectrum]], None]]) -> None:
        with self._cb_lock:
            self._on_result = cb

    # -------------------------------------------------------------- #
    # Lifecycle
    # -------------------------------------------------------------- #
    def start(self) -> None:
        super().start()

        self._unsub = self._bus.subscribe(TOPIC_NEW_SPECTRUM, self._on_new_spectrum)

        self._handle = self._cpu.stream(
            self._producer,
            on_item=self._on_spectrum,
            on_error=self._on_error,
            on_complete=self._on_complete,
            key="cpu.envelope",
            cancel_previous=True,
            drop_outdated=True,
        )

    def stop(self) -> None:
        super().stop()

        if self._handle:
            self._handle.stop()
            self._handle = None
        if self._unsub:
            self._unsub()
            self._unsub = None
        self._pending_event.clear()

    # -------------------------------------------------------------- #
    # Stream driver
    # -------------------------------------------------------------- #
    def _on_new_spectrum(self, _args) -> None:
        spec = self._buffer.get_latest()
        if spec is None:
            return
        with self._pending_lock:
            self._latest = spec
        self._pending_event.set()

    def _producer(self, stop: threading.Event):
        while not stop.is_set():
            if not self._pending_event.wait(timeout=0.1):
                continue

            # take newest spectrum (coalesce)
            with self._pending_lock:
                spec = self._latest
                self._latest = None
                self._pending_event.clear()

            if spec is None:
                continue

            # wait for rotator idle; while waiting, keep coalescing newest spectrum
            while self._rotator.is_busy and not stop.is_set():
                if self._pending_event.is_set():
                    with self._pending_lock:
                        spec = self._latest or spec
                        self._latest = None
                        self._pending_event.clear()
                time.sleep(0.01)

            if stop.is_set():
                break

            yield spec

    def _on_spectrum(self, spec: Spectrum) -> None:
        try:
            out = self.step(spec)
            if out is None:
                return

            with self._cb_lock:
                cb = self._on_result
            if cb is None:
                return

            cb(out)
        except Exception:
            import traceback
            traceback.print_exc()

    def _on_error(self, _e: BaseException) -> None:
        with self._lock:
            self._handle = None
            if self._unsub:
                self._unsub()
                self._unsub = None
            super().stop()

    def _on_complete(self) -> None:
        with self._lock:
            self._handle = None
            if self._unsub:
                self._unsub()
                self._unsub = None
            super().stop()

    # -------------------------------------------------------------- #
    # Single analysis step
    # -------------------------------------------------------------- #
    def step(self, spectrum: Spectrum) -> Optional[dict[str, Spectrum]]:
        correction, out = self._generator.update(spectrum)
        if correction is None:
            return None

        self._rotator.request_rotation(correction)
        return out
