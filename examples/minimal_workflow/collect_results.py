#!/usr/bin/env python3
"""
Collect computed HEA descriptors from Redis and write them to a CSV file.
"""

import csv
import json
import os
import sys

import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6380")
OUTPUT_QUEUE = os.getenv("OUTPUT_QUEUE", "hea:minimal:output")
OUTPUT_CSV = os.getenv("OUTPUT_CSV", "results.csv")


def main() -> None:
    r = redis.from_url(REDIS_URL)
    try:
        r.ping()
    except Exception as e:
        print(f"Redis connection failed: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Collecting results from {OUTPUT_QUEUE} -> {OUTPUT_CSV}")

    count = 0
    writer = None
    with open(OUTPUT_CSV, "w", newline="") as f:
        while True:
            msg = r.blpop(OUTPUT_QUEUE, timeout=2)
            if msg is None:
                if r.llen(OUTPUT_QUEUE) == 0:
                    break
                continue

            _, result_json = msg
            result = json.loads(
                result_json.decode() if isinstance(result_json, bytes) else result_json
            )

            row = {
                "con_index": result["con_index"],
                "elem_index": result["elem_index"],
            }
            for i, v in enumerate(result["ave_array"]):
                row[f"ave_{i}"] = v
            for i, v in enumerate(result["rmse_array"]):
                row[f"rmse_{i}"] = v
            for i, v in enumerate(result["range_array"]):
                row[f"range_{i}"] = v
            for i, v in enumerate(result["pair_array"]):
                row[f"pair_{i}"] = v
            for k in (
                "Smix_data", "lambda_data", "gamma_data", "Ev_data",
                "GG0_data", "KG_data", "TbTm_data", "Hmix_data",
                "rmse_Hmix_data", "omega_data",
            ):
                row[k] = result[k]

            if writer is None:
                writer = csv.DictWriter(f, fieldnames=row.keys())
                writer.writeheader()
            writer.writerow(row)
            count += 1

    print(f"Wrote {count} results to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
