Data start to be usable if their stamp is ~>2000 (evaporation front starts to enter field of views)

Times.txt #Time stamps associated with all the images

./some_raw_images/


#Contains some raw SFB interferograms if you want to perform the analysis described in the paper, and learn to use the code

./plots_all/

#Wetting angle, surface of evaporation, volume of the droplet vs waist height:

radius_spot1_free_evap_part2_angles_vs_waist_raw.pdf
radius_spot1_free_evap_part2_surface_vs_waist_raw.pdf
radius_spot1_free_evap_part2_volume_vs_waist_raw.pdf

#Smoothed data because discrete derivation (from flow calculation) makes it quite noisy:

radius_spot1_free_evap_part2_flow_vs_surface_smoothed.pdf
radius_spot1_free_evap_part2_flow_vs_waist_smoothed.pdf
radius_spot1_free_evap_part2_vol-v-w_flow-v-s_combined_smoothed.png

./csv_all/

    /n_D/ #contains all the n(D) profiles for each fram
    /e_D_x/ #contains e_ff, and the mica surface coordinates i.e D, vs radial coordinates
    /anchor_points/# anchor points retained from e_eff (wetting part and waist, waist is the last point of each csv.)	
	
	#Volume vs time, both catenoid and quartic		
    quartic_volume.csv
    catenoid_volume.csv
    #Volume,time, surface, flow, both catenoid and quartic, smoothed due to flow calculation
    catenoid_flow_smooth.csv	
    quartic_flow_smooth.csv