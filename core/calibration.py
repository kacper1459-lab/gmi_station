"""
Kalibracja OSL (Open-Short-Load) fixture'a pomiarowego.

Trzyterminowa korekcja błędów systematycznych:
  - OPEN:  puste PADy (Z → ∞ idealne)
  - SHORT: zworka PAD1↔PAD2 (Z → 0 idealne)
  - LOAD:  precyzyjny rezystor (np. 50 Ω)
"""

import numpy as np


class OSLCalibration:
    """Przechowuje wzorce i wykonuje korekcję impedancji."""

    def __init__(self, z_load_true: float = 50.0):
        self.z_load_true = z_load_true
        self.z_open: dict[float, complex] = {}
        self.z_short: dict[float, complex] = {}
        self.z_load: dict[float, complex] = {}
        self.is_valid = False

    def set_open(self, data: dict[float, complex]):
        self.z_open = data
        self._check_valid()

    def set_short(self, data: dict[float, complex]):
        self.z_short = data
        self._check_valid()

    def set_load(self, data: dict[float, complex]):
        self.z_load = data
        self._check_valid()

    def correct(self, z_measured: complex, freq: float) -> complex:
        """
        Korekcja trzyterminowa:
            Z_true = Z_load_true × (Z_m - Z_s)(Z_o - Z_l) / ((Z_l - Z_s)(Z_o - Z_m))
        """
        if not self.is_valid:
            return z_measured

        z_o = self.z_open.get(freq)
        z_s = self.z_short.get(freq)
        z_l = self.z_load.get(freq)
        if z_o is None or z_s is None or z_l is None:
            return z_measured

        denom = (z_l - z_s) * (z_o - z_measured)
        if abs(denom) < 1e-15:
            return z_measured

        numer = (z_measured - z_s) * (z_o - z_l)
        return self.z_load_true * (numer / denom)

    def save(self, path: str):
        """Zapis danych kalibracyjnych do JSON."""
        import json
        data = {
            'z_load_true': self.z_load_true,
            'open': _complex_dict_to_json(self.z_open),
            'short': _complex_dict_to_json(self.z_short),
            'load': _complex_dict_to_json(self.z_load),
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, path: str) -> 'OSLCalibration':
        """Odczyt danych kalibracyjnych z JSON."""
        import json
        with open(path) as f:
            data = json.load(f)
        cal = cls(data['z_load_true'])
        cal.z_open = _json_to_complex_dict(data['open'])
        cal.z_short = _json_to_complex_dict(data['short'])
        cal.z_load = _json_to_complex_dict(data['load'])
        cal._check_valid()
        return cal

    def _check_valid(self):
        self.is_valid = bool(self.z_open and self.z_short and self.z_load)


def _complex_dict_to_json(d: dict[float, complex]) -> list[list]:
    """dict{freq: complex} → [[freq, real, imag], ...]"""
    return [[f, z.real, z.imag] for f, z in sorted(d.items())]


def _json_to_complex_dict(data: list[list]) -> dict[float, complex]:
    """[[freq, real, imag], ...] → dict{freq: complex}"""
    return {row[0]: complex(row[1], row[2]) for row in data}
