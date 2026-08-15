"""
Comprehensive Statistical Verification and Analysis Engine for D²RO Paper.
Directly ingests the raw CSV datasets (N=100 Monte Carlo trials):
1. benchmark_comparison.csv
2. ablation_study.csv
3. cross_domain_benchmark.csv
4. scalability_crowd_density.csv
5. scalability_fleet_size.csv

Computes:
- Sample Mean (\mu)
- Sample Standard Deviation (\sigma) with ddof=1
- Standard Error of the Mean (SEM = \sigma / \sqrt{N})
- 95% Confidence Interval ([\mu - 1.96*SEM, \mu + 1.96*SEM])
- Two-tailed Welch's t-test p-values against D²RO
- Automatically writes exact synchronized markdown and LaTeX tables.
"""

import os
import csv
import math
import numpy as np
from scipy import stats

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "..", "experiments", "data")

def welch_ttest(sample1, sample2):
    """Computes exact Welch's t-statistic and two-tailed p-value using scipy.stats."""
    if len(sample1) < 2 or len(sample2) < 2:
        return 0.0, 1.0
    res = stats.ttest_ind(sample1, sample2, equal_var=False)
    p_val = res.pvalue if not np.isnan(res.pvalue) else 1.0
    t_stat = res.statistic if not np.isnan(res.statistic) else 0.0
    return float(t_stat), float(max(1e-15, p_val))


def run_full_statistical_verification():
    print("=" * 80)
    print("  D²RO SCIENTIFIC STATISTICAL VERIFICATION & REPORT GENERATOR (N=100)")
    print("=" * 80)
    
    # --------------------------------------------------------------------------
    # 1. Benchmark Comparison
    # --------------------------------------------------------------------------
    bench_csv = os.path.join(DATA_DIR, "benchmark_comparison.csv")
    bench_data = {}
    with open(bench_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            m = r["method"]
            if m not in bench_data:
                bench_data[m] = {
                    "success": [], "time": [], "deadlocks": [],
                    "viol": [], "pkts": [], "replan": [], "lat": []
                }
            bench_data[m]["success"].append(float(r["success"]) * 100.0)
            bench_data[m]["time"].append(float(r["travel_time_s"]))
            bench_data[m]["deadlocks"].append(float(r["deadlocks"]))
            bench_data[m]["viol"].append(float(r["proxemic_violations"]))
            bench_data[m]["pkts"].append(float(r["mesh_packets"]))
            bench_data[m]["replan"].append(float(r["replan_cycles"]))
            bench_data[m]["lat"].append(float(r["avg_replan_latency_ms"]))

    d2ro_time = bench_data["D2RO (SW-DGO Proposed)"]["time"]
    d2ro_viol = bench_data["D2RO (SW-DGO Proposed)"]["viol"]

    bench_stats = {}
    print("\n--- 1. BENCHMARK COMPARISON EXACT STATS (N=100) ---")
    for m, d in bench_data.items():
        n = len(d["success"])
        m_succ = np.mean(d["success"])
        m_time, s_time = np.mean(d["time"]), np.std(d["time"], ddof=1)
        sem_time = s_time / math.sqrt(n)
        ci_time_low, ci_time_high = m_time - 1.96 * sem_time, m_time + 1.96 * sem_time
        
        m_dead, s_dead = np.mean(d["deadlocks"]), np.std(d["deadlocks"], ddof=1)
        m_viol, s_viol = np.mean(d["viol"]), np.std(d["viol"], ddof=1)
        m_pkts, s_pkts = np.mean(d["pkts"]), np.std(d["pkts"], ddof=1)
        m_lat, s_lat = np.mean(d["lat"]), np.std(d["lat"], ddof=1)
        
        _, p_val = welch_ttest(d["time"], d2ro_time) if m != "D2RO (SW-DGO Proposed)" else (0.0, 1.0)
        p_str = "< 0.001" if p_val < 0.001 else f"{p_val:.4f}"
        if m == "D2RO (SW-DGO Proposed)":
            p_str = "—"

        bench_stats[m] = {
            "success": m_succ, "time_mean": m_time, "time_std": s_time,
            "ci_low": ci_time_low, "ci_high": ci_time_high,
            "dead_mean": m_dead, "dead_std": s_dead,
            "viol_mean": m_viol, "viol_std": s_viol,
            "pkts_mean": m_pkts, "pkts_std": s_pkts,
            "lat_mean": m_lat, "lat_std": s_lat,
            "p_val": p_str
        }
        print(f"[{m}] (N={n})")
        print(f"  Success: {m_succ:.1f}%")
        print(f"  Makespan: {m_time:.2f} ± {s_time:.2f} s [95% CI: {ci_time_low:.2f}, {ci_time_high:.2f}]")
        print(f"  Deadlocks: {m_dead:.2f} ± {s_dead:.2f}")
        print(f"  Proxemic Violations: {m_viol:.2f} ± {s_viol:.2f}")
        print(f"  V2V Packets: {m_pkts:.2f} ± {s_pkts:.2f}")
        print(f"  Latency: {m_lat:.3f} ± {s_lat:.3f} ms (p={p_str})")

    # --------------------------------------------------------------------------
    # 2. Component Ablation Study
    # --------------------------------------------------------------------------
    ablation_csv = os.path.join(DATA_DIR, "ablation_study.csv")
    ablation_data = {}
    with open(ablation_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            c = r["configuration"]
            if c not in ablation_data:
                ablation_data[c] = {
                    "omitted": r["omitted_component"],
                    "success": [], "time": [], "deadlocks": [],
                    "disc": [], "scrapes": []
                }
            ablation_data[c]["success"].append(float(r["success"]) * 100.0)
            ablation_data[c]["time"].append(float(r["travel_time_s"]))
            ablation_data[c]["deadlocks"].append(float(r["deadlocks"]))
            ablation_data[c]["disc"].append(float(r["discomfort_integral"]))
            ablation_data[c]["scrapes"].append(float(r["shelf_corner_scrapes"]))

    ablation_stats = {}
    print("\n--- 2. COMPONENT ABLATION EXACT STATS (N=100) ---")
    for c, d in ablation_data.items():
        n = len(d["success"])
        m_succ = np.mean(d["success"])
        m_time, s_time = np.mean(d["time"]), np.std(d["time"], ddof=1)
        m_dead, s_dead = np.mean(d["deadlocks"]), np.std(d["deadlocks"], ddof=1)
        m_disc, s_disc = np.mean(d["disc"]), np.std(d["disc"], ddof=1)
        m_scr, s_scr = np.mean(d["scrapes"]), np.std(d["scrapes"], ddof=1)

        ablation_stats[c] = {
            "omitted": d["omitted"],
            "success": m_succ, "time_mean": m_time, "time_std": s_time,
            "dead_mean": m_dead, "dead_std": s_dead,
            "disc_mean": m_disc, "disc_std": s_disc,
            "scr_mean": m_scr, "scr_std": s_scr
        }
        print(f"[{c}] (N={n})")
        print(f"  Success: {m_succ:.1f}% | Time: {m_time:.2f} ± {s_time:.2f}s")
        print(f"  Deadlocks: {m_dead:.2f} ± {s_dead:.2f} | Discomfort: {m_disc:.2f} ± {s_disc:.2f} | Scrapes: {m_scr:.2f} ± {s_scr:.2f}")

    # --------------------------------------------------------------------------
    # 3. Cross-Domain Benchmark
    # --------------------------------------------------------------------------
    cross_csv = os.path.join(DATA_DIR, "cross_domain_benchmark.csv")
    cross_data = {}
    with open(cross_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            env = r["environment"]
            if env not in cross_data:
                cross_data[env] = {"time": [], "pkts": [], "replan": []}
            cross_data[env]["time"].append(float(r["makespan_s"]))
            cross_data[env]["pkts"].append(float(r["mesh_packets_exchanged"]))
            cross_data[env]["replan"].append(float(r["dynamic_replans"]))

    cross_stats = {}
    print("\n--- 3. CROSS-DOMAIN EXACT STATS (N=100) ---")
    for env, d in cross_data.items():
        n = len(d["time"])
        m_time, s_time = np.mean(d["time"]), np.std(d["time"], ddof=1)
        m_pkts, s_pkts = np.mean(d["pkts"]), np.std(d["pkts"], ddof=1)
        m_rep, s_rep = np.mean(d["replan"]), np.std(d["replan"], ddof=1)
        cross_stats[env] = {
            "time_mean": m_time, "time_std": s_time,
            "pkts_mean": m_pkts, "pkts_std": s_pkts,
            "rep_mean": m_rep, "rep_std": s_rep
        }
        print(f"[{env}] (N={n}) Makespan: {m_time:.2f} ± {s_time:.2f}s | Packets: {m_pkts:.2f} ± {s_pkts:.2f} | Replans: {m_rep:.2f} ± {s_rep:.2f}")

    # --------------------------------------------------------------------------
    # 4. Crowd Density Scalability
    # --------------------------------------------------------------------------
    crowd_csv = os.path.join(DATA_DIR, "scalability_crowd_density.csv")
    crowd_data = {}
    with open(crowd_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            h = int(r["crowd_density_humans"])
            if h not in crowd_data:
                crowd_data[h] = {"success": [], "time": [], "lat": [], "pkts": []}
            crowd_data[h]["success"].append(float(r["success_rate_pct"]))
            crowd_data[h]["time"].append(float(r["makespan_s"]))
            crowd_data[h]["lat"].append(float(r["mean_replan_latency_ms"]))
            crowd_data[h]["pkts"].append(float(r["v2v_mesh_packets"]))

    crowd_stats = {}
    print("\n--- 4. CROWD DENSITY SCALABILITY (N=100) ---")
    for h in sorted(crowd_data.keys()):
        d = crowd_data[h]
        crowd_stats[h] = {
            "success": np.mean(d["success"]),
            "time_mean": np.mean(d["time"]), "time_std": np.std(d["time"], ddof=1),
            "lat_mean": np.mean(d["lat"]), "lat_std": np.std(d["lat"], ddof=1),
            "pkts_mean": np.mean(d["pkts"]), "pkts_std": np.std(d["pkts"], ddof=1),
        }
        print(f"  {h} Humans: Succ={crowd_stats[h]['success']:.1f}% | Time={crowd_stats[h]['time_mean']:.2f}s | Lat={crowd_stats[h]['lat_mean']:.3f}ms | Pkts={crowd_stats[h]['pkts_mean']:.1f}")

    # --------------------------------------------------------------------------
    # 5. Fleet Size Scalability
    # --------------------------------------------------------------------------
    fleet_csv = os.path.join(DATA_DIR, "scalability_fleet_size.csv")
    fleet_data = {}
    with open(fleet_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            fl = int(r["fleet_size_carts"])
            if fl not in fleet_data:
                fleet_data[fl] = {"success": [], "time": [], "wait": [], "pkts": []}
            fleet_data[fl]["success"].append(float(r["success_rate_pct"]))
            fleet_data[fl]["time"].append(float(r["makespan_s"]))
            fleet_data[fl]["wait"].append(float(r["corridor_mutex_wait_s"]))
            fleet_data[fl]["pkts"].append(float(r["v2v_mesh_packets"]))

    fleet_stats = {}
    print("\n--- 5. FLEET SIZE SCALABILITY (N=100) ---")
    for fl in sorted(fleet_data.keys()):
        d = fleet_data[fl]
        fleet_stats[fl] = {
            "success": np.mean(d["success"]),
            "time_mean": np.mean(d["time"]), "time_std": np.std(d["time"], ddof=1),
            "wait_mean": np.mean(d["wait"]), "wait_std": np.std(d["wait"], ddof=1),
            "pkts_mean": np.mean(d["pkts"]), "pkts_std": np.std(d["pkts"], ddof=1),
        }
        print(f"  {fl} Carts: Succ={fleet_stats[fl]['success']:.1f}% | Time={fleet_stats[fl]['time_mean']:.2f}s | Wait={fleet_stats[fl]['wait_mean']:.2f}s | Pkts={fleet_stats[fl]['pkts_mean']:.1f}")

    # --------------------------------------------------------------------------
    # 6. Generate Synchronized Markdown Report
    # --------------------------------------------------------------------------
    report_path = os.path.join(DATA_DIR, "experimental_results_analysis.md")
    lines = [
        "# Empirical Experimental Results & Statistical Analysis",
        "### Scientific Evaluation for $\\text{D}^2\\text{RO}$ (SW-DGO) Multi-Agent Research Framework",
        f"**Sample Size:** $N = 100$ independent randomized Monte Carlo trials per configuration with deterministic seeds.",
        "**Statistical Metrics:** Sample Mean $\\pm$ Sample Standard Deviation ($\\mu \\pm \\sigma$, $\\text{ddof}=1$), 95% Confidence Interval ($[\\mu - 1.96\\cdot\\text{SEM}, \\mu + 1.96\\cdot\\text{SEM}]$), and paired Welch's $t$-test $p$-values.",
        "",
        "---",
        "",
        "## 1. Comparative Benchmark Performance ($N=100$ Trials)",
        "",
        "| Navigation Algorithm | Success Rate (%) | Makespan (s) [95% CI] | Deadlocks | Intimate Violations | V2V Packets | Replan Latency (ms) | $p$-value (vs. D²RO) |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |"
    ]

    for m, s in bench_stats.items():
        succ_str = f"{s['success']:.1f}%"
        if "Timeout" in str(s['time_mean']) or s['time_mean'] >= 34.9:
            time_str = f"Timeout ($35.0\\text{{s}}$)"
        else:
            time_str = f"${s['time_mean']:.2f} \\pm {s['time_std']:.2f}$ [${s['ci_low']:.2f}, {s['ci_high']:.2f}$]"
        dead_str = f"${s['dead_mean']:.2f} \\pm {s['dead_std']:.2f}$"
        viol_str = f"${s['viol_mean']:.2f} \\pm {s['viol_std']:.2f}$"
        pkts_str = f"${s['pkts_mean']:.1f} \\pm {s['pkts_std']:.1f}$"
        lat_str = f"${s['lat_mean']:.3f} \\pm {s['lat_std']:.3f}$" if s['lat_mean'] > 0.0 else "N/A (Static)"
        p_val_str = f"$p {s['p_val']}$" if s['p_val'] != "—" else "—"

        if "D2RO" in m:
            lines.append(f"| **{m}** | $\\mathbf{{{succ_str}}}$ | $\\mathbf{{{s['time_mean']:.2f} \\pm {s['time_std']:.2f}}}$ [$\\mathbf{{{s['ci_low']:.2f}, {s['ci_high']:.2f}}}$] | $\\mathbf{{{s['dead_mean']:.2f} \\pm {s['dead_std']:.2f}}}$ | $\\mathbf{{{s['viol_mean']:.2f} \\pm {s['viol_std']:.2f}}}$ | $\\mathbf{{{s['pkts_mean']:.1f} \\pm {s['pkts_std']:.1f}}}$ | $\\mathbf{{{s['lat_mean']:.3f} \\pm {s['lat_std']:.3f}}}$ | {p_val_str} |")
        else:
            lines.append(f"| **{m}** | {succ_str} | {time_str} | {dead_str} | {viol_str} | {pkts_str} | {lat_str} | {p_val_str} |")

    lines.extend([
        "",
        "---",
        "",
        "## 2. Component Ablation Study ($N=100$ Trials)",
        "",
        "| Configuration | Omitted Component | Success Rate (%) | Travel Time (s) | Deadlocks | Discomfort Integral $\\mathcal{J}_{\\text{prox}}$ | Corner Scrapes |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: |"
    ])

    for c, s in ablation_stats.items():
        succ_str = f"{s['success']:.1f}%"
        time_str = f"${s['time_mean']:.2f} \\pm {s['time_std']:.2f}$"
        dead_str = f"${s['dead_mean']:.2f} \\pm {s['dead_std']:.2f}$"
        disc_str = f"${s['disc_mean']:.2f} \\pm {s['disc_std']:.2f}$"
        scr_str = f"${s['scr_mean']:.2f} \\pm {s['scr_std']:.2f}$"
        if "Full" in c:
            lines.append(f"| **{c}** | {s['omitted']} | $\\mathbf{{{succ_str}}}$ | $\\mathbf{{{s['time_mean']:.2f} \\pm {s['time_std']:.2f}}}$ | $\\mathbf{{{s['dead_mean']:.2f}}}$ | $\\mathbf{{{s['disc_mean']:.2f} \\pm {s['disc_std']:.2f}}}$ | $\\mathbf{{{s['scr_mean']:.2f}}}$ |")
        else:
            lines.append(f"| **{c}** | {s['omitted']} | {succ_str} | {time_str} | {dead_str} | {disc_str} | {scr_str} |")

    lines.extend([
        "",
        "---",
        "",
        "## 3. Decoupled Scalability Analysis",
        "",
        "### 3.1 Crowd Density Scalability (Fixed Fleet $N_{\\text{carts}} = 4$)",
        "",
        "| Pedestrian Crowd ($N_{\\text{humans}}$) | Success Rate (%) | Makespan (s) | Replan Latency (ms) | V2V Mesh Packets |",
        "| :---: | :---: | :---: | :---: | :---: |"
    ])
    for h, s in crowd_stats.items():
        lines.append(f"| {h} | {s['success']:.1f}% | ${s['time_mean']:.2f} \\pm {s['time_std']:.2f}$ | ${s['lat_mean']:.3f} \\pm {s['lat_std']:.3f}$ | ${s['pkts_mean']:.1f} \\pm {s['pkts_std']:.1f}$ |")

    lines.extend([
        "",
        "### 3.2 Fleet Size Scalability (Fixed Crowd $N_{\\text{humans}} = 10$)",
        "",
        "| Autonomous Fleet ($N_{\\text{carts}}$) | Success Rate (%) | Makespan (s) | Mutex Lock Queue Wait (s) | V2V Mesh Packets |",
        "| :---: | :---: | :---: | :---: | :---: |"
    ])
    for fl, s in fleet_stats.items():
        lines.append(f"| {fl} | {s['success']:.1f}% | ${s['time_mean']:.2f} \\pm {s['time_std']:.2f}$ | ${s['wait_mean']:.2f} \\pm {s['wait_std']:.2f}$ | ${s['pkts_mean']:.1f} \\pm {s['pkts_std']:.1f}$ |")

    with open(report_path, mode="w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\n-> Successfully written synchronized report to: {report_path}")

if __name__ == "__main__":
    run_full_statistical_verification()
