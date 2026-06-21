# InterfeRIOT
## Interferometric Refractive Index and Optical Thickness Analysis from Surface Force Balance Fringe Data

InterfeRIOT is a complete workflow for processing Surface Force Balance (SFB) interferograms, from raw images to calibrated wavelengths, refractive index determination, optical thickness reconstruction, and separation analysis.

The repository combines:

- MMVII-based fringe detection
- Mercury-line wavelength calibration
- Pixel-to-wavelength conversion
- Fringe tracking through time
- Refractive index (RI) estimation
- Optical thickness (OT) computation
- Separation profile extraction
- Batch processing tools for large video datasets

---

# Features

- Automated fringe extraction using MMVII
- Support for calibration using mercury emission lines
- Parallel processing of large image sequences
- Conversion from fringe position (pixels) to wavelength (Å)
- RI estimation from three-layer interferometry
- Optical thickness and separation reconstruction
- Processing of all Y positions or selected Y ranges
- Frame-range filtering for targeted analysis

---

# Requirements

## Software

- [MMVII](https://github.com/micmac-V2/MMVII)
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
Fringe tracking through time
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
Separation / force analysis
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
├── merge_p2w.py
├── mean_p2w.py
│
├── run_all.sh
├── run_triplets.sh
├── run_one_triplet.sh
├── p2w_thickness.py
│
└── README.md
```

---

# Input Data

## Mercury Calibration

### Green + Yellow Mercury Rays

```text
calibration_gy/
└── Retiga.000000001.tif
```

### Green Mercury Ray Only (Optional)

```text
calibration_g/
└── Retiga.000000001.tif
```

## Fringe Calibration

```text
calibration_p/
└── Retiga.000000001.tif
```

For RI analysis, the image should contain at least:

```text
p
p−1
p−2
```

fringes.

## Video Data

```text
video/
└── Retiga.*.tif
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

Outputs:

```text
calibration_gy/MMVII-PhgrProj/Reports/ExtractFranges/
calibration_g/MMVII-PhgrProj/Reports/ExtractFranges/
```

## Fringe Calibration

```bash
MMVII ExtractFranges Retiga_000000001.tif \
    "IntY=[980,1220]"
```

Output:

```text
calibration_p/MMVII-PhgrProj/Reports/ExtractFranges/
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
- 20 = averaging width

---

# Pixel-to-Wavelength Conversion

## Calibration Fringes

```bash
p2w_para.sh ./calibration_p 1 1
python3 merge_p2w.py ./calibration_p
```

## Video

```bash
p2w_para.sh ./video 0 9999 8
python3 merge_p2w.py ./video
```

Output:

```text
video/p2w/
├── p-0/
├── p-1/
├── p-2/
└── p-3/
```

Example file:

```text
p2w_p-3_981.csv
```

Columns:

```text
frame,pos_pix,pos_lambda
```

---

# Mean Wavelength Extraction

```bash
python3 mean_p2w.py ./calibration_p 1100 20

python3 mean_p2w.py \
    ./radius_spot1_free_evap_part2_2000_2500 \
    1100 20
```

Example output:

```text
mean_p-3_1100_20.csv
```

---

# Refractive Index and Optical Thickness Analysis

The algorithm uses consecutive parity triplets:

```text
(p-0,p-1,p-2)
(p-1,p-2,p-3)
(p-2,p-3,p-4)
...
```

For each frame:

1. Read calibration wavelengths.
2. Read measured wavelengths.
3. Generate a refractive-index search grid.
4. Evaluate parity equations.
5. Detect the first sign change.
6. Estimate refractive index.
7. Compute optical thickness.
8. Compute separation.

---

# Running the Analysis

## All Y Positions

```bash
./run_all.sh \
    --input-dir radius_spot1_free_evap_part2_2000_2500
```

## Single Y Position

```bash
./run_triplets.sh \
    --input-dir radius_spot1_free_evap_part2_2000_2500 \
    --Y 1100 \
    --jobs 18
```

## Full Example

```bash
./run_all.sh \
    --input-dir radius_spot1_free_evap_part2_2000_2500 \
    --jobs 18 \
    --mul-start 0.5 \
    --mul-stop 1.5 \
    --mul-step 0.001 \
    --y-start 1050 \
    --y-end 1150 \
    --frame-start 2000 \
    --frame-end 2025
```

---

# Output Structure

```text
<input-dir>/ri/
├── p-0_p-1/
│   ├── ri_p-0_p-1_1050.csv
│   └── ...
├── p-1_p-2/
└── p-2_p-3/
```

Each CSV contains:

```text
frame
pos_pix
op_thi
sep
ref_in
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

Frames without a valid crossing are assigned NaN values.

---

# Troubleshooting

## No Y files found

Verify that files are named:

```text
p2w_p-0_<Y>.csv
```

## Need at least 3 parity directories

The following must exist:

```text
p-0
p-1
p-2
```

## No measured p2w file found

A Y file is missing in one or more parity folders.

## No frames left after applying frame range

The selected frame interval does not overlap the available data.

---

# Citation

If you use InterfeRIOT in published work, please cite the associated Surface Force Balance methodology and indicate the repository version used for analysis.
