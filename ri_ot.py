#!/usr/bin/env python3
"""
p2w_thickness.py

Generalized version of the fringe-counting thickness/refractive-index
calculation. For a given parity triplet (p-i, p-i+1, p-i+2) and a given
Y position (Yk), this:

  1. Reads the calibration wavelength (mean pos_lambda) for p-i, p-i+1
     and p-i+2 from /main/calibration_p/p2w/p-{idx}/mean_p-{idx}*.csv
  2. Reads the measured wavelength data for p-i and p-i+1 from
     /main/file/p2w/p-{idx}/p2w_p-{idx}*{Y}.csv
  3. Computes optical thickness (op_thi), separation (sep) and
     refractive index (ref_in) for every frame, and writes a CSV with
     columns: frame, pos_pix, op_thi, sep, ref_in

Parity convention: p-0 is always parity +1, and parity alternates along
increasing index (p-1 = -1, p-2 = +1, p-3 = -1, ...).
"""

import argparse
import glob
import os
import sys

import numpy as np
import pandas as pd


# --------------------------------------------------------------------------
# Physics / math core (unchanged from the original script, just reshaped
# to work cleanly as functions of plain arrays).
# --------------------------------------------------------------------------

def mum(lmbda):
    """Dispersion relation for refractive index candidates."""
    return 1.5846 + 476000.0 / lmbda ** 2


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
    lda, lda_m1: 1-D arrays of measured wavelengths (one per frame) for
                 parity p-i and p-i+1 respectively.
    mul: 1-D array, the candidate refractive-index search grid.
    Returns (ot, ri, t) each shaped like lda (one value per frame), or
    NaN for frames where no sign change (no consistent solution) is found.
    """
    lda_col = lda.reshape(-1, 1)
    lda_m1_col = lda_m1.reshape(-1, 1)
    mul_row = mul.reshape(1, -1)

    f_p = f(l0, l0_m1, lda_col, mul_row, p)
    f_pm1 = f(l0_m1, l0_m2, lda_m1_col, mul_row, pm1)

    delta = f_p - f_pm1
    si = np.sign(delta)
    chg = (si[:, 1:] * si[:, :-1] < 0)

    has_change = chg.any(axis=1)
    first_col = np.where(has_change, chg.argmax(axis=1) + 1, -1)
    rows = np.arange(f_p.shape[0])

    ot = np.full(lda.shape[0], np.nan)
    ri = np.full(lda.shape[0], np.nan)

    valid = has_change
    ot[valid] = (f_p[rows[valid], first_col[valid]] + f_pm1[rows[valid], first_col[valid]]) / 2
    ri[valid] = mul_row[0, first_col[valid]]

    t = ot / (10 * ri)  # separation in nm
    return ot, ri, t


# --------------------------------------------------------------------------
# File discovery helpers
# --------------------------------------------------------------------------

def parity_of(idx):
    """p-0 is +1, alternates thereafter."""
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
    pattern = os.path.join(main_dir, "calibration_p", "p2w", f"p-{idx}", f"mean_p-{idx}*.csv")
    path = find_one(pattern, f"calibration p-{idx}")
    df = pd.read_csv(path)
    return float(df.iloc[:, 2].mean())


def load_measured(inputdir, idx, Y):
    pattern = os.path.join(inputdir, "p2w", f"p-{idx}", f"p2w_p-{idx}*.csv")
    candidates = sorted(glob.glob(pattern))
    candidates = [c for c in candidates if os.path.basename(c).endswith(f"{Y}.csv")]
    if not candidates:
        raise FileNotFoundError(
            f"No measured p2w file found for p-{idx}, {Y} (pattern: {pattern}, suffix {Y}.csv)"
        )
    if len(candidates) > 1:
        raise RuntimeError(
            f"Expected exactly one measured file for p-{idx}, {Y}, found {len(candidates)}: {candidates}"
        )
    df = pd.read_csv(candidates[0])
    df = df.rename(columns={df.columns[0]: "frame", df.columns[1]: "pos_pix", df.columns[2]: "pos_lambda"})
    return df[["frame", "pos_pix", "pos_lambda"]]


# --------------------------------------------------------------------------
# Main computation for one triplet + one Y
# --------------------------------------------------------------------------

def run(main_dir, inputdir, idx, Y, mul, out_path, frame_start=None, frame_end=None):
    l0 = load_calibration_l0(main_dir, idx)
    l0_m1 = load_calibration_l0(main_dir, idx + 1)
    l0_m2 = load_calibration_l0(main_dir, idx + 2)

    p = parity_of(idx)
    pm1 = parity_of(idx + 1)

    df_p = load_measured(inputdir, idx, Y)
    df_pm1 = load_measured(inputdir, idx + 1, Y)

    if frame_start is not None:
        df_p = df_p[df_p["frame"] >= frame_start]
        df_pm1 = df_pm1[df_pm1["frame"] >= frame_start]
    if frame_end is not None:
        df_p = df_p[df_p["frame"] <= frame_end]
        df_pm1 = df_pm1[df_pm1["frame"] <= frame_end]

    if df_p.empty:
        raise ValueError(
            f"No frames left for p-{idx}/{Y} after applying frame range "
            f"[{frame_start}, {frame_end}]"
        )

    merged = df_p.merge(df_pm1, on="frame", suffixes=("", "_m1"))
    if len(merged) != len(df_p):
        print(
            f"Warning: frames did not fully align between p-{idx} and p-{idx + 1} "
            f"for {Y} ({len(df_p)} vs {len(merged)} matched rows).",
            file=sys.stderr,
        )

    lda = merged["pos_lambda"].to_numpy(dtype=float)
    lda_m1 = merged["pos_lambda_m1"].to_numpy(dtype=float)

    ot, ri, t = solve_thickness_and_index(l0, l0_m1, l0_m2, lda, lda_m1, p, pm1, mul)

    out_df = pd.DataFrame({
        "frame": merged["frame"],
        "pos_pix": merged["pos_pix"],
        "op_thi": ot,
        "sep": t,
        "ref_in": ri,
    })

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    out_df.to_csv(out_path, index=False)
    print(f"Wrote {out_path} ({len(out_df)} rows)")


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--main-dir", required=True,
                         help="Path to the directory containing calibration_p/p2w/p-i/...")
    parser.add_argument("--inputdir", required=True,
                         help="Path to the directory containing p2w/p-i/... measured data "
                              "(i.e. <inputdir>/p2w/p-i/...). Independent of --main-dir.")
    parser.add_argument("--idx", type=int, required=True,
                         help="Starting parity index i of the triplet (uses p-i, p-i+1, p-i+2)")
    parser.add_argument("--Y", required=True, help="Y position identifier, e.g. Y1")
    parser.add_argument("--mul-start", type=float, default=0.5)
    parser.add_argument("--mul-stop", type=float, default=1.5)
    parser.add_argument("--mul-step", type=float, default=0.001)
    parser.add_argument("--frame-start", type=int, default=None,
                         help="Only process frames >= this value (inclusive)")
    parser.add_argument("--frame-end", type=int, default=None,
                         help="Only process frames <= this value (inclusive)")
    parser.add_argument("--out", required=True, help="Output CSV path")
    return parser.parse_args()


def main():
    args = parse_args()
    mul = np.arange(args.mul_start, args.mul_stop, args.mul_step)
    run(args.main_dir, args.inputdir, args.idx, args.Y, mul, args.out,
        frame_start=args.frame_start, frame_end=args.frame_end)


if __name__ == "__main__":
    main()
