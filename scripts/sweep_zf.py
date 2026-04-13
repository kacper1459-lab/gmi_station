"""
Sweep impedancji vs częstotliwość (bez pola H).
Do weryfikacji podłączenia i rzędu wielkości |Z|.

Użycie:
    python sweep_zf.py
"""

import numpy as np
from core import StationConfig
from drivers import MokuFRA


def main():
    cfg = StationConfig()
    moku = MokuFRA(cfg)
    moku.connect()

    freqs = np.logspace(np.log10(100e3), np.log10(55e6), 200).tolist()

    try:
        print(f"Sweep: {freqs[0]/1e6:.3f} — {freqs[-1]/1e6:.1f} MHz, {len(freqs)} pkt")
        input("Próbka zamontowana → ENTER...")

        results = moku.measure_at_frequencies(freqs)

        out = "sweep_zf.csv"
        with open(out, 'w') as fp:
            fp.write("freq_Hz,Z_mag_Ohm,Z_phase_deg\n")
            for f in freqs:
                z = results[f]
                fp.write(f"{f},{abs(z):.4f},{np.degrees(np.angle(z)):.2f}\n")

        print(f"\nZapisano: {out}")
        print("\nWybrane punkty:")
        for f_check in cfg.electrical.frequencies_hz:
            nearest = min(freqs, key=lambda x: abs(x - f_check))
            z = results[nearest]
            print(f"  {nearest/1e6:>5.1f} MHz  |Z|={abs(z):>8.2f} Ω  φ={np.degrees(np.angle(z)):>+.1f}°")

    finally:
        moku.close()


if __name__ == '__main__':
    main()
