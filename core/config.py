"""
Konfiguracja stanowiska GMI.

Dataclass — łatwa do serializacji (JSON/TOML), edycji z GUI,
i walidacji parametrów.
"""

from dataclasses import dataclass, field, asdict
import json
from pathlib import Path


@dataclass
class DeviceAddresses:
    moku_ip: str = '[fe80:0000:0000:0000:7269:79ff:feb0:06ae%24]'
    rigol_visa: str = 'USB0::0x1AB1::0x0E11::DP8F201600114::INSTR'
    siglent_visa: str = 'USB0::0xF4EC::0x1203::SDM36HCQ7R1713::INSTR'
    arduino_port: str = 'COM4'


@dataclass
class MokuChannelMap:
    """Mapowanie kanałów Moku:Pro ↔ złącza na PCB."""
    output_ch: int = 1    # OUT1 → J1 (OUT na PCB)
    ch_v1: int = 4        # IN4 → J2 (IN1 na PCB) = napięcie PRZED R_REF
    ch_v2: int = 3        # IN3 → J3 (IN2 na PCB) = napięcie ZA R_REF


@dataclass
class MokuFrontend:
    impedance: str = '1MOhm'       # wspólna impedancja (domyślna)
    coupling: str = 'AC'           # wspólny coupling (domyślny)
    range_v1: str = '4Vpp'         # zakres kanału V1 (referencja)
    range_v2: str = '4Vpp'         # zakres kanału V2 (pomiar próbki)


@dataclass
class FRAParams:
    averaging_time: float = 0.1      # [s]
    settling_time: float = 0.05      # [s]
    averaging_cycles: int = 10
    settling_cycles: int = 10
    sweep_margin: float = 0.05       # ±5% margines na krańcach sweepu


@dataclass
class ElectricalParams:
    r_ref: float = 83.0              # [Ω] rezystor wzorcowy na PCB
    amplitude_vpp: float = 0.5       # [Vpp] wymuszenie AC
    z_load_true: float = 50.0        # [Ω] wzorzec kalibracyjny LOAD
    frequencies_hz: list[float] = field(
        default_factory=lambda: [5e6, 10e6, 30e6, 40e6, 45e6, 50e6]
    )


@dataclass
class CurrentGrid:
    """Trójstrefowa siatka prądów magnesujących."""
    i_max: float = 2.0

    dense_limit: float = 0.1         # [A] granica strefy gęstej
    dense_step: float = 0.002        # [A] krok 2 mA

    medium_limit: float = 0.3        # [A] granica strefy średniej
    medium_step: float = 0.01        # [A] krok 10 mA

    coarse_step: float = 0.05        # [A] krok 50 mA


@dataclass
class TimingParams:
    settling_field: float = 0.3      # [s] po zmianie prądu
    settling_polarity: float = 1.0   # [s] po przełączeniu przekaźnika
    ramp_step: float = 0.5           # [A] krok łagodnego narastania
    ramp_delay: float = 0.1          # [s] opóźnienie per krok rampy
    saturation_hold: float = 2.0     # [s] czas nasycania próbki


@dataclass
class CoilParams:
    constant: float = 3750.98        # [A/m per A]
    rigol_channels: list[int] = field(default_factory=lambda: [2, 3])
    voltage_limit: float = 32.0      # [V]


@dataclass
class StationConfig:
    devices: DeviceAddresses = field(default_factory=DeviceAddresses)
    channels: MokuChannelMap = field(default_factory=MokuChannelMap)
    frontend: MokuFrontend = field(default_factory=MokuFrontend)
    fra: FRAParams = field(default_factory=FRAParams)
    electrical: ElectricalParams = field(default_factory=ElectricalParams)
    grid: CurrentGrid = field(default_factory=CurrentGrid)
    timing: TimingParams = field(default_factory=TimingParams)
    coil: CoilParams = field(default_factory=CoilParams)

    def save(self, path: str | Path):
        with open(path, 'w') as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls, path: str | Path) -> 'StationConfig':
        with open(path) as f:
            data = json.load(f)
        return cls(
            devices=DeviceAddresses(**data['devices']),
            channels=MokuChannelMap(**data['channels']),
            frontend=MokuFrontend(**data['frontend']),
            fra=FRAParams(**data['fra']),
            electrical=ElectricalParams(**data['electrical']),
            grid=CurrentGrid(**data['grid']),
            timing=TimingParams(**data['timing']),
            coil=CoilParams(**data['coil']),
        )
