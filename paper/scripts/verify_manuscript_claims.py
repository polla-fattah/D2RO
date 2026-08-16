"""
Cross-checks numeric claims written into paper.tex prose against the single source
of truth, experiments/data/analysis_results.json.

Generated tables cannot drift, because they are produced from the JSON. Prose can,
and does: a number quoted in a paragraph survives a regeneration that changes it.
This closes that gap, and is intended to run in CI alongside the tests.

Exit status is non-zero if any claim disagrees, so it can gate a release build.
"""

from __future__ import annotations

import io
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON = os.path.join(BASE, "experiments", "data", "analysis_results.json")

d = json.load(io.open(JSON, encoding="utf-8"))
B = d["benchmark"]["groups"]
A = d["ablation"]["groups"]
X = d["cross_domain"]["groups"]
C = d["crowd_density"]["groups"]
F = d["fleet_size"]["groups"]
W = d["weight_sensitivity"]["groups"]
R = d["comm_robustness"]["groups"]
M = d["mesh_anticipation"]
L = d["corridor_lock"]

D2 = "D2RO (SW-DGO Proposed)"
MATCHED = "Static A* (matched controller)"
APF = "Reactive Avoidance (Potential Field)"

CHECKS = [
    # --- benchmark / matched controller -------------------------------------
    ("D2RO success",              99.0,   B[D2]["success_rate"], 1),
    ("D2RO makespan",             47.18,  B[D2]["makespan_successful"]["mean"], 2),
    ("D2RO makespan sd",          13.40,  B[D2]["makespan_successful"]["sd"], 2),
    ("matched A* makespan",       19.20,  B[MATCHED]["makespan_successful"]["mean"], 2),
    ("unmatched A* makespan",     18.00,  B["Static A*"]["makespan_successful"]["mean"], 2),
    ("matched A* exposure med",   128,    B[MATCHED]["intimate_exposure"]["median"], 0),
    ("unmatched A* exposure med", 128,    B["Static A*"]["intimate_exposure"]["median"], 0),
    ("D2RO exposure median",      0,      B[D2]["intimate_exposure"]["median"], 0),
    ("APF makespan",              34.54,  B[APF]["makespan_successful"]["mean"], 2),
    ("APF exposure median",       204,    B[APF]["intimate_exposure"]["median"], 0),
    # --- timing (the corrected quantities) ----------------------------------
    ("repair median ms",          0.005,  B[D2]["repair_median_ms"]["mean"], 3),
    ("repair p95 ms",             0.19,   B[D2]["repair_p95_ms"]["mean"], 2),
    ("controller step ms",        0.227,  B[D2]["step_compute_ms"]["mean"], 3),
    # --- ablation ------------------------------------------------------------
    ("ablation full makespan",    47.38,  A["Full D2RO Framework"]["makespan"]["mean"], 2),
    ("ablation no-mesh makespan", 38.23,  A["w/o V2V Mesh Telemetry"]["makespan"]["mean"], 2),
    ("ablation no-lock makespan", 37.86,  A["w/o Corridor Mutex Lock"]["makespan"]["mean"], 2),
    ("ablation no-prox success",  11.0,   A["w/o Human Gaussian Proxemics"]["success_rate"], 1),
    ("contacts full",             5.71,   A["Full D2RO Framework"]["shelf_contact_events"]["mean"], 2),
    ("contacts no-safety",        95.14,  A["w/o Trolley Kinetic Safety Bubble"]["shelf_contact_events"]["mean"], 2),
    ("contacts no-prox",          59.18,  A["w/o Human Gaussian Proxemics"]["shelf_contact_events"]["mean"], 2),
    ("ticks full",                193.05, A["Full D2RO Framework"]["shelf_contact_ticks"]["mean"], 2),
    ("ticks no-safety",           271.71, A["w/o Trolley Kinetic Safety Bubble"]["shelf_contact_ticks"]["mean"], 2),
    # Medians now carry the ablation argument in both the table and the prose, so
    # they are checked as first-class claims rather than left to the table alone.
    ("contacts full median",      3,      A["Full D2RO Framework"]["shelf_contact_events"]["median"], 0),
    ("contacts no-safety median", 93.5,   A["w/o Trolley Kinetic Safety Bubble"]["shelf_contact_events"]["median"], 1),
    ("contacts no-prox median",   56,     A["w/o Human Gaussian Proxemics"]["shelf_contact_events"]["median"], 0),
    ("ticks full median",         154,    round(A["Full D2RO Framework"]["shelf_contact_ticks"]["median"]), 0),
    ("ticks no-safety median",    244,    A["w/o Trolley Kinetic Safety Bubble"]["shelf_contact_ticks"]["median"], 0),
    ("discomfort no-prox median", 13.5,   A["w/o Human Gaussian Proxemics"]["discomfort"]["median"], 1),
    ("discomfort full median",    0,      A["Full D2RO Framework"]["discomfort"]["median"], 1),
    # --- cross-domain --------------------------------------------------------
    ("cross supermarket success", 99.0,   X["Retail Supermarket"]["success_rate"], 1),
    ("cross hospital success",    100.0,  X["Clinical Hospital"]["success_rate"], 1),
    ("cross airport success",     95.0,   X["Airport Terminal"]["success_rate"], 1),
    ("cross hospital replans",    351.9,  X["Clinical Hospital"]["replans"]["mean"], 1),
    ("cross airport replans",     989.4,  X["Airport Terminal"]["replans"]["mean"], 1),
    ("cross supermkt replans",    502.3,  X["Retail Supermarket"]["replans"]["mean"], 1),
    # --- scalability ---------------------------------------------------------
    ("crowd step ms @2",          0.093,  C["2"]["replan_latency_ms"]["mean"], 3),
    ("crowd step ms @30",         0.175,  C["30"]["replan_latency_ms"]["mean"], 3),
    ("crowd makespan @2",         30.10,  C["2"]["makespan"]["mean"], 2),
    ("crowd makespan @30",        56.30,  C["30"]["makespan"]["mean"], 2),
    ("fleet success @10",         85.0,   F["10"]["success_rate"], 1),
    ("fleet success @12",         78.0,   F["12"]["success_rate"], 1),
    ("fleet makespan @2",         50.99,  F["2"]["makespan"]["mean"], 2),
    ("fleet makespan @12",        110.17, F["12"]["makespan"]["mean"], 2),
    ("fleet packets @2",          8.50,   F["2"]["mesh_packets"]["mean"], 2),
    ("fleet packets @12",         1158.60, F["12"]["mesh_packets"]["mean"], 2),
    # --- weight sensitivity --------------------------------------------------
    ("w_D x0.5 makespan",         63.8,   W["w_Dx0.5"]["makespan"]["mean"], 1),
    ("w_D x1.5 makespan",         39.1,   W["w_Dx1.5"]["makespan"]["mean"], 1),
    ("w_H x0.5 makespan",         37.5,   W["w_Hx0.5"]["makespan"]["mean"], 1),
    ("w_H x1.5 makespan",         47.1,   W["w_Hx1.5"]["makespan"]["mean"], 1),
    # --- mechanism experiments ----------------------------------------------
    ("mechA lead ON",             10.70,  M["conditions"]["on"]["anticipation_lead_time_s"]["mean"], 2),
    ("mechA backtrack ON",        1.08,   M["conditions"]["on"]["backtrack_distance_m"]["mean"], 2),
    ("mechA backtrack OFF",       2.73,   M["conditions"]["off"]["backtrack_distance_m"]["mean"], 2),
    ("mechB success ON",          88.0,   L["conditions"]["on"]["success_rate"], 1),
    ("mechB success OFF",         36.0,   L["conditions"]["off"]["success_rate"], 1),
    ("mechB corridor ON",         40.01,  L["conditions"]["on"]["corridor_time_s"]["mean"], 2),
    ("mechB corridor OFF",        89.41,  L["conditions"]["off"]["corridor_time_s"]["mean"], 2),
    ("mechB headon ON",           1.08,   L["conditions"]["on"]["head_on_events"]["mean"], 2),
    ("mechB outside ON",          2.16,   L["conditions"]["on"]["nodes_outside_corridor"]["mean"], 2),
    ("mechB outside OFF",         0.00,   L["conditions"]["off"]["nodes_outside_corridor"]["mean"], 2),
    ("mechB replans ON",          25.18,  L["conditions"]["on"]["replans"]["mean"], 2),
    ("mechB replans OFF",         10.16,  L["conditions"]["off"]["replans"]["mean"], 2),
    ("mechB total wait ON",       0.030,  L["conditions"]["on"]["total_lock_wait_s"]["mean"], 3),
]


def main() -> int:
    bad = 0
    for label, claimed, actual, dp in CHECKS:
        if round(float(actual), dp) != round(float(claimed), dp):
            print(f"  MISMATCH  {label:28s} paper={claimed}  data={round(float(actual), dp)}")
            bad += 1
    print(f"{len(CHECKS) - bad}/{len(CHECKS)} prose claims match analysis_results.json")

    # derived statements made in the text
    # Two different gaps, easily confused. The manuscript quotes the gap to the
    # UNMATCHED shortest path (29.18 s) and then attributes 1.20 s of it to the
    # controller, leaving ~28 s to routing -- which is the gap to the MATCHED arm.
    gap_unmatched = (B[D2]["makespan_successful"]["mean"]
                     - B["Static A*"]["makespan_successful"]["mean"])
    gap = (B[D2]["makespan_successful"]["mean"]
           - B[MATCHED]["makespan_successful"]["mean"])
    ctrl = (B[MATCHED]["makespan_successful"]["mean"]
            - B["Static A*"]["makespan_successful"]["mean"])
    print(f"\n  derived: D2RO - unmatched gap    = {gap_unmatched:.2f} s   (paper: 29.18)")
    ratio = (A["w/o Trolley Kinetic Safety Bubble"]["shelf_contact_events"]["mean"]
             / A["Full D2RO Framework"]["shelf_contact_events"]["mean"])
    ratio_med = (A["w/o Trolley Kinetic Safety Bubble"]["shelf_contact_events"]["median"]
                 / A["Full D2RO Framework"]["shelf_contact_events"]["median"])
    succ = [g["success_rate"] for g in W.values()]
    print(f"  derived: D2RO - matched gap      = {gap:.2f} s   (paper: ~28, the routing share)")
    print(f"  derived: controller share        = {ctrl:.2f} s   (paper: 1.20)")
    print(f"  derived: contact-event ratio     = {ratio:.1f}x   (paper: 16.7, by mean)")
    print(f"  derived: contact-event ratio med = {ratio_med:.1f}x   (paper: ~31, by median)")
    print(f"  derived: sensitivity success rng = {min(succ):.0f}-{max(succ):.0f}%  (paper: 97-100)")
    rs = [g["success_rate"] for g in R.values()]
    mk = [g["makespan"]["mean"] for g in R.values()]
    print(f"  derived: comm success range      = {min(rs):.0f}-{max(rs):.0f}%   (paper: 100)")
    print(f"  derived: comm makespan range     = {min(mk):.1f}-{max(mk):.1f} s (paper: 43.6-47.2)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
