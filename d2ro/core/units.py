"""
Physical SI Units, Metric Calibration, and Timing Constants for the SW-DGO Framework.
Standardizes conversions between continuous metric coordinates and discrete pixel grid spaces.
"""

# Spatial calibration: 1 pixel = 0.03 meters (30 mm per pixel) -> 1 meter = 33.333 pixels
PX_TO_M: float = 0.03
M_TO_PX: float = 1.0 / PX_TO_M

# Time and clock frequencies:
# - Physics integration and algorithmic replanning execute at 20 Hz (dt = 0.05 s)
# - GUI rendering interpolates smoothly at 60 FPS (16.6 ms)
PHYSICS_DT: float = 0.05
PLANNING_FREQ_HZ: float = 1.0 / PHYSICS_DT  # 20.0 Hz
GUI_FPS: int = 60

# Physical Vehicle Dimensions (Int-Cart / Clinical Pushchair / Luggage Trolley)
# Chassis footprint: 0.48 m width x 0.72 m length (16 px x 24 px)
ROBOT_WIDTH_M: float = 0.48
ROBOT_LENGTH_M: float = 0.72
ROBOT_RADIUS_M: float = 0.40  # Inscribed safety radius (13.3 px)
ROBOT_RADIUS_PX: float = ROBOT_RADIUS_M * M_TO_PX

# Non-Holonomic Kinematic Limits
ROBOT_VMAX_MPS: float = 1.20   # Maximum linear velocity: 1.2 m/s (~40 px/s)
ROBOT_AMAX_MPS2: float = 1.50  # Maximum linear acceleration: 1.5 m/s^2
ROBOT_WMAX_RADPS: float = 2.50 # Maximum angular steering velocity: 2.5 rad/s

# Safety Clearance Margins
SHELF_CLEARANCE_MARGIN_M: float = 0.54  # 18 pixels margin from fixture corners
SHELF_CLEARANCE_MARGIN_PX: float = SHELF_CLEARANCE_MARGIN_M * M_TO_PX
FOLLOWING_DISTANCE_GAP_M: float = 1.08  # 36 pixels anti-tailgating gap
FOLLOWING_DISTANCE_GAP_PX: float = FOLLOWING_DISTANCE_GAP_M * M_TO_PX

# Wireless V2V Mesh Parameters
V2V_MESH_COMM_RANGE_M: float = 10.5  # 350 pixels ad-hoc transmission radius
V2V_MESH_COMM_RANGE_PX: float = V2V_MESH_COMM_RANGE_M * M_TO_PX
V2V_PACKET_SIZE_BYTES: int = 64      # Standard telemetry packet size (Timestamp, Edge, Cost, ID)
V2V_TTL_HOPS: int = 3                # Maximum multi-hop forwarding hops
V2V_DECAY_RATE_PER_SEC: float = 2.0  # Exponential decay rate lambda (s^-1)

# Asymmetric Anisotropic Human Proxemics Parameters (HA-VLN 2.0 / Hall's Proxemics)
HUMAN_RADIUS_M: float = 0.36         # Physical human body radius (12 px)
HUMAN_RADIUS_PX: float = HUMAN_RADIUS_M * M_TO_PX
PROXEMIC_SIGMA_FRONT_M: float = 1.35 # Front intimate personal space: 1.35 m (45 px)
PROXEMIC_SIGMA_FRONT_PX: float = PROXEMIC_SIGMA_FRONT_M * M_TO_PX
PROXEMIC_SIGMA_SIDE_M: float = 0.90  # Lateral intimate personal space: 0.90 m (30 px)
PROXEMIC_SIGMA_SIDE_PX: float = PROXEMIC_SIGMA_SIDE_M * M_TO_PX
PROXEMIC_SIGMA_REAR_M: float = 0.60  # Rear intimate personal space: 0.60 m (20 px)
PROXEMIC_SIGMA_REAR_PX: float = PROXEMIC_SIGMA_REAR_M * M_TO_PX
PROXEMIC_AMPLITUDE: float = 400.0    # Peak discomfort potential

# 5-Component SW-DGO Cost Function Weights (Dimensionally Normalized)
WEIGHT_DISTANCE_WD: float = 1.0   # Baseline physical kinematic distance weight
WEIGHT_MESH_WM: float = 1.5       # V2V collaborative mesh congestion weight
WEIGHT_PROXEMIC_WH: float = 2.0   # Human proxemic discomfort field weight
WEIGHT_MUTEX_LOCK_WR: float = 1.0 # Single-file corridor mutex reservation weight
WEIGHT_TROLLEY_WS: float = 1.2    # Kinetic chassis safety bubble weight
