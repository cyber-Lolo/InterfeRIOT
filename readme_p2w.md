<Detailed route to calibrate the SFB interferogram, detect the fringes, anaylyse the refractive index (RI), and get the force profiles (FP)>


# Requirements

Have MMVII installed
Have Python3 

# DATA & FILE OVERVIEW
 
 /main/
--/calibration_gy/Retiga.000000001.tif : the green and two yellow mercury rays
--[OPTIONAL] /calibration_g /Retiga.000000001.tif : the green mercury ray
--/calibration_p/Retiga.000000001.tif: the positions of the p, p-1, p-2 fringes in air (minimal amount if RI), or p, p-1 if (minimal amount if FP)
--[OPTIONAL] /video /Retiga.*tif: the video to analyse, with minimum p,p-1 fringes in view (if RI),  minimum p if (FP) 

-- /mean_x.py
--/extractfranges.sh


# Rays and fringes detection using MMVII
Visualize your data prior to any command line to choose the arguments accordingly

- MMVII ExtractFranges HELP
  * [Name=SigCurv] double :: Sima for smoothig curve ,[Default=0]
  * [Name=IntY] cPtxd<int,2> :: Interval for Y ,[Default=[900,1280]]
  * [Name=NbIt] int :: Number of iter initial smoothing ,[Default=5]
  * [Name=DoVisu] bool :: Generate Visualisation ? ,[Default=false]
  * [Name=MinWidth] double :: Minimal witdh, general case ,[Default=200]
  * [Name=BorderMinWidth] double :: Minimal witdh for border ,[Default=300]
  * [Name=MinHeightBorderRight] double :: Minimal Heitgh for right border ,[Default=200]
  
 - MMVII ExtractFranges Retiga_000000001.tif 
 - MMVII ExtractFranges Retiga_.*.tif
  
## Rays 

In /main/calibration_gy  and or main/calibration_g

 <MMVII ExtractFranges Retiga_000000001.tif "IntY=[980,1220]" MinWidth=0 BorderMinWidth=0 MinHeightBorderRight=0>
 
outputs in: 
/main/calibration_gy/MMVII-PhgrProj/Reports/ExtractFranges/Frange-MMVII-Retiga_000000001.csv
/main/calibration_g/MMVII-PhgrProj/Reports/ExtractFranges/Frange-MMVII-Retiga_000000001.csv

## Fringes 
 
 In main/calibration_p
 
 <MMVII ExtractFranges Retiga_000000001.tif "IntY=[980,1220]">
 
 outputs in: 
/main/calibration_p/MMVII-PhgrProj/Reports/ExtractFranges/Frange-MMVII-Retiga_000000001.csv

## Video

<source extractfranges.sh>
<cd video>
<run_toto_parallel -j 16 --arg 'IntY=[980,1220]'> replace -j X with number of cores

## Mean positions of Mercury

<python3 mean_x.py calibration_gy 1100 20>
<python3 mean_x.py calibration_g 1100 20>


# Physical conversions

## Pixel to wavelength

### Fringes

<bash p2w_para.sh ./calibration_p 1 1>
<python3 merge_p2w.py ./calibration_p>

### Video

scripts are p2w.py, called in p2w_para.sh
then merge_p2w.py, used to reorganise the outputs of p2w_para.sh that are in a tmp
```bash
 p2w_para.sh ./video 100 500        # jobs 100 to 500, 18 cores
 ```
or 
```bashbash p2w_para.sh ./video 0 9999 8       # jobs 0 to 9999, 8 cores'
```

```bash
python3 merge_p2w.py ./video 
```

output : 
./video/p2w/p-0
./video/p2w/p-1
./video/p2w/p-2
./video/p2w/p-3


and for each ./video/p2w/p-k/
one csv per line (Y coordinate)
* example : 
p2w_p-3_981.csv 
frame	pos_pix	pos_lambda
2000	2063.3145232159600	5912.659484314660
2001	2062.8583616757800	5912.461489560370
2002	2063.535122694070	5912.755234472480
2003	2063.4258275399900	5912.70779542892
2004	2062.5827503424000	5912.341861767530
2005	2062.6962762405200	5912.391137145490

Tracks through the frames, the lateral (x) position in pix and wavelength (angstrom), of the p-3 fringe, on the 981 th line

## Get Mean

Between center and width
here center 1100 and width 20

```bash
python3 mean_p2w.py ./calibration_p 1100 20

python3 mean_p2w.py ./radius_spot1_free_evap_part2_2000-2500 1100 20 
```

output : 
./video/p2w/p-0
./video/p2w/p-1
./video/p2w/p-2
./video/p2w/p-3


and for each ./video/p2w/p-k/
one csv
* example : 
mean_p-3_1100_20.csv 
frame	pos_pix	pos_lambda
2000	217.67048765697200	5111.56643911222
2001	218.03613771583600	5111.725147787070
2002	217.8572449190040	5111.647500216570
2003	217.88586341355800	5111.659921938480
2004	217.95203674355800	5111.688644158700
2005	217.6306089151630	5111.549129933360







