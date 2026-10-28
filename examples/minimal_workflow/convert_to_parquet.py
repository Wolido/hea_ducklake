#!/usr/bin/env python3
"""
Convert the CSV results from the minimal workflow into a Parquet file.

This step demonstrates the lakehouse-style storage layer used in hea_ducklake:
results are stored as compressed columnar Parquet files, which can be queried
efficiently with DuckDB without loading the full dataset into memory.
"""

import os

import pandas as pd

INPUT_CSV = os.getenv("OUTPUT_CSV", "results.csv")
OUTPUT_PARQUET = os.getenv("OUTPUT_PARQUET", "results.parquet")


def main() -> None:
    if not os.path.exists(INPUT_CSV):
        print(f"Input CSV not found: {INPUT_CSV}", file=os.sys.stderr)
        print("Run collect_results.py first.", file=os.sys.stderr)
        os.sys.exit(1)

    df = pd.read_csv(INPUT_CSV)
    df.to_parquet(OUTPUT_PARQUET, index=False, compression="zstd")
    print(f"Converted {len(df)} rows from {INPUT_CSV} to {OUTPUT_PARQUET}")


if __name__ == "__main__":
    main()
