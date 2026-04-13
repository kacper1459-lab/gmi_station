"""
Driver: Arduino (Atmega 328) — sterownik modułu przekaźnikowego.

Moduł przekaźnikowy: aktywny przy LOW na pinie cyfrowym.
Jeden przekaźnik DPDT przełączający polaryzację prądu w cewce.

Protokół szeregowy (firmware przekazniki.ino):
  'P' → pin HIGH → moduł nieaktywny → stan spoczynkowy → polaryzacja +
  'N' → pin LOW  → moduł aktywny   → przekaźnik przełączony → polaryzacja -

Firmware NIE obsługuje komendy 'O' — stan domyślny po starcie to LOW
(moduł aktywny = polaryzacja ujemna).
"""

import time
import serial


class ArduinoRelay:

    def __init__(self, port: str, baudrate: int = 9600):
        self.arduino = None
        try:
            self.arduino = serial.Serial(port, baudrate, timeout=1)
            time.sleep(2)  # czekaj na reset Arduino po otwarciu portu
            print(f"[Arduino] OK: {port}")
            self.set_positive()  # ustaw stan znany (P = HIGH = moduł off)
        except Exception as e:
            print(f"[Arduino] Błąd: {e}")

    def set_positive(self):
        """Polaryzacja dodatnia: pin HIGH → moduł nieaktywny → stan spoczynkowy."""
        self._send(b'P')

    def set_negative(self):
        """Polaryzacja ujemna: pin LOW → moduł aktywny → przekaźnik przełączony."""
        self._send(b'N')

    def _send(self, cmd: bytes):
        if self.arduino:
            self.arduino.write(cmd)
            self.arduino.readline()

    def close(self):
        if self.arduino:
            self.set_positive()  # bezpieczny stan — moduł nieaktywny
            self.arduino.close()
            print("[Arduino] Zamknięto.")
