#!/usr/bin/env python3
"""
Minimal HEA descriptor worker.

Reads composition tasks from a Redis input queue, computes descriptors using
the calc_descriptors code in this repository, and pushes results to a Redis
output queue.

Run one or more workers in parallel to accelerate computation.
"""

import json
import os
import sys
import time

import redis

# The original calc_py scripts assume they are run directly from their own
# directory and use bare imports such as `from models import ...`. We add
# calc_descriptors/calc_py to sys.path and temporarily change the working
# directory so those imports and relative file reads (e.g. params.json) work
# unchanged.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
CALC_PY_DIR = os.path.join(REPO_ROOT, "calc_descriptors", "calc_py")
sys.path.insert(0, CALC_PY_DIR)

_original_cwd = os.getcwd()
os.chdir(CALC_PY_DIR)
try:
    from main import calc_main_progress
    from models import CONDATA
except ImportError as e:
    print(
        "Failed to import calc_py. Please compile rs_calc_faster first:\n"
        "  cd ../../calc_descriptors/calc_faster_rs\n"
        "  maturin develop --release",
        file=sys.stderr,
    )
    raise
finally:
    os.chdir(_original_cwd)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6380")
INPUT_QUEUE = os.getenv("INPUT_QUEUE", "hea:minimal:input")
OUTPUT_QUEUE = os.getenv("OUTPUT_QUEUE", "hea:minimal:output")


def main() -> None:
    r = redis.from_url(REDIS_URL)
    try:
        r.ping()
    except Exception as e:
        print(f"Redis connection failed: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Worker started. Input: {INPUT_QUEUE}, Output: {OUTPUT_QUEUE}")

    processed = 0
    start = time.time()

    while True:
        msg = r.brpop(INPUT_QUEUE, timeout=5)
        if msg is None:
            if r.llen(INPUT_QUEUE) == 0:
                break
            continue

        _, task_json = msg
        task = json.loads(task_json.decode() if isinstance(task_json, bytes) else task_json)

        try:
            calc_data = calc_main_progress(CONDATA(**task))
        except Exception as e:
            print(f"Error processing task {task.get('con_index')}: {e}", file=sys.stderr)
            continue

        def _to_native(value):
            """Convert numpy scalars to native Python types for JSON serialization."""
            if hasattr(value, "item"):
                return value.item()
            return value

        result = {
            "con_index": calc_data.con_index,
            "elem_index": calc_data.elem_index,
            "ave_array": [_to_native(x) for x in calc_data.ave_array_list],
            "rmse_array": [_to_native(x) for x in calc_data.rmse_array_list],
            "range_array": [_to_native(x) for x in calc_data.range_array_list],
            "pair_array": [_to_native(x) for x in calc_data.pair_array_list],
            "Smix_data": _to_native(calc_data.Smix_data),
            "lambda_data": _to_native(calc_data.lambda_data),
            "gamma_data": _to_native(calc_data.gamma_data),
            "Ev_data": _to_native(calc_data.Ev_data),
            "GG0_data": _to_native(calc_data.GG0_data),
            "KG_data": _to_native(calc_data.KG_data),
            "TbTm_data": _to_native(calc_data.TbTm_data),
            "Hmix_data": _to_native(calc_data.Hmix_data),
            "rmse_Hmix_data": _to_native(calc_data.rmse_Hmix_data),
            "omega_data": _to_native(calc_data.omega_data),
        }
        r.rpush(OUTPUT_QUEUE, json.dumps(result))

        processed += 1
        if processed % 10 == 0:
            speed = processed / (time.time() - start)
            print(f"Processed {processed} tasks @ {speed:.1f}/s")

    elapsed = time.time() - start
    print(f"Done. Processed {processed} tasks in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
