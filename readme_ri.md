# Refractive Index and Optical Thickness Computation Pipeline

## Overview

This workflow computes:

- Optical thickness (`op_thi`)
- Physical separation (`sep`)
- Refractive index (`ref_in`)

from wavelength measurements extracted from fringe positions.

The computation is performed using consecutive parity triplets:

- `(p-0, p-1, p-2)`
- `(p-1, p-2, p-3)`
- `(p-2, p-3, p-4)`
- ...

For each triplet and each Y position, the pipeline:

1. Reads calibration wavelengths.
2. Reads measured wavelength data.
3. Solves for refractive index by detecting sign changes between parity equations.
4. Computes optical thickness.
5. Computes physical separation.
6. Writes one CSV per `(triplet, Y)` pair.

---

# Directory Structure

The scripts are intended to be executed from the project root:

```text
project_root/
├── calibration_p/
│   └── p2w/
│       ├── p-0/
│       ├── p-1/
│       ├── p-2/
│       └── ...
│
├── radius_spot1_free_evap_part2_2000_2500/
│   └── p2w/
│       ├── p-0/
│       ├── p-1/
│       ├── p-2/
│       └── p-3/
│
├── run_all.sh
├── run_triplets.sh
├── run_one_triplet.sh
└── ri_ot.py
```

---

# Calibration Data

Calibration files must be stored in:

```text
calibration_p/p2w/p-i/
```

Example:

```text
calibration_p/p2w/p-0/mean_p-0.csv
calibration_p/p2w/p-1/mean_p-1.csv
calibration_p/p2w/p-2/mean_p-2.csv
```

The script uses the mean value of the third column (`pos_lambda`) as the calibration wavelength.

---

# Measured Data

Measured wavelength files must be stored in:

```text
<input-dir>/p2w/p-i/
```

Example:

```text
radius_spot1_free_evap_part2_2000_2500/p2w/p-0/p2w_p-0_1050.csv
radius_spot1_free_evap_part2_2000_2500/p2w/p-1/p2w_p-1_1050.csv
```

The numeric suffix is interpreted as the Y position.

Example:

```text
p2w_p-0_1050.csv
```

corresponds to:

```text
Y = 1050
```

Input CSV files must contain:

```text
frame,pos_pix,pos_lambda
```

---

# Output Structure

Results are automatically written to:

```text
<input-dir>/ri/
```

Example:

```text
radius_spot1_free_evap_part2_2000_2500/
└── ri/
    ├── p-0_p-1/
    │   ├── ri_p-0_p-1_1050.csv
    │   ├── ri_p-0_p-1_1051.csv
    │   └── ...
    │
    ├── p-1_p-2/
    │   ├── ri_p-1_p-2_1050.csv
    │   └── ...
    │
    └── p-2_p-3/
```

Each output CSV contains:

```text
frame
pos_pix
op_thi
sep
ref_in
```

---

# Running All Y Positions

Process all detected Y values:

```bash
./run_all.sh \
    --input-dir radius_spot1_free_evap_part2_2000_2500
```

---

# Restricting the Y Range

```bash
./run_all.sh \
    --input-dir radius_spot1_free_evap_part2_2000_2500 \
    --y-start 1050 \
    --y-end 1150
```

Only Y positions satisfying:

```text
1050 <= Y <= 1150
```

are processed.

---

# Restricting the Frame Range

```bash
./run_all.sh \
    --input-dir radius_spot1_free_evap_part2_2000_2500 \
    --frame-start 2000 \
    --frame-end 2025
```

Only frames satisfying:

```text
2000 <= frame <= 2025
```

are processed.

---

# Parallel Processing

```bash
./run_all.sh \
    --input-dir radius_spot1_free_evap_part2_2000_2500 \
    --jobs 18
```

This launches up to 18 concurrent workers.

---

# Refractive Index Search Grid

The refractive index search grid is:

```python
np.arange(mul_start, mul_stop, mul_step)
```

Default values:

```text
mul_start = 0.5
mul_stop  = 1.5
mul_step  = 0.001
```

Custom example:

```bash
./run_all.sh \
    --input-dir radius_spot1_free_evap_part2_2000_2500 \
    --mul-start 1.0 \
    --mul-stop 2.0 \
    --mul-step 0.0005
```

---

# Complete Example

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

This command:

- processes Y positions from 1050 to 1150,
- processes frames from 2000 to 2025,
- searches refractive indices between 0.5 and 1.5,
- uses 18 parallel workers,
- writes output into `<input-dir>/ri/`.

---

# Processing a Single Y Position

```bash
./run_triplets.sh \
    --input-dir radius_spot1_free_evap_part2_2000_2500 \
    --Y 1100 \
    --jobs 18
```

This processes all parity triplets for a single Y value.

---

# Mathematical Method

For each frame:

1. Generate a grid of candidate refractive indices.
2. Evaluate the parity equation for `(p-i, p-i+1)`.
3. Evaluate the parity equation for `(p-i+1, p-i+2)`.
4. Compute the difference between both solutions.
5. Detect the first sign change in the refractive-index grid.
6. Select the refractive index corresponding to the first crossing.
7. Compute optical thickness.
8. Compute separation:

```text
sep = op_thi / (10 * ref_in)
```

Frames with no sign change are assigned NaN values.

---

# Common Errors

## No Y files found

```text
No Y files found under <input-dir>/p2w/p-0
```

Check that files are named:

```text
p2w_p-0_<Y>.csv
```

and exist inside `p-0`.

---

## Need at least 3 parity directories

```text
Need at least 3 parity directories under <input-dir>/p2w
```

At minimum:

```text
p-0
p-1
p-2
```

must exist.

---

## No measured p2w file found

```text
No measured p2w file found for p-i, Y
```

The requested Y value is missing from one or more parity directories.

---

## No frames left after applying frame range

```text
No frames left for p-i/Y after applying frame range
```

The chosen frame interval does not overlap the available data.

---

# Notes

The current version of `run_all.sh` should contain only the corrected Y-detection logic for filenames of the form:

```text
p2w_p-0_1050.csv
```

If an older Y-detection block looking for `Y1050.csv` remains in the script, remove it to avoid filtering errors.
