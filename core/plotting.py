"""
Wizualizacja wyników pomiarów GMI.

Oddzielony od logiki pomiarowej — można wywołać:
  - z CLI po zakończeniu pomiaru
  - z GUI w czasie rzeczywistym (on_point callback)
  - offline na zapisanym CSV
"""

import csv
import numpy as np
from pathlib import Path
from collections import defaultdict


def load_csv(path: str | Path) -> dict:
    """
    Wczytuje CSV wynikowy i zwraca strukturę:
    {freq: {'UP': [(H, Z_mag)], 'DOWN': [(H, Z_mag)]}}
    """
    data = defaultdict(lambda: {'UP': [], 'DOWN': []})

    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            freq = float(row['freq_Hz'])
            branch = row['branch']
            h = float(row['H_Am'])
            z = float(row['Z_cal_mag_Ohm'])
            data[freq][branch].append((h, z))

    return dict(data)


def plot_gmi(
    data: dict,
    freqs: list[float] | None = None,
    save_path: str | None = None,
    show: bool = True
):
    """
    Wykres ΔZ/Z(%) vs H(A/m) — publication-ready.

    Args:
        data: {freq: {'UP': [(H,Z)], 'DOWN': [(H,Z)]}}
        freqs: lista częstotliwości do wykreślenia (None = wszystkie)
        save_path: ścieżka zapisu PNG (None = nie zapisuj)
        show: czy wyświetlić plt.show()
    """
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        'axes.linewidth': 1.5,
        'font.size': 12,
        'font.family': 'sans-serif',
    })

    fig, ax = plt.subplots(figsize=(12, 7))
    colors = ['#e67e22', '#e74c3c', '#2c3e50', '#2980b9', '#27ae60', '#8e44ad',
              '#d35400', '#c0392b', '#16a085', '#2c3e50']

    if freqs is None:
        freqs = sorted(data.keys())

    for idx, f in enumerate(freqs):
        if f not in data:
            continue

        c = colors[idx % len(colors)]
        f_label = f"{f / 1e6:.0f} MHz" if f >= 1e6 else f"{f / 1e3:.0f} kHz"

        all_z = []
        for branch in ['UP', 'DOWN']:
            pts = data[f].get(branch, [])
            all_z.extend([p[1] for p in pts])

        if not all_z:
            continue
        z_ref = min(all_z)
        if z_ref < 1e-12:
            continue

        for branch in ['UP', 'DOWN']:
            pts = data[f].get(branch, [])
            if not pts:
                continue

            h_arr = np.array([p[0] for p in pts])
            z_arr = np.array([p[1] for p in pts])
            gmi = ((z_arr - z_ref) / z_ref) * 100.0

            ls = '-' if branch == 'UP' else '--'
            label = f_label if branch == 'UP' else None
            ax.plot(h_arr, gmi, color=c, linewidth=1.5, linestyle=ls, label=label)

    ax.set_xlabel('H (A/m)', fontsize=14)
    ax.set_ylabel(r'$\Delta Z / Z$ (%)', fontsize=14)
    ax.tick_params(direction='in', length=6, width=1.5,
                   bottom=True, top=True, left=True, right=True)

    legend = ax.legend(loc='upper right', frameon=True,
                       edgecolor='black', fancybox=False)
    if legend:
        legend.get_frame().set_linewidth(1.5)

    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=200, bbox_inches='tight')
        print(f"Wykres zapisany: {save_path}")

    if show:
        plt.show()

    return fig, ax


def plot_impedance_vs_field(
    data: dict,
    freqs: list[float] | None = None,
    save_path: str | None = None,
    show: bool = True
):
    """Wykres |Z|(Ω) vs H(A/m) — surowe wartości impedancji."""
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        'axes.linewidth': 1.5,
        'font.size': 12,
        'font.family': 'sans-serif',
    })

    fig, ax = plt.subplots(figsize=(12, 7))
    colors = ['#e67e22', '#e74c3c', '#2c3e50', '#2980b9', '#27ae60', '#8e44ad']

    if freqs is None:
        freqs = sorted(data.keys())

    for idx, f in enumerate(freqs):
        if f not in data:
            continue

        c = colors[idx % len(colors)]
        f_label = f"{f / 1e6:.0f} MHz" if f >= 1e6 else f"{f / 1e3:.0f} kHz"

        for branch in ['UP', 'DOWN']:
            pts = data[f].get(branch, [])
            if not pts:
                continue

            h_arr = np.array([p[0] for p in pts])
            z_arr = np.array([p[1] for p in pts])

            ls = '-' if branch == 'UP' else '--'
            label = f_label if branch == 'UP' else None
            ax.plot(h_arr, z_arr, color=c, linewidth=1.5, linestyle=ls, label=label)

    ax.set_xlabel('H (A/m)', fontsize=14)
    ax.set_ylabel('|Z| (Ω)', fontsize=14)
    ax.tick_params(direction='in', length=6, width=1.5,
                   bottom=True, top=True, left=True, right=True)

    legend = ax.legend(loc='upper right', frameon=True,
                       edgecolor='black', fancybox=False)
    if legend:
        legend.get_frame().set_linewidth(1.5)

    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=200, bbox_inches='tight')

    if show:
        plt.show()

    return fig, ax
