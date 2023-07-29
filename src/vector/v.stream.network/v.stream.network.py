#!/usr/bin/env python
############################################################################
#
# MODULE:       v.stream.network
#
# AUTHOR(S):    Andrew Wickert
#               Vaclav Petras (v8 fixes and interface improvements)
#
# PURPOSE:      Attach IDs of upstream and downstream nodes as well as the
#               category value of the next downstream stream segment
#               (0 if the stream exits the map)
#
# COPYRIGHT:    (c) 2016-2023 Andrew Wickert and the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################
#
# REQUIREMENTS:
#      -  uses inputs from r.stream.extract

# %module
# % description: Build a linked stream network: each link knows its downstream link
# % keyword: vector
# % keyword: stream network
# % keyword: hydrology
# % keyword: geomorphology
# %end

# %option G_OPT_V_INPUT
# %  key: map
# %  label: Vector stream network from r.stream.extract
# %  required: yes
# %  guidependency: layer,column
# %end

# %option
# %  key: upstream_easting_column
# %  type: string
# %  description: Upstream easting (or x or lon) column name
# %  answer: x1
# %  required : no
# %end

# %option
# %  key: upstream_northing_column
# %  type: string
# %  description: Upstream northing (or y or lat) column name
# %  answer: y1
# %  required : no
# %end

# %option
# %  key: downstream_easting_column
# %  type: string
# %  description: Downstream easting (or x or lon) column name
# %  answer: x2
# %  required : no
# %end

# %option
# %  key: downstream_northing_column
# %  type: string
# %  description: Downstream northing (or y or lat) column name
# %  answer: y2
# %  required : no
# %end

# %option
# %  key: tostream_cat_column
# %  type: string
# %  label: Adjacent downstream segment category
# %  description: Zero (0) indicates off-map flow
# %  answer: tostream
# %  required : no
# %end

"""Add stream network links to attribute table"""

import numpy as np

from grass import script as gs

from grass.pygrass.modules.shortcuts import vector as v
from grass.pygrass.vector import VectorTopo
from grass.script import vector_db_select


def main():
    """Links each segment to its downstream segment

    Links each river segment to the next downstream segment in a tributary
    network by referencing its category (cat) number in a new column. "0"
    means that the river exits the map.
    """
    options, unused_flags = gs.parser()
    streams = options["map"]
    x1 = options["upstream_easting_column"]
    y1 = options["upstream_northing_column"]
    x2 = options["downstream_easting_column"]
    y2 = options["downstream_northing_column"]
    to_stream = options["tostream_cat_column"]

    # Get coordinates of points: 1 = start, 2 = end
    v.to_db(map=streams, option="start", columns=x1 + "," + y1)
    v.to_db(map=streams, option="end", columns=x2 + "," + y2)

    # Read in and save the start and end coordinate points
    col_names = np.array(vector_db_select(streams)["columns"])
    col_values = np.array(list(vector_db_select(streams)["values"].values()))
    # river number
    cats = col_values[:, col_names == "cat"].astype(int).squeeze()
    # upstream
    xy1 = col_values[:, (col_names == "x1") + (col_names == "y1")].astype(float)
    # downstream
    xy2 = col_values[:, (col_names == "x2") + (col_names == "y2")].astype(float)

    # Build river network
    to_cats = []
    for i in range(len(cats)):
        to_segment_mask = np.prod(xy1 == xy2[i], axis=1)
        if np.sum(to_segment_mask) == 0:
            to_cats.append(0)
        else:
            to_cats.append(cats[to_segment_mask.nonzero()[0][0]])
    to_cats = np.asarray(to_cats).astype(int)

    streams_vector = VectorTopo(streams)
    streams_vector.open("rw")
    streams_vector.table.columns.add(f"{to_stream}", "int")
    streams_vector.table.conn.commit()
    # This gives us a set of downstream-facing adjacencies.
    # We will update the database with it.
    cur = streams_vector.table.conn.cursor()
    # Default to 0 if no stream flows to it
    cur.execute(f"update {streams} set {to_stream}=0")
    for to_cat, where_cat in zip(to_cats, cats):
        cur.execute(f"update {streams} set {to_stream}={to_cat} where cat={where_cat}")
    streams_vector.table.conn.commit()
    streams_vector.close()

    gs.message(
        _(
            'Drainage topology built. See "{to_stream}" column for the downstream cat.'
        ).format(to_stream=to_stream)
    )
    gs.message(_("A cat value of 0 indicates the downstream-most segment."))


if __name__ == "__main__":
    main()
