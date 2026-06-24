# InterfeRIOT
## Interferometric Refractive Index and Optical Thickness Analysis from Surface Force Balance Fringe Data

InterfeRIOT is a workflow for processing Surface Force Balance (SFB) interferograms, from raw images to calibrated wavelengths, refractive index determination, optical thickness reconstruction, and separation analysis.

The repository combines:

- MMVII-based fringe detection
- Mercury-line wavelength calibration
- Pixel-to-wavelength conversion
- Per-frame fringe tracking
- Refractive index (RI) estimation
- Optical thickness (OT) computation
- Separation profile extraction
- Batch processing tools for large video datasets

---

# Features

- Automated fringe extraction using MMVII
- Calibration using mercury emission lines
- Parallel processing of large image sequences
- Conversion from fringe position (pixels) to wavelength (Å)
- Per-frame fringe tracking
- RI estimation from three-layer interferometry
- Optical thickness and separation reconstruction
- Frame-range filtering for targeted analysis

---

# Requirements

## Software

- MMVII
- Python ≥ 3.9

## Python Packages

```bash
pip install numpy pandas
```

---

# Workflow Overview

```text
Raw SFB interferograms
          │
          ▼
MMVII fringe extraction
          │
          ▼
Mercury calibration
          │
          ▼
Pixel → wavelength conversion
          │
          ▼
Per-frame wavelength files
          │
          ▼
Mean wavelength extraction
          │
          ▼
Refractive index reconstruction
          │
          ▼
Optical thickness reconstruction
          │
          ▼
Separation analysis
```

---

# Repository Structure

```text
project_root/
│
├── calibration_gy/
├── calibration_g/
├── calibration_p/
│
├── video/
│
├── extractfranges.sh
├── mean_x.py
├── p2w.py
├── p2w_para.sh
├── mean_p2w.py
│
├── ri_ot.py
├── run_all.sh
│
└── README.md
```

---

# Input Data

## Mercury Calibration

### Green + Yellow Mercury Rays

```text
calibration_gy/
└── Retiga_000000001.tif
```

### Green Mercury Ray Only

```text
calibration_g/
└── Retiga_000000001.tif
```

## Fringe Calibration

```text
calibration_p/
└── Retiga_000000001.tif
```

The calibration image must contain at least:

```text
p
p−1
p−2
```

fringes.

## Video Data

```text
video/
└── Retiga_*.tif
```

---

# MMVII Fringe Extraction

## Mercury Rays

```bash
MMVII ExtractFranges Retiga_000000001.tif \
    "IntY=[980,1220]" \
    MinWidth=0 \
    BorderMinWidth=0 \
    MinHeightBorderRight=0
```

## Fringe Calibration

```bash
MMVII ExtractFranges Retiga_000000001.tif \
    "IntY=[980,1220]"
```

## Video Processing

```bash
source extractfranges.sh

cd video

run_toto_parallel -j 16 --arg 'IntY=[980,1220]'
```

---

# Mercury Mean Position Computation

```bash
python3 mean_x.py calibration_gy 1100 20
python3 mean_x.py calibration_g 1100 20
```

where:

- 1100 = Y center
- 20 = averaging half-width

---

# Pixel-to-Wavelength Conversion

## Calibration Fringes

```bash
bash p2w_para.sh ./calibration_p 1 1
```

## Video

```bash
bash p2w_para.sh ./video 1 9999 8 5
```

Output structure:

```text
video/p2w/
├── p-0/
│   ├── p2w_p-0_000000001.csv
│   ├── p2w_p-0_000000002.csv
│   └── ...
├── p-1/
├── p-2/
└── ...
```

Each file contains:

```text
Y,pos_pix,pos_lambda
```

One file corresponds to one frame and one fringe label.

---

# Mean Wavelength Extraction

```bash
python3 mean_p2w.py ./calibration_p 1100 20

python3 mean_p2w.py ./radius_spot1_free_evap_part2_2000_2500 1100 20
```

Output:

```text
mean_p-3_1100_20.csv
```

Columns:

```text
frame,pos_pix,pos_lambda
```

---

# Refractive Index and Optical Thickness Analysis

Measured data are processed as:

```text
(p-i,p-(i+1))
```

Calibration data are read from:

```text
(p-i,p-(i+1),p-(i+2))
```

For each frame:

1. Read the two measured fringe files.
2. Read the three calibration mean files.
3. Generate a refractive-index search grid.
4. Evaluate the parity equations.
5. Detect the first sign change.
6. Estimate refractive index.
7. Compute optical thickness.
8. Compute separation.

---

# Running the Analysis

```bash
./run_all.sh \
    --input-dir radius_spot1_free_evap_part2_2000_2500
```

Restrict frame range:

```bash
./run_all.sh \
    --input-dir radius_spot1_free_evap_part2_2000_2500 \
    --frame-start 2000 \
    --frame-end 2025
```

Restrict maximum fringe:

```bash
./run_all.sh \
    --input-dir radius_spot1_free_evap_part2_2000_2500 \
    --max-fringe 3
```

This uses p-0 through p-3 inclusive and computes:

```text
p-0_p-1
p-1_p-2
p-2_p-3
```

---

# Output Structure

```text
<input-dir>/ri/
├── p-0_p-1/
│   ├── ri_p-0_p-1_000000001.csv
│   ├── ri_p-0_p-1_000000002.csv
│   └── ...
├── p-1_p-2/
├── p-2_p-3/
└── ...
```

Each file contains:

```text
frame,Y,pos_pix,op_thi,sep,ref_in
```

---

# Mathematical Principle

The refractive index is obtained from the first sign change between the solutions of two consecutive parity equations.

For a valid solution:

```text
RI = n*
```

and

```text
sep = op_thi / (10 × RI)
```

Rows without a valid crossing are assigned NaN values.

---

# Troubleshooting

## No frame files found

Verify that:

```text
p2w/p-0/p2w_p-0_000000001.csv
```

exists.

## Need at least 2 fringe directories

The measured dataset must contain:

```text
p-0
p-1
```

For pair p-i_p-(i+1), calibration files must also exist for:

```text
p-i
p-(i+1)
p-(i+2)
```

---

# Citation

If you use InterfeRIOT in published work, please cite the associated paper ["Optical mapping of phases and phase boundaries in nanoconfined fluids"][ 	
https://doi.org/10.48550/arXiv.2606.24809] and indicate the repository version used for analysis.
