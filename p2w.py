#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 15 14:38:06 2026

@author: lolo
"""
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import os

def pix2wave(old_gy, new_gy, pix):
    df_gy = pd.read_csv(old_gy)
    df_g  = pd.read_csv(new_gy)

    lg, ly = 5461.0, 5790.65

    pg = df_g[df_g["Label"] == 0].iloc[0, 1]
    py = df_gy[df_gy["Label"] == 0].iloc[0, 1] - pg + df_gy[df_gy["Label"] == 2].iloc[0, 1]

    lp = lg + (pix - pg) * (ly - lg) / (py - pg)
    return lp
    

def main():
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
    csv_g  = next(Path("calibration_g").glob("output_calibration_g*.csv"))

    df = pd.read_csv(input_csv)
    pos_lbd = pix2wave(csv_gy, csv_g, df['X'])

    df_result = pd.DataFrame({
        "Label":  df['Label'],
        "X":      df['X'],
        "Lambda": pos_lbd,
        "Y":      df['Y'],
    })

    output_base = Path(args.name) / "p2w"

    for (label, y), group in df_result.groupby(['Label', 'Y']):
        folder = output_base / f"p-{label}"
        folder.mkdir(parents=True, exist_ok=True)

        tmp_csv = folder / f".tmp_{args.frames:09d}_p-{label}_{y}.csv"

        pd.DataFrame({
            "frame":    args.frames,
            "pos_pix":    group['X'].values,
            "pos_lambda": group['Lambda'].values,
        }).to_csv(tmp_csv, index=False)
        
        
        
if __name__ == "__main__":
    main()