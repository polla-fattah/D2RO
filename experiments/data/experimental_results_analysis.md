# Master Genuine Simulation Benchmark & Statistical Report

## 1. Benchmark Comparison (N=100 Genuine Trials per Algorithm)

| Algorithm | Success Rate | Makespan (s) [Mean ± SD] | [95% CI] | Personal Space Violations | Welch's p-value |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **D2RO (SW-DGO Proposed)** | 0.0% | 35.00 ± 0.00 | [35.00, 35.00] | 3.77 ± 28.30 | Baseline (N/A) |
| **Static A*** | 100.0% | 18.00 ± 0.00 | [18.00, 18.00] | 96.89 ± 10.88 | p = 1.000 |
| **Reactive Avoidance (Potential Field)** | 0.0% | 35.00 ± 0.00 | [35.00, 35.00] | 230.17 ± 74.44 | p = 1.000 |
| **Reactive ORCA (Velocity Obstacles)** | 0.0% | 35.00 ± 0.00 | [35.00, 35.00] | 25.08 ± 65.79 | p = 1.000 |
| **Decentralized Local MAPF** | 0.0% | 35.00 ± 0.00 | [35.00, 35.00] | 102.43 ± 16.38 | p = 1.000 |

## 2. Component Ablation Analysis (N=100 Genuine Trials per Configuration)

| Configuration | Omitted Component | Success Rate | Makespan (s) | Discomfort Integral | Shelf Scrapes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Full D2RO Framework** | - | 1.0% | 34.95 ± 0.54 | 0.77 ± 2.66 | 375.58 ± 169.37 |
| **w/o V2V Mesh Telemetry** | - | 51.0% | 31.04 ± 4.13 | 0.62 ± 2.49 | 305.56 ± 178.99 |
| **w/o Corridor Mutex Lock** | - | 51.0% | 31.04 ± 4.13 | 0.62 ± 2.49 | 305.56 ± 178.99 |
| **w/o Human Gaussian Proxemics** | - | 0.0% | 35.00 ± 0.00 | 82.75 ± 23.31 | 120.86 ± 22.22 |
| **w/o Trolley Kinetic Safety Bubble** | - | 64.0% | 33.25 ± 1.54 | 0.87 ± 6.60 | 406.48 ± 202.41 |

## 3. Cross-Domain Generalization (N=100 Genuine Trials per Domain)

| Environment Domain | Success Rate | Makespan (s) | Mean Transit Time (s) | V2V Packets | Replans |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Retail Supermarket** | 84.0% | 41.25 ± 7.86 | 26.38 ± 4.89 | 14.9 ± 2.6 | 384.9 ± 105.0 |
| **Clinical Hospital** | 70.0% | 42.16 ± 9.79 | 31.50 ± 4.56 | 3.2 ± 1.1 | 265.1 ± 75.1 |
| **Airport Terminal** | 0.0% | 55.05 ± 0.00 | 36.70 ± 0.00 | 2.0 ± 0.0 | 886.0 ± 0.0 |
