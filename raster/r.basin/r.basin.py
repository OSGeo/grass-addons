#!/usr/bin/env python

############################################################################
#
# MODULE:      r.basin.py
# AUTHOR(S):   Margherita Di Leo, Massimo Di Stefano
# PURPOSE:     Morphometric characterization of river basins
# COPYRIGHT:   (C) 2010 by the GRASS Development Team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################

#%module
#% description: Morphometric characterization of river basins
#% keywords: raster
#%end
#%option
#% key: map
#% type: string
#% gisprompt: old,raster,raster
#% key_desc: name
#% description: Name of elevation raster map 
#% required: yes
#%end
#%option
#% key: prefix
#% type: string
#% key_desc: output prefix
#% description: output prefix (must start with a letter)
#% required: yes
#%end
#%option
#% key: easting
#% type: double
#% key_desc: easting
#% description: east coordinate of outlet point (must belong to river network) 
#% required : yes
#%end
#%option
#% key: northing
#% type: double
#% key_desc: northing
#% description: north coordinate of outlet point (must belong to river network)
#% required : yes
#%end
#%option
#% key: threshold
#% type: double
#% key_desc: threshold
#% description: threshold
#% required : no
#%end
#%flag
#% key: a
#% description: Use default Threshold (1km^2)
#%END
#%flag
#% key: c
#% description: No maps output
#%END

import sys
import os
import grass.script as grass
import math
from numpy import array
from numpy import zeros

if not os.environ.has_key("GISBASE"):
    print "You must be in GRASS GIS to run this program."
    sys.exit(1)

def main():
    r_elevation = options['map'].split('@')[0] 
    mapname = options['map'].replace("@"," ")
    mapname = mapname.split()
    mapname[0] = mapname[0].replace(".","_")
    east = float(options['easting']) 
    north = float(options['northing'])
    autothreshold = flags['a']
    nomap = flags['c']
    prefix = options['prefix']+'_'+mapname[0]
    r_accumulation = prefix+'_accumulation'
    r_drainage = prefix+'_drainage'
    r_stream = prefix+'_stream'
    r_slope = prefix+'_slope'
    r_aspect = prefix+'_aspect'
    r_basin = prefix+'_basin'
    r_strahler = prefix+'_strahler'
    r_shreve = prefix+'_shreve'
    r_horton = prefix+'_horton'
    r_hack = prefix+'_hack'
    r_distance = prefix+'_distance'
    r_hillslope_distance = prefix+'_hillslope_distance'
    r_height_average = prefix+'_height_average'
    r_aspect_mod = prefix+'_aspect_mod'
    r_dtm_basin = prefix+'_dtm_basin'
    r_mainchannel = prefix+'_mainchannel'
    r_stream_e = prefix+'_stream_e'
    r_drainage_e = prefix+'_drainage_e'
    r_mask = prefix+'_mask'
    r_ord_1 = prefix+'_ord_1'
    r_average_hillslope = prefix+'_average_hillslope'
    r_mainchannel_dim = prefix+'_mainchannel_dim'
    r_outlet = prefix+'_r_outlet'
    v_outlet = prefix+'_v_outlet'
    v_basin = prefix+'_basin'
    v_centroid1 = prefix+'_centroid1'
    v_mainchannel = prefix+'_mainchannel'
    v_mainchannel_dim = prefix+'_mainchannel_dim'
    v_network = prefix+'_network'
    v_stream_e = prefix+'_stream_e'
    v_ord_1 = prefix+'_ord_1'
    grass.run_command('g.remove' , rast = 'MASK')

    # Managing flag
    if autothreshold :
        info_region = grass.read_command('g.region', flags = 'p', rast = '%s' % (r_elevation))
        dict_region = grass.parse_key_val(info_region, ':')
        resolution = float(dict_region['nsres'])
        th = 1000000 / (resolution**2)
        print 'threshold : ', th
    else :
        th = options['threshold']

    # Watershed SFD
    grass.run_command('r.watershed', elevation = r_elevation , threshold = th , accumulation = r_accumulation , drainage = r_drainage , stream = r_stream+'_nothin' , convergence = 5, flags = 'a')

    # Stream extraction
    grass.run_command('r.stream.extract', elevation = r_elevation, accumulation = r_accumulation, threshold = th, d8cut = 'infinity', mexp = 0, stream_rast = r_stream_e, stream_vect = v_stream_e, direction = r_drainage_e, flags ='-o')
    
    # Delineation of basin 
    grass.run_command('r.stream.basins', dir = r_drainage , basins = r_basin , coors = '%s,%s' % (east , north) )
    print "Delineation of basin done"
    
    # Backup and mask
    elevation_name = r_elevation = r_elevation.split('@')[0]
    grass.run_command('g.copy', rast = r_elevation+','+elevation_name+'_crop')	
    grass.run_command('r.mapcalculator', amap = r_basin , formula = '%s/%s' % (r_basin, r_basin) , outfile = r_mask, flags = '-o')
    grass.run_command('r.mapcalculator', amap = r_accumulation , formula = '%s*%s' % (r_accumulation, r_mask) , outfile = r_accumulation, flags = '-o')
    grass.run_command('r.mapcalculator', amap = r_drainage , formula = '%s*%s' % (r_drainage, r_mask) , outfile = r_drainage, flags = '-o')
    grass.run_command('r.mapcalculator', amap = r_stream+'_nothin' , formula = '%s*%s' % (r_stream+'_nothin', r_mask) , outfile = r_stream+'_nothin', flags = '-o')
    grass.run_command('r.mapcalculator', amap = r_elevation , formula = '%s*%s' % (r_elevation, r_mask) , outfile = r_elevation+'_crop', flags = '-o')
    grass.run_command('r.mapcalculator', amap = r_drainage_e , formula = '%s*%s' % (r_drainage_e, r_mask) , outfile = r_drainage_e, flags = '-o')
    grass.run_command('r.mapcalculator', amap = r_stream_e , formula = '%s*%s' % (r_stream_e, r_mask) , outfile = r_stream_e, flags = '-o')
    grass.run_command('r.thin', input = r_stream_e , output = r_stream_e+'_thin' )
    grass.run_command('r.to.vect', input = r_stream_e+'_thin' , output = v_network , feature = 'line' )
    
    # Creation of slope and aspect maps
    grass.run_command('r.slope.aspect', elevation = r_elevation+'_crop' , slope = r_slope , aspect = r_aspect )

    # Basin mask (vector)
    grass.run_command('r.to.vect', input = r_basin , output = v_basin , feature = 'area' )
    grass.run_command('v.to.db', map = v_basin , type = 'line,boundary' , layer = 1, qlayer = 1, option = 'perimeter' , units = 'kilometers', columns = 'cat', qcolumn = 'cat')
    
    # Creation of order maps: strahler, horton, hack, shreeve
    print 'creating', r_hack
    grass.run_command('r.stream.order', stream = r_stream_e , dir = r_drainage_e , strahler = r_strahler , shreve = r_shreve , horton = r_horton , hack = r_hack )
    
    # Distance to outlet
    grass.write_command('v.in.ascii', output = v_outlet, stdin = "%s|%s|9999"  % (east, north) )
    grass.run_command('v.to.rast', input = v_outlet, output = r_outlet , use = 'cat' , type = 'point,line,area' , layer = 1 , value = 1 , rows = 4096)
    grass.run_command('r.stream.distance', stream = r_outlet , dir = r_drainage , flags = 'o' , distance = r_distance )
    
    # Width Function
    grass.run_command('r.wf.py', map = r_distance, image = prefix) 

    # Ipsographic curve
    grass.run_command('r.ipso.py', map = r_elevation+'_crop', image = prefix, flags = 'ab')
    
    # Creation of map of hillslope distance to river network
    grass.run_command('r.stream.distance', stream = r_stream+'_nothin' , dir = r_drainage , dem = r_elevation+'_crop' , distance = r_hillslope_distance )
    
    # Mean elevation
    grass.run_command('r.average' , base = r_basin , cover = r_elevation+'_crop' , output = r_height_average)
    mean_elev = float(grass.read_command('r.info' , flags = 'r' , map = r_height_average).split('\n')[0].split('=')[1])
    
    # In Grass the aspect categories represent the number degrees of east and they increase counterclockwise: 
    # 90deg is North, 180 is West, 270 is South 360 is East. The aspect value 0 is used to indicate undefined aspect in flat areas with slope=0.
    # We calculate the number of degree from north, increasing counterclockwise.
    grass.run_command('r.mapcalculator', amap = r_aspect , formula = 'if(%s>90,450-%s,90-%s)' % (r_aspect, r_aspect, r_aspect) , outfile = r_aspect_mod)
    
    # Centroid and mean slope
    baricenter_slope_baricenter = grass.read_command('r.volume', data = r_slope ,clump = r_basin , centroids = v_centroid1)
    baricenter_slope_baricenter = baricenter_slope_baricenter.split()
    mean_slope = baricenter_slope_baricenter[28]
    baricenter_aspect_baricenter = grass.read_command('r.volume', data = r_aspect ,clump = r_basin )
    baricenter_aspect_baricenter = baricenter_aspect_baricenter.split()
    basin_average_aspect = baricenter_aspect_baricenter[28]
    
    # Rectangle containing basin
    basin_east = baricenter_slope_baricenter[31]
    basin_north = baricenter_slope_baricenter[32]
    info_region_basin = grass.read_command('g.region', vect = options['prefix']+'_'+mapname[0]+'_basin' ,flags = 'm')
    dict_region_basin = dict(x.split('=', 1) for x in info_region_basin.split('\n') if '=' in x)
    basin_resolution = float(dict_region_basin['nsres'])
    x_massimo = float(dict_region_basin['n']) + (basin_resolution * 10)
    x_minimo = float(dict_region_basin['w']) - (basin_resolution * 10)
    y_massimo = float(dict_region_basin['e']) + (basin_resolution * 10)
    y_minimo = float(dict_region_basin['s']) - (basin_resolution * 10)
    nw = dict_region_basin['w'] , dict_region_basin['n'] 
    se = dict_region_basin['e'] , dict_region_basin['s'] 
    
    # Area and perimeter of basin
    report_basin = grass.read_command('v.report', map = v_basin , layer = 1 , option = 'area' , units = 'kilometers') 
    report_basin = report_basin.replace('\n',' ')
    report_basin = report_basin.split()
    area_basin = float(report_basin[1].split('|')[3])  
    report_basin = grass.read_command('v.report', map = v_basin , layer = 1 , option = 'length' , units = 'meters')
    perimeter_basin = float(report_basin.split('\n')[1].split('|')[0])
    
    # Directing vector 
    delta_x = abs(float(basin_east) - east)
    delta_y = abs(float(basin_north) - north)
    L_orienting_vect = math.sqrt((delta_x**2)+(delta_y**2)) / 1000
    
    # Prevalent orientation 
    prevalent_orientation = math.atan(delta_y/delta_x)
    
    # Compactness coefficient 
    C_comp = perimeter_basin / ( 2 * math.sqrt( area_basin / math.pi))
    
    # Circularity ratio 
    R_c = ( 4 * math.pi * area_basin ) / (perimeter_basin **2)
    
    # Mainchannel
    grass.run_command('r.mapcalculator', amap = r_hack , formula = 'if(%s==1,1,null())' % (r_hack) , outfile = r_mainchannel)
    grass.run_command('r.thin', input = r_mainchannel , output = r_mainchannel+'_thin' )
    grass.run_command('r.to.vect', input = r_mainchannel+'_thin' , output = v_mainchannel , feature = 'line' , flags = 'v')
    param_mainchannel = grass.read_command('v.what', map = v_mainchannel , east_north = '%s,%s' % (east,north) )
    dict_mainchannel = dict(x.split(':', 1) for x in param_mainchannel.split('\n')if ':' in x)
    mainchannel = float(dict_mainchannel['Length']) / 1000
    
    # Topological Diameter
    grass.run_command('r.mapcalculator', amap = r_shreve , formula = '-(%s - %s)' % (r_mainchannel,r_shreve) , outfile = r_mainchannel_dim)
    grass.run_command('r.thin', input = r_mainchannel_dim , output = r_mainchannel_dim+'_thin' )
    grass.run_command('r.to.vect', input = r_mainchannel_dim+'_thin' , output = v_mainchannel_dim , feature = 'line' , flags = 'v')
    try:
        D_topo = float(grass.read_command('v.info', map = v_mainchannel_dim, layer = 1, flags = 't').split('\n')[2].split('=')[1])
    except:
        D_topo = 1
        print 'Topological Diameter = WARNING'
    
    # Mean slope of mainchannel
    grass.run_command('v.to.points', flags='n', input = v_mainchannel_dim, output = v_mainchannel_dim+'_point', type = 'line')
    vertex = grass.read_command('v.out.ascii', flags = '-v' , input = v_mainchannel_dim+'_point').strip().split('\n')
    nodi = zeros((len(vertex),4),float)
    pendenze = []
    for i in range(len(vertex)):
        x, y = float(vertex[i].split('|')[0]) , float(vertex[i].split('|')[1])
        vertice = grass.read_command('r.what', flags = '-v' , input = r_elevation+'_crop', east_north='%s,%s' % (x,y)).replace('\n','').replace('||','|').split('|')
        nodi[i,0],nodi[i,1], nodi[i,2] = float(vertice[0]), float(vertice[1]), float(vertice[2])
    for i in range(0,len(vertex)-1,2):
        dist = math.sqrt(math.fabs((nodi[i,0] - nodi[i+1,0]))**2 + math.fabs((nodi[i,1] - nodi[i+1,1]))**2)
        deltaz = math.fabs(nodi[i,2]-nodi[i+1,2])
        # Control to prevent float division by zero (dist=0)
        try: 
            pendenza = deltaz / dist 
            pendenze.append(pendenza)
            mainchannel_slope = sum(pendenze) / len(pendenze) * 100
        except :
            print 'Mean slope of mainchannel = WARNING'
            
    # Elongation Ratio
    R_al = (2 * math.sqrt( area_basin / math.pi) ) / mainchannel
    
    # Shape factor
    S_f = area_basin / mainchannel
    
    # Characteristic altitudes 
    height_basin_average = grass.read_command('r.what' , input = r_height_average , cache = 500 , east_north = '%s,%s' % (east , north ))
    height_basin_average = height_basin_average.replace('\n','')
    height_basin_average = float(height_basin_average.split('|')[-1])
    minmax_height_basin = grass.read_command('r.info' , flags = 'r' , map = r_elevation+'_crop')
    minmax_height_basin = minmax_height_basin.strip().split('\n')
    min_height_basin , max_height_basin = float(minmax_height_basin[0].split('=')[-1]) , float(minmax_height_basin[1].split('=')[-1])
    H1 = max_height_basin 
    H2 = min_height_basin
    HM = H1 - H2
      
    # Concentration time (Giandotti, 1934)
    t_c = ((4 * math.sqrt(area_basin)) + (1.5 * mainchannel)) / (0.8 * math.sqrt(HM))
    
    # Mean hillslope length
    grass.run_command('r.average', cover = r_stream_e, base = r_mask, output = r_average_hillslope)
    mean_hillslope_length = float(grass.read_command('r.info' , flags = 'r' , map = r_average_hillslope).split('\n')[0].split('=')[1])
    
    # Magnitudo
    grass.run_command('r.mapcalculator', amap = r_strahler , formula = 'if(%s==1,1,null())' % (r_strahler) , outfile = r_ord_1)
    grass.run_command('r.thin', input = r_ord_1 , output = r_ord_1+'_thin', iterations = 200 )
    grass.run_command('r.to.vect', input = r_ord_1+'_thin' , output = v_ord_1 , feature = 'line', flags = 'v' )
    magnitudo = float(grass.read_command('v.info', map = v_ord_1, layer = 1, flags = 't').split('\n')[2].split('=')[1])
    
    # First order stream frequency 
    FSF = magnitudo/area_basin
    
    # Statistics
    stream_stats = grass.read_command('r.stream.stats', stream = r_strahler, dir = r_drainage_e, dem = r_elevation+'_crop' )
    print 'output r.stream.stats', stream_stats
    stream_stats_summary = stream_stats.split('\n')[4].split('|')
    stream_stats_mom = stream_stats.split('\n')[8].split('|')
    Max_order , Num_streams , Len_streams , Stream_freq = stream_stats_summary[0] , stream_stats_summary[1] , stream_stats_summary[2] , stream_stats_summary[5] 
    Bif_ratio , Len_ratio , Area_ratio , Slope_ratio = stream_stats_mom[0] , stream_stats_mom[1] , stream_stats_mom[2] , stream_stats_mom[3]
    drainage_density = float(Len_streams) / float(area_basin)
      
    # Cleaning up
    grass.run_command('g.remove', rast = r_height_average)
    grass.run_command('g.remove', rast = r_aspect_mod)
    grass.run_command('g.remove', rast = r_mainchannel)
    grass.run_command('g.remove', rast = r_stream_e)
    grass.run_command('g.remove', rast = r_drainage_e)
    grass.run_command('g.remove', rast = r_mask)
    grass.run_command('g.remove', rast = r_ord_1)
    grass.run_command('g.remove', rast = r_average_hillslope)
    grass.run_command('g.remove', rast = r_mainchannel_dim)
    grass.run_command('g.remove', rast = r_outlet)               
    grass.run_command('g.remove', rast = r_basin)
    grass.run_command('g.remove', rast = prefix+'_mainchannel_thin')
    grass.run_command('g.remove', rast = prefix+'_mainchannel_dim_thin')
    grass.run_command('g.remove', rast = prefix+'_ord_1_thin')
    grass.run_command('g.remove', rast = prefix+'_stream_nothin')
    grass.run_command('g.remove', rast = prefix+'_stream_e_thin')   
    grass.run_command('g.remove', vect = v_mainchannel_dim+'_point')
    grass.run_command('g.remove', vect = v_centroid1)
    grass.run_command('g.remove', vect = v_mainchannel_dim)
    grass.run_command('g.remove', vect = v_ord_1)
    
    if nomap :
        grass.run_command('g.remove', vect = v_outlet)
        grass.run_command('g.remove', vect = v_basin)
        grass.run_command('g.remove', vect = v_mainchannel)
        grass.run_command('g.remove', vect = v_stream_e)
        grass.run_command('g.remove', rast = r_accumulation)
        grass.run_command('g.remove', rast = r_drainage)
        grass.run_command('g.remove', rast = r_aspect)
        grass.run_command('g.remove', rast = r_strahler)
        grass.run_command('g.remove', rast = r_shreve)
        grass.run_command('g.remove', rast = r_horton)
        grass.run_command('g.remove', rast = r_hack)
        grass.run_command('g.remove', rast = r_distance)
        grass.run_command('g.remove', rast = r_hillslope_distance)
        grass.run_command('g.remove', rast = r_slope)
        
    ####################################################
    
    parametri_bacino = {}
    parametri_bacino["mean_slope"] = float(mean_slope)
    parametri_bacino["mean_elev"] = float(mean_elev)
    parametri_bacino["basin_average_aspect"] = float(basin_average_aspect)
    parametri_bacino["basin_east"] = float(basin_east)
    parametri_bacino["basin_north"] = float(basin_north)
    parametri_bacino["basin_resolution"] = float(basin_resolution)
    parametri_bacino["nw"] = nw
    parametri_bacino["se"] = se
    parametri_bacino["area_basin"] = float(area_basin)
    parametri_bacino["perimeter_basin"] = float(perimeter_basin)
    parametri_bacino["L_orienting_vect"] = float(L_orienting_vect)
    parametri_bacino["prevalent_orientation"] = float(prevalent_orientation)
    parametri_bacino["C_comp"] = float(C_comp)
    parametri_bacino["R_c"] = float(R_c)
    parametri_bacino["mainchannel"] = float(mainchannel)
    parametri_bacino["D_topo"] = float(D_topo)
    parametri_bacino["mainchannel_slope" ] = float(mainchannel_slope)
    parametri_bacino["R_al"] = float(R_al)
    parametri_bacino["S_f"] = float(S_f)
    parametri_bacino["H1"] = float(H1)
    parametri_bacino["H2"] = float(H2)
    parametri_bacino["HM"] = float(HM)
    parametri_bacino["t_c"] = float(t_c)
    parametri_bacino["mean_hillslope_length"] = float(mean_hillslope_length)
    parametri_bacino["magnitudo"] = float(magnitudo)
    parametri_bacino["Max_order"] = float(Max_order)
    parametri_bacino["Num_streams"] = float(Num_streams)
    parametri_bacino["Len_streams"] = float(Len_streams)
    parametri_bacino["Stream_freq"] = float(Stream_freq)
    parametri_bacino["Bif_ratio"] = float(Bif_ratio)
    parametri_bacino["Len_ratio"] = float(Len_ratio)
    parametri_bacino["Area_ratio"] = float(Area_ratio)
    parametri_bacino["Slope_ratio"] = float(Slope_ratio)
    parametri_bacino["drainage_density"] = float(drainage_density)
    parametri_bacino["FSF"] = float(FSF) 
    print "\n"
    print "##################################" 
    print "Morphometric parameters of basin :"
    print "##################################\n"	
    print "Easting Centroid of basin : " , basin_east 
    print "Northing Centroid of Basin : " , basin_north 
    print "Rectangle containing basin (N-W) : " , nw 
    print "Rectangle containing basin (S-E) : " , se 
    print "Area of basin [km^2] : " , '%.2f' % area_basin 
    print "Perimeter of basin [km] : " , '%.2f' % perimeter_basin 
    print "Max Elevation [m s.l.m.] : " , '%.2f' % H1
    print "Min Elevation [m s.l.m.]: " , '%.2f' % H2 
    print "Elevation Difference [m]: " , '%.2f' % HM
    print "Mean Elevation [m s.l.m.]: " , '%.2f' % mean_elev        
    print "Mean Slope : " , mean_slope 
    print "Length of Directing Vector [km] : " , '%.2f' % L_orienting_vect 
    print "Prevalent Orientation [degree from north, counterclockwise] : " , '%.3f' % prevalent_orientation
    print "Compactness Coefficient : " , '%.2f' % C_comp 
    print "Circularity Ratio : " , '%.2f' % R_c       
    print "Topological Diameter : " , '%.2f' % D_topo 
    print "Elongation Ratio : " , '%.2f' % R_al 
    print "Shape Factor : " , '%.2f' % S_f
    print "Concentration Time (Giandotti, 1934) [hr] : " , '%.2f' % t_c
    print "Length of Mainchannel [km] : " , '%.2f' % mainchannel 
    print "Mean slope of mainchannel [%]: " , '%.2f' % mainchannel_slope
    print "Mean hillslope length [m] : " , '%.2f' % mean_hillslope_length
    print "Magnitudo : " , '%.0f' % magnitudo
    print "Max order (Strahler) : " , Max_order 
    print "Number of streams : " , Num_streams 
    print "Total Stream Length [km] : " , Len_streams 
    print "First order stream frequency : " , '%.2f' % FSF
    print "Drainage Density [km/km^2]: " , '%.2f' % drainage_density
    print "Bifurcation Ratio (Horton) : " , Bif_ratio 
    print "Length Ratio (Horton) : " , Len_ratio 
    print "Area ratio (Horton) : " , Area_ratio
    print "Slope ratio (Horton): " , Slope_ratio, "\n"
    
    #print parametri_bacino
    grass.run_command('g.message' , message = 'Done!')	

if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
