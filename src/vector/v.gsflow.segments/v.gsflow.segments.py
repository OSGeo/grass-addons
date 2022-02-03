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

# %module
# % description: Prepares stream segments for PRMS and GSFLOW
# % keyword: vector
# % keyword: stream network
# % keyword: hydrology
# % keyword: GSFLOW
# %end

# %option G_OPT_V_INPUT
# %  key: input
# %  label: Vector stream network from r.stream.extract
# %  required: yes
# %  guidependency: layer,column
# %end

# %option G_OPT_V_OUTPUT
# %  key: output
# %  label: Segments: stream segments for GSFLOW / PRMS
# %  required: yes
# %  guidependency: layer,column
# %end

# %option
# %  key: icalc
# %  type: integer
# %  description: Stream depth option: 0-const; 1,2-Manning (rect/8-pt); 3-aQ^b
# %  answer: 1
# %  required: no
# %end

# %option
# %  key: cdpth
# %  type: double
# %  description: Flow depth coefficient [meters]; used if ICALC=3
# %  answer: 0.4
# %  required: no
# %end

# %option
# %  key: fdpth
# %  type: double
# %  description: Flow depth exponent; used if ICALC=3
# %  answer: 0.42
# %  required: no
# %end

# %option
# %  key: awdth
# %  type: double
# %  description: Flow width coefficient [meters]; used if ICALC=3
# %  answer: 4
# %  required: no
# %end

# %option
# %  key: bwdth
# %  type: double
# %  description: Flow width exponent; used if ICALC=3
# %  answer: 0.23
# %  required: no
# %end

# %option
# %  key: iupseg
# %  type: string
# %  description: Category of upstream diversion segment (from_cat,to_cat,...)
# %  answer: 0,0
# %  required: no
# %end

# %option
# %  key: flow
# %  type: string
# %  description: Streamflow entering the upstream-most segs (cat,Q,cat,Q,...)
# %  answer: 0,0
# %  required: no
# %end

# %option
# %  key: runoff
# %  type: string
# %  description: Diffuse runoff entering each segment (cat,Q,cat,Q,...)
# %  answer: 0,0
# %  required: no
# %end

# %option
# %  key: etsw
# %  type: string
# %  description: Direct removal of in-channel water by ET (cat,Q,cat,Q)
# %  answer: 0,0
# %  required: no
# %end

# %option
# %  key: pptsw
# %  type: string
# %  description: Direct precipitation on the stream (cat,Q,cat,Q)
# %  answer: 0,0
# %  required: no
# %end

# %option
# %  key: roughch_value
# %  type: double
# %  description: In-channel Manning's n (single value) for ICALC=1,2
# %  answer: 0.035
# %  required: no
# %end

# %option
# %  key: roughch_raster
# %  type: string
# %  description: In-channel Manning's n raster map for ICALC=1,2
# %  required: no
# %end

# %option
# %  key: roughch_points
# %  type: string
# %  description: In-channel Manning's n vector point meas for ICALC=1,2
# %  required: no
# %end

# %option
# %  key: roughch_pt_col
# %  type: string
# %  description: Column name for in-channel n point measurements
# %  required: no
# %end

# %option
# %  key: roughbk_value
# %  type: double
# %  description: Overbank Manning's n for ICALC=2
# %  answer: 0.06
# %  required: no
# %end

# %option
# %  key: roughbk_raster
# %  type: string
# %  description: Overbank Manning's n raster map for ICALC=2
# %  required: no
# %end

# %option
# %  key: roughbk_points
# %  type: string
# %  description: Overbank Manning's n vector point meas for ICALC=2
# %  required: no
# %end

# %option
# %  key: roughbk_pt_col
# %  type: string
# %  description: Column name for overbank n point measurements
# %  required: no
# %end

# %option
# %  key: width1
# %  type: double
# %  description: Upstream width in segment [m], uniform in watershed
# %  answer: 5
# %  required: no
# %end

# %option
# %  key: width2
# %  type: double
# %  description: Downstream width in segment [m], uniform in watershed
# %  answer: 5
# %  required: no
# %end

# %option
# %  key: width_points
# %  type: string
# %  description: Channel width point meas vect (instead of width1,width2)
# %  required: no
# %end

# %option
# %  key: width_points_col
# %  type: string
# %  description: Channel width point meas vect column
# %  required: no
# %end

# %option
# %  key: width1
# %  type: double
# %  description: Upstream width in segment [m], uniform in watershed
# %  answer: 5
# %  required: no
# %end

# %option
# %  key: width2
# %  type: double
# %  description: Downstream width in segment [m], uniform in watershed
# %  answer: 5
# %  required: no
# %end

# %option
# %  key: width_points
# %  type: string
# %  description: Channel width point meas vect (instead of width1,width2)
# %  required: no
# %end

# %option
# %  key: width_points_col
# %  type: string
# %  description: Channel width point meas vect column
# %  required: no
# %end

# %option
# %  key: fp_width_value
# %  type: double
# %  description: Floodplain width as constant value (ICALC=2)
# %  answer: 0
# %  required: no
# %end

# %option
# %  key: fp_width_pts
# %  type: string
# %  description: Floodplain width measurement vector (ICALC=2)
# %  required: no
# %end

# %option
# %  key: fp_width_pts_col
# %  type: string
# %  description: Floodplain width measurement column (ICALC=2)
# %  required: no
# %end

##################
# IMPORT MODULES #
##################
# PYTHON
import numpy as np

# GRASS
from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.modules.shortcuts import raster as r
from grass.pygrass.modules.shortcuts import vector as v
from grass.pygrass.modules.shortcuts import miscellaneous as m
from grass.pygrass.gis import region
from grass.pygrass import vector  # Change to "v"?
from grass.script import vector_db_select
from grass.pygrass.vector import Vector, VectorTopo
from grass.pygrass.raster import RasterRow
from grass.pygrass import utils
from grass import script as gscript

# from pygrass.messages import Messenger
import sys
import time

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
    streams = options["input"]
    segments = options["output"]

    # Hydraulic geometry
    ICALC = int(options["icalc"])

    # ICALC=0: Constant depth
    WIDTH1 = options["width1"]
    WIDTH2 = options["width2"]

    # ICALC=1,2: Manning (in channel and overbank): below

    # ICALC=3: Power-law relationships (following Leopold and others)
    # The at-a-station default exponents are from Rhodes (1977)
    CDPTH = str(float(options["cdpth"]) / 35.3146667)  # cfs to m^3/s
    FDPTH = options["fdpth"]
    AWDTH = str(float(options["awdth"]) / 35.3146667)  # cfs to m^3/s
    BWDTH = options["bwdth"]

    ##################################################
    # CHECKING DEPENDENCIES WITH OPTIONAL PARAMETERS #
    ##################################################

    if ICALC == 3:
        if CDPTH and FDPTH and AWDTH and BWDTH:
            pass
        else:
            gscript.fatal(
                "Missing CDPTH, FDPTH, AWDTH, and/or BWDTH. \
                         These are required when ICALC = 3."
            )

    ###########
    # RUNNING #
    ###########

    # New Columns for Segments
    segment_columns = []
    # Self ID
    segment_columns.append("id integer")  # segment number
    segment_columns.append("ISEG integer")  # segment number
    segment_columns.append("NSEG integer")  # segment number
    # for GSFLOW
    segment_columns.append(
        "ICALC integer"
    )  # 1 for channel, 2 for channel+fp, 3 for power function
    segment_columns.append(
        "OUTSEG integer"
    )  # downstream segment -- tostream, renumbered
    segment_columns.append("ROUGHCH double precision")  # overbank roughness
    segment_columns.append("ROUGHBK double precision")  # in-channel roughness
    segment_columns.append("WIDTH1 double precision")  # overbank roughness
    segment_columns.append("WIDTH2 double precision")  # in-channel roughness
    segment_columns.append("CDPTH double precision")  # depth coeff
    segment_columns.append("FDPTH double precision")  # depth exp
    segment_columns.append("AWDTH double precision")  # width coeff
    segment_columns.append("BWDTH double precision")  # width exp
    segment_columns.append(
        "floodplain_width double precision"
    )  # floodplain width (8-pt approx channel + flat fp)
    # The below will be all 0
    segment_columns.append(
        "IUPSEG varchar"
    )  # upstream segment ID number, for diversions
    segment_columns.append("FLOW varchar")
    segment_columns.append("RUNOFF varchar")
    segment_columns.append("ETSW varchar")
    segment_columns.append("PPTSW varchar")

    segment_columns = ",".join(segment_columns)

    # CONSIDER THE EFFECT OF OVERWRITING COLUMNS -- WARN FOR THIS
    # IF MAP EXISTS ALREADY?

    # Create a map to work with
    g.copy(vector=(streams, segments), overwrite=gscript.overwrite())
    # and add its columns
    v.db_addcolumn(map=segments, columns=segment_columns)

    # Produce the data table entries
    ##################################
    colNames = np.array(gscript.vector_db_select(segments, layer=1)["columns"])
    colValues = np.array(gscript.vector_db_select(segments, layer=1)["values"].values())
    number_of_segments = colValues.shape[0]
    cats = colValues[:, colNames == "cat"].astype(int).squeeze()

    nseg = np.arange(1, len(cats) + 1)
    nseg_cats = []
    for i in range(len(cats)):
        nseg_cats.append((nseg[i], cats[i]))

    segmentsTopo = VectorTopo(segments)
    segmentsTopo.open("rw")
    cur = segmentsTopo.table.conn.cursor()

    # id = cat (as does ISEG and NSEG)
    cur.executemany("update " + segments + " set id=? where cat=?", nseg_cats)
    cur.executemany("update " + segments + " set ISEG=? where cat=?", nseg_cats)
    cur.executemany("update " + segments + " set NSEG=? where cat=?", nseg_cats)

    # outseg = tostream: default is 0 if "tostream" is off-map
    cur.execute("update " + segments + " set OUTSEG=0")
    cur.executemany("update " + segments + " set OUTSEG=? where tostream=?", nseg_cats)

    # Hydraulic geometry selection
    cur.execute("update " + segments + " set ICALC=" + str(ICALC))
    segmentsTopo.table.conn.commit()
    segmentsTopo.close()
    if ICALC == 0:
        gscript.message("")
        gscript.message("ICALC=0 (constant) not supported")
        gscript.message("Continuing nonetheless.")
        gscript.message("")
    if ICALC == 1:
        if options["width_points"] is not "":
            # Can add machinery here for separate upstream and downstream widths
            # But really should not vary all that much
            # v.to_db(map=segments, option='start', columns='xr1,yr1')
            # v.to_db(map=segments, option='end', columns='xr2,yr2')
            gscript.run_command(
                "v.distance",
                from_=segments,
                to=options["width_points"],
                upload="to_attr",
                to_column=options["width_points_col"],
                column="WIDTH1",
            )
            v.db_update(map=segments, column="WIDTH2", query_column="WIDTH1")
        else:
            segmentsTopo = VectorTopo(segments)
            segmentsTopo.open("rw")
            cur = segmentsTopo.table.conn.cursor()
            cur.execute("update " + segments + " set WIDTH1=" + str(WIDTH1))
            cur.execute("update " + segments + " set WIDTH2=" + str(WIDTH2))
            segmentsTopo.table.conn.commit()
            segmentsTopo.close()
    if ICALC == 2:
        # REMOVE THIS MESSAGE ONCE THIS IS INCLUDED IN INPUT-FILE BUILDER
        gscript.message("")
        gscript.message("ICALC=2 (8-point channel + floodplain) not supported")
        gscript.message("Continuing nonetheless.")
        gscript.message("")
        if options["fp_width_pts"] is not "":
            gscript.run_command(
                "v.distance",
                from_=segments,
                to=options["fp_width_pts"],
                upload="to_attr",
                to_column=options["fp_width_pts_col"],
                column="floodplain_width",
            )
        else:
            segmentsTopo = VectorTopo(segments)
            segmentsTopo.open("rw")
            cur = segmentsTopo.table.conn.cursor()
            cur.execute(
                "update "
                + segments
                + " set floodplain_width="
                + str(options["fp_width_value"])
            )
            segmentsTopo.table.conn.commit()
            segmentsTopo.close()
    if ICALC == 3:
        segmentsTopo = VectorTopo(segments)
        segmentsTopo.open("rw")
        cur = segmentsTopo.table.conn.cursor()
        cur.execute("update " + segments + " set CDPTH=" + str(CDPTH))
        cur.execute("update " + segments + " set FDPTH=" + str(FDPTH))
        cur.execute("update " + segments + " set AWDTH=" + str(AWDTH))
        cur.execute("update " + segments + " set BWDTH=" + str(BWDTH))
        segmentsTopo.table.conn.commit()
        segmentsTopo.close()

    # values that are 0
    gscript.message("")
    gscript.message("NOTICE: not currently used:")
    gscript.message("IUPSEG, FLOW, RUNOFF, ETSW, and PPTSW.")
    gscript.message("All set to 0.")
    gscript.message("")

    segmentsTopo = VectorTopo(segments)
    segmentsTopo.open("rw")
    cur = segmentsTopo.table.conn.cursor()
    cur.execute("update " + segments + " set IUPSEG=" + str(0))
    cur.execute("update " + segments + " set FLOW=" + str(0))
    cur.execute("update " + segments + " set RUNOFF=" + str(0))
    cur.execute("update " + segments + " set ETSW=" + str(0))
    cur.execute("update " + segments + " set PPTSW=" + str(0))
    segmentsTopo.table.conn.commit()
    segmentsTopo.close()

    # Roughness
    # ICALC=1,2: Manning (in channel)
    if (options["roughch_raster"] is not "") and (options["roughch_points"] is not ""):
        gscript.fatal(
            "Choose either a raster or vector or a value as Manning's n input."
        )
    if options["roughch_raster"] is not "":
        ROUGHCH = options["roughch_raster"]
        v.rast_stats(
            raster=ROUGHCH,
            method="average",
            column_prefix="tmp",
            map=segments,
            flags="c",
        )
        # v.db_renamecolumn(map=segments, column='tmp_average,ROUGHCH', quiet=True)
        v.db_update(
            map=segments, column="ROUGHCH", query_column="tmp_average", quiet=True
        )
        v.db_dropcolumn(map=segments, columns="tmp_average", quiet=True)
    elif options["roughch_points"] is not "":
        ROUGHCH = options["roughch_points"]
        gscript.run_command(
            "v.distance",
            from_=segments,
            to=ROUGHCH,
            upload="to_attr",
            to_column=options["roughch_pt_col"],
            column="ROUGHCH",
        )
    else:
        segmentsTopo = VectorTopo(segments)
        segmentsTopo.open("rw")
        cur = segmentsTopo.table.conn.cursor()
        ROUGHCH = options["roughch_value"]
        cur.execute("update " + segments + " set ROUGHCH=" + str(ROUGHCH))
        segmentsTopo.table.conn.commit()
        segmentsTopo.close()

    # ICALC=2: Manning (overbank)
    if (options["roughbk_raster"] is not "") and (options["roughbk_points"] is not ""):
        gscript.fatal(
            "Choose either a raster or vector or a value as Manning's n input."
        )
    if options["roughbk_raster"] is not "":
        ROUGHBK = options["roughbk_raster"]
        v.rast_stats(
            raster=ROUGHBK,
            method="average",
            column_prefix="tmp",
            map=segments,
            flags="c",
        )
        v.db_renamecolumn(map=segments, column="tmp_average,ROUGHBK", quiet=True)
    elif options["roughbk_points"] is not "":
        ROUGHBK = options["roughbk_points"]
        gscript.run_command(
            "v.distance",
            from_=segments,
            to=ROUGHBK,
            upload="to_attr",
            to_column=options["roughbk_pt_col"],
            column="ROUGHBK",
        )
    else:
        segmentsTopo = VectorTopo(segments)
        segmentsTopo.open("rw")
        cur = segmentsTopo.table.conn.cursor()
        ROUGHBK = options["roughbk_value"]
        cur.execute("update " + segments + " set ROUGHBK=" + str(ROUGHBK))
        segmentsTopo.table.conn.commit()
        segmentsTopo.close()


if __name__ == "__main__":
    main()
