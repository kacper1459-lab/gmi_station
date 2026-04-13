"""
Silnik pomiarowy GMI.

Orkiestruje pełny cykl histerezowy Z(H).
Komunikuje się z warstwą prezentacji wyłącznie przez MeasurementCallback.
Nie importuje niczego z GUI — można go użyć z CLI, GUI, lub w testach.
"""

import time
import csv
import numpy as np
from pathlib import Path

from core.config import StationConfig
from core.calibration import OSLCalibration
from core.grid import get_sweep_vectors, total_hysteresis_points
from core.callbacks import MeasurementCallback, MeasurementPoint


class GMIMeasurementEngine:
    """
    Główny silnik pomiarowy.

    Zależności (drivers) wstrzykiwane przez set_drivers().
    GUI/CLI podłączane przez set_callback().
    """

    def __init__(self, cfg: StationConfig):
        self.cfg = cfg
        self.cal = OSLCalibration(cfg.electrical.z_load_true)
        self.cb: MeasurementCallback | None = None

        # Drivers — wstrzykiwane (nie tworzone tutaj)
        self._rigol = None
        self._siglent = None
        self._arduino = None
        self._moku = None

        # Stan pomiaru
        self._z_ref: dict[float, float] = {}
        self._csv_file = None
        self._csv_writer = None
        self._point_counter = 0
        self._total_points = 0
        self._running = False

    def set_drivers(self, rigol, siglent, arduino, moku):
        self._rigol = rigol
        self._siglent = siglent
        self._arduino = arduino
        self._moku = moku

    def set_callback(self, cb: MeasurementCallback):
        self.cb = cb

    # -----------------------------------------------------------------
    # Kalibracja
    # -----------------------------------------------------------------

    def run_calibration(self):
        """Procedura kalibracji OSL — wymaga interakcji operatora."""
        freqs = self.cfg.electrical.frequencies_hz
        self._rigol.output_off()

        self._emit_status("Kalibracja OSL — zasilacz wyłączony")

        self.cb.prompt_user("[OPEN] Usuń próbkę, zostaw puste PADy")
        z_open = self._moku.measure_at_frequencies(freqs)
        self.cal.set_open(z_open)
        self._log_cal("OPEN", z_open)

        self.cb.prompt_user("[SHORT] Włóż zworkę między PAD1 a PAD2")
        z_short = self._moku.measure_at_frequencies(freqs)
        self.cal.set_short(z_short)
        self._log_cal("SHORT", z_short)

        self.cb.prompt_user(
            f"[LOAD] Włóż rezystor {self.cfg.electrical.z_load_true} Ω między PADy"
        )
        z_load = self._moku.measure_at_frequencies(freqs)
        self.cal.set_load(z_load)
        self._log_cal("LOAD", z_load)

        self._emit_status("Kalibracja OSL zakończona")

    # -----------------------------------------------------------------
    # Pomiar główny
    # -----------------------------------------------------------------

    def run_measurement(self, output_path: str | Path) -> str:
        """
        Pełny cykl histerezowy GMI.
        Zwraca ścieżkę do pliku wynikowego.
        """
        output_path = Path(output_path)
        self._total_points = total_hysteresis_points(self.cfg.grid)
        self._point_counter = 0
        self._z_ref.clear()
        self._running = True

        ramp_down, ramp_up = get_sweep_vectors(self.cfg.grid)

        self._open_csv(output_path)

        try:
            self._rigol.set_voltage(self.cfg.coil.voltage_limit)

            # Nasycenie przy -I_MAX
            self._emit_status("Nasycanie próbki przy -I_MAX...")
            self._arduino.set_negative()
            self._rigol.output_on()
            self._rigol.ramp_to(
                self.cfg.grid.i_max,
                step=self.cfg.timing.ramp_step,
                delay=self.cfg.timing.ramp_delay
            )
            time.sleep(self.cfg.timing.saturation_hold)

            # Gałąź UP: -I_MAX → 0 → +I_MAX
            self._emit_status("Gałąź rosnąca (UP)")
            self._sweep_branch(ramp_down, polarity='-', branch='UP')

            time.sleep(self.cfg.timing.settling_polarity)
            self._arduino.set_positive()
            time.sleep(self.cfg.timing.settling_polarity)

            self._sweep_branch(ramp_up, polarity='+', branch='UP')

            # Gałąź DOWN: +I_MAX → 0 → -I_MAX
            self._emit_status("Gałąź opadająca (DOWN)")
            self._sweep_branch(ramp_down, polarity='+', branch='DOWN')

            time.sleep(self.cfg.timing.settling_polarity)
            self._arduino.set_negative()
            time.sleep(self.cfg.timing.settling_polarity)

            self._sweep_branch(ramp_up, polarity='-', branch='DOWN')

        except KeyboardInterrupt:
            self._emit_status("Przerwano (Ctrl+C)")
        except Exception as e:
            self._emit_error(str(e))
        finally:
            self._running = False
            self._close_csv()
            self._shutdown()
            self._emit_finished(str(output_path))

        return str(output_path)

    def stop(self):
        """Sygnał zatrzymania — sprawdzany w pętli pomiarowej."""
        self._running = False

    # -----------------------------------------------------------------
    # Internals
    # -----------------------------------------------------------------

    def _sweep_branch(self, currents: np.ndarray, polarity: str, branch: str):
        freqs = self.cfg.electrical.frequencies_hz

        for i_set in currents:
            if not self._running:
                break

            self._rigol.set_current(i_set)
            time.sleep(self.cfg.timing.settling_field)

            i_raw = self._siglent.read_dc_current()
            i_meas = abs(i_raw) if i_raw is not None else i_set
            i_signed = i_meas if polarity == '+' else -i_meas
            h_val = i_signed * self.cfg.coil.constant

            z_all = self._moku.measure_at_frequencies(freqs)

            for f in freqs:
                z_raw = z_all[f]
                z_cor = self.cal.correct(z_raw, f)
                z_mag = abs(z_cor)
                z_ph = np.degrees(np.angle(z_cor))

                if f not in self._z_ref:
                    self._z_ref[f] = z_mag

                gmi = (
                    ((z_mag - self._z_ref[f]) / self._z_ref[f]) * 100.0
                    if self._z_ref[f] > 1e-12 else 0.0
                )

                point = MeasurementPoint(
                    freq_hz=f, branch=branch,
                    i_set=i_set, i_measured=i_signed, h_field=h_val,
                    z_raw_mag=abs(z_raw),
                    z_raw_phase=np.degrees(np.angle(z_raw)),
                    z_cal_mag=z_mag, z_cal_phase=z_ph,
                    gmi_ratio=gmi
                )

                self._write_csv_row(point)
                if self.cb:
                    self.cb.on_point(point)

            self._point_counter += 1
            if self.cb:
                self.cb.on_progress(self._point_counter, self._total_points)

    def _shutdown(self):
        try:
            self._rigol.set_current(0.0)
            time.sleep(0.5)
            self._rigol.output_off()
        except Exception:
            pass

    # -----------------------------------------------------------------
    # CSV
    # -----------------------------------------------------------------

    def _open_csv(self, path: Path):
        self._csv_file = open(path, 'w', newline='')
        self._csv_writer = csv.writer(self._csv_file)
        self._csv_writer.writerow([
            'freq_Hz', 'branch', 'I_set_A', 'I_meas_A', 'H_Am',
            'Z_raw_mag_Ohm', 'Z_raw_phase_deg',
            'Z_cal_mag_Ohm', 'Z_cal_phase_deg',
            'GMI_pct'
        ])

    def _write_csv_row(self, p: MeasurementPoint):
        if self._csv_writer:
            self._csv_writer.writerow([
                p.freq_hz, p.branch, p.i_set, p.i_measured, p.h_field,
                f"{p.z_raw_mag:.4f}", f"{p.z_raw_phase:.2f}",
                f"{p.z_cal_mag:.4f}", f"{p.z_cal_phase:.2f}",
                f"{p.gmi_ratio:.2f}"
            ])
            self._csv_file.flush()

    def _close_csv(self):
        if self._csv_file:
            self._csv_file.close()
            self._csv_file = None

    # -----------------------------------------------------------------
    # Emisja zdarzeń
    # -----------------------------------------------------------------

    def _log_cal(self, name: str, data: dict[float, complex]):
        for f, z in data.items():
            self._emit_status(
                f"  [{name}] {f/1e6:>5.1f} MHz  "
                f"|Z|={abs(z):>8.2f} Ω  φ={np.degrees(np.angle(z)):>+.1f}°"
            )

    def _emit_status(self, msg: str):
        if self.cb:
            self.cb.on_status(msg)

    def _emit_error(self, msg: str):
        if self.cb:
            self.cb.on_error(msg)

    def _emit_finished(self, path: str):
        if self.cb:
            self.cb.on_finished(path)
