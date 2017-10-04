#!/usr/bin/env python
############################################################################
#
# MODULE:       v.gsflow.segments
#
# AUTHOR(S):    Andrew Wickert
#
# PURPOSE:      Build stream segments for the USGS models MODFLOW or GSFLOW.
#
# COPYRIGHT:    (c) 2016-2017 Andrew Wickert
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################
#
# REQUIREMENTS:
#      -  uses inputs from v.stream.network
 
# More information
# Started December 2016

#%module
#% description: Prepares stream segments for PRMS and GSFLOW
#% keyword: vector
#% keyword: stream network
#% keyword: hydrology
#% keyword: GSFLOW
#%end

#%option G_OPT_V_INPUT
#%  key: input
#%  label: Vector stream network from r.stream.extract
#%  required: yes
#%  guidependency: layer,column
#%end

#%option G_OPT_V_OUTPUT
#%  key: output
#%  label: Segments: stream segments for GSFLOW / PRMS
#%  required: yes
#%  guidependency: layer,column
#%end

#%option
#%  key: icalc
#%  type: integer
#%  description: Stream depth option: 0-const; 1,2-Manning; 3-aQ^b
#%  answer: 3
#%  required: no
#%end

#%option
#%  key: cdpth
#%  type: double
#%  description: Flow depth coefficient [meters]; used if ICALC=3
#%  answer: 0.4
#%  required: no
#%end

#%option
#%  key: fdpth
#%  type: double
#%  description: Flow depth exponent; used if ICALC=3
#%  answer: 0.42
#%  required: no
#%end

#%option
#%  key: awdth
#%  type: double
#%  description: Flow width coefficient [meters]; used if ICALC=3
#%  answer: 4
#%  required: no
#%end

#%option
#%  key: bwdth
#%  type: double
#%  description: Flow width exponent; used if ICALC=3
#%  answer: 0.23
#%  required: no
#%end

#%option
#%  key: iupseg
#%  type: string
#%  description: Category of upstream diversion segment (from_cat,to_cat,...)
#%  answer: 0,0
#%  required: no
#%end

#%option
#%  key: flow
#%  type: string
#%  description: Streamflow entering the upstream-most segments (cat,Q,cat,Q,...)
#%  answer: 0,0
#%  required: no
#%end

#%option
#%  key: runoff
#%  type: string
#%  description: Diffuse runoff entering each segment (cat,Q,cat,Q,...)
#%  answer: 0,0
#%  required: no
#%end

#%option
#%  key: etsw
#%  type: string
#%  description: Direct removal of in-channel water by ET (cat,Q,cat,Q)
#%  answer: 0,0
#%  required: no
#%end

#%option
#%  key: pptsw
#%  type: string
#%  description: Direct precipitation on the stream (cat,Q,cat,Q)
#%  answer: 0,0
#%  required: no
#%end

#%option
#%  key: roughch
#%  type: double
#%  description: In-channel Manning's n for ICALC=1,2
#%  answer: 0.035
#%  required: no
#%end

#%option
#%  key: roughbk
#%  type: double
#%  description: Overbank Manning's n for ICALC=2
#%  answer: 0.06
#%  required: no
#%end

#%option
#%  key: width1
#%  type: double
#%  description: Upstream width in segment, assumed constant through watershed
#%  answer: 5
#%  required: no
#%end

#%option
#%  key: width2
#%  type: double
#%  description: Downstream width in segment, assumed constant through watershed
#%  answer: 5
#%  required: no
#%end

##################
# IMPORT MODULES #
##################
# PYTHON
import numpy as np
from matplotlib import pyplot as plt
import sys
# GRASS
from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.modules.shortcuts import raster as r
from grass.pygrass.modules.shortcuts import vector as v
from grass.pygrass.modules.shortcuts import miscellaneous as m
from grass.pygrass.gis import region
from grass.pygrass import vector # Change to "v"?
from grass.script import vector_db_select
from grass.pygrass.vector import Vector, VectorTopo
from grass.pygrass.raster import RasterRow
from grass.pygrass import utils
from grass import script as gscript

###############
# MAIN MODULE #
###############

def main():
    """
    Builds river segments for input to the USGS hydrologic models
    PRMS and GSFLOW.
    """

    ##################
    # OPTION PARSING #
    ##################

    options, flags = gscript.parser()
    
    # I/O
    streams = options['input']
    segments = options['output']
    
    # Hydraulic geometry
    ICALC = options['icalc']
    
    # ICALC=0: Constant depth
    WIDTH1 = options['width1']
    WIDTH2 = options['width2']
    
    # ICALC=1: Manning
    ROUGHCH = options['roughch']
    
    # ICALC=2: Manning
    ROUGHBK = options['roughbk']

    # ICALC=3: Power-law relationships (following Leopold and others)
    # The at-a-station default exponents are from Rhodes (1977)
    CDPTH = str(float(options['cdpth']) / 35.3146667) # cfs to m^3/s
    FDPTH = options['fdpth']
    AWDTH = str(float(options['awdth']) / 35.3146667) # cfs to m^3/s
    BWDTH = options['bwdth']
    
    ##################################################
    # CHECKING DEPENDENCIES WITH OPTIONAL PARAMETERS #
    ##################################################
    
    if ICALC == 3:
        if CDPTH and FDPTH and AWDTH and BWDTH:
            pass
        else:
            grass.fatal('Missing CDPTH, FDPTH, AWDTH, and/or BWDTH. \
                         These are required when ICALC = 3.')

    ###########
    # RUNNING #
    ###########

    # New Columns for Segments
    segment_columns = []
    # Self ID
    segment_columns.append('id integer') # segment number
    segment_columns.append('ISEG integer') # segment number
    segment_columns.append('NSEG integer') # segment number
    # for GSFLOW
    segment_columns.append('ICALC integer') # 3 for power function
    segment_columns.append('OUTSEG integer') # downstream segment -- tostream, renumbered
    segment_columns.append('ROUGHCH double precision') # overbank roughness
    segment_columns.append('ROUGHBK double precision') # in-channel roughness
    segment_columns.append('WIDTH1 double precision') # overbank roughness
    segment_columns.append('WIDTH2 double precision') # in-channel roughness
    segment_columns.append('CDPTH double precision') # depth coeff
    segment_columns.append('FDPTH double precision') # depth exp
    segment_columns.append('AWDTH double precision') # width coeff
    segment_columns.append('BWDTH double precision') # width exp
    # The below will be all 0
    segment_columns.append('IUPSEG varchar') # upstream segment ID number, for diversions
    segment_columns.append('FLOW varchar')
    segment_columns.append('RUNOFF varchar')
    segment_columns.append('ETSW varchar')
    segment_columns.append('PPTSW varchar')

    segment_columns = ",".join(segment_columns)

    # CONSIDER THE EFFECT OF OVERWRITING COLUMNS -- WARN FOR THIS
    # IF MAP EXISTS ALREADY?

    # Create a map to work with
    g.copy(vector=(streams, segments), overwrite=gscript.overwrite())
    # and add its columns
    v.db_addcolumn(map=segments, columns=segment_columns)

    # Produce the data table entries
    ##################################
    colNames = np.array(gscript.vector_db_select(segments, layer=1)['columns'])
    colValues = np.array(gscript.vector_db_select(segments, layer=1)['values'].values())
    number_of_segments = colValues.shape[0]
    cats = colValues[:,colNames == 'cat'].astype(int).squeeze()

    nseg = np.arange(1, len(cats)+1)
    nseg_cats = []
    for i in range(len(cats)):
        nseg_cats.append( (nseg[i], cats[i]) )

    segmentsTopo = VectorTopo(segments)
    segmentsTopo.open('rw')
    cur = segmentsTopo.table.conn.cursor()

    # id = cat (as does ISEG and NSEG)
    cur.executemany("update "+segments+" set id=? where cat=?", nseg_cats)
    cur.executemany("update "+segments+" set ISEG=? where cat=?", nseg_cats)
    cur.executemany("update "+segments+" set NSEG=? where cat=?", nseg_cats)

    # outseg = tostream: default is 0 if "tostream" is off-map
    cur.execute("update "+segments+" set OUTSEG=0")
    cur.executemany("update "+segments+" set OUTSEG=? where tostream=?", nseg_cats)

    # Discharge and hydraulic geometry
    cur.execute("update "+segments+" set WIDTH1="+str(WIDTH1))
    cur.execute("update "+segments+" set WIDTH2="+str(WIDTH2))
    cur.execute("update "+segments+" set ROUGHCH="+str(ROUGHCH))
    cur.execute("update "+segments+" set ROUGHBK="+str(ROUGHBK))
    cur.execute("update "+segments+" set ICALC="+str(ICALC))
    cur.execute("update "+segments+" set CDPTH="+str(CDPTH))
    cur.execute("update "+segments+" set FDPTH="+str(FDPTH))
    cur.execute("update "+segments+" set AWDTH="+str(AWDTH))
    cur.execute("update "+segments+" set BWDTH="+str(BWDTH))

    gscript.message('')
    gscript.message('NOTICE: not currently used:')
    gscript.message('IUPSEG, FLOW, RUNOFF, ETSW, and PPTSW.')
    gscript.message('All set to 0.')
    gscript.message('')

    # values that are 0
    cur.execute("update "+segments+" set IUPSEG="+str(0))
    cur.execute("update "+segments+" set FLOW="+str(0))
    cur.execute("update "+segments+" set RUNOFF="+str(0))
    cur.execute("update "+segments+" set ETSW="+str(0))
    cur.execute("update "+segments+" set PPTSW="+str(0))

    segmentsTopo.table.conn.commit()
    segmentsTopo.close()


if __name__ == "__main__":
    main()
