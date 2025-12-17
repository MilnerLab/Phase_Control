# phase_control/modules/stabilization/engine.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, cast

import numpy as np

from base_lib.functions import usCFG_projection
from base_lib.models import Angle
from elliptec.elliptec_ell14 import ElliptecRotator

from phase_control.core.models import Spectrum
from phase_control.io.interfaces import FrameBufferProtocol
from phase_control.modules.stabilization.config import AnalysisConfig, FitParameter
from phase_control.modules.stabilization.phase_corrector import PhaseCorrector
from phase_control.modules.stabilization.phase_tracker import PhaseTracker


@dataclass
class AnalysisPlotResult:
    """
    Everything the UI needs after a single analysis step.
    """
    x: np.ndarray
    y_current: np.ndarray
    y_fit: Optional[np.ndarray]
    y_zero_phase: Optional[np.ndarray]
    current_phase: Optional[Angle]
    correction_angle: Optional[Angle]
    spectrum: Spectrum


class AnalysisEngine:
    """
    Core analysis engine for the phase stabilization module.

    - pulls spectra from a FrameBufferProtocol
    - tracks the current phase via PhaseTracker
    - computes fit and zero-phase reference curves
    - computes a correction angle via PhaseCorrector
    - sends the correction to the ElliptecRotator
    """

    def __init__(
        self,
        config: AnalysisConfig,
        buffer: FrameBufferProtocol,
    ) -> None:
        self.config = config
        self._buffer = buffer
        self._phase_tracker = PhaseTracker(cast(AnalysisConfig, self.config))
        self._phase_corrector = PhaseCorrector()
        self._rotator = ElliptecRotator(max_address="0")

    def reset(self) -> None:
        """
        Reset internal state (phase tracking), keep current config.
        """
        self._phase_tracker = PhaseTracker(self.config)

    def step(self) -> Optional[AnalysisPlotResult]:
        """
        Perform a single analysis step.

        Returns:
            AnalysisPlotResult if a new spectrum was available,
            otherwise None (nothing to update).
        """
        spectrum = self._buffer.get_latest()
        if spectrum is None:
            return None

        # Cut spectrum to configured wavelength range
        spectrum = spectrum.cut(self.config.wavelength_range)

        # Update phase tracker
        self._phase_tracker.update(spectrum)
        current_phase: Optional[Angle] = self._phase_tracker.current_phase

        # Compute fit and zero-phase reference
        try:
            kwargs_fit = self.config.to_fit_kwargs(usCFG_projection)
            y_fit = usCFG_projection(spectrum.wavelengths_nm, **kwargs_fit)

            kwargs_zero = dict(kwargs_fit)
            if "phase" in kwargs_zero:
                kwargs_zero["phase"] = 0.0
            y_zero = usCFG_projection(spectrum.wavelengths_nm, **kwargs_zero)
        except Exception:
            y_fit = None
            y_zero = None

        # Compute and send correction
        correction_angle: Optional[Angle] = None
        if current_phase is not None:
            correction_angle = self._phase_corrector.update(current_phase)
            self._rotator.rotate(correction_angle)

        x = np.asarray(spectrum.wavelengths_nm, dtype=float)
        y_current = np.asarray(spectrum.intensity, dtype=float)
        y_fit_arr = None if y_fit is None else np.asarray(y_fit, dtype=float)
        y_zero_arr = None if y_zero is None else np.asarray(y_zero, dtype=float)

        return AnalysisPlotResult(
            x=x,
            y_current=y_current,
            y_fit=y_fit_arr,
            y_zero_phase=y_zero_arr,
            current_phase=current_phase,
            correction_angle=correction_angle,
            spectrum=spectrum,
        )
