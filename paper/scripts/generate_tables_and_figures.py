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
    "Local Social D* Lite": "Local social",
    "Static A* (matched controller)": "A* matched",
    "Static A*": "Static A*",
    "Reactive Avoidance (Potential Field)": "APF",
    "Artificial Potential Fields (APF)": "APF",
    "Reactive ORCA (Velocity Obstacles)": "ORCA",
    "Decentralized Local MAPF": "MAPF",
}
# Primary comparison: the planners that complete their missions and whose
# implementations we are prepared to stand behind.
#
# ORCA and Local MAPF are deliberately NOT here. Both are our own implementations,
# both return 0% success, and we decline to infer from that that the published
# algorithms fail. Plotting them at 0% beside D2RO would communicate visually a
# comparison the text then asks the reader to distrust, so they are reported in a
# a sentence of prose in the failure-mode discussion instead, clearly labelled
# as diagnostic. SUPPLEMENTARY is retained so that list stays documented.
ORDER = [
    "D2RO (SW-DGO Proposed)",
    # Local Social D* Lite is the comparator a reader most wants: ordinary
    # human-aware navigation (proxemics, yielding, safety, replanning) WITHOUT the
    # distributed layer. It sits second so that the question "what does the
    # distributed part add?" is put to the reader immediately rather than deferred
    # to an ablation, where it would read as an internal component study.
    "Local Social D* Lite",
    # The matched-controller arm sits next: it is the comparison that isolates
    # routing from the vehicle model, and should be met before the unmatched one.
    "Static A* (matched controller)",
    "Static A*",
    "Reactive Avoidance (Potential Field)",
]
SUPPLEMENTARY = [
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
    # Person-seconds, not control ticks. The tick count is an artefact of the
    # integration step (dt = 0.05 s) and is not comparable across anything that
    # changes the step; person-seconds is the quantity the manuscript reasons about
    # and the one every other exposure figure and table reports.
    ex = [groups[m]["exposure_person_s"] for m in methods]
    med = [d.get("median", 0.0) for d in ex]
    q1 = [d.get("iqr", [0, 0])[0] for d in ex]
    q3 = [d.get("iqr", [0, 0])[1] for d in ex]
    lo = [max(0.0, m_ - a) for m_, a in zip(med, q1)]
    hi = [max(0.0, b - m_) for m_, b in zip(med, q3)]
    bars = ax.bar(labels, med, color=colors, width=0.68, zorder=3)
    ax.errorbar(labels, med, yerr=[lo, hi], fmt="none", ecolor=MUTED,
                elinewidth=0.9, capsize=2.5, zorder=4)
    top = max(q3 + [1.0])
    adj = bench.get("holm_adjusted_p", {})
    for b, v, e, m in zip(bars, med, hi, methods):
        ax.text(b.get_x() + b.get_width() / 2, v + e + top * 0.05, f"{v:.1f}",
                ha="center", va="bottom", fontsize=8, color=INK)
        # Significance against D2RO, printed beneath each bar. This previously lived
        # in a separate table that otherwise duplicated this figure; carrying it here
        # lets the comparison and its evidence be read in one place.
        if not m.startswith("D2RO"):
            p = adj.get(f"{m}|intimate")
            if p is not None:
                exp = int(f"{p:.0e}".split("e")[1])
                ax.text(b.get_x() + b.get_width() / 2, top * 0.03,
                        f"$p\\!<\\!10^{{{exp + 1}}}$", ha="center", va="bottom",
                        fontsize=6.5, color=MUTED)
    ax.set_ylabel("Intimate-space exposure (person-s)")
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
# The ablation dataset carries seven configurations, and they answer two different
# questions. Splitting them into blocks makes the causal structure legible: the
# first asks what each ROUTING term contributes, the second separates the safety
# COST TERM from the reactive safety CONTROLLER, which are distinct mechanisms that
# the earlier single-block table conflated.
#
# The keys are the config strings written by run_experiments.py. They are listed
# exhaustively on purpose: a previous revision of this table silently dropped four
# configurations because its label map had drifted from the experiment, so
# table_ablation now fails loudly on an unrecognised key instead of omitting a row.
ABLATION_ROUTING = {
    "Full D2RO Framework": "\\textbf{Full $\\text{D}^2\\text{RO}$}",
    "w/o V2V Mesh Telemetry": "w/o V2V mesh $W_{\\text{mesh}}$",
    "w/o Human Gaussian Proxemics": "w/o proxemics $H_{\\text{prox}}$",
    "w/o Corridor Reservation": "reservation constraint $R_{\\text{lock}}$ lifted",
}
ABLATION_SAFETY = {
    "Full D2RO Framework": "\\textbf{Full $\\text{D}^2\\text{RO}$}",
    "w/o S_trolley cost only": "$w_S = 0$, reactive controller retained",
    "w/o safety controller only": "controller off, $w_S$ retained",
    "w/o safety (full stack)": "both off",
}
ABLATION_LABEL = {**ABLATION_ROUTING, **ABLATION_SAFETY}


def table_ablation(res: Dict[str, Any]) -> bool:
    if not _usable(res.get("status")) or not res.get("groups"):
        _placeholder("table_ablation", f"ablation dataset {res.get('status', 'missing')}")
        return False
    groups = res["groups"]
    unknown = [k for k in groups if k not in ABLATION_LABEL]
    if unknown:
        raise KeyError(
            "ablation configurations present in the data but absent from the label "
            f"map, which would drop them silently from Table: {unknown}")
    n = groups[next(iter(groups))].get("n", 0)
    L = _header(
        f"Component ablation in the retail supermarket domain ($N={n}$ trials per "
        f"configuration). The upper block removes one soft cost term at a time from "
        f"Eq.~(1), or lifts the reservation feasibility constraint; the lower block "
        f"separates the kinematic safety \\emph{{cost term}} from the reactive safety "
        f"\\emph{{controller}}, which are distinct mechanisms. All other parameters "
        f"are held fixed. Counts are reported as median [IQR] because they are "
        f"right-skewed; makespan is mean $\\pm$ SD. No configuration recorded a "
        f"deadlock in any trial.",
        "tab:ablation", "lccccc",
        "\\textbf{Configuration} & \\textbf{Success (95\\% CI)} & \\textbf{Makespan (s)} & "
        "\\textbf{Discomfort} & \\textbf{Fixture contacts} & "
        "\\textbf{Contact ticks} \\\\",
        wide=True, resize=True)

    def block(title: str, labels: Dict[str, str], first: bool) -> None:
        if not first:
            L.append("\\midrule")
        L.append(f"\\multicolumn{{6}}{{l}}{{\\emph{{{title}}}}} \\\\")
        for k, lab in labels.items():
            if k not in groups:
                continue
            g = groups[k]
            # Discomfort and contact counts are right-skewed and, for several arms,
            # have a standard deviation larger than their mean -- "5.71 +/- 7.29"
            # implies negative counts, which cannot occur. They are reported as
            # median [IQR], the same treatment already applied to intimate exposure.
            # Makespan stays mean +/- SD: it is continuous and roughly symmetric.
            L.append(f"{lab} & {_pct(g)} & {_f(g['makespan'])} & "
                     f"{_med(g['discomfort'], 1)} & {_med(g['shelf_contact_events'])} & "
                     f"{_med(g['shelf_contact_ticks'])} \\\\")

    block("Routing-cost ablations", ABLATION_ROUTING, first=True)
    block("Safety attribution", ABLATION_SAFETY, first=False)
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
    # No "Test" column. Every continuous row uses the same test, so a column
    # repeating it carries no information and costs a fifth of the table width; the
    # caption states it once instead.
    #
    # The mission-success row is included ONLY when the two arms differ. Where both
    # complete every mission, a row reading "100.0% / 100.0% / p = 1" tells the
    # reader nothing they cannot be told in half a sentence of prose.
    on_succ = on.get("success_rate", 0.0)
    off_succ = off.get("success_rate", 0.0)
    success_differs = abs(on_succ - off_succ) > 1e-9

    succ_note = ("" if success_differs else
                 f" Both arms completed {on_succ:.1f}\\% of missions, so mission "
                 f"success does not separate them and is omitted from the table.")
    L = _header(
        f"{caption} ($N={n}$ paired trials; the same seed drives both arms, so each "
        f"row is a within-pair comparison). Continuous outcomes use the Wilcoxon "
        f"signed-rank test; rows whose two arms were equal in every pair admit no "
        f"test. $p$-values are Holm-adjusted across the rows of this table.{succ_note}",
        label, "lccc",
        "\\textbf{Metric} & \\textbf{ON} & \\textbf{OFF} & "
        "\\textbf{$p$ (Holm)} \\\\",
        wide=False, resize=True)
    for key, pretty, prec in rows:
        if key not in on:
            continue
        L.append(f"{pretty} & {_f(on[key], prec)} & {_f(off[key], prec)} & "
                 f"{_p(adj.get(key))} \\\\")
    if success_differs:
        L.append("\\midrule")
        L.append(f"Mission success (McNemar) & {on_succ:.1f}\\% & "
                 f"{off_succ:.1f}\\% & {_p(adj.get('success'))} \\\\")
    L += _footer(wide=False, resize=True)
    return _emit(name, L)


def table_mesh_anticipation(res: Dict[str, Any]) -> bool:
    return _table_mechanism(
        res, "table_mesh_anticipation", "tab:mech_mesh",
        "Mechanism experiment A: V2V mesh anticipation. A corridor is blocked outside "
        "the follower's onboard sensing radius; with the mesh enabled the follower "
        "learns of the obstruction before observing it",
        [("anticipation_lead_time_s", "Anticipation lead time (s)", 2),
         ("backtrack_distance_m", "Backtrack distance (m)", 2),
         ("path_length_m", "Path length (m)", 2),
         ("makespan_s", "Makespan (s)", 2)])


def table_corridor_lock(res: Dict[str, Any]) -> bool:
    return _table_mechanism(
        res, "table_corridor_lock", "tab:mech_lock",
        "Mechanism experiment B: directional corridor reservation. Two carts are routed into "
        "the same single-file corridor from opposite ends",
        [("head_on_events", "Head-on encounters", 2),
         ("deadlocks", "Deadlocks", 2),
         ("total_lock_wait_s", "Lock wait, total (s)", 2),
         ("nodes_outside_corridor", "Off-corridor vertices", 2),
         ("replans", "Route reconsiderations", 1),
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


def figure_degradation(res: Dict[str, Any]) -> bool:
    """
    The PAIRED mesh effect as the channel degrades, with bootstrap CIs.

    Plotting the absolute Mesh-ON lead time would discard the controlled design:
    every channel condition runs a Mesh-ON and a Mesh-OFF trial on the same seed,
    so the quantity that the experiment actually estimates is the within-pair
    difference. That is what is drawn here, one line per latency level, against
    packet loss. A point above the zero rule means the mesh still bought
    anticipation under that channel.
    """
    if not _usable(res.get("status")) or not res.get("channels"):
        _placeholder("fig_degradation",
                     f"mesh_degradation dataset {res.get('status', 'missing')}")
        return False
    chans = res["channels"]
    losses = sorted({c["loss_rate"] for c in chans.values()})
    lats = sorted({c["latency_s"] for c in chans.values()})

    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.2))
    for ax, (metric, ylabel, title) in zip(axes, [
            ("delta_lead_time", "$\\Delta$ anticipation lead time (s)",
             "(a) Anticipation advantage of the mesh"),
            ("delta_backtrack", "$\\Delta$ backtracking avoided (m)",
             "(b) Backtracking avoided by the mesh")]):
        for i, lat in enumerate(lats):
            sel = [(c["loss_rate"], c[metric]) for c in chans.values()
                   if c["latency_s"] == lat]
            sel.sort()
            xs = [s[0] * 100 for s in sel]
            ys = [s[1]["bootstrap"]["mean_difference"] for s in sel]
            lo = [y - s[1]["bootstrap"]["ci95_difference"][0] for y, s in zip(ys, sel)]
            hi = [s[1]["bootstrap"]["ci95_difference"][1] - y for y, s in zip(ys, sel)]
            ax.errorbar(xs, ys, yerr=[lo, hi], marker="o", markersize=4,
                        linewidth=1.4, elinewidth=0.9, capsize=2.5,
                        color=PALETTE[i % len(PALETTE)], zorder=3,
                        label=f"{lat * 1000:.0f} ms latency")
        ax.axhline(0.0, color=MUTED, linewidth=0.8, linestyle="--", zorder=2)
        ax.set_xlabel("Packet loss (%)")
        ax.set_ylabel(ylabel)
        ax.set_title(title, loc="left")
        ax.set_xticks([l * 100 for l in losses])
        ax.yaxis.set_major_locator(MaxNLocator(5))
        _style(ax)
    axes[0].legend(frameon=False, fontsize=7, loc="lower left")

    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(FIG_DIR, f"fig_degradation.{ext}"))
    plt.close(fig)
    print("  [ok]   fig_degradation.{pdf,png}")

    n = next(iter(chans.values()))["n_pairs"]
    return _emit("fig_degradation", [
        "% GENERATED FILE - do not edit by hand.",
        "% Produced by paper/scripts/generate_tables_and_figures.py",
        "\\begin{figure*}[t]",
        "\\centering",
        "\\includegraphics[width=\\textwidth]{fig_degradation.pdf}",
        f"\\caption{{Paired effect of the V2V mesh on Mechanism~A as the channel "
        f"degrades ($N={n}$ seed-matched Mesh-ON/Mesh-OFF pairs per channel "
        f"condition). Each point is the within-pair difference, not an absolute "
        f"arm value, so the controlled design of the mechanism experiment is "
        f"preserved; error bars are percentile bootstrap 95\\% intervals on the "
        f"mean difference. The dashed rule marks no mesh advantage.}}",
        "\\label{fig:degradation}",
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


def commit_stamp() -> None:
    """
    Records the exact commit the artefacts were generated from, as a LaTeX macro
    the manuscript can cite.

    The reviewer's first required revision was that the submitted PDF and the
    repository must be the same, verifiable thing. Writing the SHA by hand is how
    that guarantee decays, so it is derived from git at generation time.

    Uncommitted SOURCE changes are reported with a `-dirty` suffix: a manuscript
    generated from uncommitted code is not reproducible and should say so rather
    than cite a commit it does not match. Regenerated artefacts are excluded from
    that test, because this function runs after the pipeline has rewritten them and
    would otherwise mark every build dirty, including a clean checkout from a tag.
    """
    import subprocess

    # Paths that this pipeline itself produces. They are OUTPUTS of the very command
    # that writes this stamp, so they are always modified by the time we look, and
    # counting them would make every build report "-dirty" including a clean CI
    # checkout from a tag. What the stamp asserts is that the SOURCES match the named
    # commit; regenerated artefacts are the consequence of that source, not evidence
    # against it.
    GENERATED_PREFIXES = (
        "paper/generated/",
        "paper/figures/",
        "paper/paper.pdf",
        "paper/paper.aux", "paper/paper.bbl", "paper/paper.blg",
        "paper/paper.log", "paper/paper.out",
        "experiments/data/analysis_results.json",
        "experiments/data/analysis_report.md",
    )

    try:
        sha = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"],
                                      cwd=PROJECT_ROOT, text=True).strip()
        porcelain = subprocess.check_output(["git", "status", "--porcelain"],
                                            cwd=PROJECT_ROOT, text=True).splitlines()
        # `git status --porcelain` lines look like "XY path" or "XY old -> new".
        changed = []
        for line in porcelain:
            path = line[3:].strip().split(" -> ")[-1].strip('"')
            if not path.startswith(GENERATED_PREFIXES):
                changed.append(path)
        stamp = f"{sha}-dirty" if changed else sha
        if changed:
            print(f"         source changes present: {', '.join(changed[:4])}"
                  + (" ..." if len(changed) > 4 else ""))
    except Exception:
        stamp = "unknown"
    with open(os.path.join(TAB_DIR, "commit.tex"), "w", encoding="utf-8") as f:
        f.write("% GENERATED FILE - do not edit by hand.\n"
                f"\\newcommand{{\\PaperCommitSHA}}{{{stamp}}}\n")
    print(f"  [ok]   generated/commit.tex ({stamp})")



# --------------------------------------------------------------------------- #
# Supplementary + Phase-B experiments
# --------------------------------------------------------------------------- #
FACTORIAL_LABEL = {
    "A_prox_off_yield_off": "$H_{\\text{prox}}$ OFF, yield OFF",
    "B_prox_off_yield_on":  "$H_{\\text{prox}}$ OFF, yield ON",
    "C_prox_on_yield_off":  "$H_{\\text{prox}}$ ON, yield OFF",
    "D_prox_on_yield_on":   "$H_{\\text{prox}}$ ON, yield ON (\\textbf{$\\text{D}^2\\text{RO}$})",
    "A_frozen_noyield":     "Frozen route, no yielding",
    "B_frozen_yield":       "Frozen route, yielding",
    "C_social_noyield":     "Social route, no yielding",
    "D_social_yield":       "Social route, yielding (\\textbf{$\\text{D}^2\\text{RO}$})",
}


def table_factorial(res):
    """Route x yield factorial: the attribution experiment."""
    if not _usable(res.get("status")) or not res.get("groups"):
        _placeholder("table_factorial",
                     f"route_yield_factorial dataset {res.get('status', 'missing')}")
        return False
    g = res["groups"]
    order = [k for k in FACTORIAL_LABEL if k in g]
    n = g[order[0]].get("n", 0)
    L = _header(
        f"Proxemic routing ($H_{{\\text{{prox}}}}$) versus reactive human yielding "
        f"($N={n}$ seed-paired trials per cell). Mesh and corridor reservation are "
        f"disabled in \\emph{{every}} cell and the dynamic $\\text{{D}}^*$ Lite search "
        f"is active in every cell, so the only quantities that vary are the two named "
        f"factors. Exposure is person-seconds inside the intimate boundary, reported "
        f"as median [IQR] because it is zero-inflated once $H_{{\\text{{prox}}}}$ is "
        f"active, with mean $\\pm$ SD alongside. The lower block gives the "
        f"pre-specified paired contrasts: each is tested against zero across the "
        f"seed-matched trials and Holm-adjusted within its outcome family.",
        "tab:factorial", "lccccc",
        r"\textbf{Configuration} & \textbf{Success (95\% CI)} & "
        r"\textbf{Makespan (s)} & \textbf{Exposure median [IQR]} & "
        r"\textbf{Exposure mean $\pm$ SD} & \textbf{Encounters} \\",
        wide=True, resize=True)
    for k in order:
        e = g[k]
        L.append(f"{FACTORIAL_LABEL[k]} & {_pct(e)} & {_f(e['makespan'])} & "
                 f"{_med(e['exposure_person_s'], 2)} & {_f(e['exposure_person_s'])} & "
                 f"{_med(e['encounters'], 1)} \\\\")

    L += _footer(wide=True, resize=True)
    return _emit("table_factorial", L)


# Pre-specified contrasts, in the order the manuscript argues them.
FACTORIAL_CONTRASTS = [
    ("routing_effect_yield_off", "$H_{\\text{prox}}$ main effect, yielding OFF",
     "C $-$ A"),
    ("routing_effect_yield_on",  "$H_{\\text{prox}}$ main effect, yielding ON",
     "D $-$ B"),
    ("yielding_effect_prox_off", "Yielding main effect, $H_{\\text{prox}}$ OFF",
     "B $-$ A"),
    ("yielding_effect_prox_on",  "Yielding main effect, $H_{\\text{prox}}$ ON",
     "D $-$ C"),
    ("interaction",              "\\textbf{Interaction}",
     "(D $-$ C) $-$ (B $-$ A)"),
]


def table_factorial_contrasts(res: Dict[str, Any]) -> bool:
    """
    The inferential half of the factorial.

    Cell summaries cannot establish a main effect or an interaction: those are
    statements about differences, and the differences are what this table tests.
    Every contrast is computed within seed-matched trials, so the pairing the
    design establishes is preserved rather than discarded in favour of comparing
    two marginal means.
    """
    con = res.get("contrasts")
    if not _usable(res.get("status")) or not con:
        _placeholder("table_factorial_contrasts",
                     f"route_yield_factorial dataset {res.get('status', 'missing')}")
        return False
    succ = res.get("success_contrasts", {})
    n = con["interaction_exposure"].get("n", 0)

    def mediqr(d: Dict[str, Any]) -> str:
        q1, q3 = d.get("iqr", [0.0, 0.0])
        return f"${d.get('median', 0.0):.2f}$ [${q1:.2f}$, ${q3:.2f}$]"

    L = _header(
        f"Pre-specified paired contrasts for the $2\\times2$ factorial "
        f"($N={n}$ seed-matched trials per contrast). Exposure is in person-seconds; "
        f"a negative effect is a reduction. Each contrast is tested against zero "
        f"across matched trials --- by paired $t$-test where the differences are "
        f"normal by Shapiro--Wilk and Wilcoxon signed-rank otherwise, with the test "
        f"used named in the table --- and $p$ values are Holm-adjusted within the "
        f"outcome family. Intervals are percentile bootstrap 95\\% CIs on the mean "
        f"difference. Binary success is compared by exact McNemar on the same "
        f"matched trials.",
        "tab:factorial_contrasts", "llccccc",
        r"\textbf{Contrast} & \textbf{Cells} & \textbf{Median [IQR]} & "
        r"\textbf{Mean (95\% CI)} & \textbf{Test} & \textbf{$p_{\text{Holm}}$} & "
        r"\textbf{Success $p_{\text{Holm}}$} \\",
        wide=True, resize=True)
    for key, lab, cells in FACTORIAL_CONTRASTS:
        c = con.get(f"{key}_exposure")
        if not c:
            continue
        lo, hi = c["bootstrap"]["ci95_difference"]
        s = succ.get(f"{key}_success")
        sp = _p(s.get("p_holm")) if s else "--"
        L.append(f"{lab} & {cells} & {mediqr(c)} & "
                 f"${c['mean']:.2f}$ (${lo:.2f}$, ${hi:.2f}$) & "
                 f"{c.get('test', '--')} & {_p(c.get('p_holm'))} & {sp} \\\\")
    L += _footer(wide=True, resize=True)
    return _emit("table_factorial_contrasts", L)


def figure_weight_sensitivity(res):
    """One panel per outcome; one line per weight, across the multiplier grid."""
    if not _usable(res.get("status")) or not res.get("groups"):
        _placeholder("fig_weight_sensitivity",
                     f"weight_sensitivity dataset {res.get('status', 'missing')}")
        return False
    groups = res["groups"]
    if "nominal" not in groups:
        _placeholder("fig_weight_sensitivity", "nominal configuration missing")
        return False

    weights = ["w_D", "w_M", "w_H", "w_S"]
    mults = [0.5, 0.75, 1.0, 1.25, 1.5]
    panels = [("success_rate", "Mission success (%)", "(a) Success"),
              ("makespan", "Makespan (s)", "(b) Makespan"),
              ("intimate_exposure", "Intimate exposure (ticks)", "(c) Social exposure")]

    fig, axes = plt.subplots(1, 3, figsize=(10.4, 3.2))
    for ax, (key, ylabel, title) in zip(axes, panels):
        for i, w in enumerate(weights):
            xs, ys = [], []
            for m in mults:
                name = "nominal" if m == 1.0 else f"{w}x{m}"
                g = groups.get(name)
                if not g:
                    continue
                xs.append(m)
                ys.append(g["success_rate"] if key == "success_rate"
                          else g[key]["mean"])
            if xs:
                ax.plot(xs, ys, marker="o", markersize=3.5, linewidth=1.3,
                        color=PALETTE[i % len(PALETTE)], label=f"${w[0]}_{w[2]}$",
                        zorder=3)
        ax.set_xlabel("Weight multiplier")
        ax.set_ylabel(ylabel)
        ax.set_title(title, loc="left")
        ax.set_xticks(mults)
        if key == "success_rate":
            ax.set_ylim(0, 108)
        ax.yaxis.set_major_locator(MaxNLocator(5))
        _style(ax)
    axes[0].legend(frameon=False, fontsize=7, ncol=2)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(FIG_DIR, f"fig_weight_sensitivity.{ext}"))
    plt.close(fig)
    print("  [ok]   fig_weight_sensitivity.{pdf,png}")

    return _emit("fig_weight_sensitivity", [
        r"% GENERATED FILE - do not edit by hand.",
        r"\begin{figure*}[t]", r"\centering",
        r"\includegraphics[width=\textwidth]{fig_weight_sensitivity.pdf}",
        r"\caption{Sensitivity of the four soft cost weights ($w_D, w_M, w_H, w_S$). Each weight is scaled in turn "
        r"while the other three are held at nominal; the $\times 1.0$ point is the shared "
        r"nominal configuration. Corridor reservation is a hard feasibility constraint and is evaluated separately. "
        r"Evaluated on a seed set disjoint from every other experiment.}",
        r"\label{fig:weight_sensitivity}", r"\end{figure*}", "",
    ])


def main() -> None:
    results = load_analysis()
    print("Generating manuscript artefacts from analysis_results.json\n")
    bench_ok = figure_benchmark(results.get("benchmark", {}))
    commit_stamp()

    # Each generator emits its artefact when the dataset is usable and a
    # placeholder recording the reason when it is not, so a missing experiment can
    # never be silently represented by values left over from an earlier run.
    table_ablation(results.get("ablation", {}))
    table_cross_domain(results.get("cross_domain", {}))
    table_mesh_anticipation(results.get("mesh_anticipation", {}))
    table_corridor_lock(results.get("corridor_lock", {}))
    figure_crowd_density(results.get("crowd_density", {}))
    figure_fleet_size(results.get("fleet_size", {}))
    table_factorial(results.get("route_yield_factorial", {}))
    table_factorial_contrasts(results.get("route_yield_factorial", {}))
    figure_weight_sensitivity(results.get("weight_sensitivity", {}))
    figure_degradation(results.get("mesh_degradation", {}))

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
