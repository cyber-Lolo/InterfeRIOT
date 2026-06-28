#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import re

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd


def moving_average(y, window):
    y = np.asarray(y, dtype=float)
    if window < 1:
        raise ValueError("window must be >= 1")
    if window > len(y):
        return y.copy()
    kernel = np.ones(window) / window
    return np.convolve(y, kernel, mode="valid")


def read_elapsed_times(time_file):
    """
    Parse Time.txt and return {frame_number: elapsed_seconds}.
    Expects entries containing lines like:
      "Filename": "Retiga_000000001.tif"
      "ElapsedTime-ms": 315
    """
    text = Path(time_file).read_text(errors="ignore")

    filenames = re.findall(r'Filename"\s*:\s*"Retiga_(\d+)\.tif"', text)
    elapsed_ms = re.findall(r'ElapsedTime-ms"\s*:\s*(\d+)', text)

    if not filenames or not elapsed_ms:
        raise ValueError(f"Could not parse frame/time pairs from {time_file}")

    n = min(len(filenames), len(elapsed_ms))
    time_map = {}
    for f, ms in zip(filenames[:n], elapsed_ms[:n]):
        time_map[int(f)] = int(ms) / 1000.0

    return time_map


# ---------------------------------------------------------------------
# Parameters to edit
# ---------------------------------------------------------------------
base_dir = Path("/Users/lolo/Documents/expe/paper2_demix/20260124_f8h7_partial/radius1_static_contact10A_26C_reduced")
first_fringes = [0, 1 ]
frames = [7977,7978,7979,7980,7985,7990,7995,8000]
save_dir = base_dir / "riot_plots"
show = True
dpi = 300

# Choose anchor colors for the gradient
anchor_colors = ["deepskyblue", "darkblue"]
# ---------------------------------------------------------------------

ri_dir = base_dir / "ri"
time_file = base_dir / "Times.txt"

if save_dir is not None:
    save_dir.mkdir(parents=True, exist_ok=True)

required_cols = {"frame", "Y", "pos_pix", "op_thi", "sep", "ref_in"}

time_map = read_elapsed_times(time_file)

# Keep only frames that exist in the time map
valid_frames = []
elapsed_list = []
for frame in frames:
    if frame not in time_map:
        print(f"Missing elapsed time for frame {frame:09d}")
        continue
    valid_frames.append(frame)
    elapsed_list.append(time_map[frame])
elapsed_list=np.array(elapsed_list)-np.min(elapsed_list)
if not valid_frames:
    raise ValueError("No valid frames to plot.")

cmap = mcolors.LinearSegmentedColormap.from_list("elapsed_gradient", anchor_colors, N=256)
norm = mcolors.Normalize(vmin=min(elapsed_list), vmax=max(elapsed_list))

fig1, ax1 = plt.subplots(figsize=(7, 5))
fig2, ax2 = plt.subplots(figsize=(7, 5))
fig3, ax3 = plt.subplots(figsize=(7, 5))

for frame in valid_frames:
    elapsed_s = time_map[frame]-time_map[valid_frames[0]]
    color = cmap(norm(elapsed_s))

    SEP, RI, Y = [], [], []

    for idx in first_fringes:
        pair_dir = ri_dir / f"p-{idx}_p-{idx + 1}"
        csv_path = pair_dir / f"ri_p-{idx}_p-{idx + 1}_{frame:09d}.csv"

        if not csv_path.exists():
            print(f"Missing: {csv_path}")
            continue

        df = pd.read_csv(csv_path)
        missing = required_cols - set(df.columns)
        if missing:
            raise ValueError(f"{csv_path} is missing columns: {sorted(missing)}")

        df = df.sort_values("Y", kind="mergesort")

        SEP.append(df["sep"].to_numpy())
        RI.append(df["ref_in"].to_numpy())
        Y.append(df["Y"].to_numpy())

    if not SEP:
        continue

    sep = np.concatenate(SEP)
    ri = np.concatenate(RI)
    y = np.concatenate(Y)
    
    sep = sep[y<1101]
    ri = ri[y<1101]
    y = y[y<1101]
    
    idx_sep = np.argsort(sep)
    sep_sort = sep[idx_sep]
    ri_sep = ri[idx_sep]

    idx_y = np.argsort(y)
    y_sort = y[idx_y]
    ri_y = ri[idx_y]
    sep_y = sep[idx_y]

    sep_sort_smooth = moving_average(sep_sort, 20)
    ri_sep_smooth = moving_average(ri_sep, 20)

    y_sort_smooth = moving_average(y_sort, 1)
    ri_y_smooth = moving_average(ri_y, 1)
    sep_y_smooth = moving_average(sep_y, 1)

    ax1.plot(
        sep_sort_smooth,
        ri_sep_smooth,
        color=color,
        label=f"{frame} ({elapsed_s:.2f} s)",
    )
    ax2.scatter(
        y_sort_smooth,
        ri_y_smooth,
        color=color,
        s=2,
        label=f"{frame} ({elapsed_s:.2f} s)",
    )
    ax3.scatter(
        y_sort_smooth,
        sep_y_smooth,
        color=color,
        s=2,
        label=f"{frame} ({elapsed_s:.2f} s)",
    )

ax1.set_title("Refractive index vs separation")
ax1.set_xlabel("Separation / nm")
ax1.set_xlim(0, 120)
#ax1.set_ylim(1.27, 1.43)
ax1.set_ylabel("Refractive index")
#ax1.legend(fontsize=8)

ax2.set_title("Refractive index vs Y")
ax2.set_xlabel("Y")
ax2.set_ylabel("Refractive index")
ax2.legend(fontsize=8)

ax3.set_title("Separation vs Y")
ax3.set_xlabel("Y")
ax3.set_ylabel("Separation")
ax3.legend(fontsize=8)

sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
sm.set_array([])
cbar = fig1.colorbar(sm, ax=ax1, fraction=0.046, pad=0.04)
cbar.set_label("Elapsed time (s)")
fig2.colorbar(sm, ax=ax2, fraction=0.046, pad=0.04).set_label("Elapsed time (s)")
fig3.colorbar(sm, ax=ax3, fraction=0.046, pad=0.04).set_label("Elapsed time (s)")

if save_dir is not None:
    fig1.savefig(save_dir / "ri_sep_over_time.png", dpi=dpi, bbox_inches="tight")
    fig2.savefig(save_dir / "ri_y_over_time.png", dpi=dpi, bbox_inches="tight")
    fig3.savefig(save_dir / "sep_y_over_time.png", dpi=dpi, bbox_inches="tight")

if show:
    plt.show()

plt.close(fig1)
plt.close(fig2)
plt.close(fig3)