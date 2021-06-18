#!/usr/bin/env python
#
############################################################################
#
# MODULE:		Applying a focal filter based on real distance (cost map)
# AUTHOR(S):		Johannes Radinger <johannesradinger@gmail.com>
# COPYRIGHT:    	(C) 2012 Johannes Radinger
#
#               	This program is free software under the GNU General Public
#               	License (>=v2). Read the file COPYING that comes with GRASS
#               	for details.
#############################################################################
#%Module
#% description: Calculating focal raster based on a r.cost distance of a raster cell
#% keywords: raster, focal
#%End
#%option
#% key: input
#% type: string
#% gisprompt: old,cell,raster
#% description: input raster
#% required: yes
#%end
#%option
#% key: stop_points
#% type: string
#% gisprompt: old,vector, vector
#% description: stop point vector for r.cost
#% required: no
#%end
#%option
#% key: output
#% type: string
#% gisprompt: new,cell,raster
#% description: output raster
#% required: no
#%end
#%option
#% key: stat
#% type: string
#% multiple:no
#% options:mean,min,max,sum,median,range
#% description: Desired focal statistic for output raster
#% required: yes
#%end
#%option
#% key: distance
#% type: double
#% required: yes
#% multiple: no
#% description: Distance for filter/buffer
#%End



import sys
import os
import atexit



import grass.script as grass


tmp_map_rast = None
tmp_map_vect = None

def cleanup():
    if (tmp_map_rast or tmp_map_vect):
        grass.run_command("g.remove", 
                        rast = tmp_map_rast,
                        vect = tmp_map_vect,
                        quiet = True)




def main():	 
    #defining temporary maps
    tmp_map_rast = ["tmp"+str(os.getpid()),"distance_mask"+str(os.getpid()),"masked_map"+str(os.getpid())]
    tmp_map_vect = ["point_tmp"+str(os.getpid())]

    # check if db is connected if not create a connection!
    if grass.read_command("db.connect", flags="p").split()[1].split(":")[1]:
        grass.message("DB is set")
    else:
        grass.run_command("db.connect",driver = "sqlite",database = "$GISDBASE/$LOCATION_NAME/$MAPSET/sqlite.db")


    # Getting resolution of raster map
    res = int(grass.read_command("g.region", flags = "m").strip().split('\n')[4].split('=')[1])  


    # Defining variables
    input_map = options['input']
    distance = options['distance']
    stop_points = options['stop_points']
    if options['output']:
        output_map = str(options['output'])
    else:
        output_map = "d"+str(distance)+"_"+str(input_map)


    # creating temporary map
    grass.mapcalc("$tmp = if($raster>=0,$res,null())",	
                                    tmp = "tmp"+str(os.getpid()),
                                    res = res,
                                    raster = input_map)


    # make points from raster
    grass.run_command("r.to.vect",
                                    overwrite = True,
                                    input = "tmp"+str(os.getpid()),
                                    output = "point_tmp"+str(os.getpid()),
                                    feature = "point")

    # Get coordinates for each point
    grass.run_command("v.db.addcol",
                                    map = "point_tmp"+str(os.getpid()),
                                    columns = "X DOUBLE, Y DOUBLE, univar DOUBLE")					
    grass.run_command("v.to.db",
                                    map = "point_tmp"+str(os.getpid()),
                                    type = "point",
                                    option = "coor",
                                    columns = "X,Y")


    # Get "list" of coordinates
    pointcoords = grass.read_command("v.db.select",
                                    flags = "c",
                                    fs ="|",
                                    map = "point_tmp"+str(os.getpid()),
                                    columns = "cat,X,Y")

    for line in pointcoords.split():

        cat,X,Y = line.split('|')

        #creating coordinates
        coors = str(X)+","+str(Y)



        # creating "focal distance mask" (using r.cost with a specified distance as input)
        if options['stop_points']:
            grass.run_command("r.cost",
                                    flags = 'n',
                                    overwrite = True,
                                    max_cost = distance,
                                    stop_points = stop_points,
                                    input = "tmp"+str(os.getpid()),
                                    output = "distance_mask"+str(os.getpid()),
                                    coordinate = coors)
        else:			
            grass.run_command("r.cost",
                                    flags = 'n',
                                    overwrite = True,
                                    max_cost = distance,
                                    input = "tmp"+str(os.getpid()),
                                    output = "distance_mask"+str(os.getpid()),
                                    coordinate = coors)

        # creating "masked map" based on input
        grass.mapcalc("$masked_map= if(!isnull($distance_mask),$input_map,null())",
                                masked_map = "masked_map"+str(os.getpid()),
                                input_map = input_map,
                                distance_mask = "distance_mask"+str(os.getpid()))


        # Getting focal statistics (e.g. mean) for masked_map
        univar = grass.read_command("r.univar", map = "masked_map"+str(os.getpid()), flags = 'e')
        d = {'min': 6, 'max': 7, 'mean': 9, 'sum': 14, 'median':16, 'range':8}
        stat = float(univar.split('\n')[d[str(options['stat'])]].split(':')[1])


        #update point map with new stat value
        grass.write_command("db.execute", stdin = 'UPDATE point_tmp%s SET univar=%s WHERE cat = %d' % (str(os.getpid()),str(stat),int(cat)))


        # Remove temp maps of loop
        grass.run_command("g.remove",rast = ["masked_map"+str(os.getpid()),"distance_mask"+str(os.getpid())])

        # End of loop

    # Create new raster from the temporary point vector with the newly generated values
    grass.run_command("v.to.rast",
                                    input = "point_tmp"+str(os.getpid()),
                                    output = output_map,
                                    use = "attr",
                                    column= "univar") 

    grass.run_command("g.remove", vect = "point_tmp"+str(os.getpid()))
    grass.run_command("g.remove", rast = "tmp"+str(os.getpid()))


    return 0


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())
