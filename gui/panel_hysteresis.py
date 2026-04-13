"""
Panel definiowania pętli histerezy — siatka prądów.
"""

from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QFormLayout, QHBoxLayout,
    QDoubleSpinBox, QLabel, QPushButton
)

from core.config import CurrentGrid, TimingParams
from core.grid import build_grid, total_hysteresis_points


class HysteresisPanel(QGroupBox):
    """Definiowanie siatki prądów magnesujących."""

    def __init__(self, parent=None):
        super().__init__("Pętla histerezy", parent)

        layout = QVBoxLayout()
        form = QFormLayout()
        form.setSpacing(4)

        self.spin_i_max = QDoubleSpinBox()
        self.spin_i_max.setRange(0.01, 10.0)
        self.spin_i_max.setDecimals(2)
        self.spin_i_max.setSuffix(" A")
        form.addRow("I_MAX:", self.spin_i_max)

        layout.addLayout(form)
        layout.addWidget(QLabel("Strefa gęsta (piki GMI):"))
        form1 = QFormLayout()

        self.spin_dense_limit = QDoubleSpinBox()
        self.spin_dense_limit.setRange(0.001, 5.0)
        self.spin_dense_limit.setDecimals(3)
        self.spin_dense_limit.setSuffix(" A")
        form1.addRow("  Zakres 0 …", self.spin_dense_limit)

        self.spin_dense_step = QDoubleSpinBox()
        self.spin_dense_step.setRange(0.0001, 1.0)
        self.spin_dense_step.setDecimals(4)
        self.spin_dense_step.setSuffix(" A")
        form1.addRow("  Krok:", self.spin_dense_step)

        layout.addLayout(form1)
        layout.addWidget(QLabel("Strefa średnia:"))
        form2 = QFormLayout()

        self.spin_medium_limit = QDoubleSpinBox()
        self.spin_medium_limit.setRange(0.001, 5.0)
        self.spin_medium_limit.setDecimals(3)
        self.spin_medium_limit.setSuffix(" A")
        form2.addRow("  Zakres …", self.spin_medium_limit)

        self.spin_medium_step = QDoubleSpinBox()
        self.spin_medium_step.setRange(0.0001, 1.0)
        self.spin_medium_step.setDecimals(4)
        self.spin_medium_step.setSuffix(" A")
        form2.addRow("  Krok:", self.spin_medium_step)

        layout.addLayout(form2)
        layout.addWidget(QLabel("Strefa rzadka (nasycenie):"))
        form3 = QFormLayout()

        self.spin_coarse_step = QDoubleSpinBox()
        self.spin_coarse_step.setRange(0.001, 1.0)
        self.spin_coarse_step.setDecimals(3)
        self.spin_coarse_step.setSuffix(" A")
        form3.addRow("  Krok:", self.spin_coarse_step)

        layout.addLayout(form3)

        # Timing
        layout.addWidget(QLabel("Timing:"))
        form4 = QFormLayout()

        self.spin_settling = QDoubleSpinBox()
        self.spin_settling.setRange(0.01, 10.0)
        self.spin_settling.setDecimals(2)
        self.spin_settling.setSuffix(" s")
        form4.addRow("  Stabilizacja pola:", self.spin_settling)

        self.spin_polarity = QDoubleSpinBox()
        self.spin_polarity.setRange(0.1, 10.0)
        self.spin_polarity.setDecimals(1)
        self.spin_polarity.setSuffix(" s")
        form4.addRow("  Przełączanie polar.:", self.spin_polarity)

        layout.addLayout(form4)

        # Info
        self.lbl_info = QLabel()
        layout.addWidget(self.lbl_info)

        btn_preview = QPushButton("Przelicz siatkę")
        btn_preview.clicked.connect(self._update_info)
        layout.addWidget(btn_preview)

        # Connect spinboxes to auto-update
        for spin in [self.spin_i_max, self.spin_dense_limit, self.spin_dense_step,
                     self.spin_medium_limit, self.spin_medium_step, self.spin_coarse_step,
                     self.spin_settling]:
            spin.valueChanged.connect(self._update_info)

        layout.addStretch()
        self.setLayout(layout)

    def _update_info(self):
        try:
            grid_cfg = self._build_grid_config()
            grid = build_grid(grid_cfg)
            n = total_hysteresis_points(grid_cfg)
            t_est = n * (self.spin_settling.value() + 0.5)
            self.lbl_info.setText(
                f"Punktów siatki: {len(grid)} | "
                f"Histereza: {n} pkt | "
                f"~{t_est/60:.1f} min"
            )
        except Exception:
            self.lbl_info.setText("Błąd parametrów")

    def _build_grid_config(self) -> CurrentGrid:
        return CurrentGrid(
            i_max=self.spin_i_max.value(),
            dense_limit=self.spin_dense_limit.value(),
            dense_step=self.spin_dense_step.value(),
            medium_limit=self.spin_medium_limit.value(),
            medium_step=self.spin_medium_step.value(),
            coarse_step=self.spin_coarse_step.value(),
        )

    def set_from_config(self, grid: CurrentGrid, timing: TimingParams):
        self.spin_i_max.setValue(grid.i_max)
        self.spin_dense_limit.setValue(grid.dense_limit)
        self.spin_dense_step.setValue(grid.dense_step)
        self.spin_medium_limit.setValue(grid.medium_limit)
        self.spin_medium_step.setValue(grid.medium_step)
        self.spin_coarse_step.setValue(grid.coarse_step)
        self.spin_settling.setValue(timing.settling_field)
        self.spin_polarity.setValue(timing.settling_polarity)
        self._update_info()

    def apply_to_config(self, grid: CurrentGrid, timing: TimingParams):
        grid.i_max = self.spin_i_max.value()
        grid.dense_limit = self.spin_dense_limit.value()
        grid.dense_step = self.spin_dense_step.value()
        grid.medium_limit = self.spin_medium_limit.value()
        grid.medium_step = self.spin_medium_step.value()
        grid.coarse_step = self.spin_coarse_step.value()
        timing.settling_field = self.spin_settling.value()
        timing.settling_polarity = self.spin_polarity.value()
