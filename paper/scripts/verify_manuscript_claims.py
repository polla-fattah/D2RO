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
Y = d["route_yield_factorial"]["groups"]
DG = d["mesh_degradation"].get("channels", d["mesh_degradation"].get("groups", {}))

D2 = "D2RO (SW-DGO Proposed)"
MATCHED = "Static A* (matched controller)"
LOCAL = "Local Social D* Lite"
APF = "Reactive Avoidance (Potential Field)"

# Timing claims are wall-clock measurements and therefore machine-dependent: the
# same deterministic simulation reports different microsecond figures on a loaded
# laptop and on a CI runner. Every other quantity here is a property of the seeded
# simulation and reproduces exactly.
#
# Checking timings for exact equality would make this gate fail on any machine other
# than the one the manuscript was last written on -- including CI, which is precisely
# where it most needs to pass. They are therefore checked against a tolerance band,
# wide enough to absorb hardware and load differences but narrow enough to catch a
# genuine regression such as a repair that has become milliseconds rather than
# microseconds. The manuscript already tells the reader to read these ordinally.
TIMING_TOLERANCE = 0.60      # +/-60% of the quoted value

TIMING_CHECKS = [
    ("repair median ms",   0.002,  lambda: B[D2]["repair_median_ms"]["mean"]),
    ("repair p95 ms",      0.10,   lambda: B[D2]["repair_p95_ms"]["mean"]),
    ("controller step ms", 0.118,  lambda: B[D2]["step_compute_ms"]["mean"]),
    ("crowd step ms @2",   0.093,  lambda: C["2"]["replan_latency_ms"]["mean"]),
    ("crowd step ms @30",  0.172,  lambda: C["30"]["replan_latency_ms"]["mean"]),
]

CHECKS = [
    # --- benchmark ------------------------------------------------------------
    ("D2RO success",              99.0,   B[D2]["success_rate"], 1),
    ("D2RO makespan",             47.18,  B[D2]["makespan_successful"]["mean"], 2),
    ("D2RO makespan sd",          13.40,  B[D2]["makespan_successful"]["sd"], 2),
    ("D2RO exposure person-s",    0.00,   B[D2]["exposure_person_s"]["median"], 2),
    ("local social success",     100.0,   B[LOCAL]["success_rate"], 1),
    ("local social makespan",     39.06,  B[LOCAL]["makespan_successful"]["mean"], 2),
    ("local social makespan sd",  15.12,  B[LOCAL]["makespan_successful"]["sd"], 2),
    ("local social exposure",      0.00,  B[LOCAL]["exposure_person_s"]["median"], 2),
    ("matched A* makespan",       19.20,  B[MATCHED]["makespan_successful"]["mean"], 2),
    ("unmatched A* makespan",     18.00,  B["Static A*"]["makespan_successful"]["mean"], 2),
    ("matched A* exposure",        6.40,  B[MATCHED]["exposure_person_s"]["median"], 2),
    ("APF exposure",              10.18,  B[APF]["exposure_person_s"]["median"], 2),
    ("APF makespan",              34.54,  B[APF]["makespan_successful"]["mean"], 2),
    # --- timing ---------------------------------------------------------------
    # --- factorial (the attribution experiment) -------------------------------
    ("factorial A makespan",      19.20,  (Y.get("A_prox_off_yield_off") or Y.get("A_frozen_noyield"))["makespan"]["mean"], 2),
    ("factorial A exposure",       6.45,  (Y.get("A_prox_off_yield_off") or Y.get("A_frozen_noyield"))["exposure_person_s"]["median"], 2),
    ("factorial B exposure",      48.00,  (Y.get("B_prox_off_yield_on") or Y.get("B_frozen_yield"))["exposure_person_s"]["median"], 2),
    ("factorial C exposure",       0.00,  (Y.get("C_prox_on_yield_off") or Y.get("C_social_noyield"))["exposure_person_s"]["median"], 2),
    ("factorial D exposure",       0.00,  (Y.get("D_prox_on_yield_on") or Y.get("D_social_yield"))["exposure_person_s"]["median"], 2),
    # --- ablation with the safety split ---------------------------------------
    ("ablation full contacts",       3,   A["Full D2RO Framework"]["shelf_contact_events"]["median"], 0),
    ("ablation cost-only contacts",  5,   A["w/o S_trolley cost only"]["shelf_contact_events"]["median"], 0),
    ("ablation ctl-only contacts",  48,   A["w/o safety controller only"]["shelf_contact_events"]["median"], 0),
    ("ablation fullstack contacts", 93.5, A["w/o safety (full stack)"]["shelf_contact_events"]["median"], 1),
    ("ablation no-prox success",  11.0,   A["w/o Human Gaussian Proxemics"]["success_rate"], 1),
    ("ablation no-mesh makespan", 38.23,  A["w/o V2V Mesh Telemetry"]["makespan"]["mean"], 2),
    # --- cross-domain ----------------------------------------------------------
    ("cross supermarket success", 99.0,   X["Retail Supermarket"]["success_rate"], 1),
    ("cross hospital success",   100.0,   X["Clinical Hospital"]["success_rate"], 1),
    ("cross airport success",     95.0,   X["Airport Terminal"]["success_rate"], 1),
    # --- scalability ------------------------------------------------------------
    ("fleet success @12",         78.0,   F["12"]["success_rate"], 1),
    # --- sensitivity (post heuristic fix) --------------------------------------
    ("w_H x0.5 makespan",         37.5,   W["w_Hx0.5"]["makespan"]["mean"], 1),
    ("w_H x1.5 makespan",         47.1,   W["w_Hx1.5"]["makespan"]["mean"], 1),
    ("w_D x0.5 makespan",         52.7,   W["w_Dx0.5"]["makespan"]["mean"], 1),
    ("w_D x1.5 makespan",         40.7,   W["w_Dx1.5"]["makespan"]["mean"], 1),
    # --- mechanisms -------------------------------------------------------------
    ("mechA lead ON",             10.70,  M["conditions"]["on"]["anticipation_lead_time_s"]["mean"], 2),
    ("mechB success ON",          88.0,   L["conditions"]["on"]["success_rate"], 1),
    ("mechB success OFF",         36.0,   L["conditions"]["off"]["success_rate"], 1),
    ("mechB outside ON",           2.16,  L["conditions"]["on"]["nodes_outside_corridor"]["mean"], 2),
]


def main() -> int:
    bad = 0
    for label, claimed, actual, dp in CHECKS:
        if round(float(actual), dp) != round(float(claimed), dp):
            print(f"  MISMATCH  {label:28s} paper={claimed}  data={round(float(actual), dp)}")
            bad += 1
    print(f"{len(CHECKS) - bad}/{len(CHECKS)} exact claims match analysis_results.json")

    print("\n  timing claims (machine-dependent, checked within "
          f"+/-{TIMING_TOLERANCE:.0%}):")
    for label, claimed, getter in TIMING_CHECKS:
        actual = float(getter())
        lo, hi = claimed * (1 - TIMING_TOLERANCE), claimed * (1 + TIMING_TOLERANCE)
        ok = lo <= actual <= hi
        if not ok:
            bad += 1
        mark = "ok " if ok else "OUT"
        print(f"    [{mark}] {label:20s} paper={claimed:.3f}  data={actual:.3f} "
              f"  band=[{lo:.3f}, {hi:.3f}]")

    # derived statements made in the text
    gap_unmatched = (B[D2]["makespan_successful"]["mean"]
                     - B["Static A*"]["makespan_successful"]["mean"])
    ctrl = (B[MATCHED]["makespan_successful"]["mean"]
            - B["Static A*"]["makespan_successful"]["mean"])
    cell_C = Y.get("C_prox_on_yield_off") or Y.get("C_social_noyield")
    cell_A = Y.get("A_prox_off_yield_off") or Y.get("A_frozen_noyield")
    routing = (cell_C["makespan"]["mean"] - cell_A["makespan"]["mean"])
    ls_delta = (B[D2]["makespan_successful"]["mean"]
                - B[LOCAL]["makespan_successful"]["mean"])
    succ = [g["success_rate"] for g in W.values()]
    print(f"\n  derived: D2RO - unmatched gap    = {gap_unmatched:.2f} s   (paper: 29.18)")
    print(f"  derived: controller share        = {ctrl:.2f} s   (paper: 1.20)")
    print(f"  derived: routing cost (factorial)= {routing:.2f} s   (paper: 29.94)")
    print(f"  derived: D2RO minus local social = {ls_delta:.2f} s   (paper: ~8)")
    print(f"  derived: sensitivity success rng = {min(succ):.0f}-{max(succ):.0f}%  (paper: 97-100)")
    on_clean = DG.get("loss00_lat000ms", {}).get("on_lead_time", {}).get("mean") or DG.get("loss00_lat000ms", {}).get("lead_time_s", {}).get("mean")
    on_bad = DG.get("loss20_lat200ms", {}).get("on_lead_time", {}).get("mean") or DG.get("loss20_lat200ms", {}).get("lead_time_s", {}).get("mean")
    if on_clean and on_bad:
        print(f"  derived: pooled lead clean/20%   = {on_clean:.2f} / {on_bad:.2f} s "
              f"(prose quotes the mesh-ON arm only)")

    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
