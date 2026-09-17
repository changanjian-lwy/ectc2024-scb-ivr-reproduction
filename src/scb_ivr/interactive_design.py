"""Teacher-friendly interactive front end for the ECTC 2024 reproduction."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from datetime import datetime
from html import escape
from pathlib import Path

from scb_ivr.ivr_framework import SystemSpec, evaluate_converter, evaluate_embedded_inductor
from scb_ivr.topology_components import paper_topology


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNS = PROJECT_ROOT / "outputs" / "design_records"

# Values printed in Table 1 at nM=2 and 1 MHz.  The table scales linearly
# with module count and inversely with frequency.  Keeping this independent
# from Eq. (4) makes the published equation/table discrepancy auditable.
TABLE1_LCRIT_NH_AT_2_MODULES_1MHZ = {
    4: 6.72,
    6: 10.5,
    8: 13.28,
    16: 10.67,
}


def ask_float(prompt: str, default: float, minimum: float = 0.0) -> float:
    while True:
        raw = input(f"{prompt} [{default:g}]: ").strip()
        try:
            value = default if not raw else float(raw)
            if value <= minimum:
                raise ValueError
            return value
        except ValueError:
            print(f"  输入无效：请输入大于 {minimum:g} 的数字。")


def ask_nonnegative(prompt: str, default: float = 0.0) -> float:
    while True:
        raw = input(f"{prompt} [{default:g}]: ").strip()
        try:
            value = default if not raw else float(raw)
            if value < 0:
                raise ValueError
            return value
        except ValueError:
            print("  输入无效：请输入大于或等于0的数字。")


def ask_int(prompt: str, default: int, minimum: int = 1) -> int:
    while True:
        raw = input(f"{prompt} [{default}]: ").strip()
        try:
            value = default if not raw else int(raw)
            if value < minimum:
                raise ValueError
            return value
        except ValueError:
            print(f"  输入无效：请输入不小于 {minimum} 的整数。")


def collect_inputs() -> dict:
    print("\n" + "=" * 68)
    print("2024 IEEE ECTC：1 kW 封装级 IVR 解析模型复现")
    print("所有输入和输出都会自动保存，便于复查与对比。")
    print("=" * 68)
    print("\n当前演示案例输入（含论文值、论文推导值和明确标注的探索输入）：")
    print("  输入电压 Vin                 = 48 V")
    print("  输出电压 Vo                  = 1 V")
    print("  目标输出功率 Po              = 1000 W")
    print("  每模块相数 nP                = 4")
    print("  并联模块数 nM                = 8")
    print("  每模块串联/飞跨电容数        = 3")
    print("  每相新增串联电阻             = 0 mΩ")
    print("  开关频率 fsw                 = 5 MHz")
    print("  GaN最小导通时间              = 3.4 ns")
    print("  单个内嵌电感峰值能力         = 5 A")
    print("  探索性临界电感下调比例       = 1.5 %（不是2024原文公式输入）")
    print("\n请选择运行方式：")
    print("  1 - 一键使用以上论文参数并直接计算（推荐）")
    print("  2 - 逐项显示并修改参数")
    while True:
        mode = input("请输入选项 [1]: ").strip() or "1"
        if mode in {"1", "2"}:
            break
        print("  输入无效：请输入1或2。")
    if mode == "1":
        return {
            "vin_v": 48.0,
            "vout_v": 1.0,
            "pout_w": 1000.0,
            "phases": 4,
            "modules": 8,
            "shared_series_capacitors_per_module": 3,
            "extra_series_resistance_ohm": 0.0,
            "switching_frequency_hz": 5e6,
            "minimum_on_time_s": 3.4e-9,
            "embedded_inductor_peak_rating_a": 5.0,
            "zvs_margin_fraction": 0.015,
        }
    print("\n[1/4] 系统电气指标")
    vin = ask_float("请输入输入电压 Vin（V）", 48.0)
    vout = ask_float("请输入输出电压 Vo（V）", 1.0)
    pout = ask_float("请输入目标输出功率 Po（W）", 1000.0)

    print("\n[2/4] 模块化拓扑")
    phases = ask_int("请输入每个模块的相数 nP", 4)
    modules = ask_int("请输入并联模块数 nM", 8)
    capacitors = ask_int(
        "请输入每个模块的串联/飞跨电容数量", max(phases - 1, 1), minimum=0
    )
    resistance_mohm = ask_nonnegative(
        "请输入每相新增串联电阻（mΩ；没有则输入0）", 0.0
    )

    print("\n[3/4] 开关条件")
    frequency_mhz = ask_float("请输入开关频率 fsw（MHz）", 5.0)
    minimum_on_time_ns = ask_float("请输入GaN最小导通时间（ns）", 3.4)

    print("\n[4/4] 内嵌电感能力")
    inductor_peak = ask_float("请输入单个内嵌电感峰值电流能力（A）", 5.0)
    zvs_margin_percent = ask_float(
        "请输入探索性临界电感下调比例（%；不得当作2024原文参数）",
        1.5,
        minimum=-1e-12,
    )
    return {
        "vin_v": vin,
        "vout_v": vout,
        "pout_w": pout,
        "phases": phases,
        "modules": modules,
        "shared_series_capacitors_per_module": capacitors,
        "extra_series_resistance_ohm": resistance_mohm / 1000.0,
        "switching_frequency_hz": frequency_mhz * 1e6,
        "minimum_on_time_s": minimum_on_time_ns * 1e-9,
        "embedded_inductor_peak_rating_a": inductor_peak,
        "zvs_margin_fraction": zvs_margin_percent / 100.0,
    }


def calculate(inputs: dict) -> dict:
    spec = SystemSpec(
        vin_v=inputs["vin_v"],
        vout_v=inputs["vout_v"],
        pout_w=inputs["pout_w"],
        minimum_on_time_s=inputs["minimum_on_time_s"],
    )
    topology = paper_topology(
        inputs["phases"],
        inputs["modules"],
        inputs["shared_series_capacitors_per_module"],
        inputs["extra_series_resistance_ohm"],
    )
    converter = evaluate_converter(
        spec,
        inputs["phases"],
        inputs["modules"],
        inputs["switching_frequency_hz"],
    )
    embedded = evaluate_embedded_inductor(
        spec,
        inputs["phases"],
        inputs["modules"],
        inputs["switching_frequency_hz"],
        inputs["embedded_inductor_peak_rating_a"],
    )
    total_phases = topology.total_electrical_phases
    phase_avg = spec.iout_a / total_phases
    # For a 0-to-Ipk triangular boundary-mode waveform: Irms = Ipk/sqrt(3).
    phase_rms = converter.inductor_peak_current_a / (3.0 ** 0.5)
    added_resistor_loss = (
        phase_rms**2
        * topology.phase_template.total_series_resistance_ohm
        * total_phases
    )
    exploratory_margin_scaled_l = converter.critical_inductance_h * (
        1.0 - inputs["zvs_margin_fraction"]
    )
    paper_lcrit = None
    paper_lcrit_difference_percent = None
    if inputs["phases"] in TABLE1_LCRIT_NH_AT_2_MODULES_1MHZ:
        paper_lcrit = (
            TABLE1_LCRIT_NH_AT_2_MODULES_1MHZ[inputs["phases"]]
            * inputs["modules"]
            / 2.0
            / (inputs["switching_frequency_hz"] / 1e6)
        )
        paper_lcrit_difference_percent = (
            converter.critical_inductance_h * 1e9 - paper_lcrit
        ) / paper_lcrit * 100.0
    warnings = []
    if converter.duty_cycle >= 1:
        warnings.append("占空比不小于100%，超出本文降压模型适用范围。")
    if not converter.feasible_on_time:
        warnings.append("高侧导通时间小于器件最小导通时间，此组合不可实现。")
    if embedded.parallel_inductors_exact != embedded.parallel_inductors_engineering:
        warnings.append("论文公式得到非整数电感数量；工程结果已向上取整。")
    if inputs["shared_series_capacitors_per_module"] != inputs["phases"] - 1:
        warnings.append(
            "串联电容数量已偏离论文的 nP-1 结构；基础方程尚未重新推导。"
        )
    if inputs["extra_series_resistance_ohm"] > 0:
        warnings.append(
            "新增电阻损耗采用临界模式三角电流的一阶估算，不属于原论文模型。"
        )
    if paper_lcrit is not None and abs(paper_lcrit_difference_percent) > 1.0:
        warnings.append(
            "论文公式(4)直接计算值与Table 1报告值不一致；报告保留两者供核查。"
        )
    results = {
        "output_current_a": spec.iout_a,
        "power_per_module_w": converter.power_per_module_w,
        "total_electrical_phases": total_phases,
        "average_current_per_phase_a": phase_avg,
        "duty_cycle_percent": 100 * converter.duty_cycle,
        "high_side_on_time_ns": converter.high_side_on_time_s * 1e9,
        "minimum_on_time_ns": spec.minimum_on_time_s * 1e9,
        "on_time_feasible": converter.feasible_on_time,
        "phase_peak_inductor_current_a": converter.inductor_peak_current_a,
        "critical_inductance_nh": converter.critical_inductance_h * 1e9,
        "paper_table1_critical_inductance_nh": paper_lcrit,
        "equation4_vs_table1_difference_percent": paper_lcrit_difference_percent,
        "exploratory_margin_scaled_inductance_nh": (
            exploratory_margin_scaled_l * 1e9
        ),
        "parallel_embedded_inductors_exact": embedded.parallel_inductors_exact,
        "parallel_embedded_inductors_engineering": embedded.parallel_inductors_engineering,
        "unit_embedded_inductance_nh": embedded.unit_inductance_h * 1e9,
        "total_embedded_inductor_units": (
            total_phases * embedded.parallel_inductors_engineering
        ),
        "total_shared_series_capacitors": topology.total_shared_series_capacitors,
        "estimated_added_series_resistor_loss_w": added_resistor_loss,
    }
    return {
        "model": (
            "ECTC 2024 Equations (1)-(6) plus separately labelled derived/"
            "exploratory outputs"
        ),
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "inputs": inputs,
        "topology": topology.as_dict(),
        "results": results,
        "warnings": warnings,
        "equation_trace": [
            "[P24_DERIVED] Io = Po / Vo",
            "[P24_EXPLICIT Eq.1] D = nP * Vo / Vin",
            "[P24_EXPLICIT Eq.3] Ton = nP * Vo / (fsw * Vin)",
            "[P24_EXPLICIT Eq.2] IL,pk = 2 * Io / (nP * nM)",
            "[P24_EXPLICIT Eq.4] Lcrit = nP*nM*Vo*(1-nP*Vo/Vin)/(2*Io*fsw)",
            "[P24_EXPLICIT Eq.5] nL,emb = 2*Io/(nM*nP*Ip,emb)",
            "[PROJECT_DECISION] engineering component count uses ceiling",
            "[P24_EXPLICIT Eq.6] Lemb = Vo*(1-nP*Vo/Vin)/(fsw*Ip,emb)",
            "[EXPLORATORY_ASSUMPTION] Lscaled=(1-margin)*Lcrit",
        ],
    }


def show(record: dict) -> None:
    i, r = record["inputs"], record["results"]
    print("\n" + "=" * 68)
    print("计算结果摘要")
    print("=" * 68)
    print(
        f"输入目标 : {i['vin_v']:g} V → {i['vout_v']:g} V, "
        f"{i['pout_w']:g} W, {i['switching_frequency_hz']/1e6:g} MHz"
    )
    print(
        f"电路结构 : {i['phases']} 相/模块 × {i['modules']} 模块 "
        f"= {r['total_electrical_phases']} 个电气相位"
    )
    print(f"总输出电流                 : {r['output_current_a']:.3f} A")
    print(f"每模块功率                 : {r['power_per_module_w']:.3f} W")
    print(f"占空比                     : {r['duty_cycle_percent']:.3f} %")
    print(f"高侧开关导通时间           : {r['high_side_on_time_ns']:.3f} ns")
    print(f"导通时间可行性             : {'通过' if r['on_time_feasible'] else '不通过'}")
    print(f"每相峰值电感电流           : {r['phase_peak_inductor_current_a']:.3f} A")
    print(f"CCM/DCM临界电感            : {r['critical_inductance_nh']:.3f} nH")
    if r["paper_table1_critical_inductance_nh"] is not None:
        print(
            "论文Table 1对应报告值      : "
            f"{r['paper_table1_critical_inductance_nh']:.3f} nH"
        )
        print(
            "公式(4)相对Table 1偏差     : "
            f"{r['equation4_vs_table1_difference_percent']:+.2f} %"
        )
    print(
        "探索性裕量缩放后的电感     : "
        f"{r['exploratory_margin_scaled_inductance_nh']:.3f} nH"
    )
    print(
        "每相并联内嵌电感         : "
        f"论文公式 {r['parallel_embedded_inductors_exact']:.3f}，"
        f"工程取整 {r['parallel_embedded_inductors_engineering']} 个"
    )
    print(f"单个内嵌电感值             : {r['unit_embedded_inductance_nh']:.3f} nH")
    print(f"内嵌电感元件总数           : {r['total_embedded_inductor_units']} 个")
    print(f"串联/飞跨电容总数          : {r['total_shared_series_capacitors']} 个")
    print(
        "新增串联电阻估算损耗       : "
        f"{r['estimated_added_series_resistor_loss_w']:.3f} W"
    )
    if record["warnings"]:
        print("\n需要注意：")
        for warning in record["warnings"]:
            print(f"  - {warning}")


def flatten(record: dict) -> dict:
    row = {"created_at": record["created_at"], "model": record["model"]}
    row.update({f"input_{k}": v for k, v in record["inputs"].items()})
    row.update({f"result_{k}": v for k, v in record["results"].items()})
    row["warnings"] = " | ".join(record["warnings"])
    return row


def save(record: dict) -> Path:
    RUNS.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    run_dir = RUNS / run_id
    run_dir.mkdir()
    (run_dir / "design_record.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    row = flatten(record)
    with (run_dir / "design_record.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)

    r = record["results"]
    warnings_html = "".join(f"<li>{escape(x)}</li>" for x in record["warnings"])
    result_rows = "".join(
        f"<tr><td>{escape(k)}</td><td>{escape(str(v))}</td></tr>"
        for k, v in r.items()
    )
    input_rows = "".join(
        f"<tr><td>{escape(k)}</td><td>{escape(str(v))}</td></tr>"
        for k, v in record["inputs"].items()
    )
    html = f"""<!doctype html><meta charset='utf-8'>
<title>ECTC 2024 IVR Design Record</title>
<style>body{{font:16px system-ui;max-width:1000px;margin:40px auto;color:#172033}}
h1{{color:#123a70}} .hero{{background:#eef5ff;padding:20px;border-left:6px solid #2672c9}}
table{{border-collapse:collapse;width:100%;margin:12px 0 28px}}td,th{{border:1px solid #ccd5e0;padding:9px;text-align:left}}tr:nth-child(even){{background:#f7f9fb}}
.pass{{color:#087830;font-weight:700}} .fail{{color:#b00020;font-weight:700}}</style>
<h1>2024 IEEE ECTC IVR 解析模型复现</h1>
<div class='hero'><b>设计：</b>{i_summary(record)}<br><b>导通时间检查：</b>
<span class='{'pass' if r['on_time_feasible'] else 'fail'}'>{'通过' if r['on_time_feasible'] else '不通过'}</span></div>
<h2>模型输入</h2><table><tr><th>参数</th><th>数值</th></tr>{input_rows}</table>
<h2>模型输出</h2><table><tr><th>参数</th><th>数值</th></tr>{result_rows}</table>
<h2>提醒与模型边界</h2><ul>{warnings_html or '<li>没有触发额外警告。</li>'}</ul>
<h2>计算链</h2><ol>{''.join(f'<li>{escape(x)}</li>' for x in record['equation_trace'])}</ol>"""
    (run_dir / "design_report.html").write_text(html, encoding="utf-8")
    return run_dir


def i_summary(record: dict) -> str:
    i = record["inputs"]
    return (
        f"{i['vin_v']:g} V → {i['vout_v']:g} V，{i['pout_w']:g} W，"
        f"{i['phases']}相/模块 × {i['modules']}模块，"
        f"{i['switching_frequency_hz']/1e6:g} MHz"
    )


def main() -> None:
    inputs = collect_inputs()
    record = calculate(inputs)
    show(record)
    run_dir = save(record)
    print("\n结果已保存，可重复追踪：")
    print(f"  教师查看报告：{run_dir / 'design_report.html'}")
    print(f"  完整模型记录：{run_dir / 'design_record.json'}")
    print(f"  表格记录：    {run_dir / 'design_record.csv'}")


if __name__ == "__main__":
    main()
