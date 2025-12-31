from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget

from base_qt.views.bases.view_base import ViewBase
from phase_control.analysis_modules.randomize.ui.randomization_page_vm import RandomizationPageVM
from phase_control.core.plotting.spectrum_plot_view import SpectrumPlotView


class RandomizationPageView(ViewBase[RandomizationPageVM]):
    def build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        # --- header row -----------------------------------------------------
        header = QWidget(self)
        header_l = QHBoxLayout(header)
        header_l.setContentsMargins(0, 0, 0, 0)
        header_l.setSpacing(8)

        header_l.addWidget(QLabel("Movement speed (%)", header))

        self._speed_edit = QLineEdit(header)
        self._speed_edit.setPlaceholderText("0–100")
        self._speed_edit.setFixedWidth(90)
        self._speed_edit.setAlignment(Qt.AlignRight)
        self._speed_edit.setValidator(QIntValidator(0, 100, self._speed_edit))
        self._last_set_speed: int | None = None
        

        self._set_btn = QPushButton("Set", header)
        self._set_btn.setEnabled(False)

        header_l.addWidget(self._speed_edit)
        header_l.addWidget(self._set_btn)
        header_l.addStretch(1)

        root.addWidget(header, 0)

        # --- plot area ------------------------------------------------------
        self._plot_view = SpectrumPlotView(self.vm.plot_vm)
        root.addWidget(self._plot_view, 1)



    def bind(self) -> None:
        super().bind()
        self.connect_binding(self._set_btn.clicked, self._on_set_clicked)
        self.connect_binding(self._speed_edit.textChanged, self._on_speed_text_changed)

    # ---------------- logic ----------------

    @Slot(str)
    def _on_speed_text_changed(self, _text: str) -> None:
        self._update_set_enabled()

    @Slot()
    def _on_set_clicked(self) -> None:
        speed = self._parsed_speed()
        if speed is None:
            return
        
        self.vm.set_rotation_speed(speed)
        self._last_set_speed = speed
        self._update_set_enabled()

        # If the VM applies asynchronously, DON'T set _last_set_speed here.
        # Wait for speed_applied_changed. If it's synchronous, you can do:
        # self._last_set_speed = speed
        # self._update_set_enabled()

    def _parsed_speed(self) -> int | None:
        text = self._speed_edit.text().strip()
        if not text:
            return None
        try:
            v = int(text)
        except ValueError:
            return None
        if not (0 <= v <= 100):
            return None
        return v

    def _update_set_enabled(self) -> None:
        v = self._parsed_speed()
        enabled = v is not None and (self._last_set_speed is None or v != self._last_set_speed)
        self._set_btn.setEnabled(enabled)
