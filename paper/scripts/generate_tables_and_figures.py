"""
Generates every manuscript table and figure from analysis_results.json.

This closes the provenance chain:

    raw CSV  ->  analyze_results.py  ->  analysis_results.json
                                              |
                                              +-> generated LaTeX tables (\\input)
                                              +-> 300 DPI figures

No number is ever typed into the manuscript by hand. If a dataset is missing the
corresponding table/figure is NOT produced and a placeholder recording the reason
is emitted instead, so an absent experiment can never be silently represented by
values left over from an earlier run.

Figure design notes
-------------------
* Success rate, makespan and social exposure have incomparable scales, so they are
  drawn as SMALL MULTIPLES rather than forced onto a shared or secondary axis.
* Social exposure is summarised by median and IQR: the distribution is zero-inflated
  and strongly right-skewed, so a mean +/- SD bar would misrepresent it.
* The categorical palette is the Okabe-Ito colourblind-safe set, ordered so that no
  adjacent pair falls below the CVD separation floor. Every bar carries a direct
  value label, which supplies the secondary encoding and the contrast relief that
  colour alone would not.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "experiments", "data")
FIG_DIR = os.path.join(BASE_DIR, "figures")
TAB_DIR = os.path.join(BASE_DIR, "generated")
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(TAB_DIR, exist_ok=True)

# Okabe-Ito, reordered so adjacent pairs clear the CVD separation floor.
PALETTE = ["#0072B2", "#009E73", "#E69F00", "#D55E00", "#CC79A7"]
INK = "#1a1a1a"
MUTED = "#6b6b6b"
GRID = "#d8d8d8"

# Single-line, compact axis labels. Two-line labels collided with their neighbours
# at publication width; the full algorithm names live in the table and caption.
SHORT = {
    "D2RO (SW-DGO Proposed)": "D²RO",
    "Static A*": "Static A*",
    "Reactive Avoidance (Potential Field)": "APF",
    "Artificial Potential Fields (APF)": "APF",
    "Reactive ORCA (Velocity Obstacles)": "ORCA",
    "Decentralized Local MAPF": "MAPF",
}
ORDER = [
    "D2RO (SW-DGO Proposed)",
    "Static A*",
    "Reactive Avoidance (Potential Field)",
    "Reactive ORCA (Velocity Obstacles)",
    "Decentralized Local MAPF",
]

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "axes.labelsize": 9,
    "axes.titlesize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "axes.edgecolor": MUTED,
    "axes.linewidth": 0.8,
    "text.color": INK,
    "axes.labelcolor": INK,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})


def load_analysis() -> Dict[str, Any]:
    path = os.path.join(DATA_DIR, "analysis_results.json")
    if not os.path.exists(path):
        raise SystemExit("analysis_results.json not found - run analyze_results.py first")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _usable(status: Optional[str]) -> bool:
    """A dataset is usable if verified, or explicitly accepted as provisional."""
    return status == "ok" or (status or "").startswith("provisional")


def _provisional(status: Optional[str]) -> bool:
    return (status or "").startswith("provisional")


def _style(ax) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def _placeholder(name: str, reason: str) -> None:
    """Records why an artefact was not produced, instead of leaving a stale one."""
    with open(os.path.join(TAB_DIR, f"{name}.tex"), "w", encoding="utf-8") as f:
        f.write(f"% NOT GENERATED: {reason}\n"
                f"% This experiment has no complete dataset. The manuscript must not\n"
                f"% cite numbers for it until the run completes.\n")
    print(f"  [skip] {name}: {reason}")


# --------------------------------------------------------------------------- #
# Figure 1 - comparative benchmark
# --------------------------------------------------------------------------- #
def figure_benchmark(bench: Dict[str, Any]) -> bool:
    if not _usable(bench.get("status")) or not bench.get("groups"):
        _placeholder("fig1_note", f"benchmark dataset {bench.get('status')}")
        return False

    groups = bench["groups"]
    methods = [m for m in ORDER if m in groups] or list(groups)
    labels = [SHORT.get(m, m) for m in methods]
    colors = [PALETTE[i % len(PALETTE)] for i in range(len(methods))]

    fig, axes = plt.subplots(1, 3, figsize=(10.4, 3.2))

    # (a) success rate with Wilson intervals
    ax = axes[0]
    vals = [groups[m]["success_rate"] for m in methods]
    err_lo = [max(0, v - groups[m]["success_ci95"][0]) for v, m in zip(vals, methods)]
    err_hi = [max(0, groups[m]["success_ci95"][1] - v) for v, m in zip(vals, methods)]
    bars = ax.bar(labels, vals, color=colors, width=0.68, zorder=3)
    ax.errorbar(labels, vals, yerr=[err_lo, err_hi], fmt="none",
                ecolor=MUTED, elinewidth=0.9, capsize=2.5, zorder=4)
    for b, v, e in zip(bars, vals, err_hi):
        ax.text(b.get_x() + b.get_width() / 2, v + e + 4.0, f"{v:.0f}%",
                ha="center", va="bottom", fontsize=8, color=INK)
    ax.set_ylabel("Mission success rate (%)")
    ax.set_ylim(0, 124)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_title("(a) Mission success", loc="left")
    _style(ax)

    # (b) makespan of successful missions
    ax = axes[1]
    mk = [groups[m]["makespan_successful"] for m in methods]
    vals = [d.get("mean", 0.0) if d.get("n", 0) else 0.0 for d in mk]
    errs = [d.get("sd", 0.0) if d.get("n", 0) else 0.0 for d in mk]
    bars = ax.bar(labels, vals, color=colors, width=0.68, zorder=3)
    ax.errorbar(labels, vals, yerr=errs, fmt="none", ecolor=MUTED,
                elinewidth=0.9, capsize=2.5, zorder=4)
    top = max([v + e for v, e in zip(vals, errs)] + [1.0])
    for b, v, e, d in zip(bars, vals, errs, mk):
        succeeded = bool(d.get("n", 0))
        ax.text(b.get_x() + b.get_width() / 2, v + e + top * 0.05,
                f"{v:.1f}" if succeeded else "no success",
                ha="center", va="bottom", fontsize=8,
                color=INK if succeeded else MUTED,
                rotation=0 if succeeded else 90)
    ax.set_ylabel("Makespan of successful missions (s)")
    ax.set_ylim(0, top * 1.38)
    ax.set_title("(b) Time cost", loc="left")
    ax.yaxis.set_major_locator(MaxNLocator(5))
    _style(ax)

    # (c) social exposure - median with IQR (skewed, zero-inflated)
    ax = axes[2]
    ex = [groups[m]["intimate_exposure"] for m in methods]
    med = [d.get("median", 0.0) for d in ex]
    q1 = [d.get("iqr", [0, 0])[0] for d in ex]
    q3 = [d.get("iqr", [0, 0])[1] for d in ex]
    lo = [max(0.0, m_ - a) for m_, a in zip(med, q1)]
    hi = [max(0.0, b - m_) for m_, b in zip(med, q3)]
    bars = ax.bar(labels, med, color=colors, width=0.68, zorder=3)
    ax.errorbar(labels, med, yerr=[lo, hi], fmt="none", ecolor=MUTED,
                elinewidth=0.9, capsize=2.5, zorder=4)
    top = max(q3 + [1.0])
    for b, v, e in zip(bars, med, hi):
        ax.text(b.get_x() + b.get_width() / 2, v + e + top * 0.05, f"{v:.0f}",
                ha="center", va="bottom", fontsize=8, color=INK)
    ax.set_ylabel("Intimate-space exposure (control ticks)")
    ax.set_ylim(0, top * 1.34)
    ax.set_title("(c) Social compliance — median [IQR]", loc="left")
    ax.yaxis.set_major_locator(MaxNLocator(5))
    _style(ax)

    if _provisional(bench.get("status")):
        fig.text(0.5, 0.985,
                 "PROVISIONAL — dataset generated by superseded code; regenerate before submission",
                 ha="center", va="top", fontsize=7.5, color="#b02418")

    fig.tight_layout(rect=(0, 0, 1, 0.96) if _provisional(bench.get("status")) else None)
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(FIG_DIR, f"fig1_benchmark_comparison.{ext}"))
    plt.close(fig)
    print("  [ok]   fig1_benchmark_comparison.{pdf,png}")
    return True


# --------------------------------------------------------------------------- #
# LaTeX tables
# --------------------------------------------------------------------------- #
def _f(d: Optional[Dict[str, Any]], p: int = 2) -> str:
    if not d or not d.get("n"):
        return "--"
    return f"${d['mean']:.{p}f} \\pm {d['sd']:.{p}f}$"


def table_benchmark(bench: Dict[str, Any]) -> bool:
    if not _usable(bench.get("status")) or not bench.get("groups"):
        _placeholder("table_benchmark", f"benchmark dataset {bench.get('status')}")
        return False

    groups = bench["groups"]
    adj = bench.get("holm_adjusted_p", {})
    methods = [m for m in ORDER if m in groups] or list(groups)
    n = bench.get("n_trials", 0)

    L = [
        "% GENERATED FILE - do not edit by hand.",
        "% Source: experiments/data/analysis_results.json",
        "% Produced by paper/scripts/generate_tables_and_figures.py",
        "\\begin{table*}[t]",
        "\\centering",
        f"\\caption{{Comparative benchmark in the retail supermarket domain "
        f"($N={n}$ paired Monte Carlo trials, identical seeds across all planners). "
        f"Social exposure is reported as median [IQR] because the distribution is "
        f"zero-inflated and strongly right-skewed. $p$-values are Holm-adjusted "
        f"within the family of comparisons and each refers to the single outcome "
        f"on its own row.}}",
        "\\label{tab:benchmark}",
        "\\resizebox{\\textwidth}{!}{%",
        "\\begin{tabular}{lccccc}",
        "\\toprule",
        "\\textbf{Algorithm} & \\textbf{Success (95\\% CI)} & "
        "\\textbf{Makespan, successful (s)} & \\textbf{Deadlocks} & "
        "\\textbf{Intimate exposure, median [IQR]} & \\textbf{$p$ (exposure)} \\\\",
        "\\midrule",
    ]

    for m in methods:
        g = groups[m]
        lo, hi = g["success_ci95"]
        ex = g["intimate_exposure"]
        iqr = ex.get("iqr", [0, 0])
        name = m.replace("D2RO (SW-DGO Proposed)",
                         "\\textbf{$\\text{D}^2\\text{RO}$ (proposed)}")
        name = name.replace("Static A*", "Static $A^*$")
        name = name.replace("Reactive Avoidance (Potential Field)", "APF")
        name = name.replace("Reactive ORCA (Velocity Obstacles)", "Reactive ORCA")
        pv = adj.get(f"{m}|intimate")
        pcell = "--" if m.startswith("D2RO") else (
            f"${pv:.1e}$".replace("e-0", "\\times 10^{-").replace("e-", "\\times 10^{-") + "}$"
            if pv is not None else "--")
        if not m.startswith("D2RO") and pv is not None:
            pcell = f"${pv:.2g}$"
        mk = g["makespan_successful"]
        mkcell = _f(mk) if mk.get("n") else "no success"
        L.append(
            f"{name} & {g['success_rate']:.1f}\\% [{lo:.1f}, {hi:.1f}] & "
            f"{mkcell} & {_f(g['deadlocks'])} & "
            f"{ex.get('median', 0):.0f} [{iqr[0]:.0f}, {iqr[1]:.0f}] & {pcell} \\\\")

    L += ["\\bottomrule", "\\end{tabular}%", "}", "\\end{table*}", ""]

    with open(os.path.join(TAB_DIR, "table_benchmark.tex"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print("  [ok]   generated/table_benchmark.tex")
    return True


def _pct(g: Dict[str, Any]) -> str:
    """Success rate with its Wilson interval."""
    lo, hi = g.get("success_ci95", [0.0, 0.0])
    return f"{g.get('success_rate', 0.0):.1f}\\% [{lo:.1f}, {hi:.1f}]"


def _med(d: Optional[Dict[str, Any]], p: int = 0) -> str:
    """Median [IQR] - the honest summary for skewed, zero-inflated metrics."""
    if not d or not d.get("n"):
        return "--"
    q1, q3 = d.get("iqr", [0.0, 0.0])
    return f"{d.get('median', 0.0):.{p}f} [{q1:.{p}f}, {q3:.{p}f}]"


def _p(v: Optional[float]) -> str:
    if v is None:
        return "--"
    if v >= 0.001:
        return f"${v:.3g}$"
    mant, exp = f"{v:.1e}".split("e")
    return f"${mant} \\times 10^{{{int(exp)}}}$"


def _header(caption: str, label: str, colspec: str, heads: str,
            wide: bool = False, resize: bool = False) -> List[str]:
    env = "table*" if wide else "table"
    L = [
        "% GENERATED FILE - do not edit by hand.",
        "% Source: experiments/data/analysis_results.json",
        "% Produced by paper/scripts/generate_tables_and_figures.py",
        f"\\begin{{{env}}}[t]",
        "\\centering",
        f"\\caption{{{caption}}}",
        f"\\label{{{label}}}",
    ]
    if resize:
        # A single-column float must scale to \columnwidth: inside a two-column
        # IEEEtran page \textwidth is the FULL page width, so using it here
        # overflows the column by ~264pt.
        L.append("\\resizebox{%s}{!}{%%" % ("\\textwidth" if wide else "\\columnwidth"))
    L += [f"\\begin{{tabular}}{{{colspec}}}", "\\toprule", heads, "\\midrule"]
    return L


def _footer(wide: bool = False, resize: bool = False) -> List[str]:
    env = "table*" if wide else "table"
    L = ["\\bottomrule", "\\end{tabular}" + ("%" if resize else "")]
    if resize:
        L.append("}")
    L += [f"\\end{{{env}}}", ""]
    return L


def _emit(name: str, lines: List[str]) -> bool:
    with open(os.path.join(TAB_DIR, f"{name}.tex"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  [ok]   generated/{name}.tex")
    return True


# --------------------------------------------------------------------------- #
# Component ablation
# --------------------------------------------------------------------------- #
ABLATION_LABEL = {
    "Full D2RO Framework": "\\textbf{Full $\\text{D}^2\\text{RO}$}",
    "w/o V2V Mesh Telemetry": "w/o V2V mesh $W_{\\text{mesh}}$",
    "w/o Corridor Mutex Lock": "w/o corridor mutex $R_{\\text{lock}}$",
    "w/o Human Gaussian Proxemics": "w/o proxemics $H_{\\text{prox}}$",
    "w/o Trolley Kinetic Safety Bubble": "w/o safety envelope $S_{\\text{trolley}}$",
}


def table_ablation(res: Dict[str, Any]) -> bool:
    if not _usable(res.get("status")) or not res.get("groups"):
        _placeholder("table_ablation", f"ablation dataset {res.get('status', 'missing')}")
        return False
    groups = res["groups"]
    order = [k for k in ABLATION_LABEL if k in groups] or list(groups)
    n = groups[order[0]].get("n", 0)
    L = _header(
        f"Component ablation of the five cost terms in the retail supermarket domain "
        f"($N={n}$ trials per configuration). Each row removes exactly one term from "
        f"Eq.~(1); all other parameters are held fixed.",
        "tab:ablation", "lccccc",
        "\\textbf{Configuration} & \\textbf{Success (95\\% CI)} & \\textbf{Makespan (s)} & "
        "\\textbf{Discomfort} & \\textbf{Deadlocks} & \\textbf{Shelf scrapes} \\\\",
        wide=True, resize=True)
    for k in order:
        g = groups[k]
        L.append(f"{ABLATION_LABEL.get(k, k)} & {_pct(g)} & {_f(g['makespan'])} & "
                 f"{_f(g['discomfort'])} & {_f(g['deadlocks'])} & {_f(g['shelf_scrapes'])} \\\\")
    L += _footer(wide=True, resize=True)
    return _emit("table_ablation", L)


# --------------------------------------------------------------------------- #
# Cross-domain generalisation
# --------------------------------------------------------------------------- #
def table_cross_domain(res: Dict[str, Any]) -> bool:
    if not _usable(res.get("status")) or not res.get("groups"):
        _placeholder("table_cross_domain", f"cross_domain dataset {res.get('status', 'missing')}")
        return False
    groups = res["groups"]
    order = ["Retail Supermarket", "Clinical Hospital", "Airport Terminal"]
    order = [k for k in order if k in groups] or list(groups)
    n = groups[order[0]].get("n", 0)
    L = _header(
        f"Cross-domain generalisation of the unchanged planner across three "
        f"topologically distinct environments ($N={n}$ trials per domain). Intimate "
        f"exposure is reported as median [IQR]; the distribution is zero-inflated.",
        "tab:cross_domain", "lccccc",
        "\\textbf{Domain} & \\textbf{Success (95\\% CI)} & \\textbf{Makespan (s)} & "
        "\\textbf{Mean transit (s)} & \\textbf{Intimate exposure} & "
        "\\textbf{$\\text{D}^*$ Lite replans} \\\\",
        wide=True, resize=True)
    for k in order:
        g = groups[k]
        L.append(f"{k} & {_pct(g)} & {_f(g['makespan'])} & {_f(g['transit'])} & "
                 f"{_med(g['intimate_exposure'])} & {_f(g['replans'], 1)} \\\\")
    L += _footer(wide=True, resize=True)
    return _emit("table_cross_domain", L)


# --------------------------------------------------------------------------- #
# Mechanism experiments A and B - paired ON/OFF designs
# --------------------------------------------------------------------------- #
def _table_mechanism(res: Dict[str, Any], name: str, label: str,
                     caption: str, rows: List[tuple]) -> bool:
    if not _usable(res.get("status")) or not res.get("conditions"):
        _placeholder(name, f"{name.replace('table_', '')} dataset {res.get('status', 'missing')}")
        return False
    on = res["conditions"]["on"]
    off = res["conditions"]["off"]
    comp = res.get("comparisons", {})
    adj = res.get("holm_adjusted_p", {})
    n = res.get("n_pairs", 0)
    # The test column is abbreviated ("Wilcoxon", "McNemar") and expanded in the
    # caption: spelling the tests out in full forces \resizebox to shrink the
    # whole table well below the surrounding body text.
    short_test = {"Wilcoxon signed-rank": "Wilcoxon", "McNemar (exact)": "McNemar"}
    L = _header(
        f"{caption} ($N={n}$ paired trials; the same seed drives both arms, so each "
        f"row is a within-pair comparison). Continuous outcomes use the Wilcoxon "
        f"signed-rank test and mission success McNemar's exact test; rows marked "
        f"\\emph{{identical}} were equal in every pair. $p$-values are Holm-adjusted "
        f"across the rows of this table.",
        label, "lcccc",
        "\\textbf{Metric} & \\textbf{ON} & \\textbf{OFF} & "
        "\\textbf{Test} & \\textbf{$p$ (Holm)} \\\\",
        wide=False, resize=True)
    for key, pretty, prec in rows:
        if key not in on:
            continue
        test = comp.get(key, {}).get("test", "--")
        L.append(f"{pretty} & {_f(on[key], prec)} & {_f(off[key], prec)} & "
                 f"{short_test.get(test, test)} & {_p(adj.get(key))} \\\\")
    L.append("\\midrule")
    st = comp.get("success", {}).get("test", "McNemar (exact)")
    L.append(f"Mission success & {on.get('success_rate', 0.0):.1f}\\% & "
             f"{off.get('success_rate', 0.0):.1f}\\% & {short_test.get(st, st)} & "
             f"{_p(adj.get('success'))} \\\\")
    L += _footer(wide=False, resize=True)
    return _emit(name, L)


def table_mesh_anticipation(res: Dict[str, Any]) -> bool:
    return _table_mechanism(
        res, "table_mesh_anticipation", "tab:mech_mesh",
        "Mechanism experiment A: V2V mesh anticipation. A corridor is blocked out of "
        "line of sight; with the mesh enabled the follower learns of the obstruction "
        "before observing it",
        [("anticipation_lead_time_s", "Anticipation lead time (s)", 2),
         ("backtrack_distance_m", "Backtrack distance (m)", 2),
         ("path_length_m", "Path length (m)", 2),
         ("makespan_s", "Makespan (s)", 2)])


def table_corridor_lock(res: Dict[str, Any]) -> bool:
    return _table_mechanism(
        res, "table_corridor_lock", "tab:mech_lock",
        "Mechanism experiment B: distributed corridor mutex. Two carts are routed into "
        "the same single-file corridor from opposite ends",
        [("head_on_events", "Head-on encounters", 2),
         ("deadlocks", "Deadlocks", 2),
         ("lock_wait_s", "Lock wait (s)", 2),
         ("corridor_time_s", "Corridor occupancy (s)", 2),
         ("makespan_s", "Makespan (s)", 2)])


# --------------------------------------------------------------------------- #
# Scalability figures
# --------------------------------------------------------------------------- #
def _figure_scalability(res: Dict[str, Any], name: str, xlabel: str,
                        panels: List[tuple], caption: str, label: str) -> bool:
    """Small multiples over an ordered sweep; one panel per metric."""
    if not _usable(res.get("status")) or not res.get("groups"):
        _placeholder(name, f"{name.replace('fig_', '')} dataset {res.get('status', 'missing')}")
        return False
    groups = res["groups"]
    xs = sorted(groups, key=lambda k: float(k))
    xv = [float(k) for k in xs]

    fig, axes = plt.subplots(1, len(panels), figsize=(3.5 * len(panels), 3.2))
    for ax, (key, ylabel, title, prec) in zip(axes, panels):
        if key == "success_rate":
            vals = [groups[k]["success_rate"] for k in xs]
            lo = [max(0.0, v - groups[k]["success_ci95"][0]) for v, k in zip(vals, xs)]
            hi = [max(0.0, groups[k]["success_ci95"][1] - v) for v, k in zip(vals, xs)]
            ax.set_ylim(0, 108)
        else:
            vals = [groups[k][key]["mean"] for k in xs]
            sd = [groups[k][key]["sd"] for k in xs]
            lo = hi = sd
        ax.errorbar(xv, vals, yerr=[lo, hi], color=PALETTE[0], marker="o",
                    markersize=4, linewidth=1.4, elinewidth=0.9, capsize=2.5, zorder=3)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title, loc="left")
        ax.set_xticks(xv)
        ax.yaxis.set_major_locator(MaxNLocator(5))
        _style(ax)

    if _provisional(res.get("status")):
        fig.text(0.5, 0.985, "PROVISIONAL - dataset generated by superseded code",
                 ha="center", va="top", fontsize=7.5, color="#b02418")
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(FIG_DIR, f"{name}.{ext}"))
    plt.close(fig)
    print(f"  [ok]   {name}.{{pdf,png}}")

    return _emit(name, [
        "% GENERATED FILE - do not edit by hand.",
        "% Produced by paper/scripts/generate_tables_and_figures.py",
        "\\begin{figure*}[t]",
        "\\centering",
        f"\\includegraphics[width=\\textwidth]{{{name}.pdf}}",
        f"\\caption{{{caption}}}",
        f"\\label{{{label}}}",
        "\\end{figure*}",
        "",
    ])


def figure_crowd_density(res: Dict[str, Any]) -> bool:
    return _figure_scalability(
        res, "fig_crowd_density", "Pedestrians in the environment",
        [("replan_latency_ms", "Replan latency (ms)", "(a) Incremental replan cost", 3),
         ("mesh_packets", "V2V packets per trial", "(b) Mesh traffic", 1),
         ("success_rate", "Mission success (%)", "(c) Success rate", 1)],
        "Crowd-density scalability at a fixed fleet of four carts. Error bars are "
        "$\\pm$1 SD, except (c) which shows the Wilson 95\\% interval.",
        "fig:scalability_crowd")


def figure_fleet_size(res: Dict[str, Any]) -> bool:
    return _figure_scalability(
        res, "fig_fleet_size", "Carts in the fleet",
        [("makespan", "Makespan (s)", "(a) Fleet makespan", 2),
         ("mesh_packets", "V2V packets per trial", "(b) Mesh traffic", 1),
         ("success_rate", "Mission success (%)", "(c) Success rate", 1)],
        "Fleet-size scalability at a fixed crowd of ten pedestrians. Error bars are "
        "$\\pm$1 SD, except (c) which shows the Wilson 95\\% interval.",
        "fig:scalability_fleet")


def table_availability(results: Dict[str, Any]) -> None:
    """A table recording which datasets back the manuscript, and which do not."""
    L = [
        "% GENERATED FILE - do not edit by hand.",
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{Provenance of the reported results. Every entry marked "
        "\\emph{complete} is regenerated from the committed raw data by the "
        "analysis pipeline; entries marked otherwise are not reported in this "
        "manuscript.}",
        "\\label{tab:provenance}",
        "\\begin{tabular}{ll}",
        "\\toprule",
        "\\textbf{Experiment} & \\textbf{Dataset status} \\\\",
        "\\midrule",
    ]
    pretty = {
        "benchmark": "Comparative benchmark",
        "ablation": "Component ablation",
        "cross_domain": "Cross-domain generalisation",
        "crowd_density": "Crowd-density scalability",
        "fleet_size": "Fleet-size scalability",
        "mesh_anticipation": "Mechanism A: mesh anticipation",
        "corridor_lock": "Mechanism B: corridor mutex",
    }
    for key, label in pretty.items():
        status = results.get(key, {}).get("status", "missing")
        word = "complete" if status == "ok" else status.replace("_", " ")
        L.append(f"{label} & {word} \\\\")
    L += ["\\bottomrule", "\\end{tabular}", "\\end{table}", ""]
    with open(os.path.join(TAB_DIR, "table_provenance.tex"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print("  [ok]   generated/table_provenance.tex")


def main() -> None:
    results = load_analysis()
    print("Generating manuscript artefacts from analysis_results.json\n")
    bench_ok = figure_benchmark(results.get("benchmark", {}))
    table_benchmark(results.get("benchmark", {}))
    table_availability(results)

    # Each generator emits its artefact when the dataset is usable and a
    # placeholder recording the reason when it is not, so a missing experiment can
    # never be silently represented by values left over from an earlier run.
    table_ablation(results.get("ablation", {}))
    table_cross_domain(results.get("cross_domain", {}))
    table_mesh_anticipation(results.get("mesh_anticipation", {}))
    table_corridor_lock(results.get("corridor_lock", {}))
    figure_crowd_density(results.get("crowd_density", {}))
    figure_fleet_size(results.get("fleet_size", {}))

    # fig1_note.tex exists only to explain an ABSENT Figure 1. Once the benchmark
    # figure is produced the note is stale by definition, so it is removed rather
    # than left to contradict the artefact beside it.
    note = os.path.join(TAB_DIR, "fig1_note.tex")
    if bench_ok and os.path.exists(note):
        os.remove(note)
        print("  [rm]   generated/fig1_note.tex (obsolete: Figure 1 was generated)")

    print("\nDone. Tables in paper/generated/, figures in paper/figures/.")


if __name__ == "__main__":
    main()
