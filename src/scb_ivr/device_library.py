"""Provenance-locked device data; topology decides parallel device count."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from scb_ivr.evidence import Evidence


class CapacitanceView(str, Enum):
    TYPICAL_COSS = "typical_coss"
    ENERGY_EQUIVALENT = "energy_equivalent"
    TIME_EQUIVALENT = "time_equivalent"


@dataclass(frozen=True)
class GaNDevice:
    part_number: str
    rated_v: float
    rds_on_typ_ohm: float
    coss_typ_f: float
    co_er_f: float
    co_tr_f: float
    qoss_c: float
    qoss_voltage_v: float
    source: str
    source_revision: str
    evidence: Evidence = Evidence.EXTERNAL_DEVICE_DATA

    def capacitance(self, view: CapacitanceView, parallel_devices: int = 1) -> float:
        if not isinstance(parallel_devices, int) or parallel_devices <= 0:
            raise ValueError("parallel_devices must be a positive integer")
        per_device = {
            CapacitanceView.TYPICAL_COSS: self.coss_typ_f,
            CapacitanceView.ENERGY_EQUIVALENT: self.co_er_f,
            CapacitanceView.TIME_EQUIVALENT: self.co_tr_f,
        }[view]
        return parallel_devices * per_device

    def rds_on(self, parallel_devices: int = 1) -> float:
        if not isinstance(parallel_devices, int) or parallel_devices <= 0:
            raise ValueError("parallel_devices must be a positive integer")
        return self.rds_on_typ_ohm / parallel_devices


GS61008T = GaNDevice(
    part_number="GS61008T",
    rated_v=100.0,
    rds_on_typ_ohm=7e-3,
    coss_typ_f=250e-12,
    co_er_f=302e-12,
    co_tr_f=385e-12,
    qoss_c=20e-9,
    qoss_voltage_v=50.0,
    source=(
        "Infineon/GaN Systems GS61008T datasheet, "
        "https://www.infineon.com/assets/row/public/documents/24/49/"
        "infineon-gs61008t-datasheet-en.pdf"
    ),
    source_revision="Rev 200402",
)


@dataclass(frozen=True)
class P25SwitchPopulation:
    high_side_parallel: int = 1
    low_side_parallel: int = 2
    evidence: Evidence = Evidence.P25_SUPPLEMENT
    source_location: str = "P25 Table III"


P25_GS61008T_POPULATION = P25SwitchPopulation()
