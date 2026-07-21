"""
HEA plasticity classification predictor.

This module loads a trained ONNX classification model together with Min-Max
normalization parameters, reads descriptor parquet files produced by the
calc_descriptors pipeline, and writes prediction results to parquet files.

Typical workflow:
    1. Prepare descriptor parquet files, e.g. hea_6_c_*.parquet.
    2. Place model.onnx, minmax_params.pkl and feature_names.json under
       model_files/.
    3. Run main.py or call predict_one_system() in a loop.
"""

from __future__ import annotations

import gc
import json
import os
import pickle
from pathlib import Path
from typing import List

import numpy as np
import onnxruntime as ort
import pyarrow as pa
import pyarrow.parquet as pq
from numpy import ndarray


# ---------------------------------------------------------------------------
# Configuration (overridable via environment variables)
# ---------------------------------------------------------------------------
MODEL_PATH: str = os.getenv(
    "PLASTICITY_MODEL_PATH",
    str(Path(__file__).parent.parent / "model_files" / "model.onnx"),
)
MINMAX_PATH: str = os.getenv(
    "PLASTICITY_MINMAX_PATH",
    str(Path(__file__).parent.parent / "model_files" / "minmax_params.pkl"),
)
FEATURE_NAMES_PATH: str = os.getenv(
    "PLASTICITY_FEATURE_NAMES_PATH",
    str(Path(__file__).parent.parent / "model_files" / "feature_names.json"),
)

INPUT_DIR: str = os.getenv("PLASTICITY_INPUT_DIR", "/data/descriptors")
OUTPUT_DIR: str = os.getenv("PLASTICITY_OUTPUT_DIR", "/data/predictions")
INPUT_PATTERN: str = os.getenv("PLASTICITY_INPUT_PATTERN", "hea_6_c_{system_id}.parquet")
OUTPUT_PATTERN: str = os.getenv("PLASTICITY_OUTPUT_PATTERN", "pred_{system_id}.parquet")

BATCH_SIZE: int = int(os.getenv("PLASTICITY_BATCH_SIZE", "100000"))


# ---------------------------------------------------------------------------
# Load model artifacts once at import time
# ---------------------------------------------------------------------------
with open(FEATURE_NAMES_PATH, encoding="utf-8") as f:
    _feature_cfg: dict = json.load(f)
    FEATURE_NAMES: List[str] = _feature_cfg.get("descriptors", [])
    if not FEATURE_NAMES:
        raise ValueError("feature_names.json does not contain 'descriptors' list")

with open(MINMAX_PATH, "rb") as f:
    _minmax: dict = pickle.load(f)
    _min: ndarray = np.asarray(_minmax["Min"], dtype=np.float64)
    _max: ndarray = np.asarray(_minmax["Max"], dtype=np.float64)
    _max_min: ndarray = _max - _min
    # Avoid division by zero for constant features.
    _max_min = np.where(_max_min == 0, 1.0, _max_min)


def _normalize(descriptors: ndarray) -> ndarray:
    """Apply Min-Max normalization using the training-set parameters."""
    return (descriptors - _min) / _max_min


def _load_descriptors(system_id: int, feature_names: List[str]) -> ndarray:
    """Read selected descriptor columns from one system parquet file."""
    input_path = Path(INPUT_DIR) / INPUT_PATTERN.format(system_id=system_id)
    if not input_path.exists():
        raise FileNotFoundError(f"Descriptor file not found: {input_path}")

    table = pq.read_table(str(input_path), columns=feature_names)
    matrix = np.asarray(table.to_pandas().to_numpy(), dtype=np.float64)
    del table
    gc.collect()
    return matrix


def _load_con_index(system_id: int) -> ndarray:
    """Read the con_index column used to keep rows ordered."""
    input_path = Path(INPUT_DIR) / INPUT_PATTERN.format(system_id=system_id)
    table = pq.read_table(str(input_path), columns=["con_index"])
    return np.asarray(table.column("con_index").to_numpy(), dtype=np.int64)


class PlasticityPredictor:
    """Wrapper around the ONNX plasticity classification model."""

    def __init__(self, model_path: str | None = None) -> None:
        """
        Initialize an ONNX inference session.

        Parameters
        ----------
        model_path : str, optional
            Path to the ONNX model. Defaults to MODEL_PATH.
        """
        path = model_path or MODEL_PATH
        self._session = ort.InferenceSession(path)
        self._input_name = self._session.get_inputs()[0].name
        # Prefer a probability output with shape (N, 3) when available.
        self._output_name = self._select_probability_output()

    def _select_probability_output(self) -> str:
        """Return the name of the (N, 3) probability output node."""
        for output in self._session.get_outputs():
            shape = output.shape
            if len(shape) == 2 and shape[1] == 3:
                return output.name
        # Fall back to the first output if no probability node is found.
        return self._session.get_outputs()[0].name

    def predict(self, normalized_data: ndarray) -> ndarray:
        """
        Run inference on normalized descriptor data.

        Parameters
        ----------
        normalized_data : ndarray
            Array of shape (N, num_features) already Min-Max normalized.

        Returns
        -------
        ndarray
            Model predictions. For the default model this is a probability
            matrix of shape (N, 3).
        """
        results = self._session.run(
            [self._output_name],
            {self._input_name: normalized_data.astype(np.float32)},
        )
        return results[0]


def predict_one_system(
    system_id: int,
    predictor: PlasticityPredictor | None = None,
) -> Path:
    """
    Predict plasticity classes for one element system and write a parquet file.

    Parameters
    ----------
    system_id : int
        Index of the element system (matches hea_6_c_* file names).
    predictor : PlasticityPredictor, optional
        Reusable predictor instance. If None, a new one is created.

    Returns
    -------
    Path
        Path to the written prediction parquet file.
    """
    pred = predictor or PlasticityPredictor()

    # Read descriptors and normalize.
    descriptors = _load_descriptors(system_id, FEATURE_NAMES)
    normalized = _normalize(descriptors)
    del descriptors
    gc.collect()

    # Run inference in batches to keep peak memory low.
    predictions: List[ndarray] = []
    for start in range(0, normalized.shape[0], BATCH_SIZE):
        end = min(start + BATCH_SIZE, normalized.shape[0])
        batch = normalized[start:end]
        predictions.append(pred.predict(batch))
    all_predictions = np.concatenate(predictions, axis=0)
    del normalized, predictions
    gc.collect()

    # Read con_index and write results preserving row order.
    con_index = _load_con_index(system_id)
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / OUTPUT_PATTERN.format(system_id=system_id)

    result_table = pa.table({
        "con_index": con_index,
        "prediction": all_predictions,
    })
    pq.write_table(result_table, str(output_path))
    return output_path
