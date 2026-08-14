# Option 1: Algorithm Design & Pseudocode Specification
## Socially-Weighted Distributed Graph Optimization (SW-DGO / $\text{D}^2\text{RO}$)

This document formalizes the step-by-step algorithmic logic, data structures, message protocols, and pseudocode for the $\text{D}^2\text{RO}$ autonomous trolley framework.

---

## 1. System Architecture & Data Structures

### 1.1 World & Graph Representation
* **Topological Graph:** $G = (V, E)$, where:
  * $V$: Set of waypoint nodes located at aisle junctions, shelf corners, and docking bays.
  * $E \subseteq V \times V$: Set of directed corridor segments connecting adjacent waypoints.
* **Edge Attributes for $e = (u, v) \in E$:**
  * $d(u, v)$: Baseline physical Euclidean distance / transit time.
  * $w_{\text{mesh}}(u, v)$: Dynamic congestion penalty received from peer broadcasts (default 0, decays over time).
  * $h_{\text{prox}}(v)$: Social proxemic penalty based on real-time human detection.
  * $r_{\text{lock}}(u, v)$: Directional reservation penalty ($0$ if clear/granted, $\infty$ if locked in opposing direction $(v, u)$ by another trolley).
  * $c(u, v) = d(u, v) + w_{\text{mesh}}(u, v) + h_{\text{prox}}(v) + r_{\text{lock}}(u, v)$.

### 1.2 Agent Internal State
Each autonomous trolley $i \in \{1, \dots, N\}$ maintains:
* **Current Pose:** $p_i = (x_i, y_i, \theta_i)$ and velocity $v_i$.
* **Current Node & Goal Node:** $s_{\text{start}} \in V$, $s_{\text{goal}} \in V$.
* **$D^*$ Lite Search Structures:**
  * $g(s)$: Estimate of shortest distance from $s$ to $s_{\text{goal}}$.
  * $rhs(s)$: One-step lookahead cost based on successor $g$-values:
    $$rhs(s) = \begin{cases} 0 & \text{if } s = s_{\text{goal}} \\ \min_{s' \in Succ(s)} (c(s, s') + g(s')) & \text{otherwise} \end{cases}$$
  * Priority Queue $U$: Contains inconsistent nodes ($g(s) \neq rhs(s)$) keyed by $k(s) = [k_1(s), k_2(s)]$ where:
    $$k_1(s) = \min(g(s), rhs(s)) + h(s_{\text{start}}, s) + k_m, \quad k_2(s) = \min(g(s), rhs(s))$$
  * $k_m$: Accumulator for heuristic adjustments during agent movement.
* **Corridor Lock Table:** Active leases on single-file aisle edges with lease expiration timestamps.
* **Mesh Message Inbound/Outbound Queues.**

### 1.3 V2V Mesh Packet Schema
```
struct MeshPacket {
    enum Type { CONGESTION_ALERT, LOCK_REQUEST, LOCK_GRANT, LOCK_RELEASE }
    int sender_id;
    int seq_num;
    EdgeID edge;
    float cost_penalty;     // Used in CONGESTION_ALERT
    int priority;           // Used in LOCK_REQUEST (e.g. distance to exit / timestamp)
    int ttl;                // Hop count limit (e.g. max 3 hops)
    timestamp created_at;
}
```

---

## 2. Formal Pseudocode Algorithms

### Algorithm 1: Main $\text{D}^2\text{RO}$ Agent Control Loop
Each trolley executes this loop asynchronously at a fixed control frequency (e.g., 20 Hz).

```text
Algorithm D2RO_AgentLoop(agent_id, s_goal)
Input: agent_id, goal waypoint s_goal
Output: Autonomous, socially-compliant transit to s_goal

1:  s_start ← GetNearestNode(current_pose)
2:  s_last ← s_start
3:  km ← 0
4:  InitializeDStarLite(s_goal)
5:  ComputeShortestPath()
6:
7:  while s_start ≠ s_goal do
8:      // --- Step 1: Process Inbound V2V Mesh Messages ---
9:      changed_edges ← ProcessIncomingMeshPackets()
10:
11:     // --- Step 2: Local Perception & Human Proxemics ---
12:     detected_humans ← ScanLocalSensors(LiDAR, DepthCamera)
13:     for each edge e in LocalVisionRange() do
14:         h_new ← ComputeGaussianProxemicCost(e.target_node, detected_humans)
15:         if |h_new - e.h_prox| > ε_human then
16:             e.h_prox ← h_new
17:             changed_edges.Add(e)
18:         end if
19:     end for
20:
21:     // --- Step 3: Incremental Graph Replanning (if edge costs changed) ---
22:     if changed_edges is not empty then
23:         km ← km + Heuristic(s_last, s_start)
24:         s_last ← s_start
25:         for each (u, v) in changed_edges do
26:             UpdateEdgeCostAndInconsistency(u, v)
27:         end for
28:         ComputeShortestPath()
29:     end if
30:
31:     // --- Step 4: Next Waypoint & Corridor Lock Acquisition ---
32:     s_next ← GetNextWaypointOnShortestPath(s_start)
33:     if IsSingleFileCorridor(s_start, s_next) and not HasLock(s_start, s_next) then
34:         lock_acquired ← RequestCorridorLock(s_start, s_next)
35:         if not lock_acquired then
36:             // Temporarily mark edge blocked to force alternate route or wait
37:             r_lock(s_start, s_next) ← ∞
38:             UpdateEdgeCostAndInconsistency(s_start, s_next)
39:             ComputeShortestPath()
40:             continue
41:         end if
42:     end if
43:
44:     // --- Step 5: Kinematic Execution & Anomaly Detection ---
45:     ExecuteKinematicMoveTowards(s_next)
46:     if LocalBlockageDetected(s_start, s_next) then
47:         BroadcastMeshCongestion(edge=(s_start, s_next), penalty=PENALTY_BLOCK)
48:     end if
49:
50:     // Advance start node if reached waypoint
51:     if ReachedWaypoint(s_next) then
52:         if HasLock(s_start, s_next) then
53:             ReleaseCorridorLock(s_start, s_next)
54:         end if
55:         s_start ← s_next
56:     end if
57: end while
58: Return SUCCESS_DOCKING
```

---

### Algorithm 2: Incremental Edge Cost Update & $D^*$ Lite Integration

```text
Algorithm UpdateEdgeCostAndInconsistency(u, v)
Input: Directed edge (u, v) whose cost c(u, v) has changed

1:  c_old ← c(u, v)
2:  c(u, v) ← d(u, v) + w_mesh(u, v) + h_prox(v) + r_lock(u, v)
3:
4:  if u ≠ s_goal then
5:      rhs(u) ← min_{s' ∈ Succ(u)} (c(u, s') + g(s'))
6:  end if
7:  UpdateVertex(u)
```

```text
Algorithm UpdateVertex(u)
1:  if g(u) ≠ rhs(u) and u ∈ U then
2:      U.Update(u, CalculateKey(u))
3:  else if g(u) ≠ rhs(u) and u ∉ U then
4:      U.Insert(u, CalculateKey(u))
5:  else if g(u) = rhs(u) and u ∈ U then
6:      U.Remove(u)
7:  end if
```

```text
Algorithm ComputeShortestPath()
1:  while (U.TopKey() < CalculateKey(s_start)) or (rhs(s_start) ≠ g(s_start)) do
2:      k_old ← U.TopKey()
3:      u ← U.Pop()
4:      if k_old < CalculateKey(u) then
5:          U.Insert(u, CalculateKey(u))
6:      else if g(u) > rhs(u) then
7:          g(u) ← rhs(u)
8:          for each s in Pred(u) do
9:              if s ≠ s_goal then rhs(s) ← min(rhs(s), c(s, u) + g(u))
10:             UpdateVertex(s)
11:         end for
12:     else
13:         g(u) ← ∞
14:         for each s in Pred(u) ∪ {u} do
15:             if s ≠ s_goal then rhs(s) ← min_{s' ∈ Succ(s)} (c(s, s') + g(s'))
16:             UpdateVertex(s)
17:         end for
18:     end if
19: end while
```

---

### Algorithm 3: Corridor Deadlock Prevention & Mutex Lock Protocol

```text
Algorithm RequestCorridorLock(u, v)
Input: Directed corridor edge (u, v)
Output: Boolean (True if lock granted, False if conflict)

1:  // Check if opposing edge (v, u) is already locked by another trolley
2:  if LockTable.IsLocked(v, u) then
3:      return FALSE
4:  end if
5:
6:  // Broadcast request to mesh neighbors within 2 hops
7:  req_packet ← MeshPacket(Type=LOCK_REQUEST, edge=(u, v), priority=GetAgentPriority())
8:  BroadcastMesh(req_packet)
9:
10: // Wait for short contention window (e.g. 50ms)
11: conflicts ← CollectConflictingLockRequests(u, v, timeout=50ms)
12: if conflicts is empty then
13:     LockTable.SetLock(u, v, owner=agent_id, ttl=ESTIMATED_TRANSIT_TIME)
14:     return TRUE
15: else
16:     winner ← ResolvePriorityTieBreaker(agent_id, conflicts)
17:     if winner = agent_id then
18:         LockTable.SetLock(u, v, owner=agent_id, ttl=ESTIMATED_TRANSIT_TIME)
19:         return TRUE
20:     else
21:         return FALSE
22:     end if
23: end if
```

---

### Algorithm 4: Event-Driven Mesh Broadcast & Decay

```text
Algorithm ProcessIncomingMeshPackets()
Output: List of modified edges requiring graph recalculation

1:  changed_edges ← []
2:  while InboundMeshQueue is not empty do
3:      packet ← InboundMeshQueue.Dequeue()
4:      if packet.Type = CONGESTION_ALERT then
5:          edge ← packet.edge
6:          if packet.cost_penalty > edge.w_mesh then
7:              edge.w_mesh ← packet.cost_penalty
8:              changed_edges.Add(edge)
9:              // Re-broadcast if TTL remaining and within spatial propagation radius
10:             if packet.ttl > 1 then
11:                 packet.ttl ← packet.ttl - 1
12:                 OutboundMeshQueue.Enqueue(packet)
13:             end if
14:         end if
15:     else if packet.Type = LOCK_REQUEST or packet.Type = LOCK_RELEASE then
16:         LockTable.UpdateFromPacket(packet)
17:     end if
18: end while
19:
20: // Temporal Decay of Mesh Penalties
21: for each edge in Graph.AllEdges() do
22:     if edge.w_mesh > 0 then
23:         edge.w_mesh ← max(0, edge.w_mesh - DECAY_RATE * Δt)
24:         if edge.w_mesh decreased significantly then
25:             changed_edges.Add(edge)
26:         end if
27:     end if
28: end for
29:
30: return changed_edges
```

---

## 3. Plan for Implementation Steps in the New Simulator

1. **Step 1:** Implement the **Topological Supermarket Grid Graph** data structure ($V, E, c(u, v)$).
2. **Step 2:** Implement the **$D^*$ Lite Incremental Search Engine** (priority queue, key recalculation, dynamic start adjustment).
3. **Step 3:** Implement the **V2V Mesh Network Broker** (event-driven broadcast, TTL propagation, temporal penalty decay).
4. **Step 4:** Implement the **Human Dynamic Agent & 2D Gaussian Proxemic Bubble Generator**.
5. **Step 5:** Implement the **Corridor Lock / Mutex Protocol** to eliminate aisle live-locks.
6. **Step 6:** Build the **Benchmark Harness** comparing $\text{D}^2\text{RO}$ against baseline static $A^*$ and reactive ORCA.
