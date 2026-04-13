"""
Panel sterowania ręcznego — bezpośrednie ustawianie prądu i polaryzacji.
Emergency stop.
"""

from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QFormLayout,
    QDoubleSpinBox, QPushButton, QLabel, QRadioButton, QButtonGroup
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont


class ManualControlPanel(QGroupBox):
    """Ręczne sterowanie zasilaczem i polaryzacją."""

    emergency_stop = Signal()
    current_requested = Signal(float)
    polarity_requested = Signal(str)      # '+' or '-'
    output_on_requested = Signal()
    output_off_requested = Signal()

    def __init__(self, parent=None):
        super().__init__("Sterowanie ręczne", parent)

        layout = QVBoxLayout()

        # Emergency stop
        self.btn_estop = QPushButton("⚠ EMERGENCY STOP ⚠")
        self.btn_estop.setMinimumHeight(50)
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.btn_estop.setFont(font)
        self.btn_estop.setStyleSheet(
            "QPushButton { background-color: #e74c3c; color: white; "
            "border: 2px solid #c0392b; border-radius: 6px; }"
            "QPushButton:pressed { background-color: #c0392b; }"
        )
        self.btn_estop.clicked.connect(self.emergency_stop.emit)
        layout.addWidget(self.btn_estop)

        # Prąd
        form = QFormLayout()
        self.spin_current = QDoubleSpinBox()
        self.spin_current.setRange(0.0, 5.0)
        self.spin_current.setDecimals(4)
        self.spin_current.setSuffix(" A")
        self.spin_current.setSingleStep(0.01)
        form.addRow("Prąd:", self.spin_current)
        layout.addLayout(form)

        # Polaryzacja
        pol_row = QHBoxLayout()
        self.radio_pos = QRadioButton("Polaryzacja +")
        self.radio_neg = QRadioButton("Polaryzacja −")
        self.radio_pos.setChecked(True)

        self.pol_group = QButtonGroup()
        self.pol_group.addButton(self.radio_pos)
        self.pol_group.addButton(self.radio_neg)

        pol_row.addWidget(self.radio_pos)
        pol_row.addWidget(self.radio_neg)
        layout.addLayout(pol_row)

        # Przyciski
        btn_row = QHBoxLayout()

        self.btn_set = QPushButton("Ustaw prąd")
        self.btn_set.clicked.connect(self._on_set_current)
        btn_row.addWidget(self.btn_set)

        self.btn_on = QPushButton("Wyjście ON")
        self.btn_on.clicked.connect(self.output_on_requested.emit)
        btn_row.addWidget(self.btn_on)

        self.btn_off = QPushButton("Wyjście OFF")
        self.btn_off.clicked.connect(self.output_off_requested.emit)
        btn_row.addWidget(self.btn_off)

        layout.addLayout(btn_row)

        # Odczyt aktualny
        self.lbl_actual = QLabel("I = --- A | H = --- A/m")
        layout.addWidget(self.lbl_actual)

        layout.addStretch()
        self.setLayout(layout)

    def _on_set_current(self):
        val = self.spin_current.value()
        pol = '+' if self.radio_pos.isChecked() else '-'
        self.polarity_requested.emit(pol)
        self.current_requested.emit(val)

    def update_readout(self, current: float, h_field: float):
        self.lbl_actual.setText(f"I = {current:+.4f} A | H = {h_field:+.1f} A/m")

    def set_enabled(self, enabled: bool):
        self.spin_current.setEnabled(enabled)
        self.btn_set.setEnabled(enabled)
        self.btn_on.setEnabled(enabled)
        self.btn_off.setEnabled(enabled)
        self.radio_pos.setEnabled(enabled)
        self.radio_neg.setEnabled(enabled)
