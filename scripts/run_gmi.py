"""
Punkt wejścia CLI — pomiar GMI Z(H).

Użycie:
    python run_gmi.py
    python run_gmi.py --config station.json
"""

import sys
import time
import argparse
from pathlib import Path

from core import StationConfig, GMIMeasurementEngine, CLICallback
from drivers import RigolDP831, SiglentSDM, ArduinoRelay, MokuFRA


def main():
    parser = argparse.ArgumentParser(description='Pomiar efektu GMI')
    parser.add_argument('--config', type=str, default=None,
                        help='Ścieżka do pliku konfiguracji JSON')
    parser.add_argument('--output', type=str, default=None,
                        help='Ścieżka pliku wynikowego CSV')
    args = parser.parse_args()

    # Konfiguracja
    if args.config and Path(args.config).exists():
        cfg = StationConfig.load(args.config)
        print(f"Załadowano konfigurację: {args.config}")
    else:
        cfg = StationConfig()
        if args.config:
            print(f"Brak pliku {args.config}, używam domyślnych parametrów.")

    output_file = args.output or f"gmi_{int(time.time())}.csv"

    # Inicjalizacja driverów
    print("Inicjalizacja urządzeń...")
    rigol = RigolDP831(cfg.devices.rigol_visa, cfg.coil.rigol_channels)
    siglent = SiglentSDM(cfg.devices.siglent_visa)
    arduino = ArduinoRelay(cfg.devices.arduino_port)
    moku = MokuFRA(cfg)
    moku.connect()

    # Silnik pomiarowy
    engine = GMIMeasurementEngine(cfg)
    engine.set_drivers(rigol, siglent, arduino, moku)
    engine.set_callback(CLICallback())

    try:
        # Kalibracja
        engine.run_calibration()

        # Montaż próbki
        input("\n[GOTOWE] Zamontuj próbkę taśmy amorficznej → ENTER...")

        # Pomiar
        engine.run_measurement(output_file)

    except KeyboardInterrupt:
        print("\nPrzerwano.")
    finally:
        rigol.close()
        arduino.close()
        moku.close()
        siglent.close()

    # Wykres po pomiarze
    try:
        from core.plotting import load_csv, plot_gmi
        if Path(output_file).exists():
            data = load_csv(output_file)
            plot_path = output_file.replace('.csv', '.png')
            plot_gmi(data, save_path=plot_path)
    except Exception as e:
        print(f"Wykres niedostępny: {e}")


if __name__ == '__main__':
    main()
