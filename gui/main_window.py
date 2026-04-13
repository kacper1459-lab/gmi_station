"""
Główne okno aplikacji GMI Station.

Orkiestruje:
  - inicjalizację/zamykanie driverów
  - kalibrację OSL (w osobnym wątku)
  - pomiar GMI (w osobnym wątku)
  - sterowanie ręczne (w wątku GUI — krótkie operacje)
  - wizualizację w czasie rzeczywistym
"""

import threading
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QTabWidget, QMessageBox, QStatusBar,
    QFileDialog, QMenuBar, QMenu
)
from PySide6.QtCore import Qt, Slot

from core.config import StationConfig
from core.engine import GMIMeasurementEngine

from gui.panel_connection import ConnectionPanel
from gui.panel_parameters import ParametersPanel
from gui.panel_hysteresis import HysteresisPanel
from gui.panel_calibration import CalibrationPanel
from gui.panel_manual import ManualControlPanel
from gui.panel_measurement import MeasurementPanel
from gui.panel_moku import MokuConfigPanel
from gui.panel_plot import PlotPanel
from gui.worker import MeasurementWorker, CalibrationWorker, WorkerSignals, QtCallback


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("GMI Station — Stanowisko pomiarowe")
        self.setMinimumSize(1400, 900)

        self.cfg = StationConfig()
        self.engine: GMIMeasurementEngine | None = None

        # Drivery — None dopóki nie połączone
        self._rigol = None
        self._siglent = None
        self._arduino = None
        self._moku = None

        # Workery
        self._meas_worker: MeasurementWorker | None = None
        self._cal_worker: CalibrationWorker | None = None

        self._build_ui()
        self._build_menu()
        self._load_config_to_ui()
        self._connect_signals()

    # =================================================================
    # UI
    # =================================================================

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_split = QSplitter(Qt.Horizontal)

        # --- Lewy panel (konfiguracja) ---
        left = QTabWidget()
        left.setMaximumWidth(420)

        # Tab: Połączenia + Parametry
        tab_setup = QWidget()
        tab_setup_layout = QVBoxLayout(tab_setup)
        self.panel_conn = ConnectionPanel()
        self.panel_params = ParametersPanel()
        tab_setup_layout.addWidget(self.panel_conn)
        tab_setup_layout.addWidget(self.panel_params)
        tab_setup_layout.addStretch()
        left.addTab(tab_setup, "Konfiguracja")

        # Tab: Histereza
        self.panel_hyst = HysteresisPanel()
        left.addTab(self.panel_hyst, "Histereza")

        # Tab: Moku:Pro
        self.panel_moku = MokuConfigPanel()
        left.addTab(self.panel_moku, "Moku:Pro")

        # Tab: Kalibracja + Pomiar
        tab_measure = QWidget()
        tab_meas_layout = QVBoxLayout(tab_measure)
        self.panel_cal = CalibrationPanel()
        self.panel_meas = MeasurementPanel()
        tab_meas_layout.addWidget(self.panel_cal)
        tab_meas_layout.addWidget(self.panel_meas)
        tab_meas_layout.addStretch()
        left.addTab(tab_measure, "Pomiar")

        # Tab: Sterowanie ręczne
        self.panel_manual = ManualControlPanel()
        left.addTab(self.panel_manual, "Ręczne")

        main_split.addWidget(left)

        # --- Prawy panel (wykres) ---
        self.panel_plot = PlotPanel()
        main_split.addWidget(self.panel_plot)

        main_split.setStretchFactor(0, 0)
        main_split.setStretchFactor(1, 1)

        layout = QHBoxLayout(central)
        layout.addWidget(main_split)

        # Status bar
        self.statusBar().showMessage("Gotowy")

    def _build_menu(self):
        menu = self.menuBar()

        file_menu = menu.addMenu("Plik")
        file_menu.addAction("Wczytaj konfigurację...", self._load_config_file)
        file_menu.addAction("Zapisz konfigurację...", self._save_config_file)
        file_menu.addSeparator()
        file_menu.addAction("Wyjście", self.close)

    def _connect_signals(self):
        # Połączenia
        self.panel_conn.connect_requested.connect(self._connect_devices)
        self.panel_conn.disconnect_requested.connect(self._disconnect_devices)

        # Kalibracja
        self.panel_cal.calibration_requested.connect(self._start_calibration)
        self.panel_cal.save_cal_requested.connect(self._save_calibration)
        self.panel_cal.load_cal_requested.connect(self._load_calibration)

        # Pomiar
        self.panel_meas.start_requested.connect(self._start_measurement)
        self.panel_meas.stop_requested.connect(self._stop_measurement)

        # Sterowanie ręczne
        self.panel_manual.emergency_stop.connect(self._emergency_stop)
        self.panel_manual.current_requested.connect(self._manual_set_current)
        self.panel_manual.polarity_requested.connect(self._manual_set_polarity)
        self.panel_manual.output_on_requested.connect(self._manual_output_on)
        self.panel_manual.output_off_requested.connect(self._manual_output_off)

    def _load_config_to_ui(self):
        self.panel_conn.set_addresses(self.cfg.devices)
        self.panel_params.set_from_config(self.cfg.electrical, self.cfg.coil)
        self.panel_hyst.set_from_config(self.cfg.grid, self.cfg.timing)
        self.panel_moku.set_from_config(self.cfg.channels, self.cfg.frontend, self.cfg.fra)

    def _apply_ui_to_config(self):
        self.cfg.devices = self.panel_conn.get_addresses()
        self.panel_params.apply_to_config(self.cfg.electrical, self.cfg.coil)
        self.panel_hyst.apply_to_config(self.cfg.grid, self.cfg.timing)
        self.panel_moku.apply_to_config(self.cfg.channels, self.cfg.frontend, self.cfg.fra)

    # =================================================================
    # Połączenia
    # =================================================================

    @Slot()
    def _connect_devices(self):
        self._apply_ui_to_config()
        self.statusBar().showMessage("Łączenie z urządzeniami...")

        from drivers.rigol import RigolDP831
        from drivers.siglent import SiglentSDM
        from drivers.arduino import ArduinoRelay
        from drivers.moku_fra import MokuFRA

        ok = {}
        try:
            self._rigol = RigolDP831(
                self.cfg.devices.rigol_visa, self.cfg.coil.rigol_channels
            )
            ok['rigol_visa'] = self._rigol.instrument is not None
        except Exception:
            ok['rigol_visa'] = False

        try:
            self._siglent = SiglentSDM(self.cfg.devices.siglent_visa)
            ok['siglent_visa'] = self._siglent.instrument is not None
        except Exception:
            ok['siglent_visa'] = False

        try:
            self._arduino = ArduinoRelay(self.cfg.devices.arduino_port)
            ok['arduino_port'] = self._arduino.arduino is not None
        except Exception:
            ok['arduino_port'] = False

        try:
            self._moku = MokuFRA(self.cfg)
            self._moku.connect()
            ok['moku_ip'] = self._moku.fra is not None
        except Exception:
            ok['moku_ip'] = False

        for key, success in ok.items():
            self.panel_conn.set_device_status(key, success)

        all_ok = all(ok.values())
        self.panel_conn.set_connected_state(all_ok)

        if all_ok:
            self.engine = GMIMeasurementEngine(self.cfg)
            self.engine.set_drivers(
                self._rigol, self._siglent, self._arduino, self._moku
            )
            # Podpięcie kalibracji wczytanej z pliku przed połączeniem
            if hasattr(self, '_loaded_cal') and self._loaded_cal:
                self.engine.cal = self._loaded_cal
                self._loaded_cal = None
            self.panel_plot.set_frequencies(self.cfg.electrical.frequencies_hz)
            self.statusBar().showMessage("Wszystkie urządzenia połączone")
        else:
            failed = [k for k, v in ok.items() if not v]
            self.statusBar().showMessage(f"Błąd połączenia: {', '.join(failed)}")

    @Slot()
    def _disconnect_devices(self):
        for drv in [self._rigol, self._siglent, self._arduino, self._moku]:
            if drv:
                try:
                    drv.close()
                except Exception:
                    pass

        self._rigol = self._siglent = self._arduino = self._moku = None
        self.engine = None

        self.panel_conn.set_all_idle()
        self.panel_conn.set_connected_state(False)
        self.statusBar().showMessage("Rozłączono")

    # =================================================================
    # Kalibracja
    # =================================================================

    @Slot()
    def _start_calibration(self):
        if not self.engine:
            QMessageBox.warning(self, "Błąd", "Najpierw połącz urządzenia.")
            return

        self._apply_ui_to_config()
        self.engine.cfg = self.cfg
        self.panel_cal.reset_steps()
        self.panel_cal.set_enabled(False)

        self._cal_worker = CalibrationWorker(self.engine)
        self._cal_worker.signals.status.connect(self._on_cal_status)
        self._cal_worker.signals.error.connect(self._on_cal_error)
        self._cal_worker.signals.prompt.connect(self._on_prompt)
        self._cal_worker.finished.connect(self._on_cal_finished)
        self._cal_worker.start()

    @Slot(str)
    def _on_cal_status(self, msg: str):
        self.panel_cal.append_log(msg)
        self.statusBar().showMessage(msg)
        if '[OPEN]' in msg and 'OK' in msg:
            self.panel_cal.set_step_done('OPEN')
        elif '[SHORT]' in msg and 'OK' in msg:
            self.panel_cal.set_step_done('SHORT')
        elif '[LOAD]' in msg and 'OK' in msg:
            self.panel_cal.set_step_done('LOAD')

    @Slot(str)
    def _on_cal_error(self, msg: str):
        self.panel_cal.append_log(f"BŁĄD: {msg}")
        QMessageBox.critical(self, "Błąd kalibracji", msg)

    @Slot()
    def _on_cal_finished(self):
        self.panel_cal.set_enabled(True)
        self.panel_cal.btn_save_cal.setEnabled(True)
        self.panel_cal.set_status("Kalibracja zakończona")

    @Slot()
    def _save_calibration(self):
        if not self.engine or not self.engine.cal.is_valid:
            QMessageBox.warning(self, "Błąd", "Brak danych kalibracyjnych.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Zapisz kalibrację", "calibration_osl.json",
            "JSON (*.json)"
        )
        if path:
            self.engine.cal.save(path)
            self.panel_cal.set_status(f"Zapisano: {path}")
            self.statusBar().showMessage(f"Kalibracja zapisana: {path}")

    @Slot()
    def _load_calibration(self):
        from core.calibration import OSLCalibration

        path, _ = QFileDialog.getOpenFileName(
            self, "Wczytaj kalibrację", "",
            "JSON (*.json)"
        )
        if not path:
            return

        try:
            cal = OSLCalibration.load(path)
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się wczytać:\n{e}")
            return

        if self.engine:
            self.engine.cal = cal
        else:
            self._loaded_cal = cal

        self.panel_cal.set_step_done('OPEN')
        self.panel_cal.set_step_done('SHORT')
        self.panel_cal.set_step_done('LOAD')
        self.panel_cal.btn_save_cal.setEnabled(True)
        self.panel_cal.set_status(f"Wczytano: {path}")
        self.panel_cal.append_log(f"Wczytano kalibrację z pliku: {path}")

        freqs = sorted(cal.z_open.keys())
        for f in freqs:
            self.panel_cal.append_log(
                f"  {f/1e6:.1f} MHz — O/S/L OK"
            )

        self.statusBar().showMessage(f"Kalibracja wczytana: {path}")

    # =================================================================
    # Pomiar
    # =================================================================

    @Slot()
    def _start_measurement(self):
        if not self.engine:
            QMessageBox.warning(self, "Błąd", "Najpierw połącz urządzenia.")
            return

        self._apply_ui_to_config()
        self.engine.cfg = self.cfg

        output_path = self.panel_meas.get_output_path()
        self.panel_plot.clear_data()
        self.panel_plot.set_frequencies(self.cfg.electrical.frequencies_hz)
        self.panel_meas.set_running(True)
        self.panel_manual.set_enabled(False)

        self._meas_worker = MeasurementWorker(self.engine, output_path)
        self._meas_worker.signals.point.connect(self._on_meas_point)
        self._meas_worker.signals.status.connect(self._on_meas_status)
        self._meas_worker.signals.progress.connect(self._on_meas_progress)
        self._meas_worker.signals.error.connect(self._on_meas_error)
        self._meas_worker.signals.finished.connect(self._on_meas_finished)
        self._meas_worker.signals.prompt.connect(self._on_prompt)
        self._meas_worker.start()

    @Slot()
    def _stop_measurement(self):
        if self._meas_worker:
            self._meas_worker.stop()
            self.statusBar().showMessage("Zatrzymywanie...")

    @Slot(object)
    def _on_meas_point(self, point):
        self.panel_plot.add_point(point)

    @Slot(str)
    def _on_meas_status(self, msg: str):
        self.statusBar().showMessage(msg)
        self.panel_meas.set_status(msg)

    @Slot(int, int)
    def _on_meas_progress(self, current: int, total: int):
        self.panel_meas.set_progress(current, total)

    @Slot(str)
    def _on_meas_error(self, msg: str):
        QMessageBox.warning(self, "Błąd pomiaru", msg)

    @Slot(str)
    def _on_meas_finished(self, path: str):
        self.panel_meas.set_running(False)
        self.panel_manual.set_enabled(True)
        self.statusBar().showMessage(f"Pomiar zakończony: {path}")
        QMessageBox.information(self, "Zakończono", f"Dane zapisane:\n{path}")

    # =================================================================
    # Prompt z wątku roboczego
    # =================================================================

    @Slot(str, object)
    def _on_prompt(self, message: str, event: threading.Event):
        QMessageBox.information(self, "Akcja wymagana", message)
        event.set()

    # =================================================================
    # Sterowanie ręczne
    # =================================================================

    @Slot()
    def _emergency_stop(self):
        """Natychmiastowe wyłączenie — priorytet nad wszystkim."""
        if self._meas_worker:
            self._meas_worker.stop()

        if self._rigol:
            try:
                self._rigol.set_current(0.0)
                self._rigol.output_off()
            except Exception:
                pass

        self.panel_meas.set_running(False)
        self.panel_manual.set_enabled(True)
        self.statusBar().showMessage("⚠ EMERGENCY STOP ⚠")

    @Slot(float)
    def _manual_set_current(self, current: float):
        if self._rigol:
            self._rigol.set_current(current)
            h = current * self.cfg.coil.constant
            pol = '+' if self.panel_manual.radio_pos.isChecked() else '-'
            h_signed = h if pol == '+' else -h
            self.panel_manual.update_readout(current if pol == '+' else -current, h_signed)

    @Slot(str)
    def _manual_set_polarity(self, pol: str):
        if self._arduino:
            if pol == '+':
                self._arduino.set_positive()
            else:
                self._arduino.set_negative()

    @Slot()
    def _manual_output_on(self):
        if self._rigol:
            self._rigol.set_voltage(self.cfg.coil.voltage_limit)
            self._rigol.output_on()

    @Slot()
    def _manual_output_off(self):
        if self._rigol:
            self._rigol.set_current(0.0)
            self._rigol.output_off()

    # =================================================================
    # Konfiguracja — zapis/odczyt
    # =================================================================

    def _load_config_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Wczytaj konfigurację", "", "JSON (*.json)"
        )
        if path:
            self.cfg = StationConfig.load(path)
            self._load_config_to_ui()
            self.statusBar().showMessage(f"Wczytano: {path}")

    def _save_config_file(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Zapisz konfigurację", "station.json", "JSON (*.json)"
        )
        if path:
            self._apply_ui_to_config()
            self.cfg.save(path)
            self.statusBar().showMessage(f"Zapisano: {path}")

    # =================================================================
    # Zamknięcie
    # =================================================================

    def closeEvent(self, event):
        if self._meas_worker and self._meas_worker.isRunning():
            reply = QMessageBox.question(
                self, "Pomiar w toku",
                "Pomiar jest w trakcie. Zatrzymać i zamknąć?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
            self._meas_worker.stop()
            self._meas_worker.wait(5000)

        self._disconnect_devices()
        event.accept()
