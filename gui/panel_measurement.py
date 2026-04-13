"""
Panel sterowania pomiarem — start, stop, progress, zapis.
"""

import time
from pathlib import Path

from PySide6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QLabel, QProgressBar, QLineEdit, QFileDialog
)
from PySide6.QtCore import Signal


class MeasurementPanel(QGroupBox):
    """Start/stop pomiaru, progress bar, wybór lokalizacji zapisu."""

    start_requested = Signal()
    stop_requested = Signal()

    def __init__(self, parent=None):
        super().__init__("Pomiar GMI", parent)

        layout = QVBoxLayout()

        # Ścieżka zapisu
        path_row = QHBoxLayout()
        path_row.addWidget(QLabel("Katalog:"))
        self.edit_directory = QLineEdit(str(Path.cwd()))
        path_row.addWidget(self.edit_directory, stretch=1)
        btn_browse = QPushButton("...")
        btn_browse.setFixedWidth(40)
        btn_browse.clicked.connect(self._browse_directory)
        path_row.addWidget(btn_browse)
        layout.addLayout(path_row)

        # Nazwa pliku
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Nazwa:"))
        self.edit_filename = QLineEdit(self._default_filename())
        name_row.addWidget(self.edit_filename, stretch=1)
        btn_auto = QPushButton("Auto")
        btn_auto.setFixedWidth(50)
        btn_auto.clicked.connect(
            lambda: self.edit_filename.setText(self._default_filename())
        )
        name_row.addWidget(btn_auto)
        layout.addLayout(name_row)

        # Przyciski start/stop
        btn_row = QHBoxLayout()
        self.btn_start = QPushButton("▶ START POMIAR")
        self.btn_start.setMinimumHeight(40)
        self.btn_start.setStyleSheet(
            "QPushButton { background-color: #27ae60; color: white; "
            "font-weight: bold; font-size: 13px; border-radius: 4px; }"
            "QPushButton:disabled { background-color: #95a5a6; }"
        )
        self.btn_start.clicked.connect(self.start_requested.emit)
        btn_row.addWidget(self.btn_start)

        self.btn_stop = QPushButton("■ STOP")
        self.btn_stop.setMinimumHeight(40)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet(
            "QPushButton { background-color: #e67e22; color: white; "
            "font-weight: bold; font-size: 13px; border-radius: 4px; }"
            "QPushButton:disabled { background-color: #95a5a6; }"
        )
        self.btn_stop.clicked.connect(self.stop_requested.emit)
        btn_row.addWidget(self.btn_stop)

        layout.addLayout(btn_row)

        # Progress
        self.progress = QProgressBar()
        self.progress.setTextVisible(True)
        layout.addWidget(self.progress)

        # Status
        self.lbl_status = QLabel("Gotowy")
        layout.addWidget(self.lbl_status)

        self.setLayout(layout)

    def get_output_path(self) -> str:
        directory = self.edit_directory.text()
        filename = self.edit_filename.text()
        return str(Path(directory) / filename)

    def set_running(self, running: bool):
        self.btn_start.setEnabled(not running)
        self.btn_stop.setEnabled(running)
        self.edit_directory.setReadOnly(running)
        self.edit_filename.setReadOnly(running)

    def set_progress(self, current: int, total: int):
        self.progress.setMaximum(total)
        self.progress.setValue(current)
        pct = current / total * 100 if total > 0 else 0
        self.progress.setFormat(f"{current}/{total} ({pct:.0f}%)")

    def set_status(self, text: str):
        self.lbl_status.setText(text)

    def _browse_directory(self):
        d = QFileDialog.getExistingDirectory(self, "Wybierz katalog zapisu")
        if d:
            self.edit_directory.setText(d)

    @staticmethod
    def _default_filename() -> str:
        return f"gmi_{int(time.time())}.csv"
