"""
Plotowanie wyników GMI z zapisanego pliku CSV.

Użycie:
    python plot_results.py gmi_1234567890.csv
    python plot_results.py gmi_1234567890.csv --save gmi_plot.png
"""

import argparse
from core.plotting import load_csv, plot_gmi, plot_impedance_vs_field


def main():
    parser = argparse.ArgumentParser(description='Wykres GMI z pliku CSV')
    parser.add_argument('csv_file', help='Plik wynikowy CSV')
    parser.add_argument('--save', type=str, default=None, help='Zapisz PNG')
    parser.add_argument('--raw', action='store_true', help='Wykres |Z| zamiast ΔZ/Z')
    args = parser.parse_args()

    data = load_csv(args.csv_file)
    print(f"Załadowano {args.csv_file}")
    for f in sorted(data.keys()):
        n_up = len(data[f]['UP'])
        n_down = len(data[f]['DOWN'])
        print(f"  {f/1e6:.0f} MHz: {n_up} UP + {n_down} DOWN")

    if args.raw:
        plot_impedance_vs_field(data, save_path=args.save)
    else:
        plot_gmi(data, save_path=args.save)


if __name__ == '__main__':
    main()
