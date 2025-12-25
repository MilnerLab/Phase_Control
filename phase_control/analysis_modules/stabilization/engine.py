from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, cast

import numpy as np


from base_core.math.functions import usCFG_projection
from base_core.math.models import Angle
from phase_control.core.models import Spectrum
from phase_control.core.rotator.rotator_worker import RotatorWorker
from phase_control.io.interfaces import IFrameBuffer
from phase_control.modules.stabilization.config import AnalysisConfig
from phase_control.modules.stabilization.domain.phase_corrector import PhaseCorrector
from phase_control.modules.stabilization.domain.phase_tracker import PhaseTracker

@dataclass
class AnalysisPlotResult:
    """
    Data structure containing everything the UI needs after a single
    analysis step.
    """
    x: np.ndarray
    y_current: np.ndarray
    y_fit: Optional[np.ndarray]
    y_zero_phase: Optional[np.ndarray]
    current_phase: Optional[Angle]
    correction_angle: Optional[Angle]
    spectrum: Spectrum


class AnalysisEngine:
    def __init__(
        self,
        config: AnalysisConfig,
        buffer: IFrameBuffer,
        *,
        rotator_port: str = "COM6",
        rotator_address: str = "0",
    ) -> None:
        self.config = config
        self._buffer = buffer
        self._phase_tracker = PhaseTracker(cast(AnalysisConfig, self.config))
        self._phase_corrector = PhaseCorrector()
        self._rotator = RotatorWorker(port=rotator_port, address=rotator_address)

        
        self._last_phase: Optional[Angle] = None
        self._last_correction: Optional[Angle] = None
        self._last_fit: Optional[np.ndarray] = None
        self._last_zero: Optional[np.ndarray] = None

    # -------------------------------------------------------------- #
    # Lifecycle
    # -------------------------------------------------------------- #

    def reset(self) -> None:
        """
        Reset internal analysis state (PhaseTracker etc.) but keep
        the current config and the RotatorWorker alive.
        """
        self._phase_tracker = PhaseTracker(self.config)
        self._last_phase = None
        self._last_correction = None
        self._last_fit = None
        self._last_zero = None

    def close(self) -> None:
        """Shut down the RotatorWorker (call once at program shutdown)."""
        self._rotator.close()

    # -------------------------------------------------------------- #
    # Single analysis step
    # -------------------------------------------------------------- #

    def step(self) -> Optional[AnalysisPlotResult]:
        spectrum = self._buffer.get_latest()
        if spectrum is None:
            return None

        spectrum = spectrum.cut(self.config.wavelength_range)

        x = np.asarray(spectrum.wavelengths_nm, dtype=float)
        y_current = np.asarray(spectrum.intensity, dtype=float)

        # ---------- Case 1: rotator is busy -> only update plot ---------- #
        if self._rotator.is_busy:
            return AnalysisPlotResult(
                x=x,
                y_current=y_current,
                y_fit=self._last_fit,
                y_zero_phase=self._last_zero,
                current_phase=self._last_phase,
                correction_angle=self._last_correction,
                spectrum=spectrum,
            )

        # ---------- Case 2: rotator is idle -> full analysis ------------ #
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

            
            self._last_phase = current_phase
            self._last_correction = correction_angle
            self._last_fit = y_fit_arr
            self._last_zero = y_zero_arr

        return AnalysisPlotResult(
            x=x,
            y_current=y_current,
            y_fit=y_fit_arr,
            y_zero_phase=y_zero_arr,
            current_phase=current_phase,
            correction_angle=correction_angle,
            spectrum=spectrum,
        )
