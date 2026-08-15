# Manuscript Abstract & Index Terms

## Title
**Socially-Weighted Distributed Graph Optimization ($\text{D}^2\text{RO}$) for Autonomous Multi-Agent Service Fleets in Crowded Environments**

**Authors:** Polla Fattah, et al.  
**Affiliation:** Department of Computer Science & Robotics  

---

## 1. Standard Journal Abstract (Comprehensive 250-Word Format)

The continuous routing of autonomous service fleets—such as retail shopping carts (*Int-Cart*), clinical hospital pushchairs, and airport luggage trolleys—in crowded, human-shared public spaces poses fundamental multi-agent coordination challenges. Existing Multi-Agent Path Finding (MAPF) and reactive collision avoidance methods suffer from local potential minima traps in orthogonal $90^\circ$ shelf fixtures (Artificial Potential Fields: $0.0\%$ success), velocity obstacle constraint infeasibility in narrow single-file corridors (ORCA: $0.0\%$ success), delayed backtracking (Decentralized Local MAPF: $+21.8\%$ makespan penalty), and social discomfort violations (Static $A^*$: $11.2 \pm 2.1$ violations).

This paper introduces the **Distributed Dynamic Route Optimization ($\text{D}^2\text{RO}$)** framework powered by **Socially-Weighted Distributed Graph Optimization (SW-DGO)**. $\text{D}^2\text{RO}$ formalizes a dimensionally weighted 5-component edge traversal cost function:
$$C(u, v, t) = w_D D(u, v) + w_M W_{\text{mesh}}(u, v, t) + w_H H_{\text{prox}}(v, t) + w_R R_{\text{lock}}(u, v, t) + w_S S_{\text{trolley}}(v, t)$$
which seamlessly unifies incremental heuristic graph repair ($D^*$ Lite), event-driven Vehicle-to-Vehicle (V2V) ad-hoc mesh telemetry with exponential temporal decay, continuous 2D asymmetric anisotropic Gaussian human proxemics, spatiotemporal directional corridor mutex locks, and non-holonomic vehicle safety clearance envelopes ($S_{\text{trolley}}$).

Evaluated across $N = 100$ randomized Monte Carlo kinodynamic simulation trials in retail supermarket, clinical hospital (featuring Turnout Alcoves), and airport terminal concourses, $\text{D}^2\text{RO}$ achieves a **$100.0\%$ mission success rate** with **$0.00 \pm 0.00$ corridor deadlocks** and **$0.00 \pm 0.00$ intimate personal space violations** ($p < 0.001$), eliminating reactive shelf corner traps. Furthermore, incremental vertex repair latencies scale sub-linearly from **$0.045\text{ms}$ to $0.108\text{ms}$** across a $15\times$ scaling in pedestrian density (from 2 to 30 humans with fixed fleet $N_{\text{carts}}=4$), consuming $<2.4\text{ KB/s}$ wireless mesh bandwidth and validating deterministic real-time execution on low-cost embedded hardware.

---

## 2. Structured Abstract Format (For Journals Requiring Structured Summaries)

* **Context:** Autonomous mobile robot (AMR) fleets are transitioning from segregated industrial warehouses into unstructured, human-dense public spaces such as retail supermarkets, hospital wards, and airport terminals.
* **Objective:** Develop a fully decentralized, socially compliant, and provably deadlock-free dynamic routing framework capable of operating in fixture-dense and single-file corridor environments without centralized server bottlenecks.
* **Methods:** We formulate the SW-DGO 5-component cost function evaluated locally by Koenig and Likhachev's incremental $D^*$ Lite algorithm. Dynamic congestion events are broadcasted over an ad-hoc V2V mesh network ($\text{TTL} = 3, \lambda_{\text{decay}} = 2.0\text{ s}^{-1}$), human psychological personal space is modeled via continuous 2D asymmetric anisotropic Gaussian line-integrals, single-file bottlenecks are arbitrated via directional mutex locks ($R_{\text{lock}} = \infty$), and vehicle kinodynamics are bounded by non-holonomic turning and an $18\text{px}$ ($0.54\text{m}$) shelf clearance margin.
* **Results:** Across $N = 100$ randomized Monte Carlo kinodynamic simulation runs, $\text{D}^2\text{RO}$ eliminated the $0.0\%$ failure mode of reactive potential fields (APF and ORCA) and reduced intimate space violations from $46.25 \pm 3.19$ (in Static $A^*$) to $0.00 \pm 0.00$. Incremental replanning executed in under $0.16\text{ms}$ (95% CI [$0.152, 0.168$]), maintaining deterministic real-time control.
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
