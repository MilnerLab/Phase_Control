# phase_control/modules/stabilization/phase_corrector.py
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from base_lib.math.enums import AngleUnit
from base_lib.math.models import Angle



# Starting phase (target) and tolerance
STARTING_PHASE = Angle(0, AngleUnit.DEG)
PHASE_TOLERANCE = Angle(10, AngleUnit.DEG)

# Converts phase error [deg] to half-wave-plate rotation [deg]
CONVERSION_CONST = 1 / 4       # depends on optics
CORRECTION_SIGN = -1           # depends on QWP orientation


@dataclass
class PhaseCorrector:
    """
    Convert a measured phase offset into a physical half-wave-plate
    rotation angle, with wrapping and tolerance logic.
    """
    _correction_angle: Angle = Angle(0, AngleUnit.DEG)

    def update(self, phase: Angle) -> Angle:
        """
        Update the internal correction angle based on the current phase.

        Steps:
          1. wrap phase to [-pi, pi]
          2. compute phase error relative to STARTING_PHASE
          3. if |error| > PHASE_TOLERANCE, convert to HWP rotation
             otherwise, set correction to 0
        """
        phase_wrapped = self._wrap_phase_pi(phase)
        phase_error = Angle(phase_wrapped - STARTING_PHASE)

        if np.abs(phase_error) > PHASE_TOLERANCE:
            correction_phase = phase_error
        else:
            correction_phase = Angle(0)

        self._correction_angle = self._convert_phase_to_hwp(correction_phase)
        return self._correction_angle

    @staticmethod
    def _wrap_phase_pi(phase: Angle) -> Angle:
        """
        Wrap a phase angle to the interval [-pi, pi].
        """
        step = math.pi  # 180 deg
        k = round(phase / step)
        multiple = k * step
        return Angle(phase - multiple)

    @staticmethod
    def _convert_phase_to_hwp(phase: Angle) -> Angle:
        """
        Convert a phase in [rad/deg] to the required half-wave-plate rotation.
        """
        phase_deg = phase.Deg
        hwp_deg = CORRECTION_SIGN * phase_deg * CONVERSION_CONST
        return Angle(hwp_deg, AngleUnit.DEG)
