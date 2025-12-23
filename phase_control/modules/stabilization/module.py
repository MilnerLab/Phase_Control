# phase_control/modules/stabilization/module.py
from __future__ import annotations

from typing import Optional

from tkinter import ttk

from base_core.framework.modules import BaseModule
from phase_control.modules.stabilization.config import AnalysisConfig
from phase_control.modules.stabilization.engine import AnalysisEngine
from phase_control.modules.stabilization.ui.config_panel import ConfigPanel
from phase_control.modules.stabilization.ui.plot_panel import PlotPanel


class StabilizationModule(BaseModule):
   