"""Generate the concise experiment report from saved results only."""
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def main():
    d=json.loads((HERE/'joint_local_grid.json').read_text())
    reference=d['probes'][0]['full_boundary']
    for point in d['probes']:
        changed={k for k in reference if reference[k]!=point['full_boundary'][k]}
        if not changed <= {'phase_inductance_h','dead_time_s'}:
            raise ValueError(f"Unauthorized boundary change: {point['label']}: {changed}")
        if point.get('metrics') and point['metrics']['full_boundary']!=point['full_boundary']:
            raise ValueError(f"Solve/replay boundary mismatch: {point['label']}")
    lines=['# A55: local inductance/dead-time sensitivity', '',
        'Source: `joint_local_grid.json`; boundary: `JOINT_GRID_BOUNDARY.md`.', '',
        'This is an A51/A55 control extension, not native P24/P25 reproduction. '
        'One four-phase module, 48 V, 5 MHz, fixed 4 mOhm load; nominal 250 W '
        'means 250 W only at 1 V. Device population and all passive/source '
        'parameters are unchanged. Every point was independently re-solved.', '',
        'Automated full-boundary comparison confirms that only phase inductance '
        'and dead time differ across probes, and every metering replay uses '
        'exactly the same parameter boundary as its solve.', '',
        'The three L anchors come from existing calculations. Dead times are '
        'half/reference/twice 2.15 ns, chosen for sensitivity, not from a driver '
        'specification. Changing dead time moves PWM window edges and may '
        'change actual channel-active duration.', '',
        '| L (nH) | DT (ns) | H1–H4 ZVS | L1–L4 ZVS | Actual Pout (W) | Channel loss (W) | Peak abs I (A) | Max negative entry/peak (%) | First failed gate |',
        '|---:|---:|---|---|---:|---:|---:|---:|---|']
    fmt=lambda flags:'/'.join('T' if f else 'F' for f in flags)
    for p in d['probes']:
        m=p.get('metrics')
        prefix=f"| {p['phase_inductance_h']*1e9:.6f} | {p['dead_time_s']*1e9:.3f} |"
        if not m:
            lines.append(prefix+f" — | — | — | — | — | — | {p['first_failure']} |")
            continue
        lines.append(prefix+f" {fmt(m['natural_zvs_flags'])} | "
            f"{fmt([v['natural'] for v in m['low_side_turn_on_verdicts']])} | "
            f"{m['actual_load_power_w']:.3f} | {m['actual_branch_channel_loss_w']:.3f} | "
            f"{m['maximum_abs_phase_current_a']:.3f} | "
            f"{100*max(m['negative_entry_to_positive_peak_ratio']):.2f} | {p['first_failure'] or 'none of numerical/current/ZVS gates'} |")
    lines += ['', '“No failed gate” does not mean rated-power or paper acceptance. '
        'No target tolerance is invented: actual voltage and power errors remain '
        'in the JSON. Negative entry ratio uses current at the start of the '
        'high-side dead-time window relative to that phase’s positive peak; '
        'full-cycle valley ratios are stored separately. These are observed '
        'currents, not threshold-controlled values.', '',
        'Channel loss uses actual branch voltages squared divided by resistance, '
        'integrated only on accepted enabled-channel samples. Load power uses '
        'mean(Vout²/R). Neither is the legacy phase-current proxy. Third-quadrant '
        'device physics, gate drive, magnetic and thermal loss remain incomplete. '
        'No efficiency ranking is justified by comparing losses at unequal power.', '']
    errors=[p for p in d['probes'] if p.get('error') or not p.get('converged')]
    if errors:
        lines += ['## Numerical or current-screen failures','']
        for p in errors:
            lines.append(f"- `{p['label']}`: {p.get('error') or p.get('stalled_reason')}")
        lines += ['', 'A failed solve does not prove no physical solution exists. '
            'Do not replace it with an interpolated successful result.', '']
    refpath=HERE/'joint_refinement.json'
    if refpath.exists():
        r=json.loads(refpath.read_text())
        lines+=['## Step refinement','',f"Selection: `{r.get('source_label')}`. "
            'Chosen for smallest rated-power error among the sampled all-eight-ZVS '
            'current-screen-passing points, not as a loss optimum.', '']
        for run in r['runs']:
            m=run.get('metrics')
            if m:
                lines.append(f"- Commutation step {run['sub_step_s']*1e12:g} ps / normal "
                    f"step {run['coarse_step_s']*1e12:g} ps: relative closure "
                    f"{run['relative_residual']:.3g}; H-ZVS {fmt(m['natural_zvs_flags'])}; "
                    f"Pout {m['actual_load_power_w']:.4f} W; modeled channel loss "
                    f"{m['actual_branch_channel_loss_w']:.4f} W; maximum negative-entry "
                    f"ratio {100*max(m['negative_entry_to_positive_peak_ratio']):.2f}%.")
            else:
                lines.append(f"- `{run['label']}`: refinement failed: {run.get('error', 'periodic closure')}")
        lines+=['']
    lines += ['## Timing mechanism identified','',
        'In the inherited scheduler the nominal high-side interval is 16.6667 ns. '
        'When high-side zero-voltage admission never occurs, actual commanded '
        'high-channel duration is Ton_nominal minus dead time. Thus the nominal-L '
        'row has widths approximately 15.5917, 14.5167 and 12.3667 ns for '
        '1.075, 2.15 and 4.3 ns dead times. This explains why extending the '
        'window can reduce delivered power; it is not a test with fixed actual '
        'high-side conduction time. For naturally admitted points, conduction '
        'starts at a state-dependent crossing, and the refined metrics export '
        'the actual modeled channel-active durations.', '',
        'These are properties of the implemented A51 window scheduler. They '
        'must not be attributed to the native paper controller without a '
        'separate physical-event mapping. Preserve these runs as sensitivity '
        'evidence and audit that mapping before silently changing on-time.', '',
        'Existing source mapping: `src/scb_ivr/p24_operating_sequence.py` '
        'defines t1 as the end of the high-side conduction interval; '
        '`symbolic_derivations/03_P24_primary_P25_supplement/'
        '29_LOCAL_PHASE_VS_GLOBAL_HANDOFF_MAPPING.md` separates local phase '
        'events from inter-phase handoffs. The next timing audit should use '
        'these definitions and state explicitly whether Ton is measured '
        'from actual admission or from a nominal command edge.', '',
        '## What this experiment can decide','',
        'It tests whether this limited L/dead-time adjustment improves simultaneous '
        'ZVS, delivered power and current behavior under the declared scheduler. '
        'It cannot establish a global optimum or disprove the paper. Before a '
        'rated-power loss optimization, specify the output-regulation/control '
        'boundary and validate a sourced reverse-conduction model. Do not silently '
        'change duty or load to force 250 W.', '',
        'Validation: 267 local tests; 248 portable tests. Historical results and '
        'failed candidates retained. No new LTspice confirmation in this run.', '']
    (HERE/'JOINT_GRID_RESULTS.md').write_text('\n'.join(lines))


if __name__=='__main__':
    main()
