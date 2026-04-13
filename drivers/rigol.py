"""
Driver: Rigol DP831 — zasilacz programowalny, sterowanie polem H.

Kanały CH2 i CH3 spięte równolegle → podwojenie wydajności prądowej
(2 × 2A = 4A max). Oba kanały dostają identyczne nastawy.
Polaryzacja prądu w cewce odwracana przez zewnętrzny przekaźnik DPDT
(Arduino).
"""

import time
import numpy as np
import pyvisa


class RigolDP831:

    def __init__(self, resource_string: str, channels: list[int] | None = None):
        self.channels = channels or [2, 3]
        self.rm = pyvisa.ResourceManager()
        self.instrument = None
        try:
            self.instrument = self.rm.open_resource(resource_string)
            self.instrument.timeout = 5000
            self.instrument.read_termination = '\n'
            self.instrument.write_termination = '\n'
            idn = self.instrument.query("*IDN?").strip()
            print(f"[Rigol] OK: {idn}")
            self.output_off()
        except Exception as e:
            print(f"[Rigol] Błąd: {e}")

    def set_voltage(self, voltage: float):
        if not self.instrument:
            return
        for ch in self.channels:
            self.instrument.write(f":SOURce{ch}:VOLTage {abs(voltage)}")

    def set_current(self, current: float):
        if not self.instrument:
            return
        for ch in self.channels:
            self.instrument.write(f":SOURce{ch}:CURRent {abs(current)}")

    def output_on(self):
        if not self.instrument:
            return
        for ch in self.channels:
            self.instrument.write(f":OUTPut CH{ch},ON")

    def output_off(self):
        if not self.instrument:
            return
        for ch in self.channels:
            self.instrument.write(f":OUTPut CH{ch},OFF")

    def ramp_to(self, target: float, step: float = 0.5, delay: float = 0.1):
        if not self.instrument:
            return
        for val in np.arange(0, target + step, step):
            self.set_current(min(val, target))
            time.sleep(delay)

    def close(self):
        if self.instrument:
            self.output_off()
            self.instrument.close()
            print("[Rigol] Zamknięto.")
