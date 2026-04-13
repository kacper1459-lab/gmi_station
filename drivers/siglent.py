"""
Driver: Siglent SDM3065X — multimetr, pomiar prądu cewek.
"""

import pyvisa


class SiglentSDM:

    def __init__(self, resource_string: str):
        self.rm = pyvisa.ResourceManager()
        self.instrument = None
        try:
            self.instrument = self.rm.open_resource(resource_string)
            self.instrument.timeout = 10000
            self.instrument.read_termination = '\n'
            self.instrument.write_termination = '\n'
            idn = self.instrument.query("*IDN?").strip()
            print(f"[Siglent] OK: {idn}")
        except Exception as e:
            print(f"[Siglent] Błąd: {e}")

    def read_dc_current(self) -> float | None:
        if not self.instrument:
            return None
        try:
            return float(self.instrument.query("MEASure:CURRent:DC?").strip())
        except Exception as e:
            print(f"  [Siglent] Brak odczytu: {e}")
            return None

    def close(self):
        if self.instrument:
            self.instrument.close()
            print("[Siglent] Zamknięto.")
