#!/usr/bin/env python
#############################################################################
#
# MODULE:       v.surf.icw
#		version $Id$
#
# AUTHOR:       M. Hamish Bowman, Dunedin, New Zealand
#		Originally written aboard the NZ DoC ship M/V Renown, 
#		Bligh Sound, Fiordland National Park, November 2003
#		With thanks to Franz Smith and Steve Wing for support
#		Ported to Python for GRASS 7 December 2011
#
# PURPOSE:      Like IDW interpolation, but distance is cost to get to any
#		other site.
#
# COPYRIGHT:    (c) 2003-2011 Hamish Bowman
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################
#
# Description:
#  Non-euclidean, non-polluting IDW from areas separated by null cells
#  e.g.
#   - two parallel lakes, connected at one end (water chemistry in arms of a fjord)
#   - Population abundance constrained by topography (Kiwis crossing a land-bridge)
#
#  w(d)= 1/d^p    where p is user definable, usually 2.
#
# Notes:
#  A cost surface containing molasses barrier data may be used as well.
#  Input data points need not have direct line of sight to each other.
#  Try and keep the number of input sites to under a few dozen, as the
#  process is very computationally expensive. You might consider creating
#  a few hundred MB RAM-disk for a temporary mapset to avoid thrashing your
#  hard drive (r.cost is heavy on disk IO).


#%Module
#% description: IDW interpolation, but distance is cost to get to any other site.
#%End
#%option
#% key: input
#% type: string
#% gisprompt: old,vector,vector
#% description: Name of existing vector points map containing seed data
#% required : yes
#%end
#%option
#% key: column
#% type: string
#% description: Column name in points map that contains data values
#% required : yes
#%end
#%option
#% key: output
#% type: string
#% gisprompt: new,cell,raster
#% description: Name for output raster map
#% required : yes
#%end
#%option
#% key: cost_map
#% type: string
#% gisprompt: old,cell,raster
#% description: Name of existing raster map containing cost information
#% required : yes
#%end
#%option
#% key: friction
#% type: double
#% description: Friction of distance, (the 'n' in 1/d^n)
#% answer: 2
#% options: 1-6
#% required : no
#%end
#%option
#% key: layer
#% type: integer
#% answer: 1
#% description: Layer number of data in points map
#% required: no
#%end
#%option
#% key: where
#% type: string
#% label: WHERE conditions of SQL query statement without 'where' keyword
#% description: Example: income < 1000 and inhab >= 10000
#% required : no
#%end

##%option
##% key: max_cost
##% type: integer
##% description: Optional maximum cumulative cost before setting weight to zero
##% required : no
##%end

#%option
#% key: post_mask
#% type: string
#% gisprompt: old,cell,raster
#% description: Name of existing raster map to be used as post-processing MASK
#% required : no
#%end
#%flag
#% key: r
#% description: Use (d^n)*log(d) instead of 1/(d^n) for radial basis function
#%end
#%option
#% key: workers
#% type: integer
#% options: 1-256
#% answer: 1
#% description: Number of parallel processes to launch
#%end

import sys
import os
import grass.script as grass

def main():

    pts_input = options['input']
    output = options['output']
    cost_map = options['cost_map']
    post_mask = options['post_mask']
    column = options['column']
    friction = options['friction']
    layer = options['layer']
    where = options['where']
    workers = int(options['workers'])

    if workers is 1 and "WORKERS" in os.environ:
        workers = int(os.environ["WORKERS"])

    pid = str(os.getpid())
    tmp_base = 'tmp_icw_' + pid + '_'

    # does map exist?
    if not grass.find_file(pts_input, element = 'vector')['file']:
        grass.fatal(_("Vector map <%s> not found") % pts_input)

    if grass.findfile(post_mask):
        grass.fatal(_("A MASK already exists; remove it before using the post_mask option."))

    grass.verbose(_("v.surf.icw -- Inverse Cost Weighted Interpolation"))
    grass.verbose(_("Processing %s -> %s, column=%s, Cf=%g") % (pts_input, output, column, friction))

    if flags['r']:
        grass.verbose(_("Using (d^n)*log(d) radial basis function."))

    grass.verbose("------------------------------------------------------------------------")

    # adjust so that tiny numbers don't hog all the FP precision space
    #if friction = 4:
    #    divisor = 10.0
    #if friction = 5:
    #    divisor = 100.0
    #if friction = 6:
    #    divisor = 500.0
    # fp version:
    if friction > 4:
        divisor = 0.01 * pow(friction, 6)
    else:
        divisor = 1

    # Check that we have the column and it is the correct type
    try:
       coltype = grass.vector_columns(pts_input, layer)[column]
    except KeyError:
        grass.fatal(_("Data column <%s> not found in vector points map <%s>") % (column, pts_input))

    if coltype['type'] not in ('INTEGER', 'DOUBLE PRECISION'):
        grass.fatal(_("Data column must be numberic"))

    # cleanse cost area mask to a flat =1 for my porpoises
    grass.mapcalc("$result = if($cost_map, 1, null())",
                  result = tmp_base + 'area', cost_map = cost_map,
                  overwrite = True)


    ########################################################################
    ## Commence crunching ..
    tmp_points = grass.tempfile()

    #crop out only points in region
    grass.run_command('v.in.region', output = tmp_base + 'region', quiet = True)
    grass.run_command('v.select',
                      ainput = pts_file, alayer = layer, atype = 'point',
                      binput = tmp_base + 'region', btype = 'area',
                      output = tmp_base + 'points_sel')

    if where:
        grass.run_command('v.select', input = tmp_base + 'points_sel',
                          layer = layer, where = where,
                          output = tmp_base + 'points')
    else:
        grass.run_command('g.rename', rast = (tmp_base + 'points_sel',
                          tmp_base + 'points'), quiet = True)

    if where:
        points_list = grass.read_command('v.out.ascii', input = pts_file,
                                         where = where, output = '-',
                                         flags = 'r').splitlines()
    else:
        points_list = grass.read_command('v.out.ascii', input = pts_file,
                                         output = '-', flags = 'r').splitlines()

    # convert into a 2D list, drop unneeded cat column
    # to drop cat col, add this to the end of the line [:-1]
    #fixme: how does this all react for 3D starting points?
    for i in range(len(points_list)):
        points_list[i] = points_list[i].split('|')

    # count number of starting points (n)
    n = len(points_list)

    if n > 200:
        grass.warning(_("Computation is expensive! Please consider fewer points or get ready to wait a while ..."))
        import time
        time.sleep(5)


    #### generate cost maps for each site in range
    grass.verbose(_("Generating cost maps.."))

    num = 1

    for position in points_list:
        easting = position[0]
        northing = position[1]
        cat = position[-1]

        # retrieve data value from vector's attribute table:
        data_value = grass.vector_db_select(pts_file, column = column)['values'][cat]

        grass.message(_("Site %d of %d  e=%.4f  n=%.4f  data=%.3g"),
                      num, n, easting, northing, data_value)

        if not data_value:
            grass.messsage(_("  Skipping, no data here."))
            n = n - 1
            continue

	# we know the point is in the region, but is it in a non-null area of the cost surface?
        rast_val = grass.read_command('r.what', map = tmp_base + 'area',
				      coordinates = '%s,%s' % (position[0], position[1])
				     ).strip().split('|')[-1]
	if rast_val == '*':
	    grass.messsage(_("  Skipping, point lays outside of cost_map."))
	    n = n - 1
	    continue

	# it's ok to proceed
        try:
	    data_value = float(data_value)
	except:
	    grass.fatal('Data value [%s] is non-numeric' % data_value)

 # echo "$EASTING $NORTHING $DATA_VALUE" | v.in.ascii output=tmp_idw_cost_site_$$ fs=space

        cost_site_name = tmp_base + 'cost_site.' + str(num)
        grass.run_command('r.cost', flags = 'k', input = tmp_base + 'area',
                          output = cost_site_name, coordinate = easting + ',' + northing)

        #max_cost="$GIS_OPT_MAX_COST"  : commented out until r.null cleansing/continue code is sorted out
        #start_points=tmp_idw_cost_site_$$

        # we do this so the divisor exists and the weighting is huge at the exact sample spots
        # more efficient to reclass to 1?
        grass.mapcalc("$cost_n_cleansed = if($cost_n == 0, 0.1, $cost_n)",
                      cost_n_cleansed = cost_site_name + '.cleansed',
                      cost_n = cost_site_name, overwrite = True)
        grass.run_command('g.remove', rast = cost_site_name, quiet = True)
        grass.run_command('g.rename', rast = cost_site_name + '.cleansed'
                          + ',' + cost_site_name, quiet = True)


        # r.to.vect then r.patch output
        # v.to.rast in=tmp_idw_cost_site_29978 out=tmp_idw_cost_val_$$ use=val val=10

        if not flags['r']:
            #  exp(3,2) is 3^2  etc.  as is pow(3,2)
            # r.mapcalc "1by_cost_site_sqrd.$NUM =  1.0 / exp(cost_site.$NUM , $FRICTION)"
#      EXPRESSION="1.0 / pow(cost_site.$NUM $DIVISOR, $FRICTION )"
            expr = '1.0 / pow($cost_n / ' + str(divisor) + ', $friction)'
        else
            # use log10() or ln() ?
#      EXPRESSION="1.0 / ( pow(cost_site.$NUM, $FRICTION) * log (cost_site.$NUM) )"
            expr = '1.0 / ( pow($cost_n, $friction) * log($cost_n) )"'

        grass.debug("r.mapcalc expression is: [%s]" % expr)
        grass.mapcalc("$result.$num = " + expr,
                      result = tmp_base + '1by_cost_site_sqrd',
                      num = str(num), cost_n = cost_site_name,
                      friction = friction, overwrite = True)

        # r.patch in=1by_cost_site_sqrd.${NUM},tmp_idw_cost_val_$$ out=1by_cost_site_sqrd.${NUM} --o
        # g.remove rast=cost_site.$NUM

        num += 1
    done


    # Step 3) find sum(cost^2)
    grass.message("")
    grass.message(_("Finding sum of squares.."))

INPUT_MAPS=1by_cost_site_sqrd.1
NUM=2
while [ $NUM -le $N ] ; do
    INPUT_MAPS="$INPUT_MAPS,1by_cost_site_sqrd.$NUM"
    NUM="`expr $NUM + 1`"
done

    if post_mask:
        grass.message(_("Setting post_mask <%s>"), post_mask)
        grass.mapcalc("MASK = $maskmap", maskmap = post_mask, overwrite = True)

    grass.message(_("Summation of cost weights.."))
    grass.run_command('r.series', method = 'sum', input = input_maps,
                      output = tmp_base + 'sum_of_1by_cost_sqs')

    if post_mask:
        grass.message(_("Removing post_mask <%s>"), post_mask)
        grass.run_command('g.remove', rast = 'MASK', quiet = True)

    # Step 4) ( 1/di^2 / sum(1/d^2) ) *  ai
    grass.message("")
    grass.message(_("Creating partial weights.."))

    num = 1
for POS in `cat "$TMP_POINTS"` ; do

    EASTING=`echo "$POS" | cut -f1 -d"|"`
    NORTHING=`echo "$POS" | cut -f2 -d"|"`
    CAT=`echo "$POS" | cut -f"$CATCOL" -d"|"`
    DATA_VALUE="`v.db.select -c tmp_icw_points_$$ column="$COL_NAME" where="cat=${CAT}"`"

        grass.message(_("Site %d of %d,  data value = %.3f") % (num, n, data_value))

        if not data_value:
	    grass.message(_("  Skipping, no data here."))
            continue

    if [ -z "`r.what input=tmp_icw_area_$$  east_north=$EASTING,$NORTHING | grep -v "*"`" ] ; then
            grass.message(_("  Skipping, site lays outside of cost_map."))
	    continue
    fi

        partial_n = tmp_base + 'partial.' + str(num)
        grass.mapcalc("$partial_n = ($data * $1by_cost_sq) / $sum_of_1by_cost_sqs",
                      partial_n = partial_n, data = data_value, overwrite = True)
      r.mapcalc "$result = ( $data_value * $one_by_cost_site_sqrd ) / \
                 $sum_of_1by_cost_sqs",
        data_value = data_value,
        result = tmp_base + 'partial_icw.' + str(num), 
        one_by_cost_site_sqrd = tmp_base + '1by_cost_site_sqrd' + str(num),
        sum_of_1by_cost_sqs = tmp_base + 'sum_of_1by_cost_sqs', overwrite = True)
        #"( $DATA_VALUE / $N ) * (1.0 - ( cost_sq_site.$NUM / sum_of_cost_sqs ))"
        #"( cost_sq_site.$NUM / sum_of_cost_sqs ) * ( $DATA_VALUE / $N )"

        # g.remove rast=1by_cost_site_sqrd.$NUM

        num = num + 1
        if num > n:
	    break
    # done

INPUT_MAPS=partial_icw.1
NUM=2
while [ $NUM -le $N ] ; do
    INPUT_MAPS=$INPUT_MAPS,partial_icw.$NUM
    NUM="`expr $NUM + 1`"
done

    grass.message("")
    grass.message(_("Calculating final values.."))

    grass.run_command('r.series', method = 'sum', input = input_maps,
                      output = output)

    #TODO: r.patch in v.to.rast of values at exact seed site locations. currently set to null

    grass.run_command('r.colors', map = output, color = 'bcyr')
    grass.run_command('r.support', map = output, history = '',
                      title = 'Inverse cost-weighted interpolation')
    grass.run_command('r.support', map = output,
                      history = 'v.surf.icw interpolation:')
    grass.run_command('r.support', map = output,
                      history = '  input map=' + input + '   attribute column=' + column)
    grass.run_command('r.support', map = output,
                      history = '  cost map=' + cost_map + '   coefficient of friction=' + friction)
    if flags['r']:
        grass.run_command('r.support', map = output,
                          history = '  (d^n)*log(d) as radial basis function')
    if post_mask: 
        grass.run_command('r.support', map = output,
                          history = '  post-processing mask=' + post_mask)
    if where:
        grass.run_command('r.support', map = output,
                          history = '  SQL query= WHERE ' + where)

    # save layer #? to metadata?   command line hist?


    # Step 5) rm cost and cost_sq maps, tmp_icw_points, etc
cleanup:
    grass.verbose(_("Cleanup.."))
    grass.run_command('g.mremove', flags = 'f', rast = tmp_base + '*', quiet = True)

  g.mremove -f rast=cost_site.*
  g.mremove -f rast=1by_cost_site_sqrd.*
  g.mremove -f rast=partial_icw.*
  #g.mremove -f rast=tmp_icw_*_$$
  #g.mremove -f vect=tmp_icw_*_$$
  g.remove rast=sum_of_1by_cost_sqs
  #g.remove vect=tmp_idw_cost_site_$$
  g.remove rast=tmp_icw_area_$$
  g.remove vect=tmp_icw_region_$$,tmp_icw_points_$$
  # check if it exists
  eval `g.findfile element=vector file="tmp_icw_points_sel_$$"`
  if [ -e "$file" ] ; then
     g.remove vect=tmp_icw_points_sel_$$
  fi
  rm -f "$TMP_POINTS"
}

# TODO: trap ^C
# what to do in case of user break:
#exitprocedure()
#{
#  g.message -e 'User break!'
#  cleanup
#  exit 1
#}
# shell check for user break (signal list: trap -l)
#trap "exitprocedure" 2 3 15

cleanup

    # Step 6) done!
    grass.message(_("Done! Results written to <%s>." % output)


if __name__ == "__main__":
    options, flags = grass.parser()
    main()
