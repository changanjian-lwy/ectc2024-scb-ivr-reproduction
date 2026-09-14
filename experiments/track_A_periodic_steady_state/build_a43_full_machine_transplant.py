"""Build A43 by changing only A37's negative-current fraction to 7.77%."""

from __future__ import annotations

from pathlib import Path


TRACK = Path(__file__).resolve().parent
PARENT = (
    TRACK / "A37_p25_9pct_joint_seven_state_200ns_periodic_solve/"
    "A37_p25_9pct_joint_seven_state_200ns_periodic_solve.cir"
)
OUT = (
    TRACK / "A43_p25_device_augmented_7p77_full_event_machine/"
    "A43_p25_device_augmented_7p77_full_event_machine.cir"
)


def build() -> Path:
    source = PARENT.read_text()
    old = ".param LPHASE=1.466666666666667n IPEAK=125 NEG_FRAC=.09 INEG={NEG_FRAC*IPEAK}"
    new = ".param LPHASE=1.466666666666667n IPEAK=125 NEG_FRAC=.0777 INEG={NEG_FRAC*IPEAK}"
    if source.count(old) != 1:
        raise RuntimeError("A37 parent threshold line changed or is ambiguous")
    text = source.replace(old, new, 1)
    text = text.replace(
        "* A37 - joint seven-state 200ns periodic solve, P25 9% branch",
        "* A43 - A42 7.77% threshold transplanted into A37 full event machine",
        1,
    )
    text = text.replace(
        "* PARAM VALUES: the UNOPTIMIZED seed",
        "* ONLY ELECTRICAL CHANGE FROM A37: NEG_FRAC .09 -> .0777.\n"
        "* All seven coordinates remain A37 LOCAL_SOLVED_SEED values.\n"
        "* PARAM VALUES: the UNOPTIMIZED seed",
        1,
    )
    text = text.replace(
        ".meas tran DIL4 PARAM IL4_F-IL4_I",
        ".meas tran DIL4 PARAM IL4_F-IL4_I\n"
        ".meas tran A43_NEGATIVE_FRACTION PARAM {NEG_FRAC}\n"
        ".meas tran A43_NEGATIVE_TARGET_A PARAM {INEG}",
        1,
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    return OUT


if __name__ == "__main__":
    print(build())
