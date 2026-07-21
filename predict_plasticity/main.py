"""
Entry point for batch plasticity classification.

Predicts plasticity classes for a range of element systems and writes one
parquet file per system under the configured output directory.
"""

import os

from predict_plasticity.predictor import PlasticityPredictor, predict_one_system


def main() -> None:
    """Run predictions for all systems in the requested range."""
    start = int(os.getenv("PLASTICITY_START", "1"))
    end = int(os.getenv("PLASTICITY_END", "5005"))

    predictor = PlasticityPredictor()
    for system_id in range(start, end + 1):
        output_path = predict_one_system(system_id, predictor=predictor)
        print(f"System {system_id:04d}: {output_path}")


if __name__ == "__main__":
    main()
