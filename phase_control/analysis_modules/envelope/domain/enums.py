# phase_control/analysis_modules/envelope/ui/envelope_view_mode.py
from __future__ import annotations
from enum import Enum


class EnvelopeMode(str, Enum):
    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"
