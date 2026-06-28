#!/usr/bin/env python3
"""
Created on Wed Jun 24 11:28:16 2026

@author: lolo

ri_ot.py

Per-frame RI/thickness computation for one consecutive fringe pair.

Inputs:
  - <inputdir>/p2w/p-<idx>/p2w_p-<idx>_<frame>.csv
  - <inputdir>/p2w/p-<idx+1>/p2w_p-<idx+1>_<frame>.csv

Each input CSV is expected to contain:
  Y, pos_pix, pos_lambda

Output:
  one CSV per frame and fringe pair, with one row per Y:
  frame, Y, pos_pix, op_thi, sep, ref_in
"""

from __future__ import annotations

import argparse
import glob
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def mum(lmbda):
    return 1.5846 + 476000.0 / lmbda**2


def S(lmbda0, lmbda0_m1, lmbda):
    ratio = (1 - lmbda0 / lmbda) / (1 - lmbda0 / lmbda0_m1)
    return np.sin(np.pi * ratio)


def C(lmbda0, lmbda0_m1, lmbda):
    ratio = (1 - lmbda0 / lmbda) / (1 - lmbda0 / lmbda0_m1)
    return np.cos(np.pi * ratio)


def numerator(lmbda0, lmbda0_m1, lmbda, n):
    mu = mum(lmbda)
    s = S(lmbda0, lmbda0_m1, lmbda)
    return 2 * np.dot(mu * s, 1 / n)


def denominator(lmbda0, lmbda0_m1, lmbda, n, pa):
    c = np.diagflat(C(lmbda0, lmbda0_m1, lmbda))
    su = 1 + np.dot(mum(lmbda), 1 / n) ** 2
    di = np.dot(mum(lmbda), 1 / n) ** 2 - 1
    A = np.dot(c, su)
    return A + pa * di


def f(lmbda0, lmbda0_m1, lmbda, n, pa):
    nu = numerator(lmbda0, lmbda0_m1, lmbda, n)
    de = denominator(lmbda0, lmbda0_m1, lmbda, n, pa)
    a = np.arctan2(nu, de)
    l = np.diagflat(lmbda)
    return np.dot(l, a) / (2 * np.pi)


def solve_thickness_and_index(l0, l0_m1, l0_m2, lda, lda_m1, p, pm1, mul):
    """
    lda, lda_m1: 1-D arrays of measured wavelengths for the two consecutive
                 fringe files, matched row-by-row on Y.
    mul: 1-D array of candidate refractive indices.
    Returns:
      ot, ri, t as 1-D arrays of length len(lda)
    """
    lda_col = lda.reshape(-1, 1)
    lda_m1_col = lda_m1.reshape(-1, 1)
    mul_row = mul.reshape(1, -1)

    f_p = f(l0, l0_m1, lda_col, mul_row, p)
    f_pm1 = f(l0_m1, l0_m2, lda_m1_col, mul_row, pm1)

    delta = f_p - f_pm1
    si = np.sign(delta)
    chg = si[:, 1:] * si[:, :-1] < 0

    has_change = chg.any(axis=1)
    first_col = np.where(has_change, chg.argmax(axis=1) + 1, -1)
    rows = np.arange(f_p.shape[0])

    ot = np.full(lda.shape[0], np.nan)
    ri = np.full(lda.shape[0], np.nan)

    valid = has_change
    ot[valid] = (
        f_p[rows[valid], first_col[valid]] + f_pm1[rows[valid], first_col[valid]]
    ) / 2
    ri[valid] = mul_row[0, first_col[valid]]

    t = ot / (10 * ri)
    return ot, ri, t


def parity_of(idx):
    return 1 if idx % 2 == 0 else -1


def find_one(pattern, description):
    matches = sorted(glob.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No file found for {description} (pattern: {pattern})")
    if len(matches) > 1:
        raise RuntimeError(
            f"Expected exactly one file for {description}, found {len(matches)}: {matches}"
        )
    return matches[0]


def load_calibration_l0(main_dir, idx):
    pattern = os.path.join(
        main_dir, "calibration_p", "p2w", f"p-{idx}", f"mean_p-{idx}*.csv"
    )
    path = find_one(pattern, f"calibration p-{idx}")
    df = pd.read_csv(path)
    if "pos_lambda" in df.columns:
        return float(df["pos_lambda"].mean())
    return float(df.iloc[:, 2].mean())


def load_measured_frame(inputdir, idx, frame):
    path = (
        Path(inputdir)
        / "p2w"
        / f"p-{idx}"
        / f"p2w_p-{idx}_{frame:09d}.csv"
    )
    if not path.exists():
        raise FileNotFoundError(f"Missing measured file: {path}")
    df = pd.read_csv(path, usecols=["Y", "pos_pix", "pos_lambda"])
    return df[["Y", "pos_pix", "pos_lambda"]]


def run(main_dir, inputdir, idx, frame, mul, out_path):
    l0 = load_calibration_l0(main_dir, idx)
    l0_m1 = load_calibration_l0(main_dir, idx + 1)
    l0_m2 = load_calibration_l0(main_dir, idx + 2)

    p = parity_of(idx)
    pm1 = parity_of(idx + 1)

    df_p = load_measured_frame(inputdir, idx, frame)
    df_pm1 = load_measured_frame(inputdir, idx + 1, frame)

    merged = df_p.merge(df_pm1, on="Y", suffixes=("", "_m1"))
    if merged.empty:
        raise ValueError(
            f"No overlapping Y values for frame {frame:09d} and pair p-{idx}/p-{idx+1}"
        )

    merged = merged.sort_values("Y", kind="mergesort").reset_index(drop=True)

    lda = merged["pos_lambda"].to_numpy(dtype=float)
    lda_m1 = merged["pos_lambda_m1"].to_numpy(dtype=float)

    ot, ri, t = solve_thickness_and_index(l0, l0_m1, l0_m2, lda, lda_m1, p, pm1, mul)

    out_df = pd.DataFrame(
        {
            "frame": frame,
            "Y": merged["Y"],
            "pos_pix": merged["pos_pix"],
            "op_thi": ot,
            "sep": t,
            "ref_in": ri,
        }
    )

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(out_path, index=False)
    print(f"Wrote {out_path} ({len(out_df)} rows)")


def parse_args():
    parser = argparse.ArgumentParser(description="Per-frame RI/thickness computation.")
    parser.add_argument("--main-dir", required=True)
    parser.add_argument("--inputdir", required=True)
    parser.add_argument("--idx", type=int, required=True)
    parser.add_argument("--frame", type=int, required=True)
    parser.add_argument("--mul-start", type=float, default=0.5)
    parser.add_argument("--mul-stop", type=float, default=1.5)
    parser.add_argument("--mul-step", type=float, default=0.001)
    parser.add_argument("--out", required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    mul = np.arange(args.mul_start, args.mul_stop, args.mul_step)
    run(args.main_dir, args.inputdir, args.idx, args.frame, mul, args.out)


if __name__ == "__main__":
    main()