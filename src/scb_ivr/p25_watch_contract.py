"""D08: required watch declarations for the current ideal P25 model.

This is an assembly coverage contract, not an automatic event detector or a
proof that an external input/load model has declared all its events.
"""
from dataclasses import dataclass

from .p25_control_memory import Memory, Policy, Stage, gate_pattern
from .p25_nodal_contract import SWITCHES


@dataclass(frozen=True)
class Watch:
    name: str
    kind: str
    unit: str
    expression: str
    direction: str


@dataclass(frozen=True)
class WatchPlan:
    watches: tuple[Watch, ...]
    algebraic_checks: tuple[str, ...]
    port_event_declaration: str


def required_watches(memory: Memory, policy: Policy, *, reverse_active: tuple[str, ...],
                     external_event_names: tuple[str, ...], port_event_declaration: str) -> WatchPlan:
    """Active reverse set must come from an accepted, nondegenerate D05 result.

    The contract verifies index/gate consistency, not that the caller actually
    obtained the set that way. Boundary arming and guard aliases stay separate.
    """
    if not isinstance(policy, Policy) or not port_event_declaration.strip():
        raise ValueError("explicit control and port-event declaration required")
    if len(set(reverse_active)) != len(reverse_active) or any(x not in SWITCHES for x in reverse_active):
        raise ValueError("distinct valid reverse-active switches required")
    gates=gate_pattern(memory.phase,memory.stage)
    if memory.last_event.gates != gates:
        raise ValueError("gate/memory mismatch")
    if any(on and name in reverse_active for name,on in zip(SWITCHES,(*gates.high,*gates.low))):
        raise ValueError("ON channel cannot also be an OFF reverse-active channel")
    if len(set(external_event_names)) != len(external_event_names) or any(not n.strip() for n in external_event_names):
        raise ValueError("distinct named external events required; use explicit empty tuple if none")
    k,q=memory.phase,memory.phase%3+1
    if memory.stage == Stage.RISE:
        control=Watch("control.high_off","clock","s",f"{memory.entered_at_s!r} + {policy.on_time_s[k-1]!r}","scheduled")
    elif memory.stage == Stage.DOWN_COMM:
        control=Watch("control.low_zero","root","V",f"Vds(SL{k})","downward")
    elif memory.stage == Stage.ALL_LOW:
        control=Watch("control.next_current_zero","root","A",f"iL{q}","downward")
    elif memory.stage == Stage.NEGATIVE:
        if memory.latched_target_a is None:
            raise ValueError("missing latched target")
        control=Watch("control.negative_target","root","A",f"iL{q} - target_latched","downward")
    else:
        control=Watch("control.next_high_zero","root","V",f"Vds(SH{q})","downward")
    rows=[control]
    for name,on in zip(SWITCHES,(*gates.high,*gates.low)):
        if on:
            continue
        if name in reverse_active:
            rows.append(Watch(f"reverse.{name}.release","domain","A",f"r({name})","downward"))
        else:
            rows.append(Watch(f"reverse.{name}.entry","domain","V",f"Vds({name}) + Vf({name})","downward"))
    for phase in (1,2,3):
        if memory.stage == Stage.RISE and phase == k:
            continue
        sign=-1 if memory.stage in {Stage.NEGATIVE,Stage.UP_COMM} and phase==q else 1
        rows.append(Watch(f"mode.iL{phase}.boundary","domain","A",f"{sign} * iL{phase}","downward/outward"))
    rows.extend(Watch(f"external.{name}","external","declared_by_port",name,"declared_by_port")
                for name in external_event_names)
    return WatchPlan(tuple(rows), ("gate_voltage_constraints", "KCL", "reverse_complementarity",
                                  "nondegenerate_local_solution", "state_continuity", "model_identity"),
                     port_event_declaration)


def missing_watches(plan: WatchPlan, installed_names: tuple[str, ...]) -> tuple[str, ...]:
    if len(set(installed_names)) != len(installed_names):
        raise ValueError("duplicate installed watch name")
    return tuple(sorted({w.name for w in plan.watches}-set(installed_names)))
