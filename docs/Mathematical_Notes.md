To code the **Socially-Weighted Distributed Graph Optimization (SW-DGO)** algorithm, you need to provide your coding assistant (like Antigravity) with a rigorous mathematical foundation. This translates the conceptual ideas—like "polite routing" and "mesh alerts"—into concrete numbers and matrices that a graph-search algorithm (like $D^*$ Lite or A*) can actually process.

Here is the complete mathematical foundation and the exact prompt you should give to your coding assistant.

---

### The Mathematical Foundation of SW-DGO

The environment is modeled as a directed graph $G = (V, E)$, where $V$ represents discrete physical locations (e.g., a $1\text{m} \times 1\text{m}$ grid cell in the supermarket) and $E$ represents the traversable edges between them.

The core of the SW-DGO algorithm is the **Dynamic Edge-Cost Function**. The cost $C(u, v, t)$ to traverse an edge from node $u$ to node $v$ at time $t$ is defined as:

$$C(u, v, t) = D(u, v) + W_{\text{mesh}}(u, v, t) + H_{\text{prox}}(v, t) + R_{\text{lock}}(u, v, t)$$

#### 1. Baseline Kinematic Cost: $D(u, v)$

This is the physical distance between node $u$ and node $v$. If the grid is a standard 4-connected grid, $D(u, v) = 1$. If diagonal movement is allowed, $D(u, v) = \sqrt{2}$. If there is a static, permanent wall (a shelf), $D(u, v) = \infty$.

#### 2. Mesh Network Congestion Penalty: $W_{\text{mesh}}(u, v, t)$

This represents temporary blockages (e.g., a spilled item or a crowded aisle) detected by other trolleys and broadcasted via the mesh network.

* Let $M(v, t)$ be the number of mesh alerts active at node $v$ at time $t$.
* Let $\gamma$ be the base penalty multiplier (e.g., $\gamma = 10$).

$$W_{\text{mesh}}(u, v, t) = \gamma \times M(v, t)$$



*(If a node is completely blocked, the broadcasting trolley sends an alert that sets $W_{\text{mesh}} = \infty$.)*

#### 3. Human Proxemic Penalty: $H_{\text{prox}}(v, t)$

This models the "personal space bubble" around a human detected by the trolley's local LiDAR/sensors. It is modeled as a 2D Gaussian distribution, meaning the cost is highest right next to the human and decays exponentially as the distance increases.
Let the human be located at node $h_i$ at time $t$.


$$H_{\text{prox}}(v, t) = \sum_{i} A \cdot \exp\left( -\frac{\vert{}\vert{}v - h_i\vert{}\vert{}^2}{2\sigma^2} \right)$$

* $\vert{}\vert{}v - h_i\vert{}\vert{}$: The Euclidean distance from the grid cell $v$ to the human $h_i$.
* $A$: The peak discomfort penalty (e.g., $A = 50$, making getting too close very expensive).
* $\sigma$: The standard deviation, representing the size of the human's "bubble" (e.g., $\sigma = 1.5$ meters).

#### 4. Directional Deadlock Penalty: $R_{\text{lock}}(u, v, t)$

Aisles are narrow corridors where two trolleys cannot pass each other. To prevent ORCA live-locks, trolleys broadcast a spatiotemporal reservation when they commit to entering an aisle.


$$R_{\text{lock}}(u, v, t) = \begin{cases} \infty, & \text{if edge } (u,v) \text{ is reserved by another trolley in the opposing direction at time } t \\ 0, & \text{otherwise} \end{cases}$$

---

### The Prompt for Your Coding Assistant

You can copy and paste the following block directly to your coding assistant (like Antigravity) to instruct it to build the core simulation logic.

---

**System Role:** You are a senior robotics software engineer. I need you to implement the core pathfinding logic for a novel multi-agent routing algorithm called Socially-Weighted Distributed Graph Optimization (SW-DGO).

**Context:** We are simulating autonomous supermarket trolleys. They navigate a 2D grid using a modified $D^*$ Lite (or $A^*$) algorithm. The environment is highly dynamic, featuring narrow aisles (which cause deadlocks), human shoppers (who require personal space), and temporary obstacles (which are communicated via a peer-to-peer mesh network).

**Task:** Write the Python (or C++) classes required to manage the grid map and compute the path using the SW-DGO custom cost function. I do not need the full $D^*$ Lite implementation right now; I need the environment representation and the specific `get_edge_cost(u, v, time)` function that the planner will call.

**Mathematical Requirements:**
Implement the cost function $C(u, v, t) = D(u, v) + W_{\text{mesh}}(u, v, t) + H_{\text{prox}}(v, t) + R_{\text{lock}}(u, v, t)$.

1. **Grid Setup:** Create a `SupermarketGrid` class. It should handle a 2D array where `0` is open space and `1` is a static shelf.
2. **$D(u, v)$ (Base Cost):** Movement to adjacent cells costs 1. Movement into a shelf costs infinity.
3. **$W_{\text{mesh}}$ (Mesh Penalty):** The class must have a method `receive_mesh_alert(node, penalty, duration)`. If a node has active alerts, add the penalty to the cost.
4. **$H_{\text{prox}}$ (Human Proxemics):** The class must have a method `update_human_positions(list_of_nodes)`. For any node $v$ being evaluated, calculate a Gaussian penalty based on its distance to all known humans: `cost += A * exp(-distance^2 / (2 * sigma^2))`. Use $A=50$ and $\sigma=1.5$.
5. **$R_{\text{lock}}$ (Deadlock Prevention):** The class needs a method `reserve_directed_edge(u, v, time_window)`. If an agent tries to calculate the cost from $x$ to $y$, and the edge $(y, x)$ is currently reserved by another agent, the cost of $(x, y)$ must evaluate to infinity.

**Output:** Provide clean, well-commented, object-oriented code for the `SupermarketGrid` class and the `get_edge_cost` method. Include a small `main` block demonstrating how placing a human inflates the costs of surrounding nodes.