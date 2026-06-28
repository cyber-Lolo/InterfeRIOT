#!/usr/bin/env python3

import argparse
from pathlib import Path
import pandas as pd
import os

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("name", help="Folder name containing MMVII-PhgrProj")
    parser.add_argument("center", type=int, help="Center Y value")
    parser.add_argument("width", type=int, help="Half-width around center")
    args = parser.parse_args()

    input_csv = (
        Path(args.name)
        / "MMVII-PhgrProj"
        / "Reports"
        / "ExtractFranges"
        / "Frange-MMVII-Retiga_000000001.csv"
    )

    df = pd.read_csv(input_csv)

    ymin = args.center - args.width
    ymax = args.center + args.width

    df_sel = df[(df["Y"] >= ymin) & (df["Y"] <= ymax)]
    result = (
        df_sel.groupby("Label", as_index=False)["X"]
        .mean()
    )
    result["Y"] = args.center
    result["weights"] = 1
    output_csv = os.path.join(args.name,f"output_{args.name}_{args.center}_{args.width}.csv")
    result.to_csv(output_csv, index=False)

    print(f"Saved: {output_csv}")


if __name__ == "__main__":
    main()