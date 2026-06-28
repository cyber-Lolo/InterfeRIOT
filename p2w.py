#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Convert one frame of Frange output into per-frame per-label CSVs.

Output structure:
    Path(args.name) / "p2w" / f"p-{label}" / f"p2w_p-{label}_{frame:09d}.csv"

Each file contains columns:
    Y, pos_pix, pos_lambda
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def pix2wave(old_gy: Path, new_gy: Path, pix: pd.Series) -> pd.Series:
    df_gy = pd.read_csv(old_gy)
    df_g = pd.read_csv(new_gy)

    lg, ly = 5461.0, 5790.65

    pg = df_g[df_g["Label"] == 0].iloc[0, 1]
    py = df_gy[df_gy["Label"] == 0].iloc[0, 1] - pg + df_gy[df_gy["Label"] == 2].iloc[0, 1]

    return lg + (pix - pg) * (ly - lg) / (py - pg)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("name", help="CSV root")
    parser.add_argument("frames", type=int, help="Image number")
    args = parser.parse_args()

    input_csv = (
        Path(args.name)
        / "MMVII-PhgrProj"
        / "Reports"
        / "ExtractFranges"
        / f"Frange-MMVII-Retiga_{args.frames:09d}.csv"
    )

    csv_gy = next(Path("calibration_gy").glob("output_calibration_gy*.csv"))
    csv_g = next(Path("calibration_g").glob("output_calibration_g*.csv"))

    df = pd.read_csv(input_csv)
    pos_lbd = pix2wave(csv_gy, csv_g, df["X"])

    df_result = pd.DataFrame(
        {
            "Label": df["Label"],
            "Y": df["Y"],
            "pos_pix": df["X"],
            "pos_lambda": pos_lbd,
        }
    )

    output_base = Path(args.name) / "p2w"

    for label, group in df_result.groupby("Label", sort=False):
        out_csv = output_base / f"p-{label}" / f"p2w_p-{label}_{args.frames:09d}.csv"
        group[["Y", "pos_pix", "pos_lambda"]].to_csv(out_csv, index=False)


if __name__ == "__main__":
    main()