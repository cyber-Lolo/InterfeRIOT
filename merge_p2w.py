#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 16 10:16:14 2026

@author: lolo
"""
# merge_p2w.py


"""
from pathlib import Path
import sys
from multiprocessing import Pool, cpu_count
import pyarrow.csv as pacsv
import pyarrow as pa

def merge_folder_arrow(folder):
    if not folder.is_dir():
        return
    targets = {}
    for tmp in folder.glob(".tmp_*"):
        final_name = "p2w_" + "_".join(tmp.stem.split("_")[2:]) + ".csv"
        targets.setdefault(final_name, []).append(tmp)

    for final_name, tmps in targets.items():
        final_csv = folder / final_name
        tables = [pacsv.read_csv(t) for t in sorted(tmps)]
        merged = pa.concat_tables(tables)
        # sort by fringes
        import pyarrow.compute as pc
        idx = pc.sort_indices(merged, sort_keys=[("fringes", "ascending")])
        merged = merged.take(idx)
        pacsv.write_csv(merged, final_csv)
        for t in tmps:
            t.unlink()

    print(f"Done: {folder.name}")

if __name__ == "__main__":
    output_base = Path(sys.argv[1]) / "p2w"
    folders = [f for f in sorted(output_base.iterdir()) if f.is_dir()]

    n_jobs = int(sys.argv[2]) if len(sys.argv) > 2 else cpu_count()
    with Pool(n_jobs) as pool:
        pool.map(merge_folder_arrow, folders)

    print("Merge done.")"""
    
# merge_p2w.py
import pandas as pd
import pyarrow.csv as pacsv
import pyarrow as pa
import pyarrow.compute as pc
from pathlib import Path
import sys
from multiprocessing import Pool, cpu_count

def merge_folder(folder):
    if not folder.is_dir():
        return

    targets = {}
    for tmp in folder.glob(".tmp_*"):
        final_name = "p2w_" + "_".join(tmp.stem.split("_")[2:]) + ".csv"
        targets.setdefault(final_name, []).append(tmp)

    for final_name, tmps in targets.items():
        final_csv = folder / final_name

        # Read new tmp data
        new_table = pa.concat_tables([pacsv.read_csv(t) for t in sorted(tmps)])

        # If final csv already exists, merge with deduplication (new wins)
        if final_csv.exists():
            existing = pacsv.read_csv(final_csv)
            # Remove rows from existing whose frame appears in new data
            new_frames = pc.unique(new_table.column("frame"))
            mask = pc.invert(pc.is_in(existing.column("frame"), value_set=new_frames))
            existing_filtered = existing.filter(mask)
            merged = pa.concat_tables([existing_filtered, new_table])
        else:
            merged = new_table

        # Sort by frame
        idx = pc.sort_indices(merged, sort_keys=[("frame", "ascending")])
        merged = merged.take(idx)

        pacsv.write_csv(merged, final_csv)

        for t in tmps:
            t.unlink()

    print(f"Done: {folder.name}")

if __name__ == "__main__":
    output_base = Path(sys.argv[1]) / "p2w"
    folders = [f for f in sorted(output_base.iterdir()) if f.is_dir()]

    n_jobs = int(sys.argv[2]) if len(sys.argv) > 2 else cpu_count()
    with Pool(n_jobs) as pool:
        pool.map(merge_folder, folders)

    print("Merge done.")