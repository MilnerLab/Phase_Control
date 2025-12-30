from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, cast, Any

import threading
import time
import numpy as np

from base_core.framework.services.runnable_service_base import RunnableServiceBase
from base_core.framework.concurrency.interfaces import ITaskRunner, StreamHandle
from base_core.framework.events.event_bus import EventBus

from base_core.math.functions import usCFG_projection
from base_core.math.models import Angle
from phase_control.analysis_modules.stabilization.config import AnalysisConfig
from phase_control.analysis_modules.stabilization.domain.phase_corrector import PhaseCorrector
from phase_control.analysis_modules.stabilization.domain.phase_tracker import PhaseTracker
from phase_control.core.models import Spectrum
from phase_control.io.events import TOPIC_NEW_SPECTRUM
from phase_control.io.rotator.interfaces import IRotatorController
from phase_control.io.spectrometer.interfaces import IFrameBuffer

# importier das aus deinem IO-Modul / topics file
# from phase_control.io.spectrometer.topics import TOPIC_NEW_SPECTRUM

@dataclass
class AnalysisPlotResult:
    x: np.ndarray
    y_current: np.ndarray
    y_fit: Optional[np.ndarray]
    y_zero_phase: Optional[np.ndarray]
    current_phase: Optional[Angle]
    correction_angle: Optional[Angle]
    spectrum: Spectrum


class AnalysisEngine(RunnableServiceBase):
    def __init__(
        self,
        *,
        config: AnalysisConfig,
        buffer: IFrameBuffer,
        rotator_worker: IRotatorController,
        bus: EventBus,
        cpu: ITaskRunner,
        poll_interval_s: float = 0.01,
    ) -> None:
        super().__init__()
        self.config = config
        self._buffer = buffer
        self._rotator = rotator_worker
        self._bus = bus
        self._cpu = cpu
        self._poll = poll_interval_s

        self._phase_tracker = PhaseTracker(cast(AnalysisConfig, self.config))
        self._phase_corrector = PhaseCorrector()

        # result callback (VM sets/unsets in bind/unbind)
        self._on_result: Optional[Callable[[AnalysisPlotResult], None]] = None
        self._cb_lock = threading.Lock()

        # lifecycle / concurrency
        self._lock = threading.RLock()
        self._handle: Optional[StreamHandle] = None
        self._unsub_new_spec: Optional[Callable[[], None]] = None

        # gating: “new spectrum pending”
        self._pending_event = threading.Event()
        self._pending_lock = threading.Lock()
        self._pending_payload: Any = None  # we only need “a signal”; payload optional

    # -------------------------------------------------------------- #
    # public API
    # -------------------------------------------------------------- #
    def set_on_result(self, cb: Optional[Callable[[AnalysisPlotResult], None]]) -> None:
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
            key="cpu.analysis",
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
        self._pending.clear()
        
    def reset(self) -> None:
        # keep subscriptions/stream running (if you want), but reset analysis state
        self._phase_tracker = PhaseTracker(self.config)

    # -------------------------------------------------------------- #
    # Stream driver
    # -------------------------------------------------------------- #
    def _on_new_spectrum(self, _args) -> None:
        # Keep it short. We only latch latest spectrum.
        spec = self._buffer.get_latest()
        if spec is None:
            return
        with self._pending_lock:
            self._latest = spec
        self._pending.set()

    def _producer(self, stop: threading.Event):
        while not stop.is_set():
            if not self._pending.wait(timeout=0.1):
                continue

            # take newest spectrum (coalesce)
            with self._pending_lock:
                spec = self._latest
                self._latest = None
                self._pending.clear()

            if spec is None:
                continue

            # wait for rotator idle; while waiting, keep coalescing newest spectrum
            while self._rotator.is_busy and not stop.is_set():
                if self._pending.is_set():
                    with self._pending_lock:
                        spec = self._latest or spec
                        self._latest = None
                        self._pending.clear()
                time.sleep(0.01)

            if stop.is_set():
                break

            yield spec
    def _on_spectrum(self, spec: Spectrum) -> None:
        res = self.step(spec)
        if res is None:
            return

        with self._cb_lock:
            cb = self._on_result
        if cb is not None:
            cb(res)  # runs on CPU worker thread; VM should only Signal.emit()

    def _on_error(self, e: BaseException) -> None:
        # optional: publish/log error
        with self._lock:
            self._handle = None
            if self._unsub_new_spec is not None:
                self._unsub_new_spec()
                self._unsub_new_spec = None
            super().stop()

    def _on_complete(self) -> None:
        with self._lock:
            self._handle = None
            if self._unsub_new_spec is not None:
                self._unsub_new_spec()
                self._unsub_new_spec = None
            super().stop()

    # -------------------------------------------------------------- #
    # Single analysis step
    # -------------------------------------------------------------- #
    def step(self, spectrum: Spectrum) -> Optional[AnalysisPlotResult]:
        if spectrum is None:
            return None

        spectrum = spectrum.cut(self.config.wavelength_range)

        x = np.asarray(spectrum.wavelengths_nm, dtype=float)
        y_current = np.asarray(spectrum.intensity, dtype=float)

        self._phase_tracker.update(spectrum)
        current_phase: Optional[Angle] = self._phase_tracker.current_phase

        y_fit_arr: Optional[np.ndarray] = None
        y_zero_arr: Optional[np.ndarray] = None
        correction_angle: Optional[Angle] = None

        if current_phase is not None:
            try:
                fit_kwargs = self.config.to_fit_kwargs(usCFG_projection)
                y_fit_arr = np.asarray(
                    usCFG_projection(spectrum.wavelengths_nm, **fit_kwargs),
                    dtype=float,
                )

                zero_kwargs = dict(fit_kwargs)
                zero_kwargs["phase"] = 0.0
                y_zero_arr = np.asarray(
                    usCFG_projection(spectrum.wavelengths_nm, **zero_kwargs),
                    dtype=float,
                )
            except Exception:
                y_fit_arr = None
                y_zero_arr = None
            
            correction_angle = self._phase_corrector.update(current_phase)
            self._rotator.request_rotation(correction_angle)

        return AnalysisPlotResult(
            x=x,
            y_current=y_current,
            y_fit=y_fit_arr,
            y_zero_phase=y_zero_arr,
            current_phase=current_phase,
            correction_angle=correction_angle,
            spectrum=spectrum,
        )
