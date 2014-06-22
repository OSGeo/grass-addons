#!/usr/bin/env python

"""
MODULE:    r.valley.bottom

AUTHOR(S): Helmut Kudrnovsky <alectoria AT gmx at>

PURPOSE:   Calculates Multi-resolution Valley Bottom Flatness (MrVBF) index
           Index is inspired by 
           John C. Gallant and Trevor I. Dowling 2003.
           A multiresolution index of valley bottom flatness for mapping depositional areas.
           WATER RESOURCES RESEARCH, VOL. 39, NO. 12, 1347, doi:10.1029/2002WR001426, 2003

COPYRIGHT: (C) 2014 by the GRASS Development Team

           This program is free software under the GNU General Public
           License (>=v2). Read the file COPYING that comes with GRASS
           for details.
"""

#%module
#% description: Calculation of Multi-resolution Valley Bottom Flatness (MrVBF) index
#% keywords: raster
#% keywords: terrain
#%end

#%option G_OPT_R_ELEV
#% key: elevation
#% description: Name of elevation raster map 
#% required: yes
#%end

import sys
import os
import grass.script as grass
import math

if not os.environ.has_key("GISBASE"):
    grass.message( "You must be in GRASS GIS to run this program." )
    sys.exit(1)

def main():
    r_elevation = options['elevation'].split('@')[0] # elevation raster
    r_slope_degree = r_elevation+'_slope_degree' # slope (percent) step 1

	##################################################################################
	# Region settings	
    current_region = grass.region()
    Yres_base = current_region['nsres']
    Xres_base = current_region['ewres']
    grass.message( "Finest scale calculations" )
    grass.message( "Original resolution: %s x %s" % (Xres_base, Yres_base))
    grass.run_command('g.region', flags = 'p', save = "base_region_MrVBF", overwrite = True)

	# Region settings step 3: resolution 3 x base resolution

    Yres_step3 = Yres_base * 3
    Xres_step3 = Xres_base * 3

	# Region settings step 4: resolution 4 x Xres_step3

    Yres_step4 = Yres_step3 * 3
    Xres_step4 = Xres_step3 * 3	
	
	##################################################################################	
	# Step 1 (S1)	
	# Finest-Scale Step		
    # Calculation of slope step 1
	# 100 * tan (slope in degree)
    grass.message( "----" )
    grass.message( "Step 1: Calculation of slope" )
    grass.message( "..." )	
    grass.run_command('r.slope.aspect', elevation = r_elevation,
                                     slope = r_slope_degree, 
                                     format = "degrees",
                                     precision = "DCELL",
                                     zfactor = 1.0,
                                     overwrite = True)

    grass.message( "..." )
									 
    grass.mapcalc("$outmap = 100 * tan($slope) ",
                                     outmap = "r_slope_step1", 
                                     slope = r_slope_degree)									 

    grass.message( "..." )									 
									 
    grass.run_command("g.remove", rast = r_slope_degree,
                                     quiet = True)									 
    grass.message( "Step 1: Calculation of slope done." )
    grass.message( "----" )

    # Calculation of flatness 1 (0 to 1)
	# Flatness F1 = 1 / (1 + pow ((slope / 16), 4)
    grass.message( "Step 1: Calculation of flatness F1" )
    grass.message( "..." )	
    grass.mapcalc("F1 = 1.0 / (1.0 + pow( ( $slope / 16.0 ) ,4 ) )", 
                                     slope = "r_slope_step1")

    grass.message( "Step 1: Calculation of flatness F1 done." )
    grass.message( "----" )

    # Calculation of elevation percentile PCTL1 step 1
	# elevation percentile: ratio of the number of points of lower
	# elevation to the total number of points in the surrounding region
	# elevation of percentile step 1: radius of 3 cells
    grass.message( "Step 1: Calculation of elevation percentile PCTL1" )
    grass.message( "..." )
    grass.mapcalc("elevation_step1 = $r_elevation", 
                                     r_elevation = r_elevation)
	
    offsets = [d
         for j in xrange(1,3+1)
         for i in [j,-j]
         for d in [(i,0),(0,i),(i,i),(i,-i)]]	

    grass.message( "..." )
		 
    terms = ["(elevation_step1[%d,%d] < elevation_step1)" % d
         for d in offsets]	
		 
    expr1 = "PCTL1 = (100.0 / 24.0) * (%s)" % " + ".join(terms)
	
    grass.mapcalc( expr1 )
	
    grass.message( "Step 1: Calculation of elevation percentile PCTL1 done" )
    grass.message( "----" )
    
    # Elevation percentile is transformed to a local lowness value using
    # equation (1) with t = 0.4 and p = 3, and then combined with
    # flatness F1 to produce the preliminary valley flatness index
    # (PVF1) for the first step:
    grass.message( "Step 1: Calculation of preliminary valley flatness index PVF1" )	
    grass.message( "..." )
	
    grass.mapcalc("PVF1 = F1 * (1.0 / (1.0 + pow ( ( PCTL1 / 0.4 ), 3 ) ) )")

    grass.message( "Step 1: Calculation of preliminary valley flatness index PVF1 done." )		
    grass.message( "----" )

    # Calculation of the valley flatness step 1 VF1
	# larger values of VF1 indicate increasing valley bottom character
	# with values less than 0.5 considered not to be in valley bottoms
    grass.message( "Step 1: Calculation of valley flatness VF1" )
    grass.message( "..." )
	
    grass.mapcalc("VF1 = 1 - (1.0 / (1.0 + pow ( ( PVF1 / 0.3 ), 4 ) ) )")	
	
    grass.message( "Step 1: Calculation of valley flatness VF1 done." )	
    grass.message( "----" )

	##################################################################################
	# Step 2 (S2)	
	# base scale resolution		
    grass.message( "Step 2" )
    grass.message( "base resolution: %s x %s" % (Xres_base, Yres_base))
    grass.message( "----" )
	
    # Calculation of flatness 1 (0 to 1)
    # The second step commences the same way with the
    # original DEM at its base resolution, using a slope threshold ts,2 half of ts,1:
	# Flatness F2 = 1 / (1 + pow ((slope / 8), 4)
    grass.message( "Step 2: Calculation of flatness F2" )
    grass.message( "..." )	
    grass.mapcalc("F2 = 1.0 / (1.0 + pow( ( $slope / 8.0 ) ,4 ) )", 
                                     slope = "r_slope_step1")	
    grass.message( "Step 2: Calculation of flatness F2 done" )
    grass.message( "----" )

    # Calculation of elevation percentile PCTL2 step 2
	# elevation of percentile step 2: radius of 3 cells
    grass.message( "Step 2: Calculation of elevation percentile PCTL2" )
    grass.message( "..." )
	
    offsets2 = [d
         for j in xrange(1,6+1)
         for i in [j,-j]
         for d in [(i,0),(0,i),(i,i),(i,-i)]]	

    grass.message( "..." )
		 
    terms2 = ["(elevation_step1[%d,%d] < elevation_step1)" % d
         for d in offsets2]	
		 
    expr2 = "PCTL2 = (100.0 / 48.0) * (%s)" % " + ".join(terms2)
	
    grass.mapcalc( expr2 )
    grass.run_command("g.remove", rast = "elevation_step1",
                                     quiet = True)
	
    grass.message( "Step 2: Calculation of elevation percentile PCTL2 done" )
    grass.message( "----" )

    # PVF2 for step 2:
    grass.message( "Step 2: Calculation of preliminary valley flatness index PVF2" )	
    grass.message( "..." )
	
    grass.mapcalc("PVF2 = F2 * (1.0 / (1.0 + pow ( ( PCTL2 / 0.4 ), 3 ) ) )")

    grass.message( "Step 2: Calculation of preliminary valley flatness index PVF2 done." )		
    grass.message( "----" )

    # Calculation of the valley flatness step 2 VF2
    grass.message( "Step 2: Calculation of valley flatness VF2" )
    grass.message( "..." )
	
    grass.mapcalc("VF2 = 1 - (1.0 / (1.0 + pow ( ( PVF2 / 0.3 ), 4 ) ) )")	
	
    grass.message( "Step 2: Calculation of valley flatness VF2 done." )	
    grass.message( "----" )
	
    # Calculation of weight W2
    grass.message( "Step 2: Calculation of weight W2" )
    grass.message( "..." )

    grass.mapcalc("W2 = 1 - (1.0 / (1.0 + pow ( ( VF2 / 0.4 ), 6.68 ) ) )")	
	
    grass.message( "Step 2: Calculation of weight W2 done." )	
    grass.message( "----" )
	
    # Calculation of MRVBF2	
    grass.message( "Step 2: Calculation of MRVBF2" )
    grass.message( "..." )

    grass.mapcalc("MRVBF2 = (W2 * (1 + VF2)) + ((1 - W2) * VF1)")	
	
    grass.message( "Step 2: Calculation of MRVBF2 done." )	
    grass.message( "----" )

    # Calculation of combined flatness index CF2
    grass.message( "Step 2: Calculation  of combined flatness index CF2" )
    grass.message( "..." )

    grass.mapcalc("CF2 = F1 * F2")
	
    grass.message( "Step 2: Calculation  of combined flatness index CF2 done." )	
    grass.message( "----" )

    # step 2 finished
    grass.message( "Step 2 calculations done." )	
    grass.message( "----" )

	##################################################################################	
    # remaining steps
    grass.message( "two remaining steps" )	
    grass.message( "----" )	
	
	##################################################################################
	# Step 3	
    grass.message( "Step 3" )
	# DEM smoothing 11 x 11 windows with Gaussian smoothing kernel (sigma) 3 x 3 -> change resolution (3 x base resolution) -> calculations
    grass.message( "----" )	
	# DEM smoothing
    grass.message( "Step 3: DEM smoothing 11 x 11 windows with Gaussian smoothing kernel (sigma) 3" )	
    grass.message( "..." )	
    grass.run_command('r.neighbors',  input = r_elevation, 
                                    output = "DEM_smoothed_step3", 
                                    size = 11, 
                                    gauss=3)
	
    grass.message( "Step 3 DEM smoothing 11 x 11 windows with Gaussian smoothing kernel (sigma) 3 done." )		
    grass.message( "----" )	

	# Calculate slope step 3
    grass.message( "Step 3: Calculation of slope" )
    grass.message( "..." )	
    grass.run_command('r.slope.aspect', elevation = "DEM_smoothed_step3",
                                     slope = "DEM_smoothed_step3_slope_degree", 
                                     format = "degrees",
                                     precision = "DCELL",
                                     zfactor = 1.0,
                                     overwrite = True)

    grass.message( "..." )
									 
    grass.mapcalc("$outmap = 100 * tan($slope) ",
                                     outmap = "r_slope_step3", 
                                     slope = "DEM_smoothed_step3_slope_degree")

    grass.message( "..." )									 
									 
    grass.run_command('g.remove', rast = "DEM_smoothed_step3_slope_degree",
                                     quiet = True)									 
    grass.message( "Step 3: Calculation of slope done." )
    grass.message( "----" )

	# change resolution
    grass.message( "Step 3: change to resolution to 3 x base resolution" )
    grass.run_command('g.region', res = Xres_step3, 
                                    flags = 'a')

    current_region_step3 = grass.region()
    Y_step3 = current_region_step3['nsres']
    X_step3 = current_region_step3['ewres']
    grass.message( "Resolution step 3: %s x %s" % (X_step3, Y_step3))	
    grass.message( "----" )

	# coarsening DEM to resolution step 3 and calculate PCTL3 step 3

    grass.message( "Step 3: Calculation of elevation percentile PCTL3" )
    grass.message( "..." )
    grass.mapcalc("DEM_smoothed_step3_coarsed = DEM_smoothed_step3") 

    offsets3 = [d
         for j in xrange(1,6+1)
         for i in [j,-j]
         for d in [(i,0),(0,i),(i,i),(i,-i)]]	

    grass.message( "..." )
		 
    terms3 = ["(DEM_smoothed_step3_coarsed[%d,%d] < DEM_smoothed_step3_coarsed)" % d
         for d in offsets3]	
		 
    expr3 = "PCTL3 = (100.0 / 48.0) * (%s)" % " + ".join(terms3)
	
    grass.mapcalc( expr3 )

    grass.message( "Step 3: Calculation of elevation percentile PCTL3 done." )
    grass.message( "----" )									 

	# switch back to base resolution
    grass.message( "Step 3: switch back to base resolution." )

    grass.run_command('g.region', rast = r_elevation, 
                                    align = r_elevation,                                    
                                    flags = 'a')
    current_region_step3_switched_back = grass.region()
    Y_step3_switched_back = current_region_step3_switched_back['nsres']
    X_step3_switched_back = current_region_step3_switched_back['ewres']
    grass.message( "Resolution step 3: %s x %s" % (X_step3_switched_back, Y_step3_switched_back))	
    grass.message( "----" )	

	# resample/refine PCTL3 to base resolution
    grass.message( "Step 3: refine PCTL3 to base resolution" )
    grass.message( "..." )

    grass.run_command('r.resamp.interp', input = "PCTL3", 
                                     output = "PCTL3_refined_base_resolution", 
                                     method = "bilinear")
	
    grass.message( "Step 3: refine PCTL3 to base resolution done." )	
    grass.message( "----" )

	# calculate flatness F3 at the base resolution
    grass.message( "Step 3: calculate F3 at base resolution" )
    grass.message( "..." )

    grass.mapcalc("F3 = 1.0 / (1.0 + pow( ( $slope / 8.0 ) ,4 ) )", 
                                     slope = "r_slope_step3")

    grass.message( "Step 3: calculate F3 at base resolution done." )
    grass.message( "----" )

	# calculate accumulated combined flatness CF3 at the base resolution
    grass.message( "Step 3: calculate combined flatness CF3 at base resolution" )
    grass.message( "..." )

    grass.mapcalc("CF3 = CF2 * F3")
	
    grass.message( "Step 3: calculate combined flatness CF3 at base resolution done." )
    grass.message( "----" )	

	# calculate preliminary valley flatness index PVF3 at the base resolution
    grass.message( "Step 3: calculate preliminary valley flatness index PVF3 at base resolution" )
    grass.message( "..." )

    grass.mapcalc("PVF3 = CF3 * (1.0 / (1.0 + pow ( ( PCTL3_refined_base_resolution / 0.4 ), 3 ) ) )")
	
    grass.message( "Step 3: calculate preliminary valley flatness index PVF3 at base resolution done." )
    grass.message( "----" )	

	# calculate valley flatness index VF3
    grass.message( "Step 3: calculate valley flatness index VF3 at base resolution" )
    grass.message( "..." )

    grass.mapcalc("VF3 = 1 - (1.0 / (1.0 + pow ( ( PVF3 / 0.3 ), 4 ) ) )")	
	
    grass.message( "Step 3: calculate valley flatness index VF3 at base resolution done." )
    grass.message( "----" )	

    # Calculation of weight W3
    grass.message( "Step 3: Calculation of weight W3" )
    grass.message( "..." )
    
    p3 = (math.log10((3 - 0.5) / 0.1)) / math.log10(1.5)
	
    grass.mapcalc("W3 = 1 - (1.0 / (1.0 + pow ( ( VF3 / 0.4 ), $p ) ) )", p = p3)	
	
    grass.message( "Step 3: Calculation of weight W3 done." )	
    grass.message( "----" )

    # Calculation of MRVBF3	
    grass.message( "Step 3: Calculation of MRVBF3" )
    grass.message( "..." )

    grass.mapcalc("MRVBF3 = (W3 * (3 - 1 + VF3)) + ((1 - W3) * MRVBF2)")	
	
    grass.message( "Step 3: Calculation of MRVBF3 done." )	
    grass.message( "----" )
	
	##################################################################################
	# Step 4	
    grass.message( "Step 4" )

	# change resolution
    grass.message( "Step 4: change to resolution of step 3" )
    grass.run_command('g.region', res = Xres_step3, 
                                    flags = 'a')

    current_region_step3 = grass.region()
    Y_step3 = current_region_step3['nsres']
    X_step3 = current_region_step3['ewres']
    grass.message( "Resolution 1 for step 4: %s x %s" % (X_step3, Y_step3))	
    grass.message( "----" )

	# DEM smoothing 11 x 11 windows with Gaussian smoothing kernel (sigma) 3 x 3 -> change resolution (3 x base resolution) -> calculations
    grass.message( "----" )	
	# DEM smoothing
    grass.message( "Step 4: DEM smoothing 11 x 11 windows with Gaussian smoothing kernel (sigma) 3" )	
    grass.message( "..." )	
    grass.run_command('r.neighbors',  input = "DEM_smoothed_step3_coarsed", 
                                    output = "DEM_smoothed_step4", 
                                    size = 11, 
                                    gauss=3)
	
    grass.message( "Step 4 DEM smoothing 11 x 11 windows with Gaussian smoothing kernel (sigma) 3 done." )		
    grass.message( "----" )	

	# Calculate slope step 4
    grass.message( "Step 4: Calculation of slope" )
    grass.message( "..." )	
    grass.run_command('r.slope.aspect', elevation = "DEM_smoothed_step4",
                                     slope = "DEM_smoothed_step4_slope_degree", 
                                     format = "degrees",
                                     precision = "DCELL",
                                     zfactor = 1.0,
                                     overwrite = True)

    grass.message( "..." )
									 
    grass.mapcalc("$outmap = 100 * tan($slope) ",
                                     outmap = "r_slope_step4", 
                                     slope = "DEM_smoothed_step4_slope_degree")

    grass.message( "..." )									 
									 
    grass.run_command('g.remove', rast = "DEM_smoothed_step4_slope_degree",
                                     quiet = True)									 
    grass.message( "Step 4: Calculation of slope done." )
    grass.message( "----" )

	# change resolution
    grass.message( "Step 4: change to resolution to 3 x 3 step 3 resolution" )
    grass.run_command('g.region', res = Xres_step4, 
                                    flags = 'a')

    current_region_step4 = grass.region()
    Y_step4 = current_region_step4['nsres']
    X_step4 = current_region_step4['ewres']
    grass.message( "Resolution step 3: %s x %s" % (X_step4, Y_step4))	
    grass.message( "----" )

	# coarsening DEM to resolution step 4 and calculate PCTL step 4

    grass.message( "Step 4: Calculation of elevation percentile PCTL4" )
    grass.message( "..." )
    grass.mapcalc("DEM_smoothed_step4_coarsed = DEM_smoothed_step4") 

    offsets4 = [d
         for j in xrange(1,6+1)
         for i in [j,-j]
         for d in [(i,0),(0,i),(i,i),(i,-i)]]	

    grass.message( "..." )
		 
    terms4 = ["(DEM_smoothed_step4_coarsed[%d,%d] < DEM_smoothed_step4_coarsed)" % d
         for d in offsets4]	
		 
    expr4 = "PCTL4 = (100.0 / 48.0) * (%s)" % " + ".join(terms4)
	
    grass.mapcalc( expr4 )

    grass.message( "Step 4: Calculation of elevation percentile PCTL4 done." )
    grass.message( "----" )									 

	# switch back to base resolution
    grass.message( "Step 4: switch back to base resolution." )

    grass.run_command('g.region', rast = r_elevation, 
                                    align = r_elevation,                                    
                                    flags = 'a')
    current_region_step4_switched_back = grass.region()
    Y_step4_switched_back = current_region_step4_switched_back['nsres']
    X_step4_switched_back = current_region_step4_switched_back['ewres']
    grass.message( "Resolution step 4: %s x %s" % (X_step4_switched_back, Y_step4_switched_back))	
    grass.message( "----" )	

	# resample/refine PCTL4 to base resolution
    grass.message( "Step 4: refine PCTL4 to base resolution" )
    grass.message( "..." )

    grass.run_command('r.resamp.interp', input = "PCTL4", 
                                     output = "PCTL4_refined_base_resolution", 
                                     method = "bilinear")
	
    grass.message( "Step 4: refine PCTL4 to base resolution done." )	
    grass.message( "----" )

	# calculate flatness F4 at the base resolution
    grass.message( "Step 4: calculate F4 at base resolution" )
    grass.message( "..." )

    grass.run_command('r.resamp.interp', input = "r_slope_step4", 
                                     output = "r_slope_step4_refined_base_resolution", 
                                     method = "bilinear")	
	
    grass.mapcalc("F4 = 1.0 / (1.0 + pow( ( $slope / 4.0 ) ,4 ) )", 
                                     slope = "r_slope_step4_refined_base_resolution")

    grass.message( "Step 4: calculate F4 at base resolution done." )
    grass.message( "----" )

	# calculate accumulated combined flatness CF3 at the base resolution
    grass.message( "Step 4: calculate combined flatness CF4 at base resolution" )
    grass.message( "..." )

    grass.mapcalc("CF4 = CF3 * F4")
	
    grass.message( "Step 4: calculate combined flatness CF4 at base resolution done." )
    grass.message( "----" )	

	# calculate preliminary valley flatness index PVF3 at the base resolution
    grass.message( "Step 4: calculate preliminary valley flatness index PVF4 at base resolution" )
    grass.message( "..." )

    grass.mapcalc("PVF4 = CF4 * (1.0 / (1.0 + pow ( ( PCTL4_refined_base_resolution / 0.4 ), 3 ) ) )")
	
    grass.message( "Step 4: calculate preliminary valley flatness index PVF4 at base resolution done." )
    grass.message( "----" )	

	# calculate valley flatness index VF4
    grass.message( "Step 4: calculate valley flatness index VF4 at base resolution" )
    grass.message( "..." )

    grass.mapcalc("VF4 = 1 - (1.0 / (1.0 + pow ( ( PVF4 / 0.3 ), 4 ) ) )")	
	
    grass.message( "Step 4: calculate valley flatness index VF4 at base resolution done." )
    grass.message( "----" )	

    # Calculation of weight W4
    grass.message( "Step 4: Calculation of weight W4" )
    grass.message( "..." )
    
    p4 = (math.log10((4 - 0.5) / 0.1)) / math.log10(1.5)
	
    grass.mapcalc("W4 = 1 - (1.0 / (1.0 + pow ( ( VF4 / 0.4 ), $p ) ) )", p = p3)	
	
    grass.message( "Step 4: Calculation of weight W4 done." )	
    grass.message( "----" )

    # Calculation of MRVBF4	
    grass.message( "Step 4: Calculation of MRVBF4" )
    grass.message( "..." )

    grass.mapcalc("MRVBF4 = (W4 * (3 - 1 + VF4)) + ((1 - W4) * MRVBF3)")	
	
    grass.message( "Step 4: Calculation of MRVBF4 done." )	
    grass.message( "----" )
	
	
	
if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
