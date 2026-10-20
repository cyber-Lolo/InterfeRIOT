#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import re

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
from math import *
from scipy.signal import savgol_filter

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


def thickness(n, D, nclose, nfar):
    e = (D / 2) * (n - nfar) / (nclose - nfar)
    return e


# ---------------------------------------------------------------------
# Parameters to edit
# ---------------------------------------------------------------------
base_dir = Path(
    "/Users/lolo/Documents/expe/paper2_demix/20250527/fmfp02_0.03VE_cmes/"
)
first_fringes = [0]
frames = [k for k in range(1265, 1500, 1)]
save_dir = base_dir / "riot_plots"#
#save_dir = None
show = True
dpi = 300
n1 = 1.42
n2 = 1.2
Djump = 31.9822
anchor_colors = ["hotpink", "crimson", "maroon"]
kn= 142.2 #+/-9.8 N/m old echem 
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
elapsed_list = np.array(elapsed_list) - np.min(elapsed_list)
if not valid_frames:
    raise ValueError("No valid frames to plot.")

cmap = mcolors.LinearSegmentedColormap.from_list("elapsed_gradient", anchor_colors, N=256)
norm = mcolors.Normalize(vmin=min(elapsed_list), vmax=max(elapsed_list))

fig1, ax1 = plt.subplots(figsize=(7, 5))
fig2, ax2 = plt.subplots(figsize=(7, 5))
fig3, ax3 = plt.subplots(figsize=(7, 5))
fig4, ax4 = plt.subplots(figsize=(7, 5))
fig5, ax5 = plt.subplots(figsize=(7, 5))
fig6, ax6 = plt.subplots(figsize=(7, 5))
Va=[]
Apex=[]
Time=[]
filt1=[]
Curv=[]
for frame in valid_frames:
    elapsed_s = time_map[frame] - time_map[valid_frames[0]]
    color = cmap(norm(elapsed_s))
    Time.append(elapsed_s)
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
    y = (np.concatenate(Y)-100)* 0.3757*1000
    good = np.isfinite(sep)
    sep , ri, y = sep[good],ri[good],y[good]
    dy = y[1] - y[0]
    window, order = len(sep)//2 +1,3        # tune to your noise level and sampling
    D1 = savgol_filter(sep, window, order, deriv=1, delta=dy)
    D2 = savgol_filter(sep, window, order, deriv=2, delta=dy)
    kappa = D2 / (1 + D1**2)**1.5
    rho = 1 / kappa
    Curv.append(np.mean(rho)/1e7)
    
    print(np.mean(rho)/1e7)
    idx_s = np.argsort(sep)
    y_s = y[idx_s]
    ri_s = ri[idx_s]
    sep_s = sep[idx_s]
    
    
    
    y_s_smooth = moving_average(y_s, 1) * 0.3757
    ri_s_smooth = moving_average(ri_s, 1)
    sep_s_smooth = moving_average(sep_s, 1)
    Apex.append(np.mean(sep_s_smooth[0:5]))
    
    ax1.scatter(sep_s_smooth,ri_s_smooth,color=color,zorder=10000-frame)
    ax2.scatter(y,sep,color=color)
    ax3.scatter(y,rho,color=color)
    

ax1.set_xlabel(r"D / nm")
ax1.set_ylabel("RI")
ax1.set_xlim(-1,120)
ax1.set_title("refractive index vs separation")
#ax1.set_ylim(1.1,1.5)
sm = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
sm.set_array([])
cbar = fig1.colorbar(sm, ax=ax1, fraction=0.046, pad=0.04)
cbar.set_label("Elapsed time (s)")  

ax2.set_ylabel(r"D / nm")
ax2.set_xlabel("X / nm")
ax2.set_title("Separation profile")

ax3.set_xlabel(r"X / nm")
ax3.set_ylabel(r"$\rho(x)$ in nm")
ax3.set_title("Curvature")

ax4.plot(Apex,Curv) 
ax4.set_xlabel(r"D / nm")
ax4.set_ylabel(r"$\bar{\rho}$ in  cm")
ax4.set_ylim(0,3)
ax4.set_title("Mean Curvature vs apex")

Apex,Time=np.array(Apex),np.array(Time)
ax5.plot(Time,Apex)  
ax5.set_xlabel("Time / s")
ax5.set_ylabel(r"$D_{0}$ / nm")
ax5.set_title("Distance vs time")

filt2=(Apex>40)&(Apex<100)
Tf,Af=Time[filt2],Apex[filt2]
p=np.poly1d(np.polyfit(Tf, Af, deg=1))
linA=p(Time)
dev=1e3*(Apex-linA)*kn/(2*pi*1.34*1e7)
ax6.plot(Apex,dev)
ax6.set_xlabel("Separation / nm")
ax6.set_ylabel(r" Force / mN.m$^{-1}$")
ax6.set_title("Force vs distance")
jump=1e3*Djump*kn/(2*pi*1.34*1e4)
ax6.scatter(2,-jump)
dev = np.concatenate((dev,[jump]),axis=0)
distance_fp = np.concatenate((Apex,[0]),axis=0)
print(len(dev),len(distance_fp))
out_path = base_dir /"force_profile.csv"
pd.DataFrame({"Sep in nm": distance_fp,"F in mN/m": dev}).to_csv(out_path, index=False)


if save_dir is not None:
    fig1.savefig(save_dir / "D_ri.pdf", dpi=dpi, bbox_inches="tight")
