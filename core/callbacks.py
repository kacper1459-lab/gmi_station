"""
Protokół callbacków dla warstwy prezentacji (GUI / CLI).

Logika pomiarowa nie wie czy działa pod GUI czy w terminalu.
Komunikuje się przez ten interfejs.
"""

from dataclasses import dataclass
from typing import Protocol, Callable


@dataclass
class MeasurementPoint:
    """Pojedynczy punkt pomiarowy — emitowany po każdym kroku H."""
    freq_hz: float
    branch: str             # 'UP' | 'DOWN'
    i_set: float            # [A] prąd zadany
    i_measured: float       # [A] prąd zmierzony (Siglent)
    h_field: float          # [A/m]
    z_raw_mag: float        # [Ω] surowy moduł
    z_raw_phase: float      # [deg]
    z_cal_mag: float        # [Ω] po kalibracji OSL
    z_cal_phase: float      # [deg]
    gmi_ratio: float        # [%] ΔZ/Z


class MeasurementCallback(Protocol):
    """Interfejs callbacków — implementowany przez GUI lub CLI."""

    def on_point(self, point: MeasurementPoint) -> None:
        """Nowy punkt pomiarowy."""
        ...

    def on_status(self, message: str) -> None:
        """Komunikat statusowy."""
        ...

    def on_progress(self, current: int, total: int) -> None:
        """Postęp pomiaru."""
        ...

    def on_error(self, message: str) -> None:
        """Błąd (niekrytyczny)."""
        ...

    def on_finished(self, output_file: str) -> None:
        """Pomiar zakończony."""
        ...

    def prompt_user(self, message: str) -> None:
        """Wymaga akcji operatora (np. włóż próbkę)."""
        ...


class CLICallback:
    """Domyślna implementacja — drukuje na stdout."""

    def on_point(self, point: MeasurementPoint) -> None:
        f_mhz = point.freq_hz / 1e6
        print(
            f"  {f_mhz:>5.1f} MHz  "
            f"|Z|={point.z_cal_mag:>7.2f} Ω  "
            f"GMI={point.gmi_ratio:>+7.1f}%"
        )

    def on_status(self, message: str) -> None:
        print(f"[STATUS] {message}")

    def on_progress(self, current: int, total: int) -> None:
        pct = current / total * 100 if total > 0 else 0
        print(f"[{current}/{total}] {pct:.0f}%", end='\r')

    def on_error(self, message: str) -> None:
        print(f"[BŁĄD] {message}")

    def on_finished(self, output_file: str) -> None:
        print(f"\n[DONE] Dane zapisane: {output_file}")

    def prompt_user(self, message: str) -> None:
        input(f"\n{message} → ENTER...")
