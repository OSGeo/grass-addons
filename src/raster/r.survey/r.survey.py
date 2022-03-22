#!/usr/bin/env python3

############################################################################
# MODULE:    r.survey
#
# AUTHOR(S): Ivan Marchesini and Txomin Bornaetxea
#
# PURPOSE:   Define solid angle, 3d distance and view angles area
# from multiple survey locations (points). Survey points can be at any elevation
# above ground level. 3d points, representing drone/aerial positions, are allowed
# Outputs are:
# maximum solid angle each pixel is visible from survey points
# maximum view angle each pixel is visible from survey points
# minimum 3d distance each pixel is visible from survey points
# number of survey points each pixel is visible from
# identifier of the survey point having the minimum 3d distance to each given pixel
# identifier of the survey point having the maximum solid angle to each given pixel
# identifier of the survey point having the maximum view angle angle to each given pixel
# The modulel runs in parallel but if too many processes are used it can fail due to problem
# in the management of the temporary_regions. In this case please reduce the
# number of processes.
#
# COPYRIGHT: (C) 2021 Ivan Marchesini and Txomin Bornaetxea, and by the GRASS Development Team
#
#           This program is free software under the GNU General Public
#           License (>=v2). Read the file COPYING that comes with GRASS
#           for details.
#############################################################################

# %Module
# % description: Returns maps of visibility indexes (3d distance, view angle and solid angle) from multiple survey points
# % keywords: raster
# % keywords: visibility
# % keywords: survey
# %end
# %option G_OPT_V_INPUT
# % key: points
# % description: Name of the input points map  (representing the survey location)
# % required: yes
# %end
# %option G_OPT_R_INPUT
# % key: dem
# % description: Name of the input DEM layer
# % required: yes
# %end
# %option G_OPT_R_OUTPUT
# % key: output
# % description: Prefix for the output visibility layers
# % required: yes
# %end
# %option
# % key: maxdist
# % type: double
# % description: max distance from the input points
# % required: yes
# % answer: 1000
# %end
# %option G_OPT_V_INPUT
# % key: treesmap
# % description: Name of the vector layer representing the forested areas
# % required: no
# %end
# %option G_OPT_V_INPUT
# % key: buildingsmap
# % description: Name of the vector layer representing the buildings
# % required: no
# %end
# %option
# % key: obs_heigh
# % description: observer_elevation
# % type: double
# % required: yes
# % answer: 1.75
# %end
# %option
# % key: treesheigh
# % description: field of the attribute table containing information about average threes heigh
# % type: string
# % required: no
# %end
# %option
# % key: treesheighdeviation
# % description: field of the attribute table containing information about standard deviation value relate to the heigh
# % type: string
# % required: no
# %end
# %option
# % key: buildingsheigh
# % description: field of the attribute table containing information about buildings heigh
# % type: string
# % required: no
# %end
# %option
# % key: obsabselev
# % description: field of the attribute table containing information about observer absolute elevation above the same datum used by the DEM (e.g. geodetic elevation)
# % type: string
# % required: no
# %end
# %option
# % key: layer
# % description: layer of the attribute table of the point map (can be usefull for obsabselev option)
# % type: string
# % answer: 1
# % required: no
# %end
# %option
# % key: viewangle_threshold
# % description: cut the output layers at a given threshold value (between 90 and 180 degrees)
# % gisprompt: 90-180
# % type: double
# % required: yes
# %answer: 90
# %end
# %option
# % key: object_radius
# % description: radius of the surveyed object in unit of map (default is half the DEM resolution)
# % type: double
# % required: no
# %end
# %option
# % key: nprocs
# % description: Number of processes
# % answer: 1
# % type: integer
# required: yes
# %end
# %option
# % key: memory
# % description: Amount of memory to use in MB (for r.viewshed analysis)
# % answer: 500
# % type: integer
# required: no
# %end
# %flag
# % key: b
# % description: Create a simple visible-not visible raster map
# %end
# %flag
# % key: c
# % description: Consider the curvature of the earth (current ellipsoid)
# %end
# %flag
# % key: d
# % description: allow only downward view direction (can be used for drone view)
# %end


# Importing modules
import atexit
from subprocess import PIPE
from grass.script import parser, parse_key_val
from grass.pygrass.modules import Module
import multiprocessing
import threading
import sys
import grass.script as gscript
from grass.script import core as grasscore
from math import pi

# are we in LatLong location?
s = gscript.read_command("g.proj", flags="j")
kv = gscript.parse_key_val(s)
if kv["+proj"] == "longlat":
    # gscript.fatal(_("This module does not operate in LatLong locations"))
    gscript.fatal("This module does not operate in LatLong locations")
    sys.exit()

# Verifying that there are no layers with the same name as the temporary layers created during the processes
g_list_xx = Module("g.list", type='raster', pattern="xx*", quiet=True,  stdout_=PIPE)
g_list_zz = Module("g.list", type='raster', pattern="zz*", quiet=True,  stdout_=PIPE)
g_list_kk = Module("g.list", type='raster', pattern="kk*", quiet=True,  stdout_=PIPE)
g_list_trees = Module("g.list", type='raster', pattern="treesmap", quiet=True,  stdout_=PIPE)
g_list_build = Module("g.list", type='raster', pattern="buildmap", quiet=True,  stdout_=PIPE)
g_list_mask = Module("g.list", type='raster', pattern="maskera", quiet=True,  stdout_=PIPE)


list_x = list(parse_key_val(g_list_xx.outputs.stdout))
list_z = list(parse_key_val(g_list_zz.outputs.stdout))
list_k = list(parse_key_val(g_list_zz.outputs.stdout))
list_tree = list(parse_key_val(g_list_trees.outputs.stdout))
list_build = list(parse_key_val(g_list_build.outputs.stdout))
list_mask = list(parse_key_val(g_list_mask.outputs.stdout))

lista = list_x + list_z + list_k + list_tree + list_build + list_mask

n = len(lista)

if n != 0:
    message = f"*** Exit System. Please rename or remove all the layers in the mapset having names starting with 'xx*' , 'zz*' , 'kk*' or named as 'treesmap', 'buildmap' or 'maskera' to prevent overwriting and removing them ***"
    gscript.error(message)
    sys.exit()
else:
    pass

# Verify if there is a MASK. In such a case, a copy of the MASK layer is saved to replace it at the end of the process
find_MASK = gscript.find_file("MASK", element='cell')
if find_MASK['name'] != "":
    message = "A MASK layer was found. It will be copied and updated later by the end of the process"
    gscript.warning(message)
    Module("g.copy", raster=('MASK', 'maskera'))


# function for cleaning temporary layers
def cleanup():
    message = " *** Cleaning all temporary maps *** "
    gscript.message(message)
    Module("g.remove", type='vector', pattern="xxtemp*", quiet=True, flags="f")
    Module("g.remove", type='vector', pattern="zzpnt*", quiet=True, flags="f")
    Module("g.remove", type='raster', pattern="xx*", quiet=True, flags="f")
    Module("g.remove", type='raster', pattern="zz*", quiet=True, flags="f")
    Module("g.remove", type='raster', pattern="kk*", quiet=True, flags="f")
    dem = general.dem
    find_dem_modified = gscript.find_file("zz"+dem+"_modified", element='cell')
    if find_dem_modified['name'] != "":
        Module("g.remove", type='raster', name="zz"+dem+"_modified", quiet=True, flags="f")
    find_dem_modified = gscript.find_file("zz"+dem+"_modified_full", element='cell')
    if find_dem_modified['name'] != "":
        Module("g.remove", type='raster', name="zz"+dem+"_modified_full", quiet=True, flags="f")
    if main.treesmap:
        find_treesmap = gscript.find_file(main.treesmap, element='cell')
        if find_treesmap['name'] != "":
            Module("g.remove", type='raster', name=main.treesmap, quiet=True, flags="f")
    if main.buildmap:
        find_buildmap = gscript.find_file(main.buildmap, element='cell')
        if find_buildmap['name'] != "":
            Module("g.remove", type='raster', name=main.buildmap, quiet=True, flags="f")
    # Removing the MASK based on the viewangle_threshold
    find_MASK = gscript.find_file("MASK", element='cell')
    if find_MASK['name'] != "":
        Module("r.mask", flags="r")
    # Replacing the original MASK in the mapset and removing the temporary copy "maskera"
    find_maskera = gscript.find_file("maskera", element='cell')
    if find_maskera['name'] != "":
        Module("r.mask", raster="maskera")
        message = "replacing the original MASK in the mapset"
        gscript.message(message)
        Module("g.remove", type='raster', name="maskera", quiet=True, flags="f")


# starting function. needed for preparing the data
def general(pnt, dem, treesmap, buildmap, treesheigh, treesheighdeviation, buildheigh, obsabselev):
    # raster points
    Module("v.to.rast", input=pnt, output="xxrastpnt", type="point", use="val", quiet=True)
    # altering DEM in case there are buldings and trees map (to obtain a sort of DSM) and in case observer is not flying, the dem is kept to the ground level at observer positions
    if treesmap and buildmap:
        Module("r.surf.gauss", output="xxgaussianmap", mean=0, sigma=1, quiet=True)
        Module("v.to.rast", input=treesmap, output=treesmap, use="attr", attribute_column=treesheigh, quiet=True)
        Module("v.to.rast", input=treesmap, output="xxtreesdeviationmap", use="attr", attribute_column=treesheighdeviation, quiet=True)
        Module("v.to.rast", input=buildmap, output=buildmap, use="attr", attribute_column=buildheigh, quiet=True)
        Module("r.mapcalc", expression="{B} =  {A}*{C}".format(A="xxgaussianmap", B="xxtruedeviation", C="xxtreesdeviationmap"), quiet=True)
        Module("r.mapcalc", expression="{B} =  {A}+{C}".format(A=treesmap, B=treesmap, C="xxtruedeviation"), overwrite=True, quiet=True)
        Module("r.mapcalc", expression="{A} = if(isnull({B}),{C},{B})".format(A="zztreesbuildingmap", B=buildmap, C=treesmap), quiet=True)
        Module("r.mapcalc", expression="{B} = if(isnull({A}),{C},{C}+{A})".format(A="zztreesbuildingmap", B="zz"+dem+"_modified_full", C=dem), quiet=True)
        Module("r.mapcalc", expression="{B} = if(isnull({A}),{D},{C})".format(A="xxrastpnt", B="zz"+dem+"_modified", C=dem, D="zz"+dem+"_modified_full"), quiet=True)
        if obsabselev:
            dem = "zz"+dem+"_modified_full"
        else:
            dem = "zz"+dem+"_modified"
    elif treesmap and not buildmap:
        Module("r.surf.gauss", output="xxgaussianmap", mean=0, sigma=1, quiet=True)
        Module("v.to.rast", input=treesmap, output=treesmap, use="attr", attribute_column=treesheigh, quiet=True)
        Module("v.to.rast", input=treesmap, output="xxtreesdeviationmap", use="attr", attribute_column=treesheighdeviation, quiet=True)
        Module("r.mapcalc", expression="{B} =  {A}*{C}".format(A="xxgaussianmap", B="xxtruedeviation", C="xxtreesdeviationmap"), quiet=True)
        Module("r.mapcalc", expression="{B} =  {A}+{C}".format(A=treesmap, B=treesmap, C="xxtruedeviation"), overwrite=True, quiet=True)
        Module("r.mapcalc", expression="{B} = if(isnull({A}),{C},{C}+{A})".format(A=treesmap, B="zz"+dem+"_modified_full", C=dem), quiet=True)
        Module("r.mapcalc", expression="{B} = if(isnull({A}),{D},{C})".format(A="xxrastpnt", B="zz"+dem+"_modified", C=dem, D="zz"+dem+"_modified_full"), quiet=True)
        if obsabselev:
            dem = "zz"+dem+"_modified_full"
        else:
            dem = "zz"+dem+"_modified"
    elif buildmap and not treesmap:
        Module("v.to.rast", input=buildmap, output=buildmap, use="attr", attribute_column=buildheigh, quiet=True)
        Module("r.mapcalc", expression="{B} = if(isnull({A}),{C},{C}+{A})".format(A=buildmap, B="zz"+dem+"_modified_full", C=dem), quiet=True)
        Module("r.mapcalc", expression="{B} = if(isnull({A}),{D},{C})".format(A="xxrastpnt", B="zz"+dem+"_modified", C=dem, D="zz"+dem+"_modified_full"), quiet=True)
        if obsabselev:
            dem = "zz"+dem+"_modified_full"
        else:
            dem = "zz"+dem+"_modified"
    # preparing the maps of the orientation of the DEM
    Module("r.slope.aspect", elevation=dem, slope="zzslope", aspect="zzaspect", quiet=True)
    # evaluation of the azimuth layer
    Module("r.mapcalc", expression="zzazimuth = (450-zzaspect) - int( (450-zzaspect) / 360) * 360", quiet=True)
    # evaluation of the layer of the vertical component of the versor perpendicular to the terrain slope
    Module("r.mapcalc", expression="zzc_dem = cos(zzslope)", quiet=True)
    # evaluation of the layer of the north component of the versor perpendicular to the terrain slope
    Module("r.mapcalc", expression="zzb_dem = sin(zzslope)*cos(zzazimuth)", quiet=True)
    # evaluation of the layer of the east component of the versor perpendicular to the terrain slope
    Module("r.mapcalc", expression="zza_dem = sin(zzslope)*sin(zzazimuth)", quiet=True)
    # creating a list of the categories of the available points in the input layer
    ret = Module('v.info', flags='t', map=pnt, stdout_=PIPE)
    stats = parse_key_val(ret.outputs.stdout)
    npnt = stats['points']
    ctg2 = Module("v.category", flags="g", input=pnt, option="print", type="point", stdout_=PIPE)
    ctg = ctg2.outputs.stdout.splitlines()
    # exporting variables for other functions
    general.ctg = ctg
    general.npnt = npnt
    general.dem = dem


# iterative function. needed for preparing the data for the parallel computation
def iterate(pnt, dem, obs_heigh, maxdist, hcurv, downward, oradius, ctg, nprocs, obsabselev, memory):
    # creating the list which will contain the parameters to be used to run the "compute function in parallel
    tasks = []
    k = 0
    # starting the main loop for each point in the point input layer
    for i in ctg:
        # the following i=2 can be uncommented for testing the loop
        # i=2
        k = k+1
        # appending the parameters needed for running the code in parallel to the task list
        tasks.append((pnt, dem, obs_heigh, maxdist, hcurv, downward, oradius, i, nprocs, obsabselev, memory))
        # exporting variables needed by other functions
        iterate.tasks = tasks


# the following is needed to definea a lag between the start of the parallel processes. In fact the definition of the temporary region in grass can fail if manny processes set it at the same time
def init(lock):
    global starting
    starting = lock


# function that is run iterativelly for each point location. It is used in parallell using multiprocessing.pool
def compute(pnt, dem, obs_heigh, maxdist, hcurv, downward, oradius, i, nprocs, obsabselev, memory):
    try:
        # the followig lines help to set a delay between a process and the others
        starting.acquire()  # no other process can get it until it is released
        threading.Timer(0.1, starting.release).start()  # release in a 0.1 seconds
        # using temporary regions (on the same mapset) for the different parallel computations
        gscript.use_temp_region()
        # extracting a point from the map of the locations
        Module("v.extract", input=pnt, output="zzpnt"+i, cats=i, flags="t", quiet=True)
        # getting goordinates of the point location
        coords = Module("v.to.db", flags="p", map="zzpnt"+i, type="point", option="coor", separator="|", stdout_=PIPE)
        coords = coords.outputs.stdout.splitlines()[1:][0]
        x = float(coords.split("|")[1])
        y = float(coords.split("|")[2])
        z = float(coords.split("|")[3])
        coords = str(x)+","+str(y)
        # get elevation of the terrain at the point location
        querydem = Module("r.what", coordinates=coords.split(), map=dem, stdout_=PIPE)
        obselev = float(querydem.outputs.stdout.split("|")[3])
        # setting the working region around the point location
        Module("g.region", vector="zzpnt"+i)
        region = grasscore.region()
        E = region['e']
        W = region['w']
        N = region['n']
        S = region['s']
        # Module("g.region", flags="a", e=E+maxdist, w=W-maxdist, s=S-maxdist, n=N+maxdist)
        Module("g.region", align=dem, e=E+maxdist, w=W-maxdist, s=S-maxdist, n=N+maxdist)
        # now we check if the size of the object for which we calculate solid angle in each pixel is equal to half the resolution or is set by the user
        if oradius == 0:
            circle_radius = region['nsres']/2
        else:
            circle_radius = oradius
        # Executing viewshed analysis
        if obsabselev:
            # Relative height of observer above the dem/dsm
            relative_height = z - obselev
            if hcurv:
                Module("r.viewshed", input=dem, output="zzview"+i, coordinates=coords.split(), memory=memory, observer_elevation=relative_height, max_distance=maxdist, flags="c", quiet=True)
            else:
                Module("r.viewshed", input=dem, output="zzview"+i, coordinates=coords.split(), memory=memory, observer_elevation=relative_height, max_distance=maxdist, quiet=True)
            if downward:
                # Since UAV nor Satellite are not expected to see above their level (they are only looking to the ground) vertical angles above 90 are set to null.
                Module("r.mapcalc", expression="zzview{I} = if(zzview{I}>90 && zzview{I}<180,null(),zzview{I})".format(I=i), overwrite=True, quiet=True)
        else:
            if hcurv:
                Module("r.viewshed", input=dem, output="zzview"+i, coordinates=coords.split(), memory=memory, observer_elevation=obs_heigh, max_distance=maxdist, flags="c", quiet=True)
            else:
                Module("r.viewshed", input=dem, output="zzview"+i, coordinates=coords.split(), memory=memory, observer_elevation=obs_heigh, max_distance=maxdist, quiet=True)
        # Since r.viewshed set the cell of the output visibility layer to 180 under the point, this cell is set to 0.0
        Module("r.mapcalc", expression="zzview{I} = if(zzview{I}==180,0,zzview{I})".format(I=i), overwrite=True, quiet=True)
        # estimating the layer of the horizontal angle between point and each visible cell (angle of the horizontal line of sight)
        Module("r.mapcalc", expression="{A} = \
            if( y()>{py} && x()>{px}, atan(({px}-x())/({py}-y())),  \
            if( y()<{py} && x()>{px}, 180+atan(({px}-x())/({py}-y())),  \
            if( y()<{py} && x()<{px}, 180+atan(({px}-x())/({py}-y())),  \
            if( y()>{py} && x()<{px}, 360+atan(({px}-x())/({py}-y())), \
            if( y()=={py} && x()>{px}, 90, \
            if( y()<{py} && x()=={px}, 180, \
            if( y()=={py} && x()<{px}, 270, \
            if( y()>{py} && x()=={px}, 0 \
            ) ) ) ) ) ) ) )".format(A='zzview_angle'+i, py=y, px=x), quiet=True)
        # estimating the layer of the vertical angle between point and each visible cell  (angle of the vertical line of sight) ()
        Module("r.mapcalc", expression="zzview90_{I} = zzview{I} - 90".format(I=i), quiet=True)
        # evaluate the vertical component of the versor oriented along the line of sight
        Module("r.mapcalc", expression="zzc_view{I} = sin(zzview90_{I})".format(I=i), quiet=True)
        # evaluate the northern component of the versor oriented along the line of sight
        Module("r.mapcalc", expression="zzb_view{I} = cos(zzview90_{I})*cos(zzview_angle{I})".format(I=i), quiet=True)
        # evaluate the eastern component of the versor oriented along the line of sight
        Module("r.mapcalc", expression="zza_view{I} = cos(zzview90_{I})*sin(zzview_angle{I})".format(I=i), quiet=True)
        # estimate the three-dimensional distance between the point and each visible cell
        if obsabselev:
            if hcurv:
                j = gscript.read_command("g.proj", flags="j", quiet=True)
                kvj = gscript.parse_key_val(j)
                eradius = kvj['+a']  # This is the radius of the earth for the elipsoid in the current projection
                Module("r.mapcalc", expression="{D} = pow(pow(abs(y()-{py}),2)+pow(abs(x()-{px}),2),0.5)".format(D='zzeuclidean'+i, py=y, px=x), quiet=True)  # Planar distance
                Module("r.mapcalc", expression="{D} = pow({B},2)/(2*{C})".format(D='zzdtm_correction'+i, B='zzeuclidean'+i, C=eradius), quiet=True)  # Value to substract to the original dem
                Module("r.mapcalc", expression="{D} = {dtm}-{B}".format(D='zzdtm_correct'+i, dtm=dem, B='zzdtm_correction'+i), quiet=True)  # This line can be combined with the previous one
                Module("r.mapcalc", expression="{D} = pow(pow(abs(y()-{py}),2)+pow(abs(x()-{px}),2)+pow(abs({dtm}-{Z}),2),0.5)".format(D='zzdistance'+i, dtm='zzdtm_correct'+i, Z=z, py=y, px=x), quiet=True)
            else:
                Module("r.mapcalc", expression="{D} = pow(pow(abs(y()-{py}),2)+pow(abs(x()-{px}),2)+pow(abs({dtm}-{Z}),2),0.5)".format(D='zzdistance'+i, dtm=dem, Z=z, py=y, px=x), quiet=True)
        else:
            if hcurv:
                j = gscript.read_command("g.proj", flags="j", quiet=True)
                kvj = gscript.parse_key_val(j)
                eradius = kvj['+a']  # This is the radius of the earth for the elipsoid in the current projection
                Module("r.mapcalc", expression="{D} = pow(pow(abs(y()-{py}),2)+pow(abs(x()-{px}),2),0.5)".format(D='zzeuclidean'+i, py=y, px=x), quiet=True)  # Planar distance
                Module("r.mapcalc", expression="{D} = pow({B},2)/(2*{C})".format(D='zzdtm_correction'+i, B='zzeuclidean'+i, C=eradius), quiet=True)  # Value to substract to the original dem
                Module("r.mapcalc", expression="{D} = {dtm}-{B}".format(D='zzdtm_correct'+i, dtm=dem, B='zzdtm_correction'+i), quiet=True)  # This line can be combined with the previous one
                Module("r.mapcalc", expression="{D} = pow(pow(abs(y()-{py}),2)+pow(abs(x()-{px}),2)+pow(abs({dtm}-({obs}+{obs_h})),2),0.5)".format(D='zzdistance'+i, dtm='zzdtm_correct'+i, obs=obselev, obs_h=obs_heigh, py=y, px=x), quiet=True)
            else:
                Module("r.mapcalc", expression="{D} = pow(pow(abs(y()-{py}),2)+pow(abs(x()-{px}),2)+pow(abs({dtm}-({obs}+{obs_h})),2),0.5)".format(D='zzdistance'+i, dtm=dem, obs=obselev, obs_h=obs_heigh, py=y, px=x), quiet=True)

        # estimating the layer of the angle between the versor of the terrain and the line of sight
        if hcurv:
            # Calculating the theta angle of the arc of the surface in degrees
            Module("r.mapcalc", expression="{D} = ({B}/{C})*(180/{pi})".format(D='zzarc'+i, B='zzeuclidean'+i, C=eradius, pi=pi), quiet=True)
            # Calculating the horizontal orientation of the K versor, which is perpendicular to the angle of the horizontal line of sight (zzview_angle)
            Module("r.mapcalc", expression="kkview_angle{I} = if(y()>{py} && x()>={px}, zzview_angle{I}+270, zzview_angle{I}-90)".format(I=i, py=y, px=x), quiet=True)
            # Calculating the 3 components of the K versor
            Module("r.mapcalc", expression="kkc_view{I} = 0".format(I=i), quiet=True)
            Module("r.mapcalc", expression="kkb_view{I} = cos(kkview_angle{I})".format(I=i), quiet=True)
            Module("r.mapcalc", expression="kka_view{I} = sin(kkview_angle{I})".format(I=i), quiet=True)
            # Starting the calculations for the application of the RODRIGUES' ROTATION FORMULA
            # Calculating the dot product between K and zzdem versors
            Module("r.mapcalc", expression="zz_dotproduct{I} = kka_view{I}*zza_dem + kkb_view{I}*zzb_dem + kkc_view{I}*zzc_dem".format(I=i), quiet=True)
            # Calculating a, b and c components for the first part of the equation (K(K · V)/(1-cos(theta)))
            Module("r.mapcalc", expression="zzc_equation_first{I} = kkc_view{I}*zz_dotproduct{I}*(1-cos({B}))".format(I=i, B='zzarc'+i), quiet=True)
            Module("r.mapcalc", expression="zzb_equation_first{I} = kkb_view{I}*zz_dotproduct{I}*(1-cos({B}))".format(I=i, B='zzarc'+i), quiet=True)
            Module("r.mapcalc", expression="zza_equation_first{I} = kka_view{I}*zz_dotproduct{I}*(1-cos({B}))".format(I=i, B='zzarc'+i), quiet=True)
            # Calculating a, b and c components for the second part of the equation (V * cos(theta))
            Module("r.mapcalc", expression="zzc_equation_second{I} = zzc_dem*cos({B})".format(I=i, B='zzarc'+i), quiet=True)
            Module("r.mapcalc", expression="zzb_equation_second{I} = zzb_dem*cos({B})".format(I=i, B='zzarc'+i), quiet=True)
            Module("r.mapcalc", expression="zza_equation_second{I} = zza_dem*cos({B})".format(I=i, B='zzarc'+i), quiet=True)
            # Calculating a, b and c components for the sthird part of the equation (sin(theta)(K x V))
            Module("r.mapcalc", expression="zzc_equation_third{I} = sin({B})*(kka_view{I}*zzb_dem - kkb_view{I}*zza_dem)".format(I=i, B='zzarc'+i), quiet=True)
            Module("r.mapcalc", expression="zzb_equation_third{I} = sin({B})*(kkc_view{I}*zza_dem - kka_view{I}*zzc_dem)".format(I=i, B='zzarc'+i), quiet=True)
            Module("r.mapcalc", expression="zza_equation_third{I} = sin({B})*(kkb_view{I}*zzc_dem - kkc_view{I}*zzb_dem)".format(I=i, B='zzarc'+i), quiet=True)

            # Calculating the vertical, north and east components of the rotated versor of the terrain
            Module("r.mapcalc", expression="zzc_dem_curv{I} = zzc_equation_first{I} + zzc_equation_second{I} + zzc_equation_third{I}".format(I=i), quiet=True)
            Module("r.mapcalc", expression="zzb_dem_curv{I} = zzb_equation_first{I} + zzb_equation_second{I} + zzb_equation_third{I}".format(I=i), quiet=True)
            Module("r.mapcalc", expression="zza_dem_curv{I} = zza_equation_first{I} + zza_equation_second{I} + zza_equation_third{I}".format(I=i), quiet=True)

            # calculating the view angle corrected according to the earth curvature distortion.
            Module("r.mapcalc", expression="zzangle{I} = acos((zza_view{I}*zza_dem_curv{I}+zzb_view{I}*zzb_dem_curv{I}+zzc_view{I}*zzc_dem_curv{I})/(sqrt(zza_view{I}*zza_view{I}+zzb_view{I}*zzb_view{I}+zzc_view{I}*zzc_view{I})*sqrt(zza_dem_curv{I}*zza_dem_curv{I}+zzb_dem_curv{I}*zzb_dem_curv{I}+zzc_dem_curv{I}*zzc_dem_curv{I})))".format(I=i), quiet=True)
        else:
            Module("r.mapcalc", expression="zzangle{I} = acos((zza_view{I}*zza_dem+zzb_view{I}*zzb_dem+zzc_view{I}*zzc_dem)/(sqrt(zza_view{I}*zza_view{I}+zzb_view{I}*zzb_view{I}+zzc_view{I}*zzc_view{I})*sqrt(zza_dem*zza_dem+zzb_dem*zzb_dem+zzc_dem*zzc_dem)))".format(I=i), quiet=True)
        # filtering 3d distance based on angle{I} map
        Module("r.mapcalc", expression="{D} = if(isnull(zzangle{I}),null(),{D})".format(D="zzdistance"+str(i), I=i), overwrite=True, quiet=True)
        # calculating H1 and H2 that are the distances from the observer to the more distant and less distant points of the inclinded circle representing the pixel
        Module("r.mapcalc", expression="zzH1_{I} = pow(pow({r},2)+pow({d},2)-(2*{r}*{d}*cos(270-zzangle{I})),0.5)".format(r=circle_radius, d="zzdistance"+str(i), I=i), quiet=True)
        Module("r.mapcalc", expression="zzH2_{I} = pow(pow({r},2)+pow({d},2)-(2*{r}*{d}*cos(zzangle{I}-90)),0.5)".format(r=circle_radius, d="zzdistance"+str(i), I=i), quiet=True)
        # calculating B1 and B2 that are the angles between the line passing through the observer and the center of the pixel and the distant and less distant points of the inclinded circle representing the pixel
        Module("r.mapcalc", expression="zzB1_{I} = acos( (pow({r},2)-pow(zzH1_{I},2)-pow({d},2)) / (-2*zzH1_{I}*{d}) ) ".format(r=circle_radius, d="zzdistance"+str(i), I=i), quiet=True)
        Module("r.mapcalc", expression="zzB2_{I} = acos( (pow({r},2)-pow(zzH2_{I},2)-pow({d},2)) / (-2*zzH2_{I}*{d}) ) ".format(r=circle_radius, d="zzdistance"+str(i), I=i), quiet=True)
        # calculating solid angle considering that the area of an asimetric ellipse is equal to the one of an ellipse having the minor axis equal to the sum of the tqo unequal half minor axes
        Module("r.mapcalc", expression="zzsangle{I} = ({pi}*{r}*( {d}*tan(zzB1_{I}) + {d}*tan(zzB2_{I}) )/2 )  / (pow({r},2)+pow({d},2)) ".format(r=circle_radius, d="zzdistance"+str(i), I=i, pi=pi), quiet=True)
        # approximations for calculating solid angle can create too much larger values under or very close the position of the oserver. in such a case we assume that the solid angle is half of the visible sphere (2*pi)
        # The same occur when it is used an object_radius that is larger than thepixel size. In some cases this can produce negative values of zzB2 whit the effect of creating negative values
        Module("r.mapcalc", expression="zzsangle{I} = if(zzsangle{I}>2*{pi} || zzB2_{I}>=90,2*{pi},zzsangle{I})".format(I=i, pi=pi), overwrite=True, quiet=True)
        # removing temporary region
        gscript.del_temp_region()
    except:
        # cleaning termporary layers
        # cleanup()
        message = " ******** There was an error. The cotegory of points that caused the error can be found in files 'error_cat_*.txt' ******* "
        gscript.error(message)
        # sys.exit()
        f = open("error_cat_"+i+".txt", "x")
        f.write("error in category: "+i)
        f.close()


# the following function is used in parallel to process the combination of the differnt product maps
def collectresults(task, proc):
    for i in task:
        # updating the output layer of the best angle of view among all the points in the path
        Module("r.mapcalc", expression="{A} = if(isnull({I}) ||| {I}==0,{A},max({A},{I}))".format(A='xxtemp_a_'+str(proc), I='zzangle'+i), overwrite=True, quiet=True)
        # updating the output layer of the category of the point who has the higher angles with the considered cell
        Module("r.mapcalc", expression="{A} = if({I}==0 ||| isnull({I}),{A}, if({I}<{Z},{A},{cat}))".format(A='xxtemp_c_'+str(proc), I='zzangle'+i, Z='xxtemp_a_'+str(proc), cat=i), overwrite=True, quiet=True)
        Module("r.mapcalc", expression="{A} = if({I}==0 ||| isnull({I}),{A}, if({I}<{Z},{A},{I}))".format(A='xxmaxangle_'+str(proc), I='zzangle'+i, Z='xxtemp_a_'+str(proc)), overwrite=True, quiet=True)
        # updating the output layer of the 3d distance
        Module("r.mapcalc", expression="{A} = if(isnull({I}),{A}, if({A} != 0,min({I},{A}),{I}))".format(A='xxtemp_e_'+str(proc), I='zzdistance'+i), overwrite=True, quiet=True)
        # updating the output layer of the category of the point who has the higher solid angles with the considered cell
        Module("r.mapcalc", expression="{A} = if({I}==0 ||| isnull({I}),{A}, if({I}>{Z},{A},{cat}))".format(A='xxtemp_h_'+str(proc), I='zzdistance'+i, Z='xxtemp_e_'+str(proc), cat=i), overwrite=True, quiet=True)
        Module("r.mapcalc", expression="{A} = if({I}==0 ||| isnull({I}),{A}, if({I}>{Z},{A},{I}))".format(A='xxmin3ddistance_'+str(proc), I='zzdistance'+i, Z='xxtemp_e_'+str(proc)), overwrite=True, quiet=True)
        # updating the output layer of the solid angle
        # updating the output layer of the best solid angle of view among all the points in the path
        Module("r.mapcalc", expression="{A} = if(isnull({I}) ||| {I}==0,{A},max({A},{I}))".format(A='xxtemp_f_'+str(proc), I='zzsangle'+i), overwrite=True, quiet=True)
        # updating the output layer of the category of the point who has the higher solid angles with the considered cell
        Module("r.mapcalc", expression="{A} = if({I}==0 ||| isnull({I}),{A}, if({I}<{Z},{A},{cat}))".format(A='xxtemp_g_'+str(proc), I='zzsangle'+i, Z='xxtemp_f_'+str(proc), cat=i), overwrite=True, quiet=True)
        Module("r.mapcalc", expression="{A} = if({I}==0 ||| isnull({I}),{A}, if({I}<{Z},{A},{I}))".format(A='xxmaxsangle_'+str(proc), I='zzsangle'+i, Z='xxtemp_f_'+str(proc)), overwrite=True, quiet=True)
        # updating the output layer of the number of points a pixel is visible from
        # updating the output layer of the number of points from which a cell is visible
        Module("r.mapcalc", expression="{A} = if(isnull({I}) ||| {I}==0,{A},{A}+1)".format(A='xxtemp_b_'+str(proc), I='zzangle'+i), overwrite=True, quiet=True)


def main():
    options, flags = parser()
    # PARAMETER TO BE UNCOMMENTED TO RUN A TEST OF THE PROGRAM FOR DEBUGGING
    # pnt = "pt50add"
    # dem = "Leintz_dem_50"
    # output = "test"
    # maxdist = 500.0
    # getting options from the command line
    pnt = options['points']
    dem = options['dem']
    output = options['output']
    maxdist = float(options['maxdist'])
    obs_heigh = float(options['obs_heigh'])
    nprocs = int(options['nprocs'])
    treesmap = options['treesmap']
    buildmap = options['buildingsmap']
    treesheigh = options['treesheigh']
    treesheighdeviation = options['treesheighdeviation']
    buildheigh = options['buildingsheigh']
    obsabselev = options['obsabselev']
    if options['object_radius']:
        oradius = float(options['object_radius'])
    if options['layer']:
        layer = int(options['layer'])
    if options['viewangle_threshold']:
        viewangle_threshold = float(options['viewangle_threshold'])
    memory = int(options['memory'])
    binary = flags['b']
    hcurv = flags['c']
    downward = flags['d']
    # converting points map to 3d if a layer and elevation field is provided
    try:
        if obsabselev:
            if layer:
                Module("v.to.3d", input=pnt, output="xxtemppnt3d", type="point", column=obsabselev, layer=layer, quiet=True)
                pnt = "xxtemppnt3d"
    except:
        message = "There was an error converting the layer to 3d. Plese check if you have provided column and layer information. Exiting "
        gscript.error(message)
        # cleaning termporary layers
        cleanup()
        sys.exit()
    try:
        oradius
    except:
        oradius = 0
    # exporting some variables for other functions
    main.treesmap = treesmap
    main.buildmap = buildmap
    main.nprocs = nprocs
    try:
        # setting the starting region alignement to the grid of the DEM
        Module("g.region", align=dem)
        # the following 2 lines are only to verify that there are no maps with the same names as output maps. To prevent overwrinting error after all the calculationsa have been done.
        Module("r.mapcalc", expression="{A} = {B}".format(A=output+'_maxViewAngle', B=1), quiet=True)
        Module("g.remove", type='raster', name=output+'_maxViewAngle', quiet=True, flags="f")
        # running the "general" function
        general(pnt, dem, treesmap, buildmap, treesheigh, treesheighdeviation, buildheigh, obsabselev)
        # creating the pool ofr the parallel processes. initialization of the single processes is delayed by the lock
        pool = multiprocessing.Pool(processes=nprocs, initializer=init, initargs=[multiprocessing.Lock()])
        # Running the "iterate" function
        iterate(pnt, general.dem, obs_heigh, maxdist, hcurv, downward, oradius, general.ctg, nprocs, obsabselev, memory)
        # running the "compute" function in parallel
        pool.starmap(compute, [(t) for t in iterate.tasks])
        # terminating the parallel computation
        pool.close()
        # using the generated temporary maps to create the final maps
        try:
            # the following to split the categories in nprocs chunks
            chunks = [general.ctg[x:x+nprocs] for x in range(0, len(general.ctg), nprocs)]
            # creating the tasks for the parallel processing
            tasks2 = list(zip(chunks, range(len(chunks))))
            # creating the "zeros" map to be used for the combination of the different teporary maps  (THE FOLLOWING CAN BE DONE CREATING A FIRTS MAP AND THEN COPYING IT, FASTENING THE PROCESS)
            for i in range(len(chunks)):
                message = "Creating \"maps zero\" for the chunk %s  of %s"
                gscript.message(message % (str(i), str(len(chunks))))
                # for storing maximum view angles
                Module("r.mapcalc", expression="xxtemp_a_{p} = 0".format(p=str(i)), quiet=True)
                # for storing number of points a pixel is visible from
                Module("r.mapcalc", expression="xxtemp_b_{p} = 0".format(p=str(i)), quiet=True)
                # for storing the category of the point a pixel is visible with the maximum angle
                Module("r.mapcalc", expression="xxtemp_c_{p} = 0".format(p=str(i)), quiet=True)
                # for storing the minimum 3ddistance
                Module("r.mapcalc", expression="xxtemp_e_{p} = 0".format(p=str(i)), quiet=True)
                # for storing the maximum solid angle
                Module("r.mapcalc", expression="xxtemp_f_{p} = 0".format(p=str(i)), quiet=True)
                # for storing the category of the point a pixel is visible with the maximum solid angle
                Module("r.mapcalc", expression="xxtemp_g_{p} = 0".format(p=str(i)), quiet=True)
                # for storing the category of the point a pixel is visible with the minimum distance
                Module("r.mapcalc", expression="xxtemp_h_{p} = 0".format(p=str(i)), quiet=True)
                # needed for calculating the category of the point a pixel is visible with the maximum angle
                Module("r.mapcalc", expression="xxmaxangle_{p} = 0".format(p=str(i)), quiet=True)
                # needed for calculating the category of the point a pixel is visible with the minimum distance
                Module("r.mapcalc", expression="xxmin3ddistance_{p} = 0".format(p=str(i)), quiet=True)
                # needed for calculating the category of the point a pixel is visible with the maximum solid angle
                Module("r.mapcalc", expression="xxmaxsangle_{p} = 0".format(p=str(i)), quiet=True)
            # creating the pool for the combination parallel processes
            pool2 = multiprocessing.Pool(nprocs)
            # running the "collectresults" function in parallel
            pool2.starmap(collectresults, [(t) for t in tasks2])
            # terminating the parallel computation
            pool2.close()
        except:
            # cleaning termporary layers
            cleanup()
            message = " ******** Something went wrong during the entire process of collection of results: please try to reduce the number of CPU (parameter 'procs') ******* "
            gscript.error(message)
            sys.exit()
        else:
            # creating the "zeros" map to be used for the FINAL combination of the different teporary maps (THE FOLLOWING CAN BE DONE CREATING A FIRTS MAP AND THEN COPYING IT, FASTENING THE PROCESS)
            message = "Creating Final \"zeros map \" "
            gscript.message(message)
            Module("r.mapcalc", expression="xxtemp_a = 0", quiet=True)
            Module("r.mapcalc", expression="xxtemp_b = 0", quiet=True)
            Module("r.mapcalc", expression="xxtemp_c = 0", quiet=True)
            Module("r.mapcalc", expression="xxtemp_e = 0", quiet=True)
            Module("r.mapcalc", expression="xxtemp_f = 0", quiet=True)
            Module("r.mapcalc", expression="xxtemp_g = 0", quiet=True)
            Module("r.mapcalc", expression="xxtemp_h = 0", quiet=True)
            # combining the maps. This must be done in series since xxtemp_c depends on xxtemp_a for each given chunk
            for i in range(len(chunks)):
                message = "Combining chunk %s of %s "
                gscript.message(message % (str(i), str(len(chunks))))
                # updating the map of the angles
                Module("r.mapcalc", expression="{A} = if(isnull({I}) ||| {I}==0,{A},max({A},{I}))".format(A='xxtemp_a', I="xxtemp_a_"+str(i)), overwrite=True,  quiet=True)
                # updating the output layer of the number of points from which a cell is visible
                Module("r.mapcalc", expression="{A} = if(isnull({I}) ||| {I}==0,{A},{A}+{I})".format(A='xxtemp_b', I='xxtemp_b_'+str(i)), overwrite=True, quiet=True)
                # updating the output layer of the category of the point who has the higher angle with the considered cell
                Module("r.mapcalc", expression="{A} = if({I}==0 ||| isnull({I}),{A}, if({I}<{Z},{A},{C}))".format(A='xxtemp_c', C='xxtemp_c_'+str(i), I='xxmaxangle_'+str(i), Z='xxtemp_a'), overwrite=True,  quiet=True)
                # updating the output layer of the 3d distance
                Module("r.mapcalc", expression="{A} = if({A} != 0 && {I} != 0,min({I},{A}), if({A} == 0 && {I} != 0,{I}, if({A} != 0 && {I} == 0,{A})))".format(A='xxtemp_e', I='xxtemp_e_'+str(i)), overwrite=True, quiet=True)
                # updating the map of the solid angles
                Module("r.mapcalc", expression="{A} = if(isnull({I}) ||| {I}==0,{A},max({A},{I}))".format(A='xxtemp_f', I="xxtemp_f_"+str(i)), overwrite=True,  quiet=True)
                # updating the output layer of the category of the point who has the higher solid angle with the considered cell
                Module("r.mapcalc", expression="{A} = if({I}==0 ||| isnull({I}),{A}, if({I}<{Z},{A},{C}))".format(A='xxtemp_g', C='xxtemp_g_'+str(i), I='xxmaxsangle_'+str(i), Z='xxtemp_f'), overwrite=True,  quiet=True)
                # updating the output layer of the category of the point who has the lower 3ddistance to the considered cell
                Module("r.mapcalc", expression="{A} = if({I}==0 ||| isnull({I}),{A}, if({I}>{Z},{A},{C}))".format(A='xxtemp_h', C='xxtemp_h_'+str(i), I='xxmin3ddistance_'+str(i), Z='xxtemp_e'), overwrite=True,  quiet=True)
            # set to null the 0 values
            Module("r.null", map='xxtemp_a', setnull=0, quiet=True)
            Module("r.null", map='xxtemp_b', setnull=0, quiet=True)
            Module("r.null", map='xxtemp_c', setnull=0, quiet=True)
            Module("r.null", map='xxtemp_e', setnull=0, quiet=True)
            Module("r.null", map='xxtemp_f', setnull=0, quiet=True)
            Module("r.null", map='xxtemp_g', setnull=0, quiet=True)
            Module("r.null", map='xxtemp_h', setnull=0, quiet=True)
        # creating the output layer
        # Filtering the maps according to the viewangle threashold set using a MASK
        Module("r.mapcalc", expression="MASK=if({A}>{B},1,null())".format(A='xxtemp_a', B=viewangle_threshold), quiet=True, overwrite=True)
        # if there is a threshold for the viewangles,  print a messageset a MASK  (we need to: copy the MASK of the user if it exist, make aour maskera layer, remove the mask ot the user, set out maskera as a MASK, run the following, then remove the MASK and set the old mask of the user
        if viewangle_threshold > 90.0:
            try:
                message = f"The maps are going to be filtered according to the viewangle_threshold value: {viewangle_threshold}, as requested by the user."
                gscript.warning(message)
            except:
                pass
        message = "Creating final maps"
        gscript.message(message)
        Module("r.mapcalc", expression="{A} = {B}".format(A=output+'_maxViewAngle', B='xxtemp_a'), quiet=True)
        Module("r.mapcalc", expression="{A} = {B}".format(A=output+'_numberOfViews', B='xxtemp_b'), quiet=True)
        Module("r.mapcalc", expression="{A} = {B}".format(A=output+'_pointOfViewWithMmaxAngle', B='xxtemp_c'), quiet=True)
        Module("r.mapcalc", expression="{A} = {B}".format(A=output+'_min3dDistance', B='xxtemp_e'), quiet=True)
        # add lines of code here for calculating the max solid angle the points from where we have min distance and max solid angle
        Module("r.mapcalc", expression="{A} = {B}".format(A=output+'_maxSolidAngle', B='xxtemp_f'), quiet=True)
        Module("r.mapcalc", expression="{A} = {B}".format(A=output+'_pointOfViewWithMmaxSolidAngle', B='xxtemp_g'), quiet=True)
        Module("r.mapcalc", expression="{A} = {B}".format(A=output+'_pointOfViewWithMin3dDistance', B='xxtemp_h'), quiet=True)
        # setting logaritmic colors to some maps
        Module("r.colors", map=output+'_maxSolidAngle', color='blues', flags="g", quiet=True)
        Module("r.colors", map=output+'_maxViewAngle', color='oranges', flags="g", quiet=True)
        if binary:
            Module("r.mapcalc", expression="{A} = if(isnull({B}),null(),1)".format(A=output+'_binary', B='xxtemp_a'), quiet=True)
        message = "*** Succesful run! ***"
        gscript.message(message)
    # in case of CTRL-C
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    options, flags = parser()
    atexit.register(cleanup)
    sys.exit(main())
