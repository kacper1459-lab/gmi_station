"""
Panel wizualizacji — wykres ΔZ/Z(H) w czasie rzeczywistym.
"""

import numpy as np
from collections import defaultdict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QCheckBox, QScrollArea, QFileDialog, QLabel, QComboBox
)
from PySide6.QtCore import Qt

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from core.callbacks import MeasurementPoint


COLORS = ['#e67e22', '#e74c3c', '#2c3e50', '#2980b9', '#27ae60',
          '#8e44ad', '#d35400', '#c0392b', '#16a085', '#f39c12']


class PlotPanel(QWidget):
    """Wykres GMI z wyborem częstotliwości i zapisem."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Dane: {freq: {'UP': [(H, Z_mag)], 'DOWN': [(H, Z_mag)]}}
        self._data = defaultdict(lambda: {'UP': [], 'DOWN': []})
        self._freq_colors = {}
        self._freq_checkboxes = {}

        layout = QVBoxLayout(self)

        # Matplotlib figure
        self.figure = Figure(figsize=(10, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas, stretch=1)

        # Kontrolki
        ctrl = QHBoxLayout()

        # Wybór trybu wykresu
        ctrl.addWidget(QLabel("Tryb:"))
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["ΔZ/Z (%)", "|Z| (Ω)"])
        self.combo_mode.currentIndexChanged.connect(self._redraw)
        ctrl.addWidget(self.combo_mode)

        ctrl.addStretch()

        # Przyciski zapisu
        self.btn_save_current = QPushButton("Zapisz widoczny wykres")
        self.btn_save_current.clicked.connect(self._save_current_plot)
        ctrl.addWidget(self.btn_save_current)

        self.btn_save_all = QPushButton("Zapisz wszystkie f osobno")
        self.btn_save_all.clicked.connect(self._save_all_individual)
        ctrl.addWidget(self.btn_save_all)

        layout.addLayout(ctrl)

        # Checkboxy częstotliwości
        self.freq_container = QHBoxLayout()
        self.freq_container.addWidget(QLabel("Częstotliwości:"))
        self.freq_container.addStretch()
        layout.addLayout(self.freq_container)

        self._init_axes()

    def _init_axes(self):
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        self.ax.set_xlabel('H (A/m)', fontsize=12)
        self.ax.set_ylabel(r'$\Delta Z / Z$ (%)', fontsize=12)
        self.ax.tick_params(direction='in', length=5, width=1.2,
                           bottom=True, top=True, left=True, right=True)
        self.figure.tight_layout()

    def set_frequencies(self, freqs_hz: list[float]):
        """Inicjalizacja checkboxów na podstawie listy częstotliwości."""
        # Wyczyść stare checkboxy
        for cb in self._freq_checkboxes.values():
            self.freq_container.removeWidget(cb)
            cb.deleteLater()
        self._freq_checkboxes.clear()

        for idx, f in enumerate(sorted(freqs_hz)):
            color = COLORS[idx % len(COLORS)]
            self._freq_colors[f] = color

            f_mhz = f / 1e6
            cb = QCheckBox(f"{f_mhz:.0f} MHz")
            cb.setChecked(True)
            cb.setStyleSheet(f"color: {color}; font-weight: bold;")
            cb.stateChanged.connect(self._redraw)
            self._freq_checkboxes[f] = cb
            self.freq_container.insertWidget(
                self.freq_container.count() - 1, cb
            )

    def add_point(self, point: MeasurementPoint):
        """Dodaje punkt i odrysowuje wykres."""
        self._data[point.freq_hz][point.branch].append(
            (point.h_field, point.z_cal_mag)
        )
        self._redraw()

    def clear_data(self):
        self._data.clear()
        self._redraw()

    def _redraw(self):
        mode = self.combo_mode.currentIndex()  # 0 = GMI%, 1 = |Z|
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)

        if mode == 0:
            self.ax.set_ylabel(r'$\Delta Z / Z$ (%)', fontsize=12)
        else:
            self.ax.set_ylabel('|Z| (Ω)', fontsize=12)
        self.ax.set_xlabel('H (A/m)', fontsize=12)

        for f in sorted(self._data.keys()):
            cb = self._freq_checkboxes.get(f)
            if cb and not cb.isChecked():
                continue

            color = self._freq_colors.get(f, '#333333')
            f_mhz = f / 1e6

            # Z_ref = min across both branches
            all_z = []
            for branch in ['UP', 'DOWN']:
                all_z.extend([p[1] for p in self._data[f][branch]])
            if not all_z:
                continue
            z_ref = min(all_z)

            for branch in ['UP', 'DOWN']:
                pts = self._data[f][branch]
                if not pts:
                    continue
                h = np.array([p[0] for p in pts])
                z = np.array([p[1] for p in pts])

                if mode == 0 and z_ref > 1e-12:
                    y = ((z - z_ref) / z_ref) * 100.0
                else:
                    y = z

                ls = '-' if branch == 'UP' else '--'
                label = f"{f_mhz:.0f} MHz" if branch == 'UP' else None
                self.ax.plot(h, y, color=color, linewidth=1.5,
                           linestyle=ls, label=label)

        self.ax.tick_params(direction='in', length=5, width=1.2,
                           bottom=True, top=True, left=True, right=True)
        if any(self._data.values()):
            self.ax.legend(loc='upper right', frameon=True,
                          edgecolor='black', fancybox=False)
        self.figure.tight_layout()
        self.canvas.draw_idle()

    def _save_current_plot(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Zapisz wykres", "gmi_plot.png",
            "PNG (*.png);;PDF (*.pdf);;SVG (*.svg)"
        )
        if path:
            self.figure.savefig(path, dpi=200, bbox_inches='tight')

    def _save_all_individual(self):
        directory = QFileDialog.getExistingDirectory(self, "Wybierz katalog")
        if not directory:
            return

        for f in sorted(self._data.keys()):
            fig = Figure(figsize=(10, 6), dpi=100)
            ax = fig.add_subplot(111)
            f_mhz = f / 1e6
            color = self._freq_colors.get(f, '#333')

            all_z = []
            for branch in ['UP', 'DOWN']:
                all_z.extend([p[1] for p in self._data[f][branch]])
            if not all_z:
                continue
            z_ref = min(all_z)

            for branch in ['UP', 'DOWN']:
                pts = self._data[f][branch]
                if not pts:
                    continue
                h = np.array([p[0] for p in pts])
                z = np.array([p[1] for p in pts])
                gmi = ((z - z_ref) / z_ref) * 100.0 if z_ref > 1e-12 else z

                ls = '-' if branch == 'UP' else '--'
                label = branch
                ax.plot(h, gmi, color=color, linewidth=1.5,
                       linestyle=ls, label=label)

            ax.set_xlabel('H (A/m)', fontsize=12)
            ax.set_ylabel(r'$\Delta Z / Z$ (%)', fontsize=12)
            ax.set_title(f'{f_mhz:.0f} MHz', fontsize=14)
            ax.legend()
            ax.tick_params(direction='in', length=5, width=1.2,
                          bottom=True, top=True, left=True, right=True)
            fig.tight_layout()

            fname = f"{directory}/gmi_{f_mhz:.0f}MHz.png"
            fig.savefig(fname, dpi=200, bbox_inches='tight')
