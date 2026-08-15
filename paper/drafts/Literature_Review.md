# Literature Review: Foundations of the $\text{D}^2\text{RO}$ Framework

The automation of independent, communicating agents in dynamic, confined environments—such as supermarket trolleys navigating shifting obstacles and crowds—requires the convergence of several distinct robotic domains. The proposed **Distributed Dynamic Route Optimization ($\text{D}^2\text{RO}$)** framework builds upon foundational work in Multi-Agent Path Finding (MAPF), dynamic graph replanning, local collision avoidance, ad-hoc mesh communication, physical trolley mechatronics, and human-aware navigation. This section reviews the critical literature in these areas and identifies the structural gaps that $\text{D}^2\text{RO}$ addresses.

### 1. Decentralized and Lifelong Multi-Agent Path Finding (MAPF)

At the core of the autonomous trolley return problem is the continuous routing of multiple agents without collisions. Stern et al. (2019) define the classical MAPF problem and its variants, establishing the fundamental vertex and edge conflict models used in grid-based environments. To address continuous operations, Ma et al. (2017) introduced the concept of Lifelong Multi-Agent Path Finding for Online Pickup and Delivery (MAPD), where agents dynamically receive tasks (e.g., returning to a docking station) without resting.

To overcome the limitations of centralized servers—which suffer from single-point failure risks and communication latency—recent literature has shifted toward decentralized solvers. For example, Dergachev and Yakovlev (2024) explored decentralized unlabeled MAPF using target and priority swapping, while Keskin et al. (2024) presented a decentralized MAPF framework utilizing automated negotiation protocols. Furthermore, learning-based approaches have gained traction: Sartoretti et al. (2019) introduced PRIMAL, utilizing reinforcement and imitation learning for decentralized pathfinding, and Skrynnik et al. (2024) developed "Learn to Follow" to separate global heuristic sub-goal allocation from low-level local policies. Despite their high scalability, learning-based methods often struggle with out-of-distribution environments (e.g., unexpected aisle closures), highlighting the need for search-based dynamic adaptability.

### 2. Dynamic Replanning in Unknown and Stochastic Environments

In retail environments, the topological graph changes dynamically as aisles become blocked or crowded. Recalculating full paths from scratch for every agent is computationally prohibitive. Koenig and Likhachev (2002) addressed this with $D^*$ Lite, an incremental heuristic search algorithm that recalculates only the segments of a path affected by dynamic edge-cost changes.

The application of $D^*$ Lite to multi-agent systems was successfully demonstrated by Al-Mutib et al. (2012), who utilized it for real-time path planning by treating the paths of peer agents as temporary, time-based obstacles. Additionally, Wagner and Choset (2011) developed $M^*$, dynamically varying the dimensionality of the search space only when agent paths conflict. $\text{D}^2\text{RO}$ adapts these incremental principles, allowing trolleys to dynamically inflate the traversal costs (edge weights) of specific aisles based on real-time congestion data without recomputing the entire global map.

### 3. Kinematic Coordination and Local Collision Avoidance

While MAPF and $D^*$ Lite provide global waypoints, continuous kinematic control is required for safe micro-maneuvers when agents cross paths. Van den Berg et al. (2008) introduced Optimal Reciprocal Collision Avoidance (ORCA), a highly efficient framework providing sufficient conditions for multiple robots to avoid collisions in continuous space without explicit communication.

However, standard ORCA suffers from live-locks (deadlocks) in narrow, symmetric environments like supermarket aisles, where agents cannot physically pass one another. Dergachev and Yakovlev (2021) specifically address this in their work on distributed multi-agent navigation, proposing a system that uses continuous reciprocal collision avoidance but falls back on a locally confined MAPF instance when a deadlock is detected. $\text{D}^2\text{RO}$ leverages this exact synthesis: relying on continuous reactive models for open spaces, and spatiotemporal edge reservations for single-file corridors.

### 4. Multi-Robot Ad-Hoc Communication Protocols

The transition from centralized control to a truly distributed $\text{D}^2\text{RO}$ system requires robust peer-to-peer communication. Gielis et al. (2022) emphasize the critical need for co-designing robotic planning algorithms alongside network constraints, noting a literature gap in systems that holistically optimize both.

For decentralized data sharing, robots must rely on ad-hoc networks. Slyusar and Kulich (2016) evaluated routing protocols for Mobile Ad-Hoc Networks (MANETs) in multi-robot exploration. Additionally, Edwige (2024) investigated robot communication within Swarm SLAM, demonstrating how independent agents can successfully merge local spatial data over a distributed mesh. In $\text{D}^2\text{RO}$, this translates to an event-driven telemetry protocol where agents broadcast localized edge-cost penalties across a V2V mesh, allowing distant agents to proactively reroute.

### 5. Indoor Positioning and Physical Hardware Implementation

Unlike simulated grids, physical shopping trolleys require absolute spatial grounding and customized mechatronics. Zafari et al. (2019) provide a comprehensive survey of indoor localization technologies, highlighting the superiority of Ultra-Wideband (UWB) and BLE for centimeter-level accuracy in GPS-denied environments. Clark et al. (2021) expanded on this with the TEAM framework, demonstrating effective trilateration and mapping utilizing a localized robotic network, while Nugraha et al. (2024) proved that fusing Indoor Positioning Systems (IPS) with wheel odometry via Extended Kalman Filters (EKF) drastically reduces navigation drift.

Bringing these concepts into the physical retail space, Mohamad Azlan et al. (2024) developed the *Int-Cart*, an autonomous mobile trolley robot. Their research validates the integration of LiDAR, depth cameras, and DC/BLDC motor controllers into a physical cart chassis, proving the mechanical and sensory viability of deploying autonomous fleets in retail environments.

### 6. Human-Aware Navigation

A supermarket is vastly different from a structured warehouse because the primary obstacles—human shoppers—are unpredictable and require social compliance. Recent benchmark frameworks, such as HA-VLN 2.0 (HA-VLN Authors, 2024), emphasize that robots cannot treat humans simply as "moving cylindrical obstacles." Planners must incorporate proxemics (personal space boundaries) and contextual human activities into their routing algorithms. In the context of $\text{D}^2\text{RO}$, when a trolley encounters a crowded aisle, human-aware metrics dictate that it should not execute aggressive local maneuvers (like weaving through shoppers via ORCA). Instead, it must penalize the global mesh graph, increasing the aisle's congestion cost, and choose an alternative path to preserve human comfort.

### 7. Synthesis and Identification of the Research Gap

The reviewed literature reveals highly mature individual solutions: lifelong routing (Ma et al., 2017), incremental dynamic planning (Koenig & Likhachev, 2002), collision avoidance (Van den Berg et al., 2008), physical trolley mechatronics (Mohamad Azlan et al., 2024), and human-aware guidelines (HA-VLN Authors, 2024).

**The Research Gap:** There remains a distinct lack of hybrid frameworks that fuse **proactive, mesh-informed global graph updates** with **reactive human-aware collision avoidance** in highly constrained physical retail spaces. Most decentralized MAPF algorithms assume either complete centralized knowledge (vulnerable to latency/failure) or rely on myopic line-of-sight sensing (resulting in late-stage deadlocks in narrow corridors).

The $\text{D}^2\text{RO}$ framework bridges this gap. By combining $D^*$ Lite with an ad-hoc mesh communication layer and human-centric penalty weights, $\text{D}^2\text{RO}$ allows an *Int-Cart* experiencing local shopper congestion to broadcast edge-cost penalties globally. This enables other carts to independently and proactively recalculate optimal, socially compliant trajectories *before* encountering the bottleneck.

---

### References

Al-Mutib, K., AlSulaiman, M., Emaduddin, M., & Ramdane, H. (2012). D Lite based real-time multi-agent path planning in dynamic environments. *International Journal of Engineering Research and Applications*, 2(2), 1414-1419.

Clark, L., Andre, C., Galante, J., Krishnamachari, B., & Psounis, K. (2021). TEAM: Trilateration for exploration and mapping with robotic networks.

Dergachev, S., & Yakovlev, K. (2021). Distributed multi-agent navigation based on reciprocal collision avoidance and locally confined multi-agent path finding.

Dergachev, S., & Yakovlev, K. (2024). Decentralized unlabeled multi-agent pathfinding via target and priority swapping.

Edwige, L. (2024). *Robot communication in swarm SLAM (Simultaneous Localization and Mapping)*. [Master's thesis].

Gielis, J., Shankar, A., & Prorok, A. (2022). A critical review of communications in multi-robot systems. *Current Robotics Reports*, 3(4), 229-241.

HA-VLN Authors. (2024). *HA-VLN 2.0: An open benchmark and leaderboard for human-aware navigation in discrete and continuous environments with dynamic multi-human interaction*.

Keskin, M. O., Cantürk, F., Eran, C., & Aydoğan, R. (2024). Decentralized multi-agent path finding framework and strategies based on automated negotiation. *Autonomous Agents and Multi-Agent Systems*, 38(10).

Koenig, S., & Likhachev, M. (2002). Fast replanning for navigation in unknown terrain. *IEEE Transactions on Robotics and Automation*.

Ma, H., Li, J., Kumar, T. K. S., & Koenig, S. (2017). Lifelong multi-agent path finding for online pickup and delivery tasks.

Mohamad Azlan, A. F., Mohd Nasir, N. A., Nordin, N. A. I., Shaharuddin, M. D. I., Ariffin, R., Mat Lazim, N. H. I., & Zainul Ariffin, K. N. (2024). Autonomous mobile trolley robot: Int-Cart. *Semarak Proceedings of Applied Sciences and Engineering Technology*, 1(1), 1-9.

Nugraha, M. H., Rijanto, E., Abdul, F., & Saputra, R. P. (2024). Mobile robot localization via indoor positioning system and odometry fusion.

Sartoretti, G., Kerr, J., Shi, Y., Wagner, G., Kumar, T. K. S., Koenig, S., & Choset, H. (2019). PRIMAL: Pathfinding via reinforcement and imitation multi-agent learning. *IEEE Robotics and Automation Letters*.

Skrynnik, A., Andreychuk, A., Nesterova, M., Yakovlev, K., & Panov, A. (2024). Learn to follow: Decentralized lifelong multi-agent pathfinding via planning and learning. *Proceedings of the AAAI Conference on Artificial Intelligence*.

Slyusar, K., & Kulich, M. (2016). Framework for ad hoc network communication in multi-robot systems. *Acta Polytechnica CTU Proceedings*, 6, 18-27.

Stern, R., Sturtevant, N. R., Felner, A., Koenig, S., Ma, H., Walker, T. T., ... & Barták, R. (2019). Multi-agent pathfinding: Definitions, variants, and benchmarks. *Symposium on Combinatorial Search*, 10, 151–158.

Van den Berg, J., Lin, M., & Manocha, D. (2008). Reciprocal velocity obstacles for real-time multi-agent navigation. *Proceedings of the IEEE International Conference on Robotics and Automation (ICRA)*.

Wagner, G., & Choset, H. (2011). M*: A complete multirobot path planning algorithm with optimality bounds.

Zafari, F., Gkelias, A., & Leung, K. K. (2019). A survey of indoor localization systems and technologies. *IEEE Communications Surveys & Tutorials*, 21(3), 2568-2599.