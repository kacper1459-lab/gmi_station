"""
Panel konfiguracji Moku:Pro — frontend wejść i parametry FRA.
"""

from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QFormLayout, QHBoxLayout,
    QComboBox, QDoubleSpinBox, QSpinBox, QLabel
)

from core.config import MokuChannelMap, MokuFrontend, FRAParams


# Opcje dostępne w Moku:Pro
IMPEDANCE_OPTIONS = ['50Ohm', '1MOhm']
COUPLING_OPTIONS = ['AC', 'DC']
RANGE_OPTIONS = ['400mVpp', '4Vpp', '40Vpp']


class MokuConfigPanel(QGroupBox):
    """Konfiguracja Moku:Pro: impedancja wejść, zakres, coupling, FRA params."""

    def __init__(self, parent=None):
        super().__init__("Moku:Pro", parent)

        layout = QVBoxLayout()

        # --- Mapowanie kanałów ---
        layout.addWidget(QLabel("Mapowanie kanałów:"))
        form_ch = QFormLayout()
        form_ch.setSpacing(4)

        self.spin_output_ch = QSpinBox()
        self.spin_output_ch.setRange(1, 4)
        form_ch.addRow("Wyjście (OUT):", self.spin_output_ch)

        self.spin_ch_v1 = QSpinBox()
        self.spin_ch_v1.setRange(1, 4)
        form_ch.addRow("Kanał V1 (przed R_REF):", self.spin_ch_v1)

        self.spin_ch_v2 = QSpinBox()
        self.spin_ch_v2.setRange(1, 4)
        form_ch.addRow("Kanał V2 (na próbce):", self.spin_ch_v2)

        layout.addLayout(form_ch)

        # --- Frontend V1 ---
        layout.addWidget(QLabel("Frontend — kanał V1 (referencja):"))
        form_v1 = QFormLayout()
        form_v1.setSpacing(4)

        self.combo_imp_v1 = QComboBox()
        self.combo_imp_v1.addItems(IMPEDANCE_OPTIONS)
        form_v1.addRow("Impedancja:", self.combo_imp_v1)

        self.combo_coupling_v1 = QComboBox()
        self.combo_coupling_v1.addItems(COUPLING_OPTIONS)
        form_v1.addRow("Coupling:", self.combo_coupling_v1)

        self.combo_range_v1 = QComboBox()
        self.combo_range_v1.addItems(RANGE_OPTIONS)
        form_v1.addRow("Zakres:", self.combo_range_v1)

        layout.addLayout(form_v1)

        # --- Frontend V2 ---
        layout.addWidget(QLabel("Frontend — kanał V2 (pomiarowy):"))
        form_v2 = QFormLayout()
        form_v2.setSpacing(4)

        self.combo_imp_v2 = QComboBox()
        self.combo_imp_v2.addItems(IMPEDANCE_OPTIONS)
        form_v2.addRow("Impedancja:", self.combo_imp_v2)

        self.combo_coupling_v2 = QComboBox()
        self.combo_coupling_v2.addItems(COUPLING_OPTIONS)
        form_v2.addRow("Coupling:", self.combo_coupling_v2)

        self.combo_range_v2 = QComboBox()
        self.combo_range_v2.addItems(RANGE_OPTIONS)
        form_v2.addRow("Zakres:", self.combo_range_v2)

        layout.addLayout(form_v2)

        # --- FRA ---
        layout.addWidget(QLabel("Parametry FRA:"))
        form_fra = QFormLayout()
        form_fra.setSpacing(4)

        self.spin_avg_time = QDoubleSpinBox()
        self.spin_avg_time.setRange(0.001, 10.0)
        self.spin_avg_time.setDecimals(3)
        self.spin_avg_time.setSuffix(" s")
        self.spin_avg_time.setSingleStep(0.01)
        form_fra.addRow("Averaging time:", self.spin_avg_time)

        self.spin_settle_time = QDoubleSpinBox()
        self.spin_settle_time.setRange(0.001, 10.0)
        self.spin_settle_time.setDecimals(3)
        self.spin_settle_time.setSuffix(" s")
        self.spin_settle_time.setSingleStep(0.01)
        form_fra.addRow("Settling time:", self.spin_settle_time)

        self.spin_avg_cycles = QSpinBox()
        self.spin_avg_cycles.setRange(1, 1000)
        form_fra.addRow("Averaging cycles:", self.spin_avg_cycles)

        self.spin_settle_cycles = QSpinBox()
        self.spin_settle_cycles.setRange(1, 1000)
        form_fra.addRow("Settling cycles:", self.spin_settle_cycles)

        self.spin_margin = QDoubleSpinBox()
        self.spin_margin.setRange(0.01, 0.5)
        self.spin_margin.setDecimals(2)
        self.spin_margin.setSingleStep(0.01)
        form_fra.addRow("Sweep margin (±):", self.spin_margin)

        layout.addLayout(form_fra)
        layout.addStretch()
        self.setLayout(layout)

    # -----------------------------------------------------------------

    def set_from_config(self, ch: MokuChannelMap, fe: MokuFrontend, fra: FRAParams):
        self.spin_output_ch.setValue(ch.output_ch)
        self.spin_ch_v1.setValue(ch.ch_v1)
        self.spin_ch_v2.setValue(ch.ch_v2)

        self.combo_imp_v1.setCurrentText(fe.impedance)
        self.combo_coupling_v1.setCurrentText(fe.coupling)
        self.combo_range_v1.setCurrentText(fe.range_v1)

        self.combo_imp_v2.setCurrentText(fe.impedance)
        self.combo_coupling_v2.setCurrentText(fe.coupling)
        self.combo_range_v2.setCurrentText(fe.range_v2)

        self.spin_avg_time.setValue(fra.averaging_time)
        self.spin_settle_time.setValue(fra.settling_time)
        self.spin_avg_cycles.setValue(fra.averaging_cycles)
        self.spin_settle_cycles.setValue(fra.settling_cycles)
        self.spin_margin.setValue(fra.sweep_margin)

    def apply_to_config(self, ch: MokuChannelMap, fe: MokuFrontend, fra: FRAParams):
        ch.output_ch = self.spin_output_ch.value()
        ch.ch_v1 = self.spin_ch_v1.value()
        ch.ch_v2 = self.spin_ch_v2.value()

        fe.impedance = self.combo_imp_v1.currentText()
        fe.coupling = self.combo_coupling_v1.currentText()
        fe.range_v1 = self.combo_range_v1.currentText()
        fe.range_v2 = self.combo_range_v2.currentText()

        fra.averaging_time = self.spin_avg_time.value()
        fra.settling_time = self.spin_settle_time.value()
        fra.averaging_cycles = self.spin_avg_cycles.value()
        fra.settling_cycles = self.spin_settle_cycles.value()
        fra.sweep_margin = self.spin_margin.value()
