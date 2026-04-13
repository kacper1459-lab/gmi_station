"""
Panel parametrów pomiarowych — konfiguracja elektryczna i cewek.
"""

from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QDoubleSpinBox, QLineEdit, QPushButton, QListWidget,
    QListWidgetItem, QAbstractItemView, QWidget
)
from PySide6.QtCore import Qt

from core.config import ElectricalParams, CoilParams


class ParametersPanel(QGroupBox):
    """Parametry elektryczne: R_ref, amplituda, stała cewki, częstotliwości."""

    def __init__(self, parent=None):
        super().__init__("Parametry pomiarowe", parent)

        layout = QVBoxLayout()

        # --- Parametry skalarne ---
        form = QFormLayout()
        form.setSpacing(4)

        self.spin_r_ref = QDoubleSpinBox()
        self.spin_r_ref.setRange(0.1, 10000)
        self.spin_r_ref.setDecimals(1)
        self.spin_r_ref.setSuffix(" Ω")
        form.addRow("R_REF:", self.spin_r_ref)

        self.spin_amplitude = QDoubleSpinBox()
        self.spin_amplitude.setRange(0.01, 2.0)
        self.spin_amplitude.setDecimals(2)
        self.spin_amplitude.setSuffix(" Vpp")
        self.spin_amplitude.setSingleStep(0.05)
        form.addRow("Amplituda Moku:", self.spin_amplitude)

        self.spin_z_load = QDoubleSpinBox()
        self.spin_z_load.setRange(0.1, 10000)
        self.spin_z_load.setDecimals(1)
        self.spin_z_load.setSuffix(" Ω")
        form.addRow("Z_LOAD (kalibracja):", self.spin_z_load)

        self.spin_coil_const = QDoubleSpinBox()
        self.spin_coil_const.setRange(1, 100000)
        self.spin_coil_const.setDecimals(2)
        self.spin_coil_const.setSuffix(" A/m per A")
        form.addRow("Stała cewek:", self.spin_coil_const)

        layout.addLayout(form)

        # --- Lista częstotliwości ---
        layout.addWidget(QLabel("Częstotliwości pomiarowe:"))

        freq_row = QHBoxLayout()
        self.freq_list = QListWidget()
        self.freq_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.freq_list.setMaximumHeight(120)
        freq_row.addWidget(self.freq_list)

        freq_btns = QVBoxLayout()
        self.spin_new_freq = QDoubleSpinBox()
        self.spin_new_freq.setRange(0.001, 600)
        self.spin_new_freq.setDecimals(3)
        self.spin_new_freq.setSuffix(" MHz")
        self.spin_new_freq.setValue(50.0)
        freq_btns.addWidget(self.spin_new_freq)

        btn_add = QPushButton("Dodaj")
        btn_add.clicked.connect(self._add_frequency)
        freq_btns.addWidget(btn_add)

        btn_remove = QPushButton("Usuń zaznaczone")
        btn_remove.clicked.connect(self._remove_selected)
        freq_btns.addWidget(btn_remove)

        freq_btns.addStretch()
        freq_row.addLayout(freq_btns)
        layout.addLayout(freq_row)

        self.setLayout(layout)

    def _add_frequency(self):
        f_mhz = self.spin_new_freq.value()
        f_hz = f_mhz * 1e6
        for i in range(self.freq_list.count()):
            existing = self.freq_list.item(i).data(Qt.UserRole)
            if abs(existing - f_hz) < 1e3:
                return
        item = QListWidgetItem(f"{f_mhz:.3f} MHz")
        item.setData(Qt.UserRole, f_hz)
        self.freq_list.addItem(item)
        self._sort_list()

    def _remove_selected(self):
        for item in self.freq_list.selectedItems():
            self.freq_list.takeItem(self.freq_list.row(item))

    def _sort_list(self):
        items = []
        for i in range(self.freq_list.count()):
            item = self.freq_list.item(i)
            items.append((item.data(Qt.UserRole), item.text()))
        self.freq_list.clear()
        for f_hz, text in sorted(items):
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, f_hz)
            self.freq_list.addItem(item)

    def get_frequencies_hz(self) -> list[float]:
        freqs = []
        for i in range(self.freq_list.count()):
            freqs.append(self.freq_list.item(i).data(Qt.UserRole))
        return sorted(freqs)

    def set_from_config(self, elec: ElectricalParams, coil: CoilParams):
        self.spin_r_ref.setValue(elec.r_ref)
        self.spin_amplitude.setValue(elec.amplitude_vpp)
        self.spin_z_load.setValue(elec.z_load_true)
        self.spin_coil_const.setValue(coil.constant)

        self.freq_list.clear()
        for f_hz in elec.frequencies_hz:
            f_mhz = f_hz / 1e6
            item = QListWidgetItem(f"{f_mhz:.3f} MHz")
            item.setData(Qt.UserRole, f_hz)
            self.freq_list.addItem(item)

    def apply_to_config(self, elec: ElectricalParams, coil: CoilParams):
        elec.r_ref = self.spin_r_ref.value()
        elec.amplitude_vpp = self.spin_amplitude.value()
        elec.z_load_true = self.spin_z_load.value()
        elec.frequencies_hz = self.get_frequencies_hz()
        coil.constant = self.spin_coil_const.value()
