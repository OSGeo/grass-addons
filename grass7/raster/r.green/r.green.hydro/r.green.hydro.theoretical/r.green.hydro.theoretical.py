#!/usr/bin/env python
# -- coding: utf-8 --
#
############################################################################
#
# MODULE:      r.green.hydro.potential
# AUTHOR(S):   Giulia Garegnani, Pietro Zambelli
# PURPOSE:     Calculate the theorethical hydropower energy potential for each basin and segments of river
# COPYRIGHT:   (C) 2014 by the GRASS Development Team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################
#

#%module
#% description: Calculate the hydropower energy potential for each basin starting from discharge and elevation data. If existing plants are available it computes the potential installed power in the available part of the rivers.
#% keywords: raster
#% keywords: hydropower
#% keywords: renewable energy
#%end
#%option G_OPT_R_ELEV
#% required: yes
#%end
#%option
#% key: discharge
#% type: string
#% gisprompt: old,cell,raster
#% key_desc: name
#% description: Name of river discharge [m3/s]
#% required: yes
#%end
#%option
#% key: rivers
#% type: string
#% gisprompt: old,vector,vector
#% key_desc: name
#% description: Name of river network
#% required: no
#%end
#%option
#% key: lakes
#% type: string
#% gisprompt: old,vector,vector
#% key_desc: name
#% description: Name of lakes
#% required: no
#%end
#%option
#% key: threshold
#% type: string
#% description: Minimum size of exterior watershed basin
#% required: yes
#% answer: 0
#% guisection: Basin Potential
#%end
#%option
#% key: basins
#% type: string
#% gisprompt: old,cell,raster
#% key_desc: name
#% description: Name of basin map obtained by r.watershed
#% required: no
#% guisection: Basin Potential
#%end
#%option
#% key: stream
#% type: string
#% gisprompt: old,cell,raster
#% key_desc: name
#% description: Name of stream map obtained by r.watershed
#% required: no
#% guisection: Basin Potential
#%end
#TODO: add flags
#%flag
#% key: d
#% description: Debug with intermediate maps
#%end
#%option
#% key: output
#% type: string
#% key_desc: name
#% description: Name of vector map with basin potential
#% required: yes
#% guisection: Basin Potential
#%END

from __future__ import print_function

# import system libraries
import os
import sys
import atexit
import pdb

# import grass libraries
from grass.script import core as gcore
from grass.pygrass.messages import get_msgr
from grass.pygrass.utils import set_path

set_path('r.green', 'libhydro', '..')
set_path('r.green', 'libgreen', os.path.join('..', '..'))
# finally import the module in the library
from libgreen.utils import cleanup
from libhydro import basin
from libgreen.utils import check_overlay_rr
#from libgreen.utils import check_overlay_rv
from libgreen.utils import raster2numpy
from libgreen.utils import remove_pixel_from_raster


if "GISBASE" not in os.environ:
    print("You must be in GRASS GIS to run this program.")
    sys.exit(1)


def main(options, flags):
    #############################################################
    # inizialitation
    #############################################################
    TMPRAST, TMPVECT, DEBUG = [], [], False
    atexit.register(cleanup, rast=TMPRAST, vect=TMPVECT, debug=DEBUG)
    #TOD_add the possibilities to have q_points
    # required
    discharge = options['discharge']
    dtm = options['elevation']
    # basin potential
    basins = options['basins']
    stream = options['stream']  # raster
    rivers = options['rivers']  # vec
    lakes = options['lakes']  # vec
    E = options['output']
    threshold = options['threshold']
    # existing plants
#    segments = options['segments']
#    output_segm = options['output_segm']
#    output_point = options['output_point']
#    hydro = options['hydro']
#    hydro_layer = options['hydro_layer']
#    hydro_kind_intake = options['hydro_kind_intake']
#    hydro_kind_turbine = options['hydro_kind_turbine']
#    other = options['other']
#    other_kind_intake = options['other_kind_intake']
#    other_kind_turbine = options['other_kind_turbine']

    # optional
    DEBUG = flags['d']

    msgr = get_msgr()
    # info = gcore.parse_command('g.region', flags='m')
    # print info
    #############################################################
    # check temporary raster
    #############################################################
    TMPRAST = ['dtm_mean', 'neighbors',
               'closure', 'down', 'lakes', 'stream_thin',
               'debug', 'vec_rast']
    TMPVECT = ['tmptmp', 'segments']

    if not gcore.overwrite():
        for m in TMPRAST:
            if gcore.find_file(m)['name']:
                msgr.fatal(_("Temporary raster map %s exists") % (m))

    if rivers:
        # cp the vector in the current mapset in order to clean it

        to_copy = '%s,river_new' % rivers
        gcore.run_command('g.copy', vector=to_copy)
        rivers = 'river_new'
        TMPVECT.append('river_new')
        gcore.run_command('v.build', map=rivers)
        pdb.set_trace()
        dtm_corr, tmp_v, tmp_r = basin.dtm_corr(dtm, rivers, lakes)
        TMPRAST = TMPRAST + tmp_r
        TMPVECT = TMPVECT + tmp_v
        basins, stream = basin.check_compute_basin_stream(basins, stream,
                                                          dtm_corr, threshold)
    else:
        basins, stream = basin.check_compute_basin_stream(basins, stream,
                                                          dtm, threshold)

    perc_overlay = check_overlay_rr(discharge, stream)
    #pdb.set_trace()
    if float(perc_overlay) < 90:
        warn = ("Discharge map doesn't overlay all the stream map."
                "It covers only the %s %% of rivers") % (perc_overlay)
        msgr.warning(warn)

    msgr.message("\Init basins\n")
    #pdb.set_trace()
    #############################################################
    # core
    #############################################################
    basins_tot, inputs = basin.init_basins(basins)

    msgr.message("\nCompute mean elevation\n")

    gcore.run_command('r.stats.zonal',
                      base=basins,
                      cover=dtm, flags='r',
                      output='dtm_mean',
                      method='average')

    msgr.message("\nBuild the basin network\n")
    #############################################################
    # build_network(stream, dtm, basins_tot) build relationship among basins
    # Identify the closure point with the r.neigbours module
    # if the difference betwwen the stream and the neighbours
    # is negative it means a new subsanin starts
    #############################################################
    basin.build_network(stream, dtm, basins_tot)
    stream_n = raster2numpy(stream)
    discharge_n = raster2numpy(discharge)
    #pdb.set_trace()
    basin.fill_basins(inputs, basins_tot, basins, dtm, discharge_n, stream_n)

    ###################################################################
    # check if lakes and delate stream in lakes optional
    ###################################################################

    if lakes:
        remove_pixel_from_raster(lakes, stream)

    ####################################################################
    # write results
    ####################################################################
    # if not rivers or debug I write the result in the new vector stream
    msgr.message("\nWrite results\n")

    basin.write_results2newvec(stream, E, basins_tot, inputs)

    ####################################################################
    # try tobuilt a vector shp of rivers coerent with vector input
    #TODO: and the new branches created by r.watershed, check how to add to
    # the existing vector river
    ####################################################################
#==============================================================================
#     if rivers:
#         if DEBUG:
#             basin.write_results2newvec(stream, 'debug', basins_tot, inputs)
#             basin.add_results2shp(basins, rivers, basins_tot, E, inputs)
#         else:
#             basin.add_results2shp(basins, rivers, basins_tot, E, inputs)
#==============================================================================

    ####################################################################
    # if there are plants, it deletes the piece of river
    # pdb.set_trace()
#    if (segments and hydro):
#        warn = (("%s map could have been generated by %s."
#                "%s is used for next computations")
#                % (segments, hydro, segments))
#        msgr.warning(warn)
#
#    if hydro and not(segments):
#        msgr.message("\nr.green.hydro.delplants\n")
#        gcore.run_command('r.green.hydro.delplants',
#                          hydro=hydro,
#                          hydro_layer=hydro_layer,
#                          river=E,
#                          plants='plant',
#                          output='segments',
#                          hydro_kind_intake=hydro_kind_intake,
#                          hydro_kind_turbine=hydro_kind_turbine,
#                          elevation=dtm,
#                          other=other,
#                          other_kind_intake=other_kind_intake,
#                          other_kind_turbine=other_kind_turbine)
#        segments = 'segments'
#
#    #FIXME: with temporary plants it don't work
#    if segments:
#        perc_overlay = check_overlay_rv(discharge, segments)
#        if float(perc_overlay) < 90:
#            warn = ("Discharge map doesn't overlay all the segments map."
#                    "It covers only the %s %% of rivers") % (perc_overlay)
#            msgr.warning(warn)
#        gcore.run_command('r.green.hydro.optimal',
#                          flags='c',
#                          discharge=discharge,
#                          river=segments,
#                          dtm=dtm,
#                          len_plant='10000000',
#                          output_plant=output_segm,
#                          output_point=output_point,
#                          distance='0.5',
#                          len_min='0.5')


if __name__ == "__main__":
    options, flags = gcore.parser()
    sys.exit(main(options, flags))
