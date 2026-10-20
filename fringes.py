#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 10 19:37:05 2026

@author: lauriane
"""

from pathlib import Path
import pandas as pd
import os
from PIL import Image
import numpy as np
from skimage.io import imread, imshow
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# ==== COLORMAP ====

cmap = mcolors.LinearSegmentedColormap.from_list("custom_map", ['teal','palegreen','yellow','gold'])
pnorm = mcolors.Normalize(vmin=0,vmax=2688)

pub_soft = ["cornflowerblue","darkturquoise","lightgreen","gold","darkorange","lightcoral"
]

required_cols = { "Y", "pos_pix", "pos_lambda"}
file="radius1_22.7_approach_0.5vps_retract_600ang_0.05vps_by1V"

L=[k for k in range(1,3,1)]
main=Path(f"/Users/lolo/Documents/expe/paper2_demix/20251113/{file}/")
path_in=main / "MMVII-PhgrProj/Reports/ExtractFranges"
wave= main/"p2w"


plt.figure()
ymin,ymax=[800,1400]
def p2w(pos):
    pg,lg=496.488084795507,5461.0
    py,ly=2786.931019274594,5790.65
    lp=lg+(pos-pg)*(ly-lg)/(py-pg)
    return(lp)
pnorm_wave = mcolors.Normalize(vmin=p2w(0),vmax=p2w(2688))
fig2, ax2 = plt.subplots(figsize=(7, 5))
for n in L:
    
    numim="{:09d}".format(n)
    path_img=main/f"Retiga_{numim}.tif"
    img = imread(path_img)
    plt.imshow(img[ymin:ymax,0:2689], cmap='gray',origin='lower',
               extent=[0,2689, ymin, ymax])
    path_in_csv=path_in/f"Frange-MMVII-Retiga_{numim}.csv"
    df = pd.read_csv(path_in_csv)
    
    df = df.sort_values(by=["Y", "Label"])
    index=[k for k in df["Label"]]
    lambdasD=[f"{i}" for i in index]
    lambdas0=[f"{i}"for i in index]
    ax = plt.gca()
    lbdD0=[]    
    k=0
    ax = plt.gca()
    lbdD0=[]
    for label, group in df.groupby("Label"):
        print(label)
        plt.scatter(group["X"], group["Y"],s=5,marker='.',linewidths=0,alpha=1.0,c=cmap(pnorm(group["X"])))
        abscissa=group["X"]
        ordinate=group["Y"]
        plt.plot([np.min(abscissa),np.min(abscissa)],[ymin,ymax],color=cmap(pnorm(np.min(abscissa))),linestyle=':')
        ax.text(np.min(abscissa), 1.02, f"{label}",transform=ax.get_xaxis_transform(), ha='center',va='bottom',fontsize=10,color='black')
        lbdD0.append(np.min(group["X"]))
        k+=1
        arg_top = np.argmin(abscissa)
        Yp_fit,pix_fit =  ordinate[arg_top-10:arg_top+10],abscissa[arg_top-10:arg_top+10]
        a, b ,c = np.polyfit(Yp_fit, pix_fit, 2)
        Yp_top, pix_top =   -b/(2*a),-(b**2 - 4* a*c)/(4*a)
        #print("frame",n,"fringe",label,p2w(abscissa))
        ax2.scatter(p2w(abscissa),ordinate,color=cmap(pnorm_wave(p2w(abscissa))))

  
    plt.ylabel(f"x in px")
    plt.ylim(ymin,ymax)
    plt.xlim(0,2689)
    # --- add custom x ticks at p0 with transformed labels ---
    
    ax.set_yticks([ymin,ymax])
    ax.set_yticklabels([f"{ymax}",f"{ymin}"])
    ax.set_xticks(lbdD0)
    ax.set_xticklabels([f"{p2w(lbdD0[j])/10:.2f}" for j in range(len(lbdD0))],fontsize=9)

    
    plt.tight_layout()
    plt.show()
    im_save=main/f"fringes_{n}.pdf"
plt.figure(fig2.number)
fig2.show()
