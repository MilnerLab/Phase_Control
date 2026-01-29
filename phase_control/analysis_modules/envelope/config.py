from dataclasses import dataclass

from base_core.math.models import Angle, Range
from base_core.quantities.enums import Prefix
from base_core.quantities.models import Length
from elliptec.config import AngleUnit
from phase_control.analysis_modules.envelope.domain.enums import EnvelopeMode


@dataclass
class EnvelopeSignalGeneratorConfig:
    wavelength_range: Range[Length] = Range(Length(796, Prefix.NANO), Length(810, Prefix.NANO))
    step_angle: Angle = Angle(1, AngleUnit.DEG)
    
    mode: EnvelopeMode = EnvelopeMode.MAXIMIZE

    # smoothing along wavelength axis
    smooth_window: int = 1  # 1 = off

    # deadband against noise (only flip direction if change is > eps)
    improve_eps: float = 0.0
