# Manuscript Abstract & Index Terms

## Title
**Socially-Weighted Distributed Graph Optimization ($\text{D}^2\text{RO}$) for Autonomous Multi-Agent Service Fleets in Crowded Environments**

**Authors:** Polla Fattah, et al.  
**Affiliation:** Department of Computer Science & Robotics  

---

## 1. Standard Journal Abstract (Comprehensive 250-Word Format)

The continuous routing of autonomous service fleets—such as retail shopping trolleys (*Int-Cart*), clinical hospital pushchairs, and airport luggage carts—in crowded, human-shared public spaces poses fundamental multi-agent coordination challenges. Existing Multi-Agent Path Finding (MAPF) and reactive collision avoidance methods (e.g., ORCA, Artificial Potential Fields) suffer from local potential minima traps in orthogonal $90^\circ$ shelf fixtures ($0.0\%$ success rate), symmetrical live-locks in narrow single-file corridors, and social discomfort violations. 

This paper introduces the **Distributed Dynamic Route Optimization ($\text{D}^2\text{RO}$)** framework powered by **Socially-Weighted Distributed Graph Optimization (SW-DGO)**. $\text{D}^2\text{RO}$ formalizes a dynamic 5-component edge traversal cost function:
$$C(u, v, t) = D(u, v) + W_{\text{mesh}}(u, v, t) + H_{\text{prox}}(v, t) + R_{\text{lock}}(u, v, t) + S_{\text{trolley}}(v, t)$$
which seamlessly unifies incremental heuristic graph repair ($D^*$ Lite), event-driven Vehicle-to-Vehicle (V2V) ad-hoc mesh telemetry with exponential temporal decay, continuous 2D Gaussian human proxemics, spatiotemporal directional corridor mutex locks, and non-holonomic vehicle safety clearance envelopes ($S_{\text{trolley}}$).

Evaluated across 20 randomized Monte Carlo physical trials in retail supermarket, clinical hospital (featuring Turnout Alcoves), and airport terminal concourses, $\text{D}^2\text{RO}$ achieves a **$100.0\%$ mission success rate** with **$0.0$ corridor deadlocks** and **$0.0$ intimate personal space violations**, eliminating $100\%$ of reactive shelf corner traps. Furthermore, incremental vertex repair latencies scale sub-linearly from **$0.04\text{ms}$ to $0.11\text{ms}$** across a $12\times$ scaling in pedestrian density, consuming $<2.5\text{ KB/s}$ wireless mesh bandwidth and validating deterministic 60 FPS real-time execution on low-cost embedded hardware (Raspberry Pi 5 / Jetson Orin Nano).

---

## 2. Structured Abstract Format (For Journals Requiring Structured Summaries)

* **Context:** Autonomous mobile robot (AMR) fleets are transitioning from segregated industrial warehouses into unstructured, human-dense public spaces such as retail supermarkets, hospital wards, and airport terminals.
* **Objective:** Develop a fully decentralized, socially compliant, and provably deadlock-free dynamic routing framework capable of operating in fixture-dense and single-file corridor environments without centralized server bottlenecks.
* **Methods:** We formulate the SW-DGO 5-component cost function evaluated locally by Koenig and Likhachev's incremental $D^*$ Lite algorithm. Dynamic congestion events are broadcasted over an ad-hoc V2V mesh network ($\text{TTL} = 3, \lambda_{\text{decay}} = 2.0\text{ s}^{-1}$), human psychological personal space is modeled via continuous 2D Gaussian line-integrals, single-file bottlenecks are arbitrated via directional mutex locks ($R_{\text{lock}} = \infty$), and vehicle kinodynamics are bounded by non-holonomic turning and an $18\text{px}$ shelf clearance margin.
* **Results:** Across 20 randomized Monte Carlo physical simulation runs, $\text{D}^2\text{RO}$ eliminated the $0.0\%$ failure mode of reactive potential fields (ORCA) and reduced intimate space violations from $46.25 \pm 3.19$ (in Static $A^*$) to $0.00 \pm 0.00$. Incremental replanning executed in under $0.16\text{ms}$, maintaining full 60 FPS deterministic control.
* **Significance & Practical Impact:** Bridges the gap between discrete topological graph planning, continuous kinodynamic micro-steering, and human-aware proxemics, providing a lightweight, certifiably safe navigation stack for physical service fleet deployment.

---

## 3. Keywords & IEEE Index Terms

**Primary Keywords:**
* Multi-Agent Path Finding (MAPF)
* Socially-Aware Robot Navigation
* Distributed Dynamic Route Optimization ($\text{D}^2\text{RO}$)
* Incremental Graph Search ($D^*$ Lite)
* Human Proxemics & Personal Space Discomfort
* Vehicle-to-Vehicle (V2V) Ad-Hoc Mesh Telemetry
* Directional Corridor Mutex Locks
* Non-Holonomic Service Fleet Coordination

**IEEE / ACM Classification Codes:**
* **Robotics and Automation:** Multi-Robot Systems, Motion and Path Planning, Autonomous Vehicle Navigation.
* **Computing Methodologies:** Distributed Artificial Intelligence, Heuristic Search, Multi-Agent Systems.
* **Human-Centered Computing:** Human-Robot Interaction (HRI), Socially Compliant Navigation.
