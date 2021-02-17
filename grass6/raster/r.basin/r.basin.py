#!/usr/bin/env python

############################################################################
#
# MODULE:      r.basin
# AUTHOR(S):   Margherita Di Leo, Massimo Di Stefano
# PURPOSE:     Morphometric characterization of river basins
# COPYRIGHT:   (C) 2010 by Margherita Di Leo & Massimo Di Stefano
#              dileomargherita@gmail.com
#
#              This program is free software under the GNU General Public
#              License (>=v3.0) and comes with ABSOLUTELY NO WARRANTY.
#              See the file COPYING that comes with GRASS
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
#% gisprompt: old,cell,raster
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
#% description: Use default threshold (1km^2)
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
import csv

if not os.environ.has_key("GISBASE"):
    grass.message( "You must be in GRASS GIS to run this program." )
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
    r_distance = prefix+'_dist2out'
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
    v_outlet = prefix+'_outlet'
    v_basin = prefix+'_basin'
    v_centroid1 = prefix+'_centroid1'
    v_mainchannel = prefix+'_mainchannel'
    v_mainchannel_dim = prefix+'_mainchannel_dim'
    v_network = prefix+'_network'
    v_ord_1 = prefix+'_ord_1'
    global tmp


    # Save current region
    grass.read_command('g.region', flags = 'p', save = 'original', overwrite = True)

    # Watershed SFD
    grass.run_command('r.watershed', elevation = r_elevation, 
                                     accumulation = r_accumulation, 
                                     drainage = r_drainage,  
                                     convergence = 5, 
                                     flags = 'af',
                                     overwrite = True)

    # Managing flag
    if autothreshold :
        # info_region = grass.read_command('g.region', flags = 'p', rast = '%s' % (r_elevation))
        # dict_region = grass.parse_key_val(info_region, ':')
        # resolution = float(dict_region['nsres'])
        resolution = grass.region()['nsres']
        th = 1000000 / (resolution**2)
        grass.message( "threshold : %s" % th ) 
    else :
        th = options['threshold']

    # Stream extraction
    try:
        grass.run_command('r.stream.extract', elevation = r_elevation, 
                                          accumulation = r_accumulation, 
                                          threshold = th, 
                                          d8cut = 'infinity', 
                                          mexp = 0, 
                                          stream_rast = r_stream_e,  
                                          direction = r_drainage_e, 
                                          overwrite = True)
    except:
        grass.fatal("Some dependencies seem to be missing, please make sure that you have r.stream.* modules installed.")

    try:

        # Delineation of basin 
        try:
            grass.run_command('r.stream.basins', dir = r_drainage, 
                                             basins = r_basin, 
                                             coors = '%s,%s' % (east , north),
                                             overwrite = True)
        except:
            grass.fatal("Some dependencies seem to be missing, please make sure that you have r.stream.* modules installed.")                                    

        grass.message( "Delineation of basin done" )

        # Mask and cropping
        elevation_name = r_elevation = r_elevation.split('@')[0]
        grass.mapcalc("$r_mask = $r_basin / $r_basin",
                       r_mask = r_mask,
                       r_basin = r_basin)
        grass.mapcalc("tmp = $r_accumulation / $r_mask",
                       r_accumulation = r_accumulation,
                       r_mask = r_mask)
        grass.run_command('g.remove', rast = r_accumulation, quiet = True)
        grass.run_command('g.rename', rast = ('tmp',r_accumulation))
        grass.mapcalc("tmp = $r_drainage / $r_mask",
                       r_drainage = r_drainage,
                       r_mask = r_mask)
        grass.run_command('g.remove', rast = r_drainage, quiet = True)
        grass.run_command('g.rename', rast = ('tmp', r_drainage))
        grass.mapcalc("$r_elevation_crop = $r_elevation * $r_mask",
                       r_mask = r_mask,
                       r_elevation = r_elevation,
                       r_elevation_crop = 'r_elevation_crop')
        grass.mapcalc("tmp = $r_drainage_e * $r_mask",
                       r_mask = r_mask,
                       r_drainage_e = r_drainage_e)
        grass.run_command('g.remove', rast = r_drainage_e, quiet = True)
        grass.run_command('g.rename', rast = ('tmp',r_drainage_e))
        grass.mapcalc("tmp = $r_stream_e * $r_mask",
                       r_mask = r_mask,
                       r_stream_e = r_stream_e)
        grass.run_command('g.remove', rast = r_stream_e, quiet = True)
        grass.run_command('g.rename', rast = ('tmp',r_stream_e))
        grass.run_command('r.thin', input = r_stream_e, 
                                    output = r_stream_e+'_thin',
                                    overwrite = True)
        grass.run_command('r.to.vect', input = r_stream_e+'_thin', 
                                       output = v_network, 
                                       feature = 'line',
                                       overwrite = True)

        # Creation of slope and aspect maps
        grass.run_command('r.slope.aspect', elevation = 'r_elevation_crop', 
                                            slope = r_slope, 
                                            aspect = r_aspect,
                                            overwrite = True)

        # Basin mask (vector)
        # Raster to vector
        grass.run_command('r.to.vect', input = r_basin, 
                                       output = v_basin, 
                                       feature = 'area',
                                       flags = 'sv',
                                       overwrite = True)

        # Add two columns to the table: area and perimeter                               
        grass.run_command('v.db.addcol', map = v_basin,
                                         columns = 'area double precision')

        grass.run_command('v.db.addcol', map = v_basin,
                                         columns = 'perimeter double precision')

        # Populate perimeter column                                 
        grass.run_command('v.to.db', map = v_basin, 
                                 type = 'line,boundary', 
                                 layer = 1, 
                                 qlayer = 1, 
                                 option = 'perimeter', 
                                 units = 'kilometers', 
                                 columns = 'perimeter', 
                                 overwrite = True)

        # Read perimeter
        tmp = grass.read_command('v.to.db', map = v_basin, 
                                 type = 'line,boundary', 
                                 layer = 1, 
                                 qlayer = 1, 
                                 option = 'perimeter', 
                                 units = 'kilometers', 
                                 qcolumn = 'perimeter',
                                 flags = 'p')                         
        perimeter_basin = float(tmp.split('\n')[1].split('|')[1]) 

        # Populate area column                                 
        grass.run_command('v.to.db', map = v_basin, 
                                 type = 'line,boundary', 
                                 layer = 1, 
                                 qlayer = 1, 
                                 option = 'area', 
                                 units = 'kilometers', 
                                 columns = 'area', 
                                 overwrite = True)  

        # Read area
        tmp = grass.read_command('v.to.db', map = v_basin, 
                                 type = 'line,boundary', 
                                 layer = 1, 
                                 qlayer = 1, 
                                 option = 'area', 
                                 units = 'kilometers', 
                                 qcolumn = 'area',
                                 flags = 'p')                         
        area_basin = float(tmp.split('\n')[1].split('|')[1])                 

        # Creation of order maps: strahler, horton, hack, shreeve
        grass.message( "Creating %s" % r_hack ) 

        try:
            grass.run_command('r.stream.order', stream = r_stream_e, 
                                        dir = r_drainage_e, 
                                        strahler = r_strahler, 
                                        shreve = r_shreve, 
                                        horton = r_horton, 
                                        hack = r_hack,
                                        overwrite = True)
        except:
            grass.fatal("Some dependencies seem to be missing, please make sure that you have r.stream.* modules installed.")                                


        # Distance to outlet
        grass.write_command('v.in.ascii', output = v_outlet, 
                                      stdin = "%s|%s|9999"  % (east, north),
                                      overwrite = True)

        grass.run_command('v.to.rast', input = v_outlet, 
                                   output = r_outlet, 
                                   use = 'cat', 
                                   type = 'point', 
                                   layer = 1, 
                                   value = 1, 
                                   rows = 4096,
                                   overwrite = True)

        try:                           
            grass.run_command('r.stream.distance', stream = r_outlet, 
                                           dir = r_drainage, 
                                           flags = 'o', 
                                           distance = r_distance,
                                           overwrite = True)
        except:
            grass.fatal("Some dependencies seem to be missing, please make sure that you have r.stream.* modules installed.")

        # Ipsographic curve
        grass.message( "##################################" )
        try:
            grass.run_command('r.ipso', map = 'r_elevation_crop',
                                  image = prefix, flags = 'ab')
        except:
            grass.fatal("Some dependencies seem to be missing, please make sure that you have r.ipso installed.")                          

        grass.message( "##################################" )
        # Width Function
        grass.message( "##################################" )
        try:
            grass.run_command('r.wf', map = r_distance,
                                  image = prefix)
        except:
            grass.fatal("Some dependencies seem to be missing, please make sure that you have r.wf installed.")

        grass.message( "##################################" )

        # Creation of map of hillslope distance to river network

        try:
            grass.run_command('r.stream.distance', stream = r_stream_e, 
                                           dir = r_drainage, 
                                           dem = 'r_elevation_crop' , 
                                           distance = r_hillslope_distance,
                                           overwrite = True)
        except:
            grass.fatal("Some dependencies seem to be missing, please make sure that you have r.stream.* modules installed.")

        # Mean elevation
        grass.run_command('r.average' , base = r_basin, 
                                    cover = 'r_elevation_crop', 
                                    output = r_height_average,
                                    overwrite = True)
        mean_elev = float(grass.read_command('r.info', flags = 'r', 
                                                   map = r_height_average).split('\n')[0].split('=')[1])

        # In Grass, aspect categories represent the number degrees of east and they increase 
        # counterclockwise: 90deg is North, 180 is West, 270 is South 360 is East. 
        # The aspect value 0 is used to indicate undefined aspect in flat areas with slope=0.
        # We calculate the number of degree from north, increasing counterclockwise.
        grass.mapcalc("$r_aspect_mod = if($r_aspect > 90, 450 - $r_aspect, 90 - $r_aspect)",
                  r_aspect = r_aspect,
                  r_aspect_mod = r_aspect_mod)

        # Centroid and mean slope
        baricenter_slope_baricenter = grass.read_command('r.volume', data = r_slope, 
                                                                 clump = r_basin, 
                                                                 centroids = v_centroid1,
                                                                 overwrite = True)
        baricenter_slope_baricenter = baricenter_slope_baricenter.split()
        mean_slope = baricenter_slope_baricenter[28]

        # Rectangle containing basin
        basin_east = baricenter_slope_baricenter[31]
        basin_north = baricenter_slope_baricenter[32]
        info_region_basin = grass.read_command('g.region', 
                                            vect = options['prefix']+'_'+mapname[0]+'_basin', 
                                            flags = 'm')
        dict_region_basin = dict(x.split('=', 1) for x in info_region_basin.split('\n') if '=' in x)
        basin_resolution = float(dict_region_basin['nsres'])
        x_massimo = float(dict_region_basin['n']) + (basin_resolution * 10)
        x_minimo = float(dict_region_basin['w']) - (basin_resolution * 10)
        y_massimo = float(dict_region_basin['e']) + (basin_resolution * 10)
        y_minimo = float(dict_region_basin['s']) - (basin_resolution * 10)
        nw = dict_region_basin['w'], dict_region_basin['n'] 
        se = dict_region_basin['e'], dict_region_basin['s'] 

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
        grass.mapcalc("$r_mainchannel = if($r_hack==1,1,null())",
                  r_hack = r_hack,
                  r_mainchannel = r_mainchannel)
        grass.run_command('r.thin', input = r_mainchannel, 
                                output = r_mainchannel+'_thin',
                                overwrite = True)
        grass.run_command('r.to.vect', input = r_mainchannel+'_thin', 
                                   output = v_mainchannel, 
                                   feature = 'line', 
                                   flags = 'v',
                                   overwrite = True)
        param_mainchannel = grass.read_command('v.what', map = v_mainchannel, 
                                                     east_north = '%s,%s' % (east,north) )
        tmp = param_mainchannel.split('\n')[8]
        mainchannel = float(tmp.split()[1]) / 1000   # km

        # Topological Diameter
        grass.mapcalc("$r_mainchannel_dim = -($r_mainchannel - $r_shreve) + 1",
                  r_mainchannel_dim = r_mainchannel_dim,
                  r_shreve = r_shreve,
                  r_mainchannel = r_mainchannel)
        grass.run_command('r.thin', input = r_mainchannel_dim, 
                                output = r_mainchannel_dim + '_thin',
                                overwrite = True)
        grass.run_command('r.to.vect', input = r_mainchannel_dim + '_thin', 
                                   output = v_mainchannel_dim, 
                                   feature = 'line', 
                                   flags = 'v',
                                   overwrite = True)
        try:
            D_topo1 = grass.read_command('v.info', map = v_mainchannel_dim, 
                                               layer = 1, 
                                               flags = 't')
            D_topo = float(D_topo1.split('\n')[2].split('=')[1])
        except:
            D_topo = 1
            grass.message( "Topological Diameter = WARNING" )

        # Mean slope of mainchannel
        grass.run_command('v.to.points', flags='n', 
                                     input = v_mainchannel_dim, 
                                     output = v_mainchannel_dim+'_point', 
                                     type = 'line',
                                     overwrite = True)
        vertex = grass.read_command('v.out.ascii', verbose = True, 
                                               input = v_mainchannel_dim+'_point').strip().split('\n')
        nodi = zeros((len(vertex),4),float)
        pendenze = []
        for i in range(len(vertex)):
            x, y = float(vertex[i].split('|')[0]) , float(vertex[i].split('|')[1])
            vertice1 = grass.read_command('r.what', verbose = True, 
                                               input = 'r_elevation_crop', 
                                               east_north='%s,%s' % (x,y))
            vertice = vertice1.replace('\n','').replace('||','|').split('|')
            nodi[i,0],nodi[i,1], nodi[i,2] = float(vertice[0]), float(vertice[1]), float(vertice[2])
        for i in range(0,len(vertex)-1,2):
            dist = math.sqrt(math.fabs((nodi[i,0] - nodi[i+1,0]))**2 + math.fabs((nodi[i,1] - nodi[i+1,1]))**2)
            deltaz = math.fabs(nodi[i,2] - nodi[i+1,2])
            # Control to prevent float division by zero (dist=0)
            try: 
                pendenza = deltaz / dist 
                pendenze.append(pendenza)
                mainchannel_slope = sum(pendenze) / len(pendenze) * 100
            except :
                pass

        # Elongation Ratio
        R_al = (2 * math.sqrt( area_basin / math.pi) ) / mainchannel

        # Shape factor
        S_f = area_basin / mainchannel

        # Characteristic altitudes 
        height_basin_average = grass.read_command('r.what', input = r_height_average , 
                                                        cache = 500 , 
                                                        east_north = '%s,%s' % (east , north ))
        height_basin_average = height_basin_average.replace('\n','')
        height_basin_average = float(height_basin_average.split('|')[-1])
        minmax_height_basin = grass.read_command('r.info', flags = 'r', 
                                                       map = 'r_elevation_crop')
        minmax_height_basin = minmax_height_basin.strip().split('\n')
        min_height_basin, max_height_basin = float(minmax_height_basin[0].split('=')[-1]), float(minmax_height_basin[1].split('=')[-1])
        H1 = max_height_basin 
        H2 = min_height_basin
        HM = H1 - H2

        # Concentration time (Giandotti, 1934)
        t_c = ((4 * math.sqrt(area_basin)) + (1.5 * mainchannel)) / (0.8 * math.sqrt(HM))

        # Mean hillslope length
        grass.run_command('r.average', cover = r_stream_e, 
                                   base = r_mask, 
                                   output = r_average_hillslope,
                                   overwrite = True)
        mean_hillslope_length = float(grass.read_command('r.info', flags = 'r', 
                                                               map = r_average_hillslope).split('\n')[0].split('=')[1])

        # Magnitudo
        grass.mapcalc("$r_ord_1 = if($r_strahler==1,1,null())",
                  r_ord_1 = r_ord_1,
                  r_strahler = r_strahler)
        grass.run_command('r.thin', input = r_ord_1, 
                                output = r_ord_1+'_thin', 
                                iterations = 200,
                                overwrite = True)
        grass.run_command('r.to.vect', input = r_ord_1+'_thin', 
                                   output = v_ord_1, 
                                   feature = 'line', 
                                   flags = 'v',
                                   overwrite = True)
        magnitudo = float(grass.read_command('v.info', map = v_ord_1, 
                                                   layer = 1, 
                                                   flags = 't').split('\n')[2].split('=')[1])

        # First order stream frequency 
        FSF = magnitudo / area_basin

        # Statistics
        try:
            stream_stats = grass.read_command('r.stream.stats', stream = r_strahler, 
                                                        dir = r_drainage_e, 
                                                        dem = 'r_elevation_crop' )
        except:
            grass.fatal("Some dependencies seem to be missing, please make sure that you have r.stream.* modules installed.") 

        print "##################################"         
        print "Output of r.stream.stats: "
        print  stream_stats

        stream_stats_summary = stream_stats.split('\n')[4].split('|')
        stream_stats_mom = stream_stats.split('\n')[8].split('|')
        Max_order , Num_streams , Len_streams , Stream_freq = stream_stats_summary[0] , stream_stats_summary[1] , stream_stats_summary[2] , stream_stats_summary[5] 
        Bif_ratio , Len_ratio , Area_ratio , Slope_ratio = stream_stats_mom[0] , stream_stats_mom[1] , stream_stats_mom[2] , stream_stats_mom[3]
        drainage_density = float(Len_streams) / float(area_basin)

        # Cleaning up
        grass.run_command('g.remove', rast = 'r_elevation_crop', quiet = True)
        grass.run_command('g.remove', rast = r_height_average, quiet = True)
        grass.run_command('g.remove', rast = r_aspect_mod, quiet = True)
        grass.run_command('g.remove', rast = r_mainchannel, quiet = True)
        grass.run_command('g.remove', rast = r_stream_e, quiet = True)
        grass.run_command('g.remove', rast = r_drainage_e, quiet = True)
        grass.run_command('g.remove', rast = r_mask, quiet = True)
        grass.run_command('g.remove', rast = r_ord_1, quiet = True)
        grass.run_command('g.remove', rast = r_average_hillslope, quiet = True)
        grass.run_command('g.remove', rast = r_mainchannel_dim, quiet = True)
        grass.run_command('g.remove', rast = r_outlet, quiet = True)               
        grass.run_command('g.remove', rast = r_basin, quiet = True)
        grass.run_command('g.remove', rast = prefix+'_mainchannel_thin', quiet = True)
        grass.run_command('g.remove', rast = prefix+'_mainchannel_dim_thin', quiet = True)
        grass.run_command('g.remove', rast = prefix+'_ord_1_thin', quiet = True)
        grass.run_command('g.remove', rast = prefix+'_stream_e_thin', quiet = True)   
        grass.run_command('g.remove', vect = v_mainchannel_dim+'_point', quiet = True)
        grass.run_command('g.remove', vect = v_centroid1, quiet = True)
        grass.run_command('g.remove', vect = v_mainchannel_dim, quiet = True)
        grass.run_command('g.remove', vect = v_ord_1, quiet = True)

        if nomap :
            grass.run_command('g.remove', vect = v_outlet, quiet = True)
            grass.run_command('g.remove', vect = v_basin, quiet = True)
            grass.run_command('g.remove', vect = v_mainchannel, quiet = True)
            grass.run_command('g.remove', rast = r_accumulation, quiet = True)
            grass.run_command('g.remove', rast = r_drainage, quiet = True)
            grass.run_command('g.remove', rast = r_aspect, quiet = True)
            grass.run_command('g.remove', rast = r_strahler, quiet = True)
            grass.run_command('g.remove', rast = r_shreve, quiet = True)
            grass.run_command('g.remove', rast = r_horton, quiet = True)
            grass.run_command('g.remove', rast = r_hack, quiet = True)
            grass.run_command('g.remove', rast = r_distance, quiet = True)
            grass.run_command('g.remove', rast = r_hillslope_distance, quiet = True)
            grass.run_command('g.remove', rast = r_slope, quiet = True)

        ####################################################

        parametri_bacino = {}
        parametri_bacino["mean_slope"] = float(mean_slope)
        parametri_bacino["mean_elev"] = float(mean_elev)
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

        # create .csv file
        with open(prefix+'_parameters.csv', 'w') as f:
            writer = csv.writer(f)
            writer.writerow(['Morphometric parameters of basin :'])
            writer.writerow([' '])
            writer.writerow(['Easting Centroid of basin'] + [basin_east])
            writer.writerow(['Northing Centroid of basin'] + [basin_north])
            writer.writerow(['Rectangle containing basin N-W'] + [nw])
            writer.writerow(['Rectangle containing basin S-E'] + [se])
            writer.writerow(['Area of basin [km^2]'] + [area_basin])
            writer.writerow(['Perimeter of basin [km]'] + [perimeter_basin])
            writer.writerow(['Max Elevation [m s.l.m.]'] + [H1])
            writer.writerow(['Min Elevation [m s.l.m.]'] + [H2])
            writer.writerow(['Elevation Difference [m]'] + [HM])
            writer.writerow(['Mean Elevation'] + [mean_elev])
            writer.writerow(['Mean Slope'] + [mean_slope])
            writer.writerow(['Length of Directing Vector [km]'] + [L_orienting_vect])
            writer.writerow(['Prevalent Orientation [degree from north, counterclockwise]'] + [prevalent_orientation])
            writer.writerow(['Compactness Coefficient'] + [C_comp])
            writer.writerow(['Circularity Ratio'] + [R_c])
            writer.writerow(['Topological Diameter'] + [D_topo])
            writer.writerow(['Elongation Ratio'] + [R_al])
            writer.writerow(['Shape Factor'] + [S_f])
            writer.writerow(['Concentration Time (Giandotti, 1934) [hr]'] + [t_c])
            writer.writerow(['Length of Mainchannel [km]'] + [mainchannel])
            writer.writerow(['Mean slope of mainchannel [percent]'] + [mainchannel_slope])
            writer.writerow(['Mean hillslope length [m]'] + [mean_hillslope_length])
            writer.writerow(['Magnitudo '] + [magnitudo])
            writer.writerow(['Max order (Strahler) '] + [Max_order])
            writer.writerow(['Number of streams '] + [Num_streams])
            writer.writerow(['Total Stream Length [km] '] + [Len_streams])
            writer.writerow(['First order stream frequency '] + [FSF])
            writer.writerow(['Drainage Density [km/km^2] '] + [drainage_density])
            writer.writerow(['Bifurcation Ratio (Horton) '] + [Bif_ratio])
            writer.writerow(['Length Ratio (Horton) '] + [Len_ratio])
            writer.writerow(['Area ratio (Horton) '] + [Area_ratio])
            writer.writerow(['Slope ratio (Horton) '] + [Slope_ratio])

        grass.message( "\n" ) 
        grass.message( "##################################" )
        grass.message( "Morphometric parameters of basin :" )
        grass.message( "##################################\n" )	
        grass.message( "Easting Centroid of basin : %s " % basin_east )
        grass.message( "Northing Centroid of Basin : %s " % basin_north )
        grass.message( "Rectangle containing basin N-W : %s , %s " % nw ) 
        grass.message( "Rectangle containing basin S-E : %s , %s " % se )
        grass.message( "Area of basin [km^2] : %s " % area_basin )
        grass.message( "Perimeter of basin [km] : %s " % perimeter_basin )
        grass.message( "Max Elevation [m s.l.m.] : %s " % H1 )
        grass.message( "Min Elevation [m s.l.m.]: %s " % H2 )
        grass.message( "Elevation Difference [m]: %s " % HM )
        grass.message( "Mean Elevation [m s.l.m.]: %s " % mean_elev )       
        grass.message( "Mean Slope : %s " % mean_slope )
        grass.message( "Length of Directing Vector [km] : %s " % L_orienting_vect )
        grass.message( "Prevalent Orientation [degree from north, counterclockwise] : %s " % prevalent_orientation )
        grass.message( "Compactness Coefficient : %s " % C_comp )
        grass.message( "Circularity Ratio : %s " % R_c )      
        grass.message( "Topological Diameter : %s " % D_topo )
        grass.message( "Elongation Ratio : %s " % R_al )
        grass.message( "Shape Factor : %s " % S_f )
        grass.message( "Concentration Time (Giandotti, 1934) [hr] : %s " % t_c )
        grass.message( "Length of Mainchannel [km] : %s " % mainchannel )
        grass.message( "Mean slope of mainchannel [percent] : %f " % mainchannel_slope )
        grass.message( "Mean hillslope length [m] : %s " % mean_hillslope_length )
        grass.message( "Magnitudo : %s " % magnitudo )
        grass.message( "Max order (Strahler) : %s " % Max_order )
        grass.message( "Number of streams : %s " % Num_streams )
        grass.message( "Total Stream Length [km] : %s " % Len_streams )
        grass.message( "First order stream frequency : %s " % FSF )
        grass.message( "Drainage Density [km/km^2] : %s " % drainage_density )
        grass.message( "Bifurcation Ratio (Horton) : %s " % Bif_ratio )
        grass.message( "Length Ratio (Horton) : %s " % Len_ratio )
        grass.message( "Area ratio (Horton) : %s " % Area_ratio )
        grass.message( "Slope ratio (Horton): %s " % Slope_ratio )
        grass.message( "##################################" ) 
        grass.message( "\n" )
        grass.message( "Done!")

    except:
        grass.message( "\n" )
        grass.message( "##################################" ) 
        grass.message( "\n" ) 
        grass.message( "An error occurred with the parameters calculation." )
        grass.message( "Please note that outlet coordinates must belong to the river network." )
        grass.message( "You might want to run r.stream.extract and choose coordinates matching with the extracted stream map." )
        grass.message( "Please report to the authors any other problem not related with coordinates outlet." )

    # Set region to original 
    grass.read_command('g.region', flags = 'p', region = 'original')

if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
