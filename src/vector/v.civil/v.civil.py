#!/usr/bin/env python
# -*- coding: utf-8
"""
Created on Wed Jul 23 18:37:36 2014

@author: jfcr
"""
############################################################################
#
# MODULE:       v.align, v0.6.0
#
# AUTHOR:       Jesús Fernández-Capel Rosillo
#               Civil Engineer, Spain
#               jfc at alcd net
#
# PURPOSE:      Desing roads, channels, ports...
#
# COPYRIGHT:    (c) 2014 Jesús Fernández-Capel Rosillo.
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

# %Module
# % description: Generates a alignment for designing roads, channels, and ports in civil engineering
# % keyword: vector
# % keyword: civil engineering
# % keyword: roads
# % keyword: channels
# % keyword: ports
# %End

#######################
### Required section
#######################

# %option G_OPT_V_INPUT
# % key: name
# % type: string
# % description: Name of road map
# % required: yes
# %end

#######################
### Plant section
#######################

# %option G_OPT_V_TYPE
# % key: plan
# % options: plan,pks,displ,marks
# % answer:
# % required: no
# % description: Plan options
# % guisection: Plan
# %end

# %option
# % key: pkopt
# % type: string
# % description:  Pks marks options values. (npk,mpk,dist,m)
# % required: no
# % answer: 20,100,2,4
# % guisection: Plan
# %end

# %option G_OPT_DB_TABLE
# % key: dtable
# % description: Other displaced table (Default all)
# % required: no
##% guidependency: ocolumn,scolumns
# % guisection: Plan
# %end

# %option G_OPT_DB_TABLE
# % key: mtable
# % description: Other marks table (Default all)
# % required: no
##% guidependency: ocolumn,scolumns
# % guisection: Plan
# %end

# %option
# % key: areaopt
# % type: string
# % description:  Pair of displaced lines for areas (1-2,2-5,5-6)
# % required: no
# % guisection: Plan
# %end

#######################
### Alz section
#######################

# %option G_OPT_V_TYPE
# % key: vert
# % options: vert,profile
# % answer:
# % required: no
# % description: Vertical options
# % guisection: Vert
# %end

# %option
# % key: lpscale
# % type: integer
# % description: Long profile vertical scale (V/H, V/1)
# % options: 0-100
# % answer : 4
# % required: no
# % guisection: Vert
# %end

# %option
# % key: lpopt
# % type: string
# % description: Long profile values Longmark,distMark_x,distMark_y,DistGitarr.
# % required: no
# % answer: 2,20,1,20
# % guisection: Vert
# %end

# %option
# % key: lpoffset
# % type: string
# % description: Long profile offset from origin of region
# % required: no
# % answer: 0,0
# % guisection: Vert
# %end

# %option
# % key: camber
# % type: string
# % description: General camber
# % required: no
# % answer: 0
# % guisection: Vert
# %end

# %option
# % key: displrot
# % type: string
# % description: Displaced lines to rotate
# % required: no
# % answer: 0,0
# % guisection: Vert
# %end

#######################
### Trans section
#######################

# %option G_OPT_V_TYPE
# % key: trans
# % options: trans,profiles
# % answer:
# % required: no
# % description: Vertical options
# % guisection: Trans
# %end

# %option
# % key: ltscale
# % type: double
# % description: Cross section vertical scale (V/H, V/1)
# % required: no
# % answer: 2
# % guisection: Trans
# %end

# %option
# % key: ltopt1
# % type: string
# % description: Cross section options values Longmark,distMark_x,distMark_y.
# % required: no
# % answer: 1,20,2
# % guisection: Trans
# %end

# %option
# % key: ltopt2
# % type: string
# % description: Trans section options values for nrows,distTP_x,distTP_y.
# % required: no
# % answer: 10,10,10
# % guisection: Trans
# %end

# %option
# % key: ltoffset
# % type: string
# % description: Trans sections profile offset from origin of region
# % required: no
# % answer: 0,0
# % guisection: Trans
# %end

#########################
### Terrain section
#########################

# %option G_OPT_V_TYPE
# % key: terr
# % options: slopes,sareas,topo
# % answer:
# % required: no
# % description: Terrain options
# % guisection: Terr
# %end

# %option G_OPT_R_INPUT
# % key: dem
# % key_desc: raster dem
# % description: Name of DEM raster
# % required: no
# % guisection: Terr
# %end

#########################
### TopoTools section
#########################

# %flag
# % key: o
# % description: TopoTools
# % guisection: TopoTools
# %end

# %option G_OPT_V_TYPE
# % key: actions
# % options: uppoints, pnt_info
# % answer:
# % required: no
# % description: Points tools
# % guisection: TopoTools
# %end

# %option
# % key: pk_info
# % type: double
# % description: PK
# % required: no
# % answer: 0
# % guisection: TopoTools
# %end

# %option G_OPT_V_TYPE
# % key: topotools
# % options: triangle,delaunay,curved,cut_hull
# % answer:
# % required: no
# % description: Triangulate and curved
# % guisection: TopoTools
# %end

##%option G_OPT_V_TYPE
##% key: tinraster
##% options: tintorast,nnbathy
##% answer:
##% required: no
##% description: Triangulate and curved
##% guisection: TopoTools
##%end


# %option G_OPT_V_TYPE
# % key: roundabout
# % options: roundabout
# % answer:
# % required: no
# % description: Roundabout tools
# % guisection: TopoTools
# %end

# %option
# % key: rround1
# % type: string
# % description: Minus radio for roundabout edge
# % required: no
# % guisection: TopoTools
# %end

# %option
# % key: rround2
# % type: string
# % description: Mayor radio for roundabout edge
# % required: no
# % guisection: TopoTools
# %end

# %option
# % key: azround
# % type: string
# % description: Azimut for roundabout start point
# % required: no
# % guisection: TopoTools
# %end

# %option
# % key: cround
# % type: string
# % description: Center for roundabout
# % required: no
# % guisection: TopoTools
# %end

# %option
# % key: roundname
# % type: string
# % description: Name for roundabout
# % required: no
# % guisection: TopoTools
# %end

#########################
### TableTools section
#########################

# %flag
# % key: e
# % description: TableTools
# % guisection: TableTools
# %end

# %option G_OPT_V_TYPE
# % key: add
# % options: table, row
# % answer:
# % required: no
# % description: Add new table or add row to table
# % guisection: TableTools
# %end

# %option
# % key: tab_type
# % type: string
# % label: Name of table for new table or to add row
# % description: To add new table only Displ or Marks table are supported
# % options: Vert,Displ,Trans,Terr,Marks
# % required: no
# % guisection: TableTools
# %end

# %option
# % key: tab_subname
# % type: string
# % label: Table subname for new table or row or displ subname to add or del col
# % required: no
# % guisection: TableTools
# %end

# %option
# % key: pklist
# % type: string
# % label: List of Pks
# % required: no
# % guisection: TableTools
# %end

# %option G_OPT_V_TYPE
# % key: displline
# % options: add,del
# % answer:
# % required: no
# % description: Add or del displaced line
# % guisection: TableTools
# %end

# %option
# % key: side
# % type: string
# % label: left or right side of Displ
# % options: left,right
# % required: no
# % guisection: TableTools
# %end

# %option
# % key: ncol
# % type: integer
# % label: Number of Displ to insert
# % required: no
# % guisection: TableTools
# %end

# %option
# % key: sedist
# % type: string
# % label: start and end distance and height
# % required: no
# % guisection: TableTools
# %end

#########################
### CrossTools section
#########################

# %flag
# % key: c
# % description: CrossTools
# % guisection: CrossTools
# %end

# %option G_OPT_V_TYPE
# % key: intersect
# % options: left1, right1, left2, right2, in, out, rounda, write
# % answer:
# % required: no
# % description: Plan options
# % guisection: CrossTools
# %end

# %option G_OPT_V_INPUT
# % key: plant1
# % key_desc: map plant 1
# % description: Name of first map plant
# % required: no
# % guisection: CrossTools
# %end

# %option
# % key: cat1
# % type: integer
# % label: Categorie of align
# % required: no
# % answer: 1
# % guisection: CrossTools
# %end


# %option G_OPT_V_INPUT
# % key: plant2
# % key_desc: map plant 2
# % description: Name of second map plant
# % required: no
# % guisection: CrossTools
# %end

# %option
# % key: cat2
# % type: integer
# % label: Categorie of align
# % required: no
# % answer: 1
# % guisection: CrossTools
# %end

# %option
# % key: dist1
# % type: string
# % description: Displaced distances for aling 1
# % required: no
# % guisection: CrossTools
# %end

# %option
# % key: dist2
# % type: string
# % description: Displaced distances for aling 2
# % required: no
# % guisection: CrossTools
# %end

# %option
# % key: radios
# % type: string
# % description: Intersections radios
# % required: no
# % guisection: CrossTools
# %end

#########################
### #Options section
#########################

# %flag
# % key: r
# % description: Run
# %end

# %flag
# % key: p
# % description: Update solution from polygon
# %end

# %flag
# % key: t
# % description: Update solution from table plan distances_
# %end

# %option
# % key: intr
# % type: integer
# % label: Interval in straights
# % required: no
# % answer: 1
# %end

# %option
# % key: intc
# % type: integer
# % label: Interval in curves
# % required: no
# % answer: 1
# %end

# %option
# % key: startend
# % type: string
# % label: start and end pks (last pk = -1)
# % required: no
# % answer: 0,-1
# %end

# %option G_OPT_F_OUTPUT
# % key: backup
# % description: Create backup file
# % required: no
# %end

# ######################

import os
import sys

# sys.path.insert(1, os.path.join(os.path.dirname(sys.path[0]), 'etc', 'v.road'))
import grass.script as grass
from grass.pygrass.utils import get_lib_path

path = get_lib_path(modname="v.civil")
if path is None:
    grass.fatal("Not able to find the civil library directory.")
sys.path.append(path)

import road_road as Road
import road_crosstools as Tools2
import road_topotools as Topotools


# =============================================
# Main
# =============================================


def main():
    """Manage v.road
    >>> road = Road.Road('Circuit')
    >>>

    """
    if "@" in options["name"]:
        name_map = options["name"].split("@")[0]
    else:
        name_map = options["name"]

    plan_opt = options["plan"].split(",")
    vert_opt = options["vert"].split(",")
    trans_opt = options["trans"].split(",")
    terr_opt = options["terr"].split(",")

    add = options["add"].split(",")
    displline = options["displline"].split(",")

    intersect = options["intersect"].split(",")
    topotools = options["topotools"].split(",")
    actions = options["actions"].split(",")
    roundabout = options["roundabout"].split(",")
    # tinraster = options['tinraster'].split(',')

    startend = [float(opt) for opt in options["startend"].split(",")]
    pkopt = [float(opt) for opt in options["pkopt"].split(",")]

    if options["tab_subname"]:
        options["tab_subname"] = "_" + options["tab_subname"]

    if options["tab_type"]:
        options["tab_type"] = "_" + options["tab_type"]

    ### Init road
    road = Road.Road(name_map)

    ################### TableTools ##################

    if flags["e"]:
        # Insert new point
        if "row" in add:

            road.plant_generate()

            if "," in options["pklist"]:
                list_pks = options["pklist"].split(",")
            else:
                list_pks = [options["pklist"]]

            road.rtab.add_row(
                list_pks, road.plant, options["tab_type"], options["tab_subname"]
            )
            sys.exit(0)

        # Add new table
        if "table" in add:
            road.rtab.add_table(options["tab_type"], options["tab_subname"])
            sys.exit(0)

        # Add column to Displ table
        if "add" in displline or "del" in displline:
            add_col = True
            if "del" in displline:
                add_col = False
            road.rtab.tables["_Displ" + options["tab_subname"]].displ_add_del_col(
                options["ncol"], options["side"], options["sedist"], add_col
            )
        sys.exit(0)

    ################### CrossTools ##################

    if flags["c"]:
        inout = "In"
        if "out" in intersect:
            inout = "Out"
        rounda = False
        if "rounda" in intersect:
            rounda = True
        izq1 = "Izq"
        if "right1" in intersect:
            izq1 = "Der"
        izq2 = "Izq"
        if "right2" in intersect:
            izq2 = "Der"

        if "@" in options["plant1"]:
            name_plant1 = options["plant1"].split("@")[0]
        else:
            name_plant1 = options["plant1"]

        if "@" in options["plant2"]:
            name_plant2 = options["plant2"].split("@")[0]
        else:
            name_plant2 = options["plant2"]

        inter = Tools2.Intersections(
            name_plant1,
            int(options["cat1"]),
            izq1,
            name_plant2,
            int(options["cat2"]),
            izq2,
            inout,
            rounda,
        )
        inter.dist2 = [float(p) for p in options["dist2"].split(",")]
        inter.dist1 = [float(p) for p in options["dist1"].split(",")]
        inter.radios = [float(p) for p in options["radios"].split(",")]

        if "write" in intersect:
            inter.make_intersect(True)
        else:
            inter.make_intersect()
        sys.exit(0)

    ################### Topotools ##################

    if flags["o"]:
        if actions != [""]:
            if "uppoints" in actions:
                topo = Topotools.Topo(name_map)
                topo.uppoints()

        if roundabout != [""]:
            if "roundabout" in roundabout:
                topo = Topotools.Topo(options["roundname"])
                topo.roundabout(
                    options["rround1"],
                    options["rround1"],
                    options["azround"],
                    options["cround"],
                )

        if topotools != [""]:
            tri = Topotools.Triang(name_map)
            if "triangle" in topotools:
                tri.split_maps()
                tri.triangle()
            elif "delaunay" in topotools:
                tri.delaunay()
            tri.get_area_hull()
            if "curved" in topotools:
                tri.curved()
            if "cut_hull" in topotools:
                tri.cut_by_hull()

        # if tinraster != ['']:
        # tin = Topotools.Triang(name_map)
        # if 'tintorast' in tinraster:
        # tin.tin_to_raster()
        # if 'nnbathy' in tinraster:
        # tin.nnbathy()

        sys.exit(0)

    ################### Backup ##################

    if options["backup"]:
        road.rtab.create_backup(options["backup"])
        grass.message("backup created")
        sys.exit(0)

    ##################### Run ###################

    if flags["r"]:

        if flags["t"]:
            road.plant_generate(True, float(options["camber"]))
            road.rtab.update_tables()
        elif flags["p"]:
            road.plant_generate(False, float(options["camber"]))
            road.rtab.update_tables()
        else:
            road.plant_generate(False, float(options["camber"]))

        if "plan" in plan_opt:
            road.rtab.update_tables(road.plant)

        road.elev_generate()

        road.displ_generate()

        if options["dem"]:

            road.terr_generate(options["dem"])

            road.taludes_generate()

            road.trans_generate()

            if "profile" in vert_opt:
                road.long_profile_generate(
                    options["lpopt"], options["lpscale"], options["lpoffset"]
                )

            if "profiles" in trans_opt:
                road.trans_profiles_generate(
                    options["ltopt1"],
                    options["ltopt2"],
                    options["ltscale"],
                    options["ltoffset"],
                )
        else:
            road.trans_generate()

        if "marks" in plan_opt:
            road.marks_generate()

        ### Write maps

        if flags["o"]:
            if actions != [""]:
                if "pnt_info" in actions:
                    pto_inf = Topotools.Topo(name_map)
                    pto_inf.pts_info(options["pk_info"], road)
            sys.exit(0)

        #
        road.plant.set_roadline(
            startend[0], startend[1], float(options["intr"]), float(options["intc"])
        )
        road.plant.add_pks(road.rtab.get_tables_pks())

        road.vert.set_pnts_elev(road.plant.roadline)

        road.displ.set_roadlines(road.plant.roadline)

        #
        if "plan" in plan_opt:
            grass.message("writing plan")
            road.plant_write()

        if "displ" in plan_opt:
            grass.message("writing displ")
            road.displ_write()

        if "marks" in plan_opt:
            grass.message("writing marks")
            road.marks_write()

        if "pks" in plan_opt:
            grass.message("writing pks")
            road.trans_write_pks(startend, pkopt)

        #
        if "vert" in vert_opt:
            grass.message("writing elev")
            road.elev_write()

        #
        if "trans" in trans_opt:
            grass.message("writing trans")
            road.trans_write()

        if options["dem"]:

            road.terr.set_pnts_terr(road.plant.roadline)

            road.taludes.set_roadlines(road.plant.roadline, road.displ)

            #
            if "profile" in vert_opt:
                grass.message("writing profile")
                road.long_profile_write()

            if "profiles" in trans_opt:
                grass.message("writing profiles")
                road.trans_profiles_write()

            #
            if "slopes" in terr_opt:
                grass.message("writing slopes")
                road.taludes_write()

            if "sareas" in terr_opt:
                grass.message("writing slopes_areas")
                road.taludes_areas_write()

            if "topo" in terr_opt:
                grass.message(
                    "writing pnts, breakliness and hull for \
                               triangulation"
                )
                road.tri_write()

        tab_subname_d = ""
        if options["dtable"]:
            tab_subname_d = options["dtable"].split("_Displ")[-1]
            road.displ_generate(tab_subname_d)
            road.displ.set_roadlines(road.plant.roadline)
            road.displ_write("_" + tab_subname_d)

        if options["mtable"]:
            road.marks_generate(options["mtable"])
            tab_subname_m = "_" + options["mtable"].split("_Marks")[-1]
            road.marks_write(tab_subname_m)

        if options["areaopt"]:
            grass.message("writing displ_areas")
            road.displ_areas_write(options["areaopt"], tab_subname_d)

    sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--doctest":
        import doctest

        doctest.testmod()

    else:
        options, flags = grass.parser()
        main()
