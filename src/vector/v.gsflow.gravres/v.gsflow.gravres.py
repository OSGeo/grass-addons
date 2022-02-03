#!/usr/bin/env python
############################################################################
#
# MODULE:       v.gsflow.gravres
#
# AUTHOR(S):    Andrew Wickert
#
# PURPOSE:      Build gravity reservoirs -- intersections of HRU sub-basins and
#               MODFLOW grid cells -- for GSFLOW
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
#      -  uses inputs from r.stream.basins & r.to.vect
#      -  uses inputs from v.gsflow.grid

# More information
# Started December 2016

# %module
# % description: Set parameters for GSFLOW Hydrologic Response Units (HRUs)
# % keyword: vector
# % keyword: stream network
# % keyword: hydrology
# % keyword: GSFLOW
# %end

# %option G_OPT_V_INPUT
# %  key: hru_input
# %  label: Sub-basins
# %  required: yes
# %  guidependency: layer,column
# %end

# %option G_OPT_V_INPUT
# %  key: grid_input
# %  label: MODFLOW grid
# %  required: yes
# %  guidependency: layer,column
# %end

# %option G_OPT_V_OUTPUT
# %  key: output
# %  label: Gravity reservoirs: union (AND) of sub-basins and MODFLOW grid
# %  required: yes
# %  guidependency: layer,column
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

###############
# MAIN MODULE #
###############


def main():
    """
    Build gravity reservoirs in GSFLOW: combines MODFLOW grid and HRU sub-basins
    These define the PRMS soil zone that connects to MODFLOW cells
    """

    ##################
    # OPTION PARSING #
    ##################

    # I/O
    options, flags = gscript.parser()

    # I/O
    HRUs = options["hru_input"]
    grid = options["grid_input"]
    segments = options["output"]
    # col = options['col']
    gravity_reservoirs = options["output"]

    ############
    # ANALYSIS #
    ############

    """
    # Basin areas
    v.db_addcolumn(map=basins, columns=col)
    v.to_db(map=basins, option='area', units='meters', columns=col)
    """

    # Create gravity reservoirs -- overlay cells=grid and HRUs
    v.overlay(
        ainput=HRUs,
        binput=grid,
        atype="area",
        btype="area",
        operator="and",
        output=gravity_reservoirs,
        overwrite=gscript.overwrite(),
    )
    v.db_dropcolumn(map=gravity_reservoirs, columns="a_cat,a_label,b_cat", quiet=True)
    # Cell and HRU ID's
    v.db_renamecolumn(map=gravity_reservoirs, column=("a_id", "gvr_hru_id"), quiet=True)
    v.db_renamecolumn(
        map=gravity_reservoirs, column=("b_id", "gvr_cell_id"), quiet=True
    )
    # Percent areas
    v.db_renamecolumn(
        map=gravity_reservoirs, column=("a_hru_area_m2", "hru_area_m2"), quiet=True
    )
    v.db_renamecolumn(
        map=gravity_reservoirs, column=("b_area_m2", "cell_area_m2"), quiet=True
    )
    v.db_addcolumn(
        map=gravity_reservoirs, columns="area_m2 double precision", quiet=True
    )
    v.to_db(
        map=gravity_reservoirs,
        option="area",
        units="meters",
        columns="area_m2",
        quiet=True,
    )
    v.db_addcolumn(
        map=gravity_reservoirs,
        columns="gvr_cell_pct double precision, gvr_hru_pct double precision",
        quiet=True,
    )
    v.db_update(
        map=gravity_reservoirs,
        column="gvr_cell_pct",
        query_column="100*area_m2/cell_area_m2",
        quiet=True,
    )
    v.db_update(
        map=gravity_reservoirs,
        column="gvr_hru_pct",
        query_column="100*area_m2/hru_area_m2",
        quiet=True,
    )
    v.extract(
        input=gravity_reservoirs,
        output="tmp_",
        where="gvr_cell_pct > 0.001",
        overwrite=True,
        quiet=True,
    )
    g.rename(vector=("tmp_", gravity_reservoirs), overwrite=True, quiet=True)


if __name__ == "__main__":
    main()
