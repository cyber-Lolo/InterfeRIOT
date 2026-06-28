#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 23 21:31:36 2026

@author: lolo
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def frame_of(csv_file: Path) -> int:
    # p2w_p-3_000000123.csv -> 123
    return int(csv_file.stem.split("_")[-1])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("name", help="CSV root (e.g. ./calibration_p)")
    parser.add_argument("center", type=int, help="Center Y value")
    parser.add_argument("width", type=int, help="Half-width around center")
    args = parser.parse_args()

    p2w_base = Path(args.name) / "p2w"
    y_min = args.center - args.width
    y_max = args.center + args.width

    for folder in sorted(p2w_base.iterdir()):
        if not folder.is_dir() or not folder.name.startswith("p-"):
            continue

        label = folder.name  # e.g. "p-3"
        frame_files = sorted(folder.glob(f"p2w_{label}_*.csv"), key=frame_of)

        rows = []
        for csv_file in frame_files:
            frame = frame_of(csv_file)

            df = pd.read_csv(csv_file, usecols=["Y", "pos_pix", "pos_lambda"])
            df = df[(df["Y"] >= y_min) & (df["Y"] <= y_max)]

            if df.empty:
                continue

            means = df[["pos_pix", "pos_lambda"]].mean()

            rows.append(
                {
                    "frame": frame,
                    "pos_pix": means["pos_pix"],
                    "pos_lambda": means["pos_lambda"],
                }
            )

        if not rows:
            continue

        out_df = pd.DataFrame(rows).sort_values("frame")
        output_csv = folder / f"mean_{label}_{args.center}_{args.width}.csv"
        out_df.to_csv(output_csv, index=False)
        print(f"Saved {output_csv}")


if __name__ == "__main__":
    main()