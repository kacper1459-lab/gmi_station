"""
Driver: Moku:Pro Frequency Response Analyzer — pomiar impedancji.

Topologia obwodu na PCB:
    OUT1 → [V1 = IN4] → R_REF (83 Ω) → [V2 = IN3] → taśma GMI → GND

Wzór:
    h = V2 / V1
    Z_GMI = R_REF × h / (1 - h)
"""

import math
import cmath
import numpy as np
from moku.instruments import FrequencyResponseAnalyzer

from core.config import StationConfig


class MokuFRA:

    def __init__(self, cfg: StationConfig):
        self.cfg = cfg
        self.fra: FrequencyResponseAnalyzer | None = None

    def connect(self):
        self.fra = FrequencyResponseAnalyzer(
            self.cfg.devices.moku_ip, force_connect=True
        )
        print(f"[Moku FRA] OK: {self.cfg.devices.moku_ip}")

        ch_v1 = self.cfg.channels.ch_v1
        ch_v2 = self.cfg.channels.ch_v2
        fe = self.cfg.frontend

        self.fra.set_frontend(
            ch_v1, impedance=fe.impedance,
            coupling=fe.coupling, range=fe.range_v1
        )
        self.fra.set_frontend(
            ch_v2, impedance=fe.impedance,
            coupling=fe.coupling, range=fe.range_v2
        )
        self.fra.set_output(
            self.cfg.channels.output_ch,
            amplitude=self.cfg.electrical.amplitude_vpp
        )

    def measure_at_frequencies(self, freqs_hz: list[float]) -> dict[float, complex]:
        """
        Jeden sweep pokrywający wszystkie żądane częstotliwości.
        Zwraca {freq: Z_complex} dla każdej żądanej f.
        """
        if not self.fra:
            raise RuntimeError("Moku nie podłączony.")

        f_min, f_max = min(freqs_hz), max(freqs_hz)
        margin = self.cfg.fra.sweep_margin
        num_pts = max(64, len(freqs_hz) * 8)

        self.fra.set_sweep(
            start_frequency=f_min * (1.0 - margin),
            stop_frequency=f_max * (1.0 + margin),
            num_points=num_pts,
            averaging_time=self.cfg.fra.averaging_time,
            settling_time=self.cfg.fra.settling_time,
            averaging_cycles=self.cfg.fra.averaging_cycles,
            settling_cycles=self.cfg.fra.settling_cycles,
            strict=False
        )

        self.fra.start_sweep()
        data = self.fra.get_data(wait_complete=True, timeout=300)

        ch_v1_key = f'ch{self.cfg.channels.ch_v1}'
        ch_v2_key = f'ch{self.cfg.channels.ch_v2}'

        sweep_f = np.array(data[ch_v2_key]['frequency'])
        mag1_db = np.array(data[ch_v1_key]['magnitude'])
        ph1_deg = np.array(data[ch_v1_key]['phase'])
        mag2_db = np.array(data[ch_v2_key]['magnitude'])
        ph2_deg = np.array(data[ch_v2_key]['phase'])

        r_ref = self.cfg.electrical.r_ref
        results: dict[float, complex] = {}

        for f_target in freqs_hz:
            idx = int(np.argmin(np.abs(sweep_f - f_target)))

            v1 = _db_phase_to_complex(mag1_db[idx], ph1_deg[idx])
            v2 = _db_phase_to_complex(mag2_db[idx], ph2_deg[idx])

            h = v2 / v1 if abs(v1) > 1e-15 else complex(0, 0)

            if abs(1.0 - h) < 1e-8:
                z = complex(1e9, 0)
            else:
                z = r_ref * (h / (1.0 - h))

            results[f_target] = z

        return results

    def close(self):
        if self.fra:
            try:
                self.fra.relinquish_ownership()
                print("[Moku FRA] Zamknięto.")
            except Exception as e:
                print(f"[Moku FRA] Wymuszono zamknięcie: {e.__class__.__name__}")


def _db_phase_to_complex(mag_db: float, phase_deg: float) -> complex:
    mag_lin = 10.0 ** (mag_db / 20.0)
    return mag_lin * cmath.exp(1j * math.radians(phase_deg))
