"""
Generator siatki prądów magnesujących.

Trzy strefy gęstości:
  gęsta:   |I| ≤ dense_limit,         krok dense_step   (piki GMI)
  średnia: dense_limit < |I| ≤ medium_limit, krok medium_step
  rzadka:  medium_limit < |I| ≤ i_max,      krok coarse_step (nasycenie)
"""

import numpy as np
from core.config import CurrentGrid


def build_grid(cfg: CurrentGrid) -> np.ndarray:
    """Wektor prądów od 0 do i_max (wartości bezwzględne, rosnąco)."""
    dense = np.arange(0.0, cfg.dense_limit + 1e-9, cfg.dense_step)
    medium = np.arange(
        cfg.dense_limit + cfg.medium_step,
        cfg.medium_limit + 1e-9,
        cfg.medium_step
    )
    coarse = np.arange(
        cfg.medium_limit + cfg.coarse_step,
        cfg.i_max + 1e-9,
        cfg.coarse_step
    )
    return np.round(np.concatenate((dense, medium, coarse)), 6)


def get_sweep_vectors(cfg: CurrentGrid) -> tuple[np.ndarray, np.ndarray]:
    """
    Zwraca (ramp_down, ramp_up):
      ramp_down: I_MAX → 0 (malejąco)
      ramp_up:   0+ → I_MAX (rosnąco, bez zera — bo zero już zmierzone)
    """
    grid = build_grid(cfg)
    return grid[::-1].copy(), grid[1:].copy()


def total_hysteresis_points(cfg: CurrentGrid) -> int:
    """Łączna liczba punktów w pełnym cyklu histerezowym (UP + DOWN)."""
    n = len(build_grid(cfg))
    one_branch = 2 * n - 1   # ramp_down + ramp_up (zero raz)
    return 2 * one_branch
