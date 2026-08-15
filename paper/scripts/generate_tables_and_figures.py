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
    figure_benchmark(results.get("benchmark", {}))
    table_benchmark(results.get("benchmark", {}))
    table_availability(results)

    for key, name in (("ablation", "table_ablation"),
                      ("cross_domain", "table_cross_domain"),
                      ("crowd_density", "fig_crowd_density"),
                      ("fleet_size", "fig_fleet_size"),
                      ("mesh_anticipation", "table_mesh_anticipation"),
                      ("corridor_lock", "table_corridor_lock")):
        res = results.get(key, {})
        if not _usable(res.get("status")):
            _placeholder(name, f"{key} dataset {res.get('status', 'missing')}")

    print("\nDone. Tables in paper/generated/, figures in paper/figures/.")


if __name__ == "__main__":
    main()
