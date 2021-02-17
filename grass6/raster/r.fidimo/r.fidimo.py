#!/usr/bin/env python
#
############################################################################
#
# MODULE:		FIDIMO Fish Dispersal Model for River Networks
#
# AUTHOR(S):		Johannes Radinger
#				
# VERSION:		V0.1 Beta
#
# DATE:			2011-10-02
#
#############################################################################
#%Module
#% description: Calculating fish dispersal in a river network from source populations with species specific dispersal parameters
#% keywords: Fish Dispersal Model
#%End
#%option
#% key: river
#% type: string
#% gisprompt: old,cell,raster
#% description: River network (raster-file, e.g. output from r.stream.extract or fidimo.river)
#% required: no
#% guisection: Stream parameters
#%end
#%option
#% key: coors
#% type: string
#% required: no
#% multiple: no
#% key_desc: x,y
#% description: River networks' outlet coordinates: E,N
#% guisection: Stream parameters
#%End
#%option
#% key: barriers
#% type: string
#% gisprompt:old,file,input
#% description: Barrier point file
#% required: no
#% guisection: Stream parameters
#%end
#%option
#% key: n_source
#% type: string
#% key_desc: number[%]
#% description: Either: Number of random cells with source populations
#% required: no
#% guisection: Source populations
#%end
#%option
#% key: source_populations
#% type: string
#% gisprompt: old,cell,raster
#% description: Or: Source population raster, e.g output from SDM
#% required: no
#% guisection: Source populations
#%end
#%Option
#% key: species
#% type: string
#% required: no
#% multiple: no
#% options:Custom species,Catostomus commersoni,Moxostoma duquesnii,Moxostoma erythrurum,Ambloplites rupestris,Lepomis auritus,Lepomis cyanellus,Lepomis macrochirus,Lepomis megalotis,Micropterus dolomieui,Micropterus punctulatus,Micropterus salmoides,Pomoxis annularis,Cottus bairdii,Cottus gobio,Abramis brama,Barbus barbus,Cyprinus carpio carpio,Gobio gobio,Leuciscus idus,Rutilus rutilus,Squalius cephalus,Tinca tinca,Esox lucius,Fundulus heteroclitus heteroclitus,Ameiurus natalis,Ictalurus punctatus,Morone americana,Etheostoma flabellare,Etheostoma nigrum,Perca fluviatilis,Percina nigrofasciata,Sander lucioperca,Oncorhynchus mykiss, Oncorhynchus gilae,Salmo salar,Salmo trutta fario,Salvelinus fontinalis,Salvelinus malma malma,Thymallus thymallus,Aplodinotus grunniens,Salmo trutta,Gobio gobio,Rutilus rutilus
#% description: Select fish species
#% guisection: Dispersal parameters
#%End
#%Option
#% key: L
#% type: integer
#% required: no
#% multiple: no
#% description: Fish Length [mm] (If no species is given)
#% guisection: Dispersal parameters
#% options: 39-810
#%End
#%Option
#% key: AR
#% type: double
#% required: no
#% multiple: no
#% description: Aspect Ratio of Caudal Fin (If no species is given) (valid range 0.51 - 2.29)
#% guisection: Dispersal parameters
#%End
#%Option
#% key: T
#% type: integer
#% required: no
#% multiple: no
#% description: Time interval for model step [d]
#% guisection: Dispersal parameters
#% options: 1-3285
#% answer: 30
#%End
#%option
#% key: p
#% type: double
#% required: no
#% multiple: no
#% description: Share of the stationary component (valid range 0 - 1)
#% answer:0.67 
#% guisection: Dispersal parameters
#%End
#%Flag
#% key: b
#% description: Don't keep basic vector maps (source_points, barriers)
#%end
#%Flag
#% key: a
#% description: Keep all temporal vector and raster maps
#%end
#%Option
#% key: truncation
#% type: string
#% required: no
#% multiple: no
#% options: 0.9,0.95,0.99,0.995,0.999,0.99999,0.999999999,inf
#% description: kernel truncation criterion (precision)
#% answer: 0.99
#% guisection: Optional
#%End
#%Option
#% key: seed
#% type: integer
#% required: no
#% multiple: no
#% description: fixed seed for generating dispersal parameters via fishmove
#% guisection: Optional
#%End
#%Option
#% key: output
#% type: string
#% required: no
#% multiple: no
#% key_desc: name
#% description: Base name for output raster
#% guisection: Output
#% answer: fidimo_out
#%end
#%Option
#% key: statistical_interval
#% type: string
#% required: no
#% multiple: no
#% key_desc: name
#% description: Statistical Intervals
#% guisection: Output
#% options:no,Confidence Interval,Prediction Interval
#% answer:no
#%end


# import required base modules
import sys
import os
import atexit
import time
import sqlite3
import math #for function sqrt()

# import required grass modules
import grass.script as grass
import grass.script.setup as gsetup
import grass.script.array as garray


# import required numpy/scipy modules
import numpy
from scipy import stats
from scipy import optimize





tmp_map_rast = None
tmp_map_vect = None

def cleanup():
    if (tmp_map_rast or tmp_map_vect) and not flags['a']:
        grass.run_command("g.remove", 
                        rast = [f + str(os.getpid()) for f in tmp_map_rast],
                        vect = [f + str(os.getpid()) for f in tmp_map_vect],
                        quiet = True)




def main():

    ############ DEFINITION CLEANUP TEMPORARY FILES ##############
    #global variables for cleanup
    global tmp_map_rast
    global tmp_map_vect

    tmp_map_rast = ['density_final_','density_final_corrected_','density_from_point_tmp_', 'density_from_point_unmasked_tmp_', 'distance_from_point_tmp_', 'distance_raster_tmp_','distance_raster_buffered_tmp_','distance_raster_grow_tmp_','division_overlay_tmp_', 'downstream_drain_tmp_','drainage_tmp_','flow_direction_tmp_', 'lower_distance_tmp_', 'rel_upstream_shreve_tmp_', 'river_raster_cat_tmp_', 'river_raster_tmp_', 'river_raster_combine_tmp_', 'river_raster_buffer_tmp_', 'river_raster_grow_start_tmp_', 'river_raster_nearest_tmp_', 'shreve_tmp_', 'source_populations_scalar_','source_populations_scalar_corrected_', 'strahler_tmp_', 'stream_segments_tmp_', 'upper_distance_tmp_', 'upstream_part_tmp_', 'upstream_shreve_tmp_']


    tmp_map_vect = ['river_points_tmp_', 'river_vector_tmp_', 'river_vector_nocat_tmp_','source_points_']


    if options['barriers']:
        tmp_map_rast = tmp_map_rast + ['density_below_barrier_tmp_','distance_barrier_tmp_', 'distance_barrier_downstream_tmp_','distance_from_point_within_segment_tmp_', 'distance_upstream_point_within_segment_tmp_', 'lower_distance_barrier_tmp_', 'upper_distance_barrier_tmp_', 'upstream_barrier_tmp_',  'upstream_density_tmp_', 'upstream_segment_tmp_']
        tmp_map_vect = tmp_map_vect + ["barriers_",'barriers_tmp_', 'point_within_segment_tmp_']



    ############ PARAMETER INPUT ##############
    #Stream parameters input
    river = options['river']
    coors = options['coors']
    if options['barriers']:
        input_barriers = options['barriers']



    #Source population input
    if (options['source_populations'] and options['n_source']) or (str(options['source_populations']) == '' and str(options['n_source']) == ''):
        grass.fatal(_("Provide either fixed or random source population"))

    n_source = options['n_source'] #number of random source points
    source_populations = options['source_populations']





    # multiplication value as workaround for very small FLOAT values
    #imporatant for transformation of source population raster into point vector
    scalar = 10**200

    # Statistical interval
    if (str(options['statistical_interval']) == 'Prediction Interval'):
        interval = "prediction"
    else:
        interval = "confidence"


    #Set fixed seed if specified
    if options['seed']:
        seed = ",seed="+str(options['seed'])
    else:
        seed = ""


    #Options and Output
    output = options['output']





    ############ FISHMOVE ##############

    # import required rpy2 module
    import rpy2.robjects as robjects
    from rpy2.robjects.packages import importr
    fm = importr('fishmove')

    #Dispersal parameter input
    if str(options['species']!="Custom species") and (options['L'] or options['AR']):
        grass.message(_("Species settings will be overwritten with L and AR"))
    species = str(options['species'])
    if options['L']:
        L = float(options['L'])
    if options['AR']:
        AR = float(options['AR'])
    T = float(options['T'])
    # Setting Stream order to a vector of 1:9 and calculate fishmove for all streamorders at once
    SO = robjects.IntVector((1,2,3,4,5,6,7,8,9))
    m = 0 # m-parameter in dispersal function
    if (float(options['p']) >= 0 and float(options['p']) < 1):
        p =float(options['p'])
    else:
        grass.fatal(_("Valid range for p: 0 - 1"))


    ##### Calculating 'fishmove' depending on species or L & AR
    if species == "Custom species":
        fishmove = eval("fm.fishmove(L=L,AR=AR,SO=SO,T=T,interval=interval,rep=200%s)"%(seed))
    else:
        fishmove = eval("fm.fishmove(L=L,AR=AR,SO=SO,T=T,interval=interval,rep=200%s)"%(seed))


    # using only part of fishmove results (only regression coeffients)
    fishmove = fishmove[1]
    nrun = ['fit','lwr','upr']





    ############ REGION, DB-CONNECTION ##############
    #Setting region to extent of input River
    grass.run_command("g.region",
                                      flags = "a",
                                      rast = river,
                                      overwrite = True,
                                      save = "region_Fidimo")

    #Getting resultion, res=cellsize
    res = int(grass.read_command("g.region",
                                      flags = "m").strip().split('\n')[4].split('=')[1])


    #database-connection
    env = grass.gisenv()
    gisdbase = env['GISDBASE']
    location = env['LOCATION_NAME']
    mapset = env['MAPSET']
    grass.run_command("db.connect",
                                      driver = "sqlite",
                                      database = "$GISDBASE/$LOCATION_NAME/$MAPSET/sqlite.db")	 
    database = sqlite3.connect(os.path.join(gisdbase, location, mapset, 'sqlite.db'))
    db = database.cursor()

    #############################################
    ############################################# 



    ################ Preparation River Raster (Distance-Raster) ################


    # Populate input-river (raster) with value of resolution
    # *1.0 to get float raster instead of integer
    grass.mapcalc("$river_raster = if($river,$res*1.0)",
                                      river_raster = "river_raster_tmp_%d" % os.getpid(),
                                      river = river,
                                      res = res)


    # Converting river_raster to river_vector
    grass.run_command("r.to.vect",
                                      overwrite = True,
                                      input="river_raster_tmp_%d" % os.getpid(),
                                      output="river_vector_tmp_%d" % os.getpid(),
                                      feature="line")

    # Converting river_raster to river_point
    grass.run_command("r.to.vect",
                                      overwrite = True,
                                      input="river_raster_tmp_%d" % os.getpid(),
                                      output="river_points_tmp_%d" % os.getpid(),
                                      feature="point")	



    #Prepare Barriers/Snap barriers to river_vector
    if options['barriers']:
        grass.run_command("v.in.ascii",
                                          flags = "n",
                                          overwrite = True,
                                          input=input_barriers,
                                          output="barriers_tmp_%d" % os.getpid(),
                                          columns="x DOUBLE, y DOUBLE, passability DOUBLE")
        grass.run_command("v.db.addcol",
                                          map ="barriers_tmp_%d" % os.getpid(),
                                          columns="adj_X DOUBLE, adj_Y DOUBLE")					
        grass.run_command("v.distance",
                                          overwrite = True,
                                          _from="barriers_tmp_%d" % os.getpid(),
                                          to="river_vector_tmp_%d" % os.getpid(),
                                          upload="to_x,to_y",
                                          column="adj_X,adj_Y")
        grass.run_command("v.in.db",
                                          overwrite = True,
                                          table="barriers_tmp_%d" % os.getpid(),
                                          x="adj_X",
                                          y="adj_Y",
                                          key="cat",
                                          output="barriers_%d" % os.getpid())
        grass.run_command("v.db.addcol",
                                          map ="barriers_%d" % os.getpid(),
                                          columns="dist DOUBLE, affected_barriers DOUBLE") # dist = distance of barrier to segment, affected_barriers = all barriers which are considered to be the scope of a segement
        # Copy to make barriers permament
        grass.run_command("g.copy", 
                vect = "barriers_%d" % os.getpid() + "," + output + "_barriers")

        #Breaking river_vector at position of barriers to get segments
        for adj_X,adj_Y in db.execute('SELECT adj_X, adj_Y FROM barriers_%d'% os.getpid()):
            barrier_coors = str(adj_X)+","+str(adj_Y)

            grass.run_command("v.edit",
                                      map="river_vector_tmp_%d" % os.getpid(),
                                      tool="break",
                                      thresh="1,0,0",
                                      coords=barrier_coors)


    #Getting category values (ASC) for river_network segements
    grass.run_command("v.category",
                                    overwrite=True,
                                    input="river_vector_tmp_%d" % os.getpid(),
                                    option="del",
                                    output="river_vector_nocat_tmp_%d" % os.getpid())
    grass.run_command("v.category",
                                    overwrite=True,
                                    input="river_vector_nocat_tmp_%d" % os.getpid(),
                                    option="add",
                                    output="river_vector_tmp_%d" % os.getpid()) 



    #Check if outflow coors are on river
    # For GRASS7 snap coors to river. Check r.stream.snap - add on
    # !!!!!!


    #Calculation of distance from outflow and flow direction for total river
    grass.run_command("r.cost",
                                      flags = 'n',
                                      overwrite = True,
                                      input = "river_raster_tmp_%d" % os.getpid(),
                                      output = "distance_raster_tmp_%d" % os.getpid(),
                                      coordinate = coors)

    largest_cost_value = grass.raster_info("distance_raster_tmp_%d" % os.getpid())['max']

    # buffer
    grass.run_command("r.grow.distance",
                                    overwrite=True,
                                    input="distance_raster_tmp_%d" % os.getpid(),
                                    value="river_raster_nearest_tmp_%d" % os.getpid())

    #get value of nearest river cell
    grass.run_command("r.grow",
                                    overwrite=True,
                                    input="distance_raster_tmp_%d" % os.getpid(),
                                    output="distance_raster_grow_tmp_%d" % os.getpid(),
                                    radius=2.01,
                                    old=1,
                                    new=largest_cost_value*2)

    # remove buffer for start
    grass.mapcalc("$river_raster_grow_start_tmp = if($river_raster_nearest_tmp==0,null(),$distance_raster_grow_tmp)",
                                    river_raster_grow_start_tmp = "river_raster_grow_start_tmp_%d" % os.getpid(),
                                    river_raster_nearest_tmp = "river_raster_nearest_tmp_%d" % os.getpid(),
                                    distance_raster_grow_tmp = "distance_raster_grow_tmp_%d" % os.getpid())


    #grow by one cell to make sure taht the start point is the only cell
    grass.run_command("r.grow",
                                    overwrite=True,
                                    input="river_raster_grow_start_tmp_%d" % os.getpid(),
                                    output="river_raster_buffer_tmp_%d" % os.getpid(),
                                    radius=1.01,
                                    old=largest_cost_value*2,
                                    new=largest_cost_value*2)

    #patch river raster with buffer
    grass.run_command("r.patch",
                                    overwrite=True,
                                    input="distance_raster_tmp_%d,river_raster_buffer_tmp_%d" % (os.getpid(),os.getpid()),
                                    output="distance_raster_buffered_tmp_%d" % os.getpid())

    # Getting flow direction and stream segments
    grass.run_command("r.watershed", 
                                      flags = 'mf', #depends on memory!! #
                                      elevation = "distance_raster_buffered_tmp_%d" % os.getpid(),
                                      drainage = "drainage_tmp_%d" % os.getpid(),
                                      stream = "stream_segments_tmp_%d" % os.getpid(),
                                      threshold = 3,
                                      overwrite = True)

    grass.mapcalc("$flow_direction_tmp = if($stream_segments_tmp,$drainage_tmp,null())",
                                                    flow_direction_tmp = "flow_direction_tmp_%d" % os.getpid(),
                                                    stream_segments_tmp = "stream_segments_tmp_%d" % os.getpid(),
                                                    drainage_tmp = "drainage_tmp_%d" % os.getpid())

    # Stream segments depicts new river_raster (corrected for small tributaries of 1 cell)	
    grass.mapcalc("$river_raster_combine_tmp = if(!isnull($stream_segments_tmp) && !isnull($river_raster_tmp),$res*1.0,null())",
                                                    river_raster_combine_tmp =  "river_raster_combine_tmp_%d" % os.getpid(),
                                                    river_raster_tmp =  "river_raster_tmp_%d" % os.getpid(),
                                                    stream_segments_tmp = "stream_segments_tmp_%d" % os.getpid(),
                                                    res = res)

    grass.run_command("g.copy",
                                    overwrite=True, 
                                    rast = "river_raster_combine_tmp_%d" % os.getpid() + "," "river_raster_tmp_%d" % os.getpid())

    #Calculation of stream order (Shreve/Strahler)
    grass.run_command("r.stream.order",
                                      stream = "stream_segments_tmp_%d" % os.getpid(),
                                      dir = "flow_direction_tmp_%d" % os.getpid(),
                                      shreve = "shreve_tmp_%d" % os.getpid(),
                                      strahler = "strahler_tmp_%d" % os.getpid(),
                                      overwrite = True)




    ################ Preparation Source Populations ################
    #Defining source points either as random points in river or from input raster
    if options['n_source']:
        grass.run_command("r.random",
                                          overwrite=True,
                                          input = "river_raster_tmp_%d" % os.getpid(),
                                          n = n_source,
                                          vector_output="source_points_%d" % os.getpid())
        grass.run_command("v.db.addcol",
                                  map = "source_points_%d" % os.getpid(),
                                  columns = "prob DOUBLE")


        # Set starting propability of occurence to 1*scalar for all random source_points	
        grass.write_command("db.execute",
                                stdin = 'UPDATE source_points_%d SET prob=%d' % (os.getpid(),scalar))

    #if source population raster is provided, then use it, transform raster in vector points
    #create an attribute column "prob" and update it with the values from the raster map
    if options['source_populations']:
        #Multiplying source probability with very large scalar to avoid problems 
        #with very small floating points (problem: precision of FLOAT); needs retransforamtion in the end
        grass.mapcalc("$source_populations_scalar = $source_populations*$scalar",
                                                source_populations = source_populations,
                                                source_populations_scalar = "source_populations_scalar_%d" % os.getpid(),
                                                scalar = scalar)

        #Exclude source Populations that are outside the river_raster
        grass.mapcalc("$source_populations_scalar_corrected = if($river_raster_tmp,$source_populations_scalar)",
                                                source_populations_scalar_corrected = "source_populations_scalar_corrected_%d" % os.getpid(),
                                                river_raster_tmp = "river_raster_tmp_%d" % os.getpid(),
                                                source_populations_scalar = "source_populations_scalar_%d" % os.getpid())

        # Convert to source population points
        grass.run_command("r.to.vect",
                                                overwrite = True,
                                                input = "source_populations_scalar_corrected_%d" % os.getpid(),
                                                output = "source_points_%d" % os.getpid(),
                                                feature = "point")
        grass.run_command("v.db.addcol",
                                  map = "source_points_%d" % os.getpid(),
                                  columns = "prob DOUBLE")

        #populate sample prob from input prob-raster (multiplied by scalar)
        grass.run_command("v.what.rast",
                                        vector = "source_points_%d" % os.getpid(),
                                        raster = "source_populations_scalar_%d" % os.getpid(),
                                        column = "prob")

    #Adding columns and coordinates to source points
    grass.run_command("v.db.addcol",
                                      map = "source_points_%d" % os.getpid(),
                                      columns = "X DOUBLE, Y DOUBLE, Segment INT, Strahler INT")					
    grass.run_command("v.to.db",
                                      map = "source_points_%d" % os.getpid(),
                                      type = "point",
                                      option = "coor",
                                      columns = "X,Y")


    #Convert river from vector to raster format and get cat-value
    grass.run_command("v.to.rast",
                                      input = "river_vector_tmp_%d" % os.getpid(),
                                      overwrite = True,
                                      output = "river_raster_cat_tmp_%d" % os.getpid(),
                                      use = "cat")

    #Adding information of segment to source points					 
    grass.run_command("v.what.rast",
                                      vector = "source_points_%d" % os.getpid(),
                                      raster = "river_raster_cat_tmp_%d" % os.getpid(),
                                      column = "Segment")

    #Adding information of Strahler stream order to source points					 
    grass.run_command("v.what.rast",
                                      vector = "source_points_%d" % os.getpid(),
                                      raster = "strahler_tmp_%d" % os.getpid(),
                                      column = "Strahler") 

    # Make source points permanent
    grass.run_command("g.copy", 
            vect = "source_points_%d" % os.getpid() + "," + output + "_source_points")	

    ########### Looping over nrun, over segements, over source points ##########

    if str(options['statistical_interval']) == "no":
        nrun = ['fit']
    else:
        nrun = ['fit','lwr','upr']


    for i in nrun:
        database = sqlite3.connect(os.path.join(gisdbase, location, mapset, 'sqlite.db'))
        #update database-connection
        db = database.cursor()


        mapcalc_list_B = []

        # Loop over Segments
        for Segment in sorted(list(set(db.execute('SELECT Segment FROM source_points_%d ORDER BY Segment ASC' % os.getpid())))):
            grass.debug(_("This is segment nr.: " +str(Segment)))

            segment_cat = str(Segment[0])

            mapcalc_list_A = []

            # Loop over Source points
            source_points_loop = db.execute('SELECT cat, X, Y, prob, Strahler FROM source_points_%d WHERE Segment=?' % os.getpid(), (str(Segment[0]),))
            for cat,X,Y,prob,Strahler in source_points_loop:
                grass.debug(_("Start looping over source points"))

                coors = str(X)+","+str(Y)
                grass.debug(_("Source point coors:"+coors+" in segment nr: " +str(Segment)))

                #Select dispersal parameters
                SO = 'SO='+str(Strahler)
                grass.debug(_("This is i:"+str(i)))
                grass.debug(_("This is "+str(SO)))
                sigma_stat = fishmove.rx(i,'sigma_stat',1,1,SO,1)
                sigma_mob = fishmove.rx(i,'sigma_mob',1,1,SO,1)


                # Getting maximum distance (cutting distance) based on truncation criterion	  
                def func(x,sigma_stat,sigma_mob,m,truncation,p):
                    return p * stats.norm.cdf(x, loc=m, scale=sigma_stat) + (1-p) * stats.norm.cdf(x, loc=m, scale=sigma_mob) - truncation
                if options['truncation'] == "inf":
                    max_dist = 0
                else:
                    truncation = float(options['truncation'])
                    max_dist = int(optimize.zeros.newton(func, 1., args=(sigma_stat,sigma_mob,m,truncation,p)))


                grass.debug(_("Distance from each source point is calculated up to a treshold of: "+str(max_dist)))

                grass.run_command("r.cost",
                                          flags = 'n',
                                          overwrite = True,
                                          input = "river_raster_tmp_%d" % os.getpid(),
                                          output = "distance_from_point_tmp_%d" % os.getpid(),
                                          coordinate = coors,
                                          max_cost = max_dist)



                # Getting upper and lower distance (cell boundaries) based on the fact that there are different flow lenghts through a cell depending on the direction (diagonal-orthogonal)		  
                grass.mapcalc("$upper_distance = if($flow_direction==2||$flow_direction==4||$flow_direction==6||$flow_direction==8||$flow_direction==-2||$flow_direction==-4||$flow_direction==-6||$flow_direction==-8, $distance_from_point+($ds/2.0), $distance_from_point+($dd/2.0))",
                                        upper_distance = "upper_distance_tmp_%d" % os.getpid(),
                                        flow_direction = "flow_direction_tmp_%d" % os.getpid(),
                                        distance_from_point = "distance_from_point_tmp_%d" % os.getpid(), 
                                        ds = res,
                                        dd = math.sqrt(2)*res)

                grass.mapcalc("$lower_distance = if($flow_direction==2||$flow_direction==4||$flow_direction==6||$flow_direction==8||$flow_direction==-2||$flow_direction==-4||$flow_direction==-6||$flow_direction==-8, $distance_from_point-($ds/2.0), $distance_from_point-($dd/2.0))",
                                        lower_distance = "lower_distance_tmp_%d" % os.getpid(),
                                        flow_direction = "flow_direction_tmp_%d" % os.getpid(),
                                        distance_from_point = "distance_from_point_tmp_%d" % os.getpid(), 
                                        ds = res,
                                        dd = math.sqrt(2)*res)



                # MAIN PART: leptokurtic probability density kernel based on fishmove
                grass.debug(_("Begin with core of fidimo, application of fishmove on garray"))

                def cdf(x):
                    return (p * stats.norm.cdf(x, loc=m, scale=sigma_stat) + (1-p) * stats.norm.cdf(x, loc=m, scale=sigma_mob)) * prob


                #Calculation Kernel Density from Distance Raster
                #only for m=0 because of cdf-function
                if grass.find_file(name = "density_from_point_unmasked_tmp_%d" % os.getpid(), element = 'cell')['file']:
                    grass.run_command("g.remove", rast = "density_from_point_unmasked_tmp_%d" % os.getpid())

                x1 = garray.array()
                x1.read("lower_distance_tmp_%d" % os.getpid())
                x2 = garray.array()
                x2.read("upper_distance_tmp_%d" % os.getpid())
                Density = garray.array()
                Density[...] = cdf(x2) - cdf(x1)
                grass.debug(_("Write density from point to garray. unmasked"))
                Density.write("density_from_point_unmasked_tmp_%d" % os.getpid())

                # Mask density output because Density.write doesn't provide nulls()
                grass.mapcalc("$density_from_point = if($distance_from_point>=0, $density_from_point_unmasked, null())",
                                        density_from_point = "density_from_point_tmp_%d" % os.getpid(), 
                                        distance_from_point = "distance_from_point_tmp_%d" % os.getpid(), 
                                        density_from_point_unmasked = "density_from_point_unmasked_tmp_%d" % os.getpid())


                # Defining up and downstream of source point
                grass.debug(_("Defining up and downstream of source point"))

                # Defining area upstream source point
                grass.run_command("r.stream.basins",
                                          overwrite = True,
                                          dir = "flow_direction_tmp_%d" % os.getpid(),
                                          coors = coors,
                                          basins = "upstream_part_tmp_%d" % os.getpid())

                # Defining area downstream source point
                grass.run_command("r.drain",
                                                input = "distance_raster_tmp_%d" % os.getpid(),
                                                output = "downstream_drain_tmp_%d" % os.getpid(),
                                                overwrite = True,
                                                coordinate = coors)


                # Applying upstream split at network nodes based on inverse shreve stream order	
                grass.debug(_("Applying upstream split at network nodes based on inverse shreve stream order"))

                grass.mapcalc("$upstream_shreve = if($upstream_part, $shreve)",
                                        upstream_shreve = "upstream_shreve_tmp_%d" % os.getpid(), 
                                        upstream_part = "upstream_part_tmp_%d" % os.getpid(), 
                                        shreve = "shreve_tmp_%d" % os.getpid())	  
                max_shreve = grass.raster_info("upstream_shreve_tmp_%d" % os.getpid())['max']
                grass.mapcalc("$rel_upstream_shreve = $upstream_shreve / $max_shreve", 
                                        rel_upstream_shreve = "rel_upstream_shreve_tmp_%d" % os.getpid(), 
                                        upstream_shreve = "upstream_shreve_tmp_%d" % os.getpid(), 
                                        max_shreve = max_shreve)

                grass.mapcalc("$division_overlay = if(isnull($downstream_drain), $rel_upstream_shreve, $downstream_drain)", 
                                        division_overlay = "division_overlay_tmp_%d" % os.getpid(), 
                                        downstream_drain = "downstream_drain_tmp_%d" % os.getpid(), 
                                        rel_upstream_shreve = "rel_upstream_shreve_tmp_%d" % os.getpid())
                grass.mapcalc("$density = if($density_from_point, $density_from_point*$division_overlay, null())",
                                        density = "density_"+str(cat),
                                        density_from_point = "density_from_point_tmp_%d" % os.getpid(),
                                        division_overlay = "division_overlay_tmp_%d" % os.getpid())

                grass.run_command("r.null", map="density_"+str(cat), null="0")


                mapcalc_list_A.append("density_"+str(cat))	

            mapcalc_string_A1 = "+".join(mapcalc_list_A)
            mapcalc_string_A2 = ",".join(mapcalc_list_A)

            grass.mapcalc("$density_segment = $mapcalc_string_A1",
                                            density_segment = "density_segment_"+segment_cat,
                                            mapcalc_string_A1 = mapcalc_string_A1)

            grass.run_command("r.null", map="density_segment_"+segment_cat, setnull="0") # Final density map per segment without barriers



            grass.run_command("g.remove", rast = mapcalc_string_A2, flags ="f")

            ################### Barriers ########################
            if options['barriers']:

                grass.run_command("r.mask",
                                        flags="o",
                                        input = "river_raster_cat_tmp_%d" % os.getpid(),
                                        maskcats = segment_cat)


                #Create one single random point within analyzed segment
                grass.run_command("r.random",
                                        overwrite=True,
                                        input = "river_raster_cat_tmp_%d" % os.getpid(),
                                        n = 1,
                                        cover="MASK",
                                        vector_output="point_within_segment_tmp_%d" % os.getpid())

                #Important to remove mask after calculation
                grass.run_command("g.remove", rast = "MASK")   


                # Getting pseudo-flowdirection for defining upstream area
                grass.run_command("r.stream.basins",
                                                  overwrite = True,
                                                  dir = "flow_direction_tmp_%d" % os.getpid(),
                                                  points = "point_within_segment_tmp_%d" % os.getpid(),
                                                  basins = "upstream_segment_tmp_%d" % os.getpid())



                #Defining area upstream analyzed segment
                grass.run_command("r.cost",
                                          flags = 'n',
                                          overwrite = True,
                                          input = "river_raster_tmp_%d" % os.getpid(),
                                          output = "distance_from_point_within_segment_tmp_%d" % os.getpid(),
                                          start_points = "point_within_segment_tmp_%d" % os.getpid())

                #Remove "point within segment"
                grass.run_command("g.remove", vect = "point_within_segment_tmp_%d" % os.getpid())


                grass.mapcalc("$distance_upstream_point_within_segment = if($upstream_segment, $distance_from_point_within_segment, null())",
                                                distance_upstream_point_within_segment = "distance_upstream_point_within_segment_tmp_%d" % os.getpid(),
                                                upstream_segment ="upstream_segment_tmp_%d" % os.getpid(),
                                                distance_from_point_within_segment = "distance_from_point_within_segment_tmp_%d" % os.getpid())



                #Getting distance of barriers from segment and information if barrier is involved/affected
                grass.run_command("v.what.rast",
                                                vector = "barriers_%d" % os.getpid(),
                                                raster = "distance_upstream_point_within_segment_tmp_%d" % os.getpid(),
                                                column = "dist")

                grass.run_command("v.what.rast",
                                                vector = "barriers_%d" % os.getpid(),
                                                raster = "density_segment_"+segment_cat,
                                                column = "affected_barriers")


                #To find out if a loop over the affected barriers is the last loop (find the upstream most barrier)
                db.execute('SELECT MAX(dist) FROM barriers_%d WHERE affected_barriers > 0 AND dist > 0 ORDER BY dist' % os.getpid())
                last_barrier = db.fetchone()[0]


                # Loop over the affected barriers (from most downstream barrier to most upstream barrier)
                # Initally affected = all barriers where density > 0
                for cat,adj_X,adj_Y,dist,passability in db.execute('SELECT cat, adj_X, adj_Y, dist, passability FROM barriers_%d WHERE affected_barriers > 0 AND dist > 0 ORDER BY dist' % os.getpid()):
                    coors_barriers = str(adj_X)+","+str(adj_Y)

                    grass.debug(_("Starting with corrections for barriers"))

                    #Defining upstream the barrier
                    grass.run_command("r.stream.basins",
                                              overwrite = True,
                                              dir = "flow_direction_tmp_%d" % os.getpid(),
                                              coors = coors_barriers,
                                              basins = "upstream_barrier_tmp_%d" % os.getpid())

                    #Getting density upstream barrier only
                    grass.mapcalc("$upstream_density = if($upstream_barrier, $density_segment, null())",
                                            upstream_density = "upstream_density_tmp_%d" % os.getpid(), 
                                            upstream_barrier = "upstream_barrier_tmp_%d" % os.getpid(), 
                                            density_segment = "density_segment_"+segment_cat)

                    #Getting sum of upstream density and density to relocate downstream
                    d = {'n':5, 'min': 6, 'max': 7, 'mean': 9, 'sum': 14, 'median':16, 'range':8}
                    univar = grass.read_command("r.univar", map = "upstream_density_tmp_%d" % os.getpid(), flags = 'e')
                    if univar:
                        upstream_density = float(univar.split('\n')[d['sum']].split(':')[1])
                    else:
                        # if no upstream density to allocate than stop that "barrier-loop" and contiue with next barrier
                        grass.message(_("No upstream denisty to allocate downstream for that barrier: "+coors_barriers))
                        continue



                    density_for_downstream = upstream_density*(1-passability)


                    # barrier_effect = Length of Effect of barriers (linear decrease up to max (barrier_effect)
                    barrier_effect=200 #units as in mapset (m)

                    # Calculating distance from barriers (up- and downstream)
                    grass.run_command("r.cost",
                                              overwrite = True,
                                              input = "river_raster_tmp_%d" % os.getpid(),
                                              output = "distance_barrier_tmp_%d" % os.getpid(),
                                              coordinate = coors_barriers,
                                              max_cost=barrier_effect)


                    # Getting distance map for downstream of barrier only
                    grass.mapcalc("$distance_barrier_downstream = if(isnull($upstream_barrier) && $distance_barrier < $barrier_effect, $distance_barrier, null())",
                                            distance_barrier_downstream = "distance_barrier_downstream_tmp_%d" % os.getpid(),
                                            upstream_barrier = "upstream_barrier_tmp_%d" % os.getpid(), 
                                            distance_barrier = "distance_barrier_tmp_%d" % os.getpid(),
                                            barrier_effect = barrier_effect)

                    # Getting parameters for distance weighted relocation of densities below the barrier (linear decrease)
                    univar = grass.read_command("r.univar", map = "distance_barrier_downstream_tmp_%d" % os.getpid(), flags = 'e')
                    sum_distance_downstream_barrier = float(univar.split('\n')[d['sum']].split(':')[1])
                    number_distance_downstream_barrier = float(univar.split('\n')[d['n']].split(':')[1])
                    max_distance_downstream_barrier = float(univar.split('\n')[d['max']].split(':')[1])

                    a = density_for_downstream/(number_distance_downstream_barrier-sum_distance_downstream_barrier/max_distance_downstream_barrier)	

                    #Remove any old density_below_barrier map	 
                    grass.run_command("g.remove", rast = "density_below_barrier_tmp_%d" % os.getpid())

                    #Calculation Kernel Density downstream the barrier	
                    grass.mapcalc("$density_below_barrier = $a-($a/$distance_max)*$distance_barrier_downstream",
                                            density_below_barrier = "density_below_barrier_tmp_%d" % os.getpid(),
                                            a = a, 
                                            distance_max = max_distance_downstream_barrier,
                                            distance_barrier_downstream = "distance_barrier_downstream_tmp_%d" % os.getpid())				

                    # Combination upstream and downstream density from barrier
                    grass.run_command("r.null", map="density_segment_"+str(Segment[0]), null="0")
                    grass.run_command("r.null", map="density_below_barrier_tmp_%d" % os.getpid(), null="0")

                    grass.mapcalc("$density_segment = if(isnull($upstream_barrier), $density_below_barrier+$density_segment, $upstream_density*$passability)",
                                            density_segment = "density_segment_"+str(Segment[0]), 
                                            upstream_barrier = "upstream_barrier_tmp_%d" % os.getpid(), 
                                            density_below_barrier = "density_below_barrier_tmp_%d" % os.getpid(),
                                            upstream_density = "upstream_density_tmp_%d" % os.getpid(),
                                            passability=passability)

                    if dist == last_barrier :
                        grass.run_command("r.null", map="density_segment_"+segment_cat, null="0")
                    else:
                        grass.run_command("r.null", map="density_segment_"+segment_cat, setnull="0")


            grass.run_command("r.null", map="density_segment_"+segment_cat, null="0") # Final density map per segment


            mapcalc_list_B.append("density_segment_"+segment_cat)



        mapcalc_string_B1 = "+".join(mapcalc_list_B)
        mapcalc_string_B2 = ",".join(mapcalc_list_B)

        # Final raster map, Final map is sum of all 
        # density maps (for each segement), All contirbuting maps (string_B2) are deleted
        # in the end.
        grass.mapcalc("$density_final = $mapcalc_string_B1",
                                        density_final = "density_final_%d" % os.getpid(),
                                        mapcalc_string_B1 = mapcalc_string_B1)

        # backtransformation (divide by scalar which was defined before)
        grass.mapcalc("$density_final_corrected = $density_final/$scalar",
                                        density_final_corrected = "density_final_corrected_%d" % os.getpid(),
                                        density_final = "density_final_%d" % os.getpid(),
                                        scalar = scalar)

        grass.run_command("g.copy", 
                rast = "density_final_corrected_%d" % os.getpid() + "," + output+"_"+i)



        # Set all 0-values to NULL, Backgroundvalues			
        grass.run_command("r.null", map=output+"_"+i, setnull="0")


        grass.run_command("g.remove", rast = mapcalc_string_B2, flags ="f")


    # Delete basic maps if flag "b" is set	 
    if flags['b']:
        grass.run_command("g.remove", vect = output + "_source_points", flags ="f")
        if options['barriers']:
            grass.run_command("g.remove", vect = output + "_barriers", flags ="f")


    return 0


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())
