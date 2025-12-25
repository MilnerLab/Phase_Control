# phase_control/modules/__init__.py
from __future__ import annotations

from typing import Dict

from .base import BaseModule, ModuleContext, ModuleFactory
from .stabilization.module import StabilizationModule
from .randomize.module import RandomizeModule
from .envelope.module import EnvelopeModule

# Registry of all available modules.
MODULES: Dict[str, ModuleFactory] = {
    "Phase stabilization": StabilizationModule,
    "Randomize": RandomizeModule,
    "Min/Max envelope": EnvelopeModule,
}

__all__ = [
    "BaseModule",
    "ModuleContext",
    "ModuleFactory",
    "MODULES",
]
