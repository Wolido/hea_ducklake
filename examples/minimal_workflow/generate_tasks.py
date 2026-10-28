#!/usr/bin/env python3
"""
Generate HEA composition tasks using the same Rust routine as the full pipeline.

This script reproduces the production task-generation path in
`calc_descriptors/calc_py/que_push.py`:

    con_list = rs_calc_faster.rs_generate_con_list_all()
    redis_list = rs_calc_faster.rs_que_push_iter(
        elem_index=elem_index, elem_tuple=elem_tuple, con_list=con_list
    )

For the minimal workflow only the first TOTAL_TASKS tasks are pushed to Redis.
"""

import json
import os
import sys

import redis

try:
    import rs_calc_faster  # type: ignore
except ImportError as e:
    print(
        "Failed to import rs_calc_faster. Please compile the Rust extension first:\n"
        "  cd ../../calc_descriptors/calc_faster_rs\n"
        "  maturin develop --release\n"
        "Then return to this directory and re-run the script.",
        file=sys.stderr,
    )
    raise

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6380")
INPUT_QUEUE = os.getenv("INPUT_QUEUE", "hea:minimal:input")
TOTAL_TASKS = int(os.getenv("TOTAL_TASKS", "100"))

# 15 elements used in hea_ducklake, in the same order as the full code base.
ELEMENTS = [
    "Fe", "Ni", "Mn", "Al", "Cr", "Cu", "Co", "Mo", "Ti",
    "Nb", "Ta", "W", "V", "Zr", "Hf",
]


def main() -> None:
    r = redis.from_url(REDIS_URL)
    try:
        r.ping()
    except Exception as e:
        print(f"Redis connection failed: {e}", file=sys.stderr)
        sys.exit(1)

    # Use the first 6-element family as a minimal example.
    elem_tuple = tuple(ELEMENTS[:6])
    elem_index = 0

    # Clear any stale tasks.
    r.delete(INPUT_QUEUE)

    # Generate the full task list using the same routine as the production code.
    con_list = rs_calc_faster.rs_generate_con_list_all()
    redis_list = rs_calc_faster.rs_que_push_iter(
        elem_index=elem_index, elem_tuple=elem_tuple, con_list=con_list
    )

    # Push only the first TOTAL_TASKS tasks for the minimal demo.
    tasks = redis_list[:TOTAL_TASKS]
    if tasks:
        r.rpush(INPUT_QUEUE, *tasks)

    print(
        f"Pushed {len(tasks)} tasks to {INPUT_QUEUE} "
        f"(family generated {len(redis_list):,} tasks total)"
    )


if __name__ == "__main__":
    main()
