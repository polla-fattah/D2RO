"""
Execution script to generate the full 2,700-trial simulation dataset with unified physics.
"""

import os
import sys
import time
import glob
from d2ro.sim.run_experiments import ExperimentRunner

def main():
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "experiments", "data")
    os.makedirs(data_dir, exist_ok=True)

    runner = ExperimentRunner(output_dir=data_dir)
    print("\nStarting full 2,700-trial simulation suite with unified physics...")
    t0 = time.time()
    runner.run_all(num_trials=100)
    print(f"\nCompleted all simulation trials in {time.time() - t0:.1f} seconds!")

if __name__ == "__main__":
    main()
