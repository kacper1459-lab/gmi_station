"""
Panel kalibracji OSL — interaktywna procedura Open/Short/Load.
"""

from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit
)
from PySide6.QtCore import Signal


class CalibrationPanel(QGroupBox):
    """Moduł kalibracji OSL z wizualnym statusem kroków."""

    calibration_requested = Signal()
    save_cal_requested = Signal()
    load_cal_requested = Signal()

    def __init__(self, parent=None):
        super().__init__("Kalibracja OSL", parent)

        layout = QVBoxLayout()

        # Status kroków
        self.lbl_open = QLabel("● OPEN:  oczekuje")
        self.lbl_short = QLabel("● SHORT: oczekuje")
        self.lbl_load = QLabel("● LOAD:  oczekuje")

        for lbl in [self.lbl_open, self.lbl_short, self.lbl_load]:
            lbl.setStyleSheet("color: #888;")

        layout.addWidget(self.lbl_open)
        layout.addWidget(self.lbl_short)
        layout.addWidget(self.lbl_load)

        # Log
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(100)
        layout.addWidget(self.log)

        # Przyciski — rząd 1: nowa kalibracja
        btn_row1 = QHBoxLayout()
        self.btn_start = QPushButton("Nowa kalibracja OSL")
        self.btn_start.clicked.connect(self.calibration_requested.emit)
        btn_row1.addWidget(self.btn_start)

        self.lbl_status = QLabel("")
        btn_row1.addWidget(self.lbl_status)
        btn_row1.addStretch()
        layout.addLayout(btn_row1)

        # Przyciski — rząd 2: zapisz / wczytaj
        btn_row2 = QHBoxLayout()
        self.btn_save_cal = QPushButton("Zapisz kalibrację...")
        self.btn_save_cal.clicked.connect(self.save_cal_requested.emit)
        self.btn_save_cal.setEnabled(False)
        btn_row2.addWidget(self.btn_save_cal)

        self.btn_load_cal = QPushButton("Wczytaj kalibrację...")
        self.btn_load_cal.clicked.connect(self.load_cal_requested.emit)
        btn_row2.addWidget(self.btn_load_cal)

        btn_row2.addStretch()
        layout.addLayout(btn_row2)

        self.setLayout(layout)

    def set_step_done(self, step: str):
        """Oznacz krok jako zakończony: 'OPEN', 'SHORT', 'LOAD'."""
        lbl = {'OPEN': self.lbl_open, 'SHORT': self.lbl_short,
               'LOAD': self.lbl_load}.get(step)
        if lbl:
            lbl.setText(f"✓ {step}: OK")
            lbl.setStyleSheet("color: #27ae60; font-weight: bold;")

    def set_step_active(self, step: str):
        lbl = {'OPEN': self.lbl_open, 'SHORT': self.lbl_short,
               'LOAD': self.lbl_load}.get(step)
        if lbl:
            lbl.setText(f"→ {step}: w toku...")
            lbl.setStyleSheet("color: #2980b9; font-weight: bold;")

    def reset_steps(self):
        self.lbl_open.setText("● OPEN:  oczekuje")
        self.lbl_short.setText("● SHORT: oczekuje")
        self.lbl_load.setText("● LOAD:  oczekuje")
        for lbl in [self.lbl_open, self.lbl_short, self.lbl_load]:
            lbl.setStyleSheet("color: #888;")
        self.log.clear()

    def append_log(self, text: str):
        self.log.append(text)

    def set_status(self, text: str):
        self.lbl_status.setText(text)

    def set_enabled(self, enabled: bool):
        self.btn_start.setEnabled(enabled)
