# avg_p2w.py
import argparse
import pandas as pd
import pyarrow.csv as pacsv
from pathlib import Path

def main():
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

        matching = []
        for csv_file in folder.glob(f"p2w_{label}_*.csv"):
            y_val = int(csv_file.stem.split("_")[-1])
            if y_min <= y_val <= y_max:
                matching.append(csv_file)

        if not matching:
            continue

        df = pd.concat(
            [pacsv.read_csv(f).to_pandas() for f in sorted(matching)],
            ignore_index=True
        )

        per_frame = (
            df.groupby("frame")[["pos_pix", "pos_lambda"]]
            .mean()
            .reset_index()
            .sort_values("frame")
        )[["frame", "pos_pix", "pos_lambda"]]

        output_csv = folder / f"mean_{label}_{args.center}_{args.width}.csv"
        per_frame.to_csv(output_csv, index=False)
        print(f"Saved {output_csv}")

if __name__ == "__main__":
    main()