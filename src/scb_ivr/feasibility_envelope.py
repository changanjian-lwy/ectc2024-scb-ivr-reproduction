"""Parameter-only feasibility envelopes for paper-derived commutation checks.

The relations in this module are necessary-condition screens, not a complete
switched-network proof.  They intentionally separate quantities fixed by an
operating point from device/control inputs that remain unknown.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import sqrt


@dataclass(frozen=True)
class OperatingPoint:
    vin_v: float
    vout_v: float
    pout_w: float
    phases: int
    modules: int
    switching_frequency_hz: float

    def __post_init__(self) -> None:
        positive = (
            self.vin_v,
            self.vout_v,
            self.pout_w,
            self.switching_frequency_hz,
        )
        if any(value <= 0 for value in positive):
            raise ValueError("voltages, power and frequency must be positive")
        if self.vout_v >= self.vin_v:
            raise ValueError("the present model requires a step-down operating point")
        if self.phases <= 0 or self.modules <= 0:
            raise ValueError("phase and module counts must be positive")

    @property
    def output_current_a(self) -> float:
        return self.pout_w / self.vout_v

    @property
    def equal_ladder_phase_voltage_v(self) -> float:
        """Conditional Vin/nP segment voltage, not a startup/balance proof."""
        return self.vin_v / self.phases

    @property
    def equal_ladder_drive_voltage_v(self) -> float:
        return self.equal_ladder_phase_voltage_v - self.vout_v

    @property
    def paper_duty(self) -> float:
        return self.phases * self.vout_v / self.vin_v

    @property
    def paper_on_time_s(self) -> float:
        return self.paper_duty / self.switching_frequency_hz


@dataclass(frozen=True)
class EnvelopePoint:
    inductance_h: float
    negative_fraction: float
    paper_zero_valley_peak_current_a: float
    corrected_peak_current_a: float
    negative_current_a: float
    available_inductor_energy_j: float
    required_ramp_inductance_paper_peak_h: float
    required_ramp_inductance_corrected_peak_h: float
    selected_over_required_corrected_inductance: float

    def as_dict(self) -> dict:
        row = asdict(self)
        row.update(
            inductance_nh=self.inductance_h * 1e9,
            negative_percent=self.negative_fraction * 100,
            available_inductor_energy_nj=self.available_inductor_energy_j * 1e9,
            required_ramp_inductance_paper_peak_nh=(
                self.required_ramp_inductance_paper_peak_h * 1e9
            ),
            required_ramp_inductance_corrected_peak_nh=(
                self.required_ramp_inductance_corrected_peak_h * 1e9
            ),
        )
        return row


@dataclass(frozen=True)
class CommutationAdmission:
    required_current_from_energy_a: float | None
    required_current_from_charge_a: float | None
    combined_required_current_a: float | None
    available_negative_current_a: float
    energy_gate: bool | None
    charge_time_gate: bool | None
    admitted: bool | None


def paper_zero_valley_peak_current_a(operating_point: OperatingPoint) -> float:
    """Peak from the paper's zero-valley triangular-current relation."""
    return (
        2 * operating_point.output_current_a
        / (operating_point.phases * operating_point.modules)
    )


def corrected_peak_current_a(
    operating_point: OperatingPoint, negative_fraction: float
) -> float:
    """Triangular average-current closure with Imin=-alpha*Ipk.

    This is a labelled mathematical extension.  The paper expression
    2*Io/(nP*nM) is recovered exactly at alpha=0.
    """
    if not 0 <= negative_fraction < 1:
        raise ValueError("negative_fraction must satisfy 0 <= alpha < 1")
    zero_valley_peak = paper_zero_valley_peak_current_a(operating_point)
    return zero_valley_peak / (1 - negative_fraction)


def negative_current_a(
    operating_point: OperatingPoint, negative_fraction: float
) -> float:
    return negative_fraction * corrected_peak_current_a(
        operating_point, negative_fraction
    )


def available_commutation_energy_j(inductance_h: float, current_a: float) -> float:
    """Maximum local inductor-energy budget, 0.5*L*I^2."""
    if inductance_h <= 0 or current_a < 0:
        raise ValueError("inductance must be positive and current non-negative")
    return 0.5 * inductance_h * current_a**2


def maximum_commutation_charge_c(current_a: float, available_time_s: float) -> float:
    """Constant-current charge-transfer ceiling |I|*dt.

    This is a screening envelope.  A nonlinear event solve must replace it
    when current changes materially during the commutation interval.
    """
    if current_a < 0 or available_time_s < 0:
        raise ValueError("current and available time must be non-negative")
    return current_a * available_time_s


def minimum_current_from_energy_a(
    inductance_h: float, commutation_energy_j: float
) -> float:
    if inductance_h <= 0 or commutation_energy_j < 0:
        raise ValueError("inductance must be positive and energy non-negative")
    return sqrt(2 * commutation_energy_j / inductance_h)


def minimum_current_from_charge_a(
    commutation_charge_c: float, available_time_s: float
) -> float:
    if commutation_charge_c < 0 or available_time_s <= 0:
        raise ValueError("charge must be non-negative and time positive")
    return commutation_charge_c / available_time_s


def required_ramp_inductance_h(
    operating_point: OperatingPoint,
    negative_fraction: float,
    *,
    drive_voltage_v: float | None = None,
    on_time_s: float | None = None,
    correct_average_for_negative_valley: bool = True,
) -> float:
    """L required to ramp from -Ineg to +Ipk under a constant drive voltage.

    ``correct_average_for_negative_valley=False`` preserves the peak-current
    value printed for a zero-valley triangular waveform and merely appends a
    negative endpoint.  ``True`` enforces the same average output current after
    that endpoint is introduced.  Both are reported because the papers do not
    explicitly reconcile these two conventions.
    """
    drive = (
        operating_point.equal_ladder_drive_voltage_v
        if drive_voltage_v is None
        else drive_voltage_v
    )
    ton = operating_point.paper_on_time_s if on_time_s is None else on_time_s
    if drive <= 0 or ton <= 0:
        raise ValueError("drive voltage and on-time must be positive")
    peak = (
        corrected_peak_current_a(operating_point, negative_fraction)
        if correct_average_for_negative_valley
        else paper_zero_valley_peak_current_a(operating_point)
    )
    negative = negative_fraction * peak
    return drive * ton / (peak + negative)


def envelope_point(
    operating_point: OperatingPoint,
    inductance_h: float,
    negative_fraction: float,
) -> EnvelopePoint:
    paper_peak = paper_zero_valley_peak_current_a(operating_point)
    peak = corrected_peak_current_a(operating_point, negative_fraction)
    negative = negative_fraction * peak
    required_l_paper = required_ramp_inductance_h(
        operating_point,
        negative_fraction,
        correct_average_for_negative_valley=False,
    )
    required_l_corrected = required_ramp_inductance_h(
        operating_point,
        negative_fraction,
        correct_average_for_negative_valley=True,
    )
    return EnvelopePoint(
        inductance_h=inductance_h,
        negative_fraction=negative_fraction,
        paper_zero_valley_peak_current_a=paper_peak,
        corrected_peak_current_a=peak,
        negative_current_a=negative,
        available_inductor_energy_j=available_commutation_energy_j(
            inductance_h, negative
        ),
        required_ramp_inductance_paper_peak_h=required_l_paper,
        required_ramp_inductance_corrected_peak_h=required_l_corrected,
        selected_over_required_corrected_inductance=(
            inductance_h / required_l_corrected
        ),
    )


def evaluate_commutation_admission(
    *,
    inductance_h: float,
    available_negative_current_a: float,
    commutation_energy_j: float | None = None,
    commutation_charge_c: float | None = None,
    available_time_s: float | None = None,
) -> CommutationAdmission:
    """Evaluate only gates for which the caller supplied physical inputs."""
    if available_negative_current_a < 0:
        raise ValueError("available negative-current magnitude cannot be negative")
    energy_required = (
        None
        if commutation_energy_j is None
        else minimum_current_from_energy_a(inductance_h, commutation_energy_j)
    )
    if (commutation_charge_c is None) != (available_time_s is None):
        raise ValueError("charge and available time must be supplied together")
    charge_required = (
        None
        if commutation_charge_c is None
        else minimum_current_from_charge_a(
            commutation_charge_c, available_time_s  # type: ignore[arg-type]
        )
    )
    requirements = tuple(
        value for value in (energy_required, charge_required) if value is not None
    )
    combined = max(requirements) if requirements else None
    energy_gate = (
        None
        if energy_required is None
        else available_negative_current_a >= energy_required
    )
    charge_gate = (
        None
        if charge_required is None
        else available_negative_current_a >= charge_required
    )
    return CommutationAdmission(
        required_current_from_energy_a=energy_required,
        required_current_from_charge_a=charge_required,
        combined_required_current_a=combined,
        available_negative_current_a=available_negative_current_a,
        energy_gate=energy_gate,
        charge_time_gate=charge_gate,
        admitted=(None if combined is None else available_negative_current_a >= combined),
    )
