#!/usr/bin/env python
############################################################################
#
# MODULE:       v.gsflow.grid
#
# AUTHOR(S):    Andrew Wickert
#
# PURPOSE:      Builds grid for the MODFLOW component of GSFLOW
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
#      -  uses inputs from r.stream.extract

# More information
# Started December 2016

# %module
# % description: Builds grid for the MODFLOW component of GSFLOW
# % keyword: vector
# % keyword: stream network
# % keyword: hydrology
# % keyword: GSFLOW
# %end

# %option G_OPT_V_INPUT
# %  key: basin
# %  label: Study basin, over which to build a MODFLOW grid
# %  required: yes
# %end

# %option G_OPT_V_INPUT
# %  key: pour_point
# %  label: Pour point, to which row and col (MODFLOW) will be added
# %  required: yes
# %end

# %option G_OPT_R_INPUT
# %  key: raster_input
# %  label: Raster to be resampled to grid resolution
# %  required: no
# %end

# %option
# %  key: dx
# %  label: Cell size suggestion (x / E / zonal), map units: rounds to DEM
# %  required: yes
# %end

# %option
# %  key: dy
# %  label: Cell size suggestion (y / N / meridional), map units: rounds to DEM
# %  required: yes
# %end

# %option G_OPT_V_OUTPUT
# %  key: output
# %  label: MODFLOW grid
# %  required: yes
# %end

# %option G_OPT_R_OUTPUT
# %  key: mask_output
# %  label: Raster basin mask: inside (1) or outside (0) the watershed?
# %  required: no
# %end

# %option G_OPT_V_OUTPUT
# %  key: bc_cell
# %  label: Constant-head boundary condition cell
# %  required: yes
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
from grass.pygrass.vector.geometry import Point

###############
# MAIN MODULE #
###############


def main():
    """
    Builds a grid for the MODFLOW component of the USGS hydrologic model,
    GSFLOW.
    """

    options, flags = gscript.parser()
    basin = options["basin"]
    pp = options["pour_point"]
    raster_input = options["raster_input"]
    dx = options["dx"]
    dy = options["dy"]
    grid = options["output"]
    mask = options["mask_output"]
    bc_cell = options["bc_cell"]
    # basin='basins_tmp_onebasin'; pp='pp_tmp'; raster_input='DEM'; raster_output='DEM_coarse'; dx=dy='500'; grid='grid_tmp'; mask='mask_tmp'

    """
    # Fatal if raster input and output are not both set
    _lena0 = (len(raster_input) == 0)
    _lenb0 = (len(raster_output) == 0)
    if _lena0 + _lenb0 == 1:
        gscript.fatal("You must set both raster input and output, or neither.")
    """

    # Fatal if bc_cell set but mask and grid are false
    if bc_cell != "":
        if (mask == "") or (pp == ""):
            gscript.fatal("Mask and pour point must be set to define b.c. cell")

    # Create grid -- overlaps DEM, three cells of padding
    g.region(raster=raster_input, ewres=dx, nsres=dy)
    gscript.use_temp_region()
    reg = gscript.region()
    reg_grid_edges_sn = np.linspace(reg["s"], reg["n"], reg["rows"])
    reg_grid_edges_we = np.linspace(reg["w"], reg["e"], reg["cols"])
    g.region(vector=basin, ewres=dx, nsres=dy)
    regnew = gscript.region()
    # Use a grid ratio -- don't match exactly the desired MODFLOW resolution
    grid_ratio_ns = np.round(regnew["nsres"] / reg["nsres"])
    grid_ratio_ew = np.round(regnew["ewres"] / reg["ewres"])
    # Get S, W, and then move the unit number of grid cells over to get N and E
    # and include 3 cells of padding around the whole watershed
    _s_dist = np.abs(reg_grid_edges_sn - (regnew["s"] - 3.0 * regnew["nsres"]))
    _s_idx = np.where(_s_dist == np.min(_s_dist))[0][0]
    _s = float(reg_grid_edges_sn[_s_idx])
    _n_grid = np.arange(
        _s, reg["n"] + 3 * grid_ratio_ns * reg["nsres"], grid_ratio_ns * reg["nsres"]
    )
    _n_dist = np.abs(_n_grid - (regnew["n"] + 3.0 * regnew["nsres"]))
    _n_idx = np.where(_n_dist == np.min(_n_dist))[0][0]
    _n = float(_n_grid[_n_idx])
    _w_dist = np.abs(reg_grid_edges_we - (regnew["w"] - 3.0 * regnew["ewres"]))
    _w_idx = np.where(_w_dist == np.min(_w_dist))[0][0]
    _w = float(reg_grid_edges_we[_w_idx])
    _e_grid = np.arange(
        _w, reg["e"] + 3 * grid_ratio_ew * reg["ewres"], grid_ratio_ew * reg["ewres"]
    )
    _e_dist = np.abs(_e_grid - (regnew["e"] + 3.0 * regnew["ewres"]))
    _e_idx = np.where(_e_dist == np.min(_e_dist))[0][0]
    _e = float(_e_grid[_e_idx])
    # Finally make the region
    g.region(
        w=str(_w),
        e=str(_e),
        s=str(_s),
        n=str(_n),
        nsres=str(grid_ratio_ns * reg["nsres"]),
        ewres=str(grid_ratio_ew * reg["ewres"]),
    )
    # And then make the grid
    v.mkgrid(map=grid, overwrite=gscript.overwrite())

    # Cell numbers (row, column, continuous ID)
    v.db_addcolumn(map=grid, columns="id int", quiet=True)
    colNames = np.array(gscript.vector_db_select(grid, layer=1)["columns"])
    colValues = np.array(gscript.vector_db_select(grid, layer=1)["values"].values())
    cats = colValues[:, colNames == "cat"].astype(int).squeeze()
    rows = colValues[:, colNames == "row"].astype(int).squeeze()
    cols = colValues[:, colNames == "col"].astype(int).squeeze()
    nrows = np.max(rows)
    ncols = np.max(cols)
    cats = np.ravel([cats])
    _id = np.ravel([ncols * (rows - 1) + cols])
    _id_cat = []
    for i in range(len(_id)):
        _id_cat.append((_id[i], cats[i]))
    gridTopo = VectorTopo(grid)
    gridTopo.open("rw")
    cur = gridTopo.table.conn.cursor()
    cur.executemany("update " + grid + " set id=? where cat=?", _id_cat)
    gridTopo.table.conn.commit()
    gridTopo.close()

    # Cell area
    v.db_addcolumn(map=grid, columns="area_m2 double precision", quiet=True)
    v.to_db(map=grid, option="area", units="meters", columns="area_m2", quiet=True)

    # Basin mask
    if len(mask) > 0:
        # Fine resolution region:
        g.region(
            n=reg["n"],
            s=reg["s"],
            w=reg["w"],
            e=reg["e"],
            nsres=reg["nsres"],
            ewres=reg["ewres"],
        )
        # Rasterize basin
        v.to_rast(
            input=basin,
            output=mask,
            use="val",
            value=1,
            overwrite=gscript.overwrite(),
            quiet=True,
        )
        # Coarse resolution region:
        g.region(
            w=str(_w),
            e=str(_e),
            s=str(_s),
            n=str(_n),
            nsres=str(grid_ratio_ns * reg["nsres"]),
            ewres=str(grid_ratio_ew * reg["ewres"]),
        )
        r.resamp_stats(
            input=mask, output=mask, method="sum", overwrite=True, quiet=True
        )
        r.mapcalc("tmp" + " = " + mask + " > 0", overwrite=True, quiet=True)
        g.rename(raster=("tmp", mask), overwrite=True, quiet=True)
        r.null(map=mask, null=0, quiet=True)
        # Add mask location (1 vs 0) in the MODFLOW grid
        v.db_addcolumn(map=grid, columns="basinmask double precision", quiet=True)
        v.what_rast(map=grid, type="centroid", raster=mask, column="basinmask")

    """
    # Resampled raster
    if len(raster_output) > 0:
        r.resamp_stats(input=raster_input, output=raster_output, method='average', overwrite=gscript.overwrite(), quiet=True)
    """

    # Pour point
    if len(pp) > 0:
        v.db_addcolumn(map=pp, columns=("row integer", "col integer"), quiet=True)
        v.build(map=pp, quiet=True)
        v.what_vect(
            map=pp, query_map=grid, column="row", query_column="row", quiet=True
        )
        v.what_vect(
            map=pp, query_map=grid, column="col", query_column="col", quiet=True
        )

    # Next point downstream of the pour point
    # Requires pp (always) and mask (sometimes)
    # Dependency set above w/ gscript.fatal
    # g.region(raster='DEM')
    # dx = gscript.region()['ewres']
    # dy = gscript.region()['nsres']
    if len(bc_cell) > 0:
        ########## NEED TO USE TRUE TEMPORARY FILE ##########
        # May not work with dx != dy!
        v.to_rast(input=pp, output="tmp", use="val", value=1, overwrite=True)
        r.buffer(input="tmp", output="tmp", distances=float(dx) * 1.5, overwrite=True)
        r.mapcalc("tmp2 = if(tmp==2,1,null()) * " + raster_input, overwrite=True)
        # r.mapcalc('tmp = if(isnull('+raster_input+',0,(tmp == 2)))', overwrite=True)
        # g.region(rast='tmp')
        # r.null(map=raster_input,
        # g.region(raster=raster_input)
        # r.resample(input=raster_input, output='tmp3', overwrite=True)
        r.resamp_stats(
            input=raster_input, output="tmp3", method="minimum", overwrite=True
        )
        r.drain(input="tmp3", start_points=pp, output="tmp", overwrite=True)
        # g.region(w=str(_w), e=str(_e), s=str(_s), n=str(_n), nsres=str(grid_ratio_ns*reg['nsres']), ewres=str(grid_ratio_ew*reg['ewres']))
        # r.resamp_stats(input='tmp2', output='tmp3', overwrite=True)
        # g.rename(raster=('tmp3','tmp2'), overwrite=True, quiet=True)
        r.mapcalc("tmp3 = tmp2 * tmp", overwrite=True, quiet=True)
        g.rename(raster=("tmp3", "tmp"), overwrite=True, quiet=True)
        # r.null(map='tmp', setnull=0) # Not necessary: center point removed above
        r.to_vect(
            input="tmp",
            output=bc_cell,
            type="point",
            column="z",
            overwrite=gscript.overwrite(),
            quiet=True,
        )
        v.db_addcolumn(
            map=bc_cell,
            columns=(
                "row integer",
                "col integer",
                "x double precision",
                "y double precision",
            ),
            quiet=True,
        )
        v.build(map=bc_cell, quiet=True)
        v.what_vect(
            map=bc_cell, query_map=grid, column="row", query_column="row", quiet=True
        )
        v.what_vect(
            map=bc_cell, query_map=grid, column="col", query_column="col", quiet=True
        )
        v.to_db(map=bc_cell, option="coor", columns=("x,y"))

        # Of the candidates, the pour point is the closest one
        # v.db_addcolumn(map=bc_cell, columns=('dist_to_pp double precision'), quiet=True)
        # v.distance(from_=bc_cell, to=pp, upload='dist', column='dist_to_pp')

        # Find out if this is diagonal: finite difference works only N-S, W-E
        colNames = np.array(gscript.vector_db_select(pp, layer=1)["columns"])
        colValues = np.array(gscript.vector_db_select(pp, layer=1)["values"].values())
        pp_row = colValues[:, colNames == "row"].astype(int).squeeze()
        pp_col = colValues[:, colNames == "col"].astype(int).squeeze()
        colNames = np.array(gscript.vector_db_select(bc_cell, layer=1)["columns"])
        colValues = np.array(
            gscript.vector_db_select(bc_cell, layer=1)["values"].values()
        )
        bc_row = colValues[:, colNames == "row"].astype(int).squeeze()
        bc_col = colValues[:, colNames == "col"].astype(int).squeeze()
        # Also get x and y while we are at it: may be needed later
        bc_x = colValues[:, colNames == "x"].astype(float).squeeze()
        bc_y = colValues[:, colNames == "y"].astype(float).squeeze()
        if (bc_row != pp_row).all() and (bc_col != pp_col).all():
            if bc_row.ndim > 0:
                if len(bc_row) > 1:
                    for i in range(len(bc_row)):
                        """
                        UNTESTED!!!!
                        And probably unimportant -- having 2 cells with river
                        going through them is most likely going to happen with
                        two adjacent cells -- so a side and a corner
                        """
                        _col1, _row1 = str(bc_col[i]), str(pp_row[i])
                        _col2, _row2 = str(pp_col[i]), str(bc_row[i])
                        # Check if either of these is covered by the basin mask
                        _ismask_1 = gscript.vector_db_select(
                            grid,
                            layer=1,
                            where="(row == " + _row1 + ") AND (col ==" + _col1 + ")",
                            columns="basinmask",
                        )
                        _ismask_1 = int(_ismask_1["values"].values()[0][0])
                        _ismask_2 = gscript.vector_db_select(
                            grid,
                            layer=1,
                            where="(row == " + _row2 + ") AND (col ==" + _col2 + ")",
                            columns="basinmask",
                        )
                        _ismask_2 = int(_ismask_2["values"].values()[0][0])
                        # check if either of these is the other point
                        """
                        NOT DOING THIS YET -- HAVEN'T THOUGHT THROUGH IF
                        ACTUALLY NECESSARY. (And this is an edge case anyway)
                        """
                        # If both covered by mask, error
                        if _ismask_1 and _ismask_2:
                            gscript.fatal(
                                "All possible b.c. cells covered by basin mask.\n\
                                         Contact the developer: awickert (at) umn(.)edu"
                            )

            # If not diagonal, two possible locations that are adjacent
            # to the pour point
            _col1, _row1 = str(bc_col), str(pp_row)
            _col2, _row2 = str(pp_col), str(bc_row)
            # Check if either of these is covered by the basin mask
            _ismask_1 = gscript.vector_db_select(
                grid,
                layer=1,
                where="(row == " + _row1 + ") AND (col ==" + _col1 + ")",
                columns="basinmask",
            )
            _ismask_1 = int(_ismask_1["values"].values()[0][0])
            _ismask_2 = gscript.vector_db_select(
                grid,
                layer=1,
                where="(row == " + _row2 + ") AND (col ==" + _col2 + ")",
                columns="basinmask",
            )
            _ismask_2 = int(_ismask_2["values"].values()[0][0])
            # If both covered by mask, error
            if _ismask_1 and _ismask_2:
                gscript.fatal(
                    "All possible b.c. cells covered by basin mask.\n\
                             Contact the developer: awickert (at) umn(.)edu"
                )
            # Otherwise, those that keep those that are not covered by basin
            # mask and set ...
            # ... wait, do we want the point that touches as few interior
            # cells as possible?
            # maybe just try setting both and seeing what happens for now!
            else:
                # Get dx and dy
                # dx = gscript.region()['ewres']
                # dy = gscript.region()['nsres']
                # Build tool to handle multiple b.c. cells?
                bcvect = vector.Vector(bc_cell)
                bcvect.open("rw")
                _cat_i = 2
                if _ismask_1 != 0:
                    # _x should always be bc_x, but writing generalized code
                    _x = bc_x + float(dx) * (int(_col1) - bc_col)  # col 1 at w edge
                    _y = bc_y - float(dy) * (int(_row1) - bc_row)  # row 1 at n edge
                    point0 = Point(_x, _y)
                    bcvect.write(
                        point0,
                        cat=_cat_i,
                        attrs=(None, _row1, _col1, _x, _y),
                    )
                    bcvect.table.conn.commit()
                    _cat_i += 1
                if _ismask_2 != 0:
                    # _y should always be bc_y, but writing generalized code
                    _x = bc_x + float(dx) * (int(_col2) - bc_col)  # col 1 at w edge
                    _y = bc_y - float(dy) * (int(_row2) - bc_row)  # row 1 at n edge
                    point0 = Point(_x, _y)
                    bcvect.write(
                        point0,
                        cat=_cat_i,
                        attrs=(None, _row2, _col2, _x, _y),
                    )
                    bcvect.table.conn.commit()
                # Build database table and vector geometry
                bcvect.build()
                bcvect.close()

    g.region(
        n=reg["n"],
        s=reg["s"],
        w=reg["w"],
        e=reg["e"],
        nsres=reg["nsres"],
        ewres=reg["ewres"],
    )


if __name__ == "__main__":
    main()
