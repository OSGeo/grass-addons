#!/usr/bin/env python

############################################################################
#
# MODULE:      r.basin
# AUTHOR(S):   Margherita Di Leo, Massimo Di Stefano
# PURPOSE:     Morphometric characterization of river basins
# COPYRIGHT:   (C) 2010-2014 by Margherita Di Leo & Massimo Di Stefano
#              dileomargherita@gmail.com
#
#              This program is free software under the GNU General Public
#              License (>=v3.0) and comes with ABSOLUTELY NO WARRANTY.
#              See the file COPYING that comes with GRASS
#              for details.
#
# TODO: does r.stream.snap's snap depend on the raster resolution? hardcoded 30 below
#
#############################################################################

# %module
# % description: Morphometric characterization of river basins
# % keyword: raster
# % keyword: hydrology
# % keyword: watershed
# % overwrite: yes
# %end

# %option G_OPT_R_ELEV
# % key: map
# % description: Name of elevation raster map
# % required: yes
# %end

# %option
# % key: prefix
# % type: string
# % key_desc: prefix
# % description: output prefix (must start with a letter)
# % required: yes
# %end

# %option G_OPT_M_COORDS
# % description: coordinates of the outlet (east,north)
# % required : yes
# %end

# %option G_OPT_M_DIR
# % key: dir
# % description: Directory where the output will be found
# % required : yes
# %end

# %option
# % key: threshold
# % type: double
# % key_desc: threshold
# % description: threshold
# % required : no
# %end

# %flag
# % key: a
# % description: Use default threshold (1km^2)
# %END

# %flag
# % key: c
# % description: No maps output
# %END

import sys
import os
import grass.script as gs
import math
from numpy import zeros
import csv

# i18N
import gettext

gettext.install("grassmods", os.path.join(os.getenv("GISBASE"), "locale"))


# check requirements
def check_progs():
    found_missing = False
    for prog in (
        "r.hypso",
        "r.stream.basins",
        "r.stream.distance",
        "r.stream.extract",
        "r.stream.order",
        "r.stream.snap",
        "r.stream.stats",
        "r.width.funct",
    ):
        if not gs.find_program(prog, "--help"):
            found_missing = True
            gs.warning(
                _("'%s' required. Please install '%s' first using 'g.extension %s'")
                % (prog, prog, prog)
            )
    if found_missing:
        gs.fatal(_("An ERROR occurred running r.basin"))


def main():
    # check dependencies
    check_progs()

    # check for unsupported locations
    in_proj = gs.parse_command("g.proj", flags="g")
    if in_proj["unit"].lower() == "degree":
        gs.fatal(_("Latitude-longitude locations are not supported"))
    if in_proj["name"].lower() == "xy_location_unprojected":
        gs.fatal(_("xy-locations are not supported"))

    r_elevation = options["map"].split("@")[0]
    mapname = options["map"].replace("@", " ")
    mapname = mapname.split()
    mapname[0] = mapname[0].replace(".", "_")
    coordinates = options["coordinates"]
    directory = options["dir"]
    # Check if directory exists
    if not os.path.isdir(directory):
        os.makedirs(directory)
    autothreshold = flags["a"]
    nomap = flags["c"]
    prefix = options["prefix"] + "_" + mapname[0]
    r_accumulation = prefix + "_accumulation"
    r_drainage = prefix + "_drainage"
    r_stream = prefix + "_stream"
    r_slope = prefix + "_slope"
    r_aspect = prefix + "_aspect"
    r_basin = prefix + "_basin"
    r_strahler = prefix + "_strahler"
    r_shreve = prefix + "_shreve"
    r_horton = prefix + "_horton"
    r_hack = prefix + "_hack"
    r_distance = prefix + "_dist2out"
    r_hillslope_distance = prefix + "_hillslope_distance"
    r_height_average = prefix + "_height_average"
    r_aspect_mod = prefix + "_aspect_mod"
    r_dtm_basin = prefix + "_dtm_basin"
    r_mainchannel = prefix + "_mainchannel"
    r_stream_e = prefix + "_stream_e"
    r_drainage_e = prefix + "_drainage_e"
    r_mask = prefix + "_mask"
    r_ord_1 = prefix + "_ord_1"
    r_average_hillslope = prefix + "_average_hillslope"
    r_mainchannel_dim = prefix + "_mainchannel_dim"
    r_outlet = prefix + "_r_outlet"
    v_outlet = prefix + "_outlet"
    v_outlet_snap = prefix + "_outlet_snap"
    v_basin = prefix + "_basin"
    v_mainchannel = prefix + "_mainchannel"
    v_mainchannel_dim = prefix + "_mainchannel_dim"
    v_network = prefix + "_network"
    v_ord_1 = prefix + "_ord_1"
    global tmp

    # Save current region
    gs.read_command("g.region", flags="p", save="original")

    # Watershed SFD
    gs.run_command(
        "r.watershed",
        elevation=r_elevation,
        accumulation=r_accumulation,
        drainage=r_drainage,
        convergence=5,
        flags="am",
    )

    # Managing flag
    if autothreshold:
        resolution = gs.region()["nsres"]
        th = 1000000 / (resolution**2)
        gs.message("threshold : %s" % th)
    else:
        th = options["threshold"]

    # Stream extraction
    gs.run_command(
        "r.stream.extract",
        elevation=r_elevation,
        accumulation=r_accumulation,
        threshold=th,
        d8cut=1000000000,
        mexp=0,
        stream_rast=r_stream_e,
        direction=r_drainage_e,
    )

    try:
        # Delineation of basin
        # Create outlet
        gs.write_command(
            "v.in.ascii",
            output=v_outlet,
            input="-",
            sep=",",
            stdin="%s,9999" % (coordinates),
        )

        # Snap outlet to stream network
        # TODO: does snap depend on the raster resolution? hardcoded 30 below
        gs.run_command(
            "r.stream.snap",
            input=v_outlet,
            output=v_outlet_snap,
            stream_rast=r_stream_e,
            radius=30,
        )

        gs.run_command(
            "v.to.rast",
            input=v_outlet_snap,
            output=r_outlet,
            use="cat",
            type="point",
            layer=1,
            value=1,
        )

        gs.run_command(
            "r.stream.basins",
            direction=r_drainage_e,
            basins=r_basin,
            points=v_outlet_snap,
        )

        gs.message("Delineation of basin done")

        # Mask and cropping
        elevation_name = r_elevation = r_elevation.split("@")[0]

        gs.mapcalc("$r_mask = $r_basin / $r_basin", r_mask=r_mask, r_basin=r_basin)

        gs.mapcalc(
            "tmp = $r_accumulation / $r_mask",
            r_accumulation=r_accumulation,
            r_mask=r_mask,
        )

        gs.run_command(
            "g.remove", flags="f", type="raster", name=r_accumulation, quiet=True
        )

        gs.run_command("g.rename", raster=("tmp", r_accumulation))

        gs.mapcalc("tmp = $r_drainage / $r_mask", r_drainage=r_drainage, r_mask=r_mask)

        gs.run_command(
            "g.remove", flags="f", type="raster", name=r_drainage, quiet=True
        )

        gs.run_command("g.rename", raster=("tmp", r_drainage))

        gs.mapcalc(
            "$r_elevation_crop = $r_elevation * $r_mask",
            r_mask=r_mask,
            r_elevation=r_elevation,
            r_elevation_crop="r_elevation_crop",
        )

        gs.mapcalc(
            "tmp = $r_drainage_e * $r_mask", r_mask=r_mask, r_drainage_e=r_drainage_e
        )

        gs.run_command(
            "g.remove", flags="f", type="raster", name=r_drainage_e, quiet=True
        )

        gs.run_command("g.rename", raster=("tmp", r_drainage_e))

        gs.mapcalc("tmp = $r_stream_e * $r_mask", r_mask=r_mask, r_stream_e=r_stream_e)

        gs.run_command(
            "g.remove", flags="f", type="raster", name=r_stream_e, quiet=True
        )
        # grass.run_command('g.rename', raster = (r_stream_e,'streams'))

        gs.run_command("g.rename", raster=("tmp", r_stream_e))

        gs.run_command("r.thin", input=r_stream_e, output=r_stream_e + "_thin")

        gs.run_command(
            "r.to.vect", input=r_stream_e + "_thin", output=v_network, type="line"
        )

        # Creation of slope and aspect maps
        gs.run_command(
            "r.slope.aspect",
            elevation="r_elevation_crop",
            slope=r_slope,
            aspect=r_aspect,
        )

        # Basin mask (vector)
        # Raster to vector
        gs.run_command(
            "r.to.vect", input=r_basin, output=v_basin, type="area", flags="sv"
        )

        # Add two columns to the table: area and perimeter
        gs.run_command("v.db.addcolumn", map=v_basin, columns="area double precision")

        gs.run_command(
            "v.db.addcolumn", map=v_basin, columns="perimeter double precision"
        )

        # Populate perimeter column
        gs.run_command(
            "v.to.db",
            map=v_basin,
            type="line,boundary",
            layer=1,
            qlayer=1,
            option="perimeter",
            units="kilometers",
            columns="perimeter",
            overwrite=True,
        )

        # Read perimeter
        tmp = gs.read_command(
            "v.to.db",
            map=v_basin,
            type="line,boundary",
            layer=1,
            qlayer=1,
            option="perimeter",
            units="kilometers",
            qcolumn="perimeter",
            flags="p",
        )
        perimeter_basin = float(tmp.split("\n")[1].split("|")[1])

        # Populate area column
        gs.run_command(
            "v.to.db",
            map=v_basin,
            type="line,boundary",
            layer=1,
            qlayer=1,
            option="area",
            units="kilometers",
            columns="area",
            overwrite=True,
        )

        # Read area
        tmp = gs.read_command(
            "v.to.db",
            map=v_basin,
            type="line,boundary",
            layer=1,
            qlayer=1,
            option="area",
            units="kilometers",
            qcolumn="area",
            flags="p",
        )
        area_basin = float(tmp.split("\n")[1].split("|")[1])

        # Creation of order maps: strahler, horton, hack, shreeve
        gs.message("Creating %s" % r_hack)

        gs.run_command(
            "r.stream.order",
            stream_rast=r_stream_e,
            direction=r_drainage_e,
            strahler=r_strahler,
            shreve=r_shreve,
            horton=r_horton,
            hack=r_hack,
        )

        # Distance to outlet
        gs.run_command(
            "r.stream.distance",
            stream_rast=r_outlet,
            direction=r_drainage_e,
            flags="o",
            distance=r_distance,
        )

        # hypsographic curve

        gs.message("------------------------------")

        gs.run_command(
            "r.hypso",
            map="r_elevation_crop",
            image=os.path.join(directory, prefix),
            flags="ab",
        )

        gs.message("------------------------------")

        # Width Function

        gs.message("------------------------------")

        gs.run_command(
            "r.width.funct", map=r_distance, image=os.path.join(directory, prefix)
        )

        gs.message("------------------------------")

        # Creation of map of hillslope distance to river network

        gs.run_command(
            "r.stream.distance",
            stream_rast=r_stream_e,
            direction=r_drainage,
            elevation="r_elevation_crop",
            distance=r_hillslope_distance,
        )

        # Mean elevation
        gs.run_command(
            "r.stats.zonal",
            base=r_basin,
            cover="r_elevation_crop",
            method="average",
            output=r_height_average,
        )

        gs.message("r.stats.zonal done")
        mean_elev = float(
            gs.read_command("r.info", flags="r", map=r_height_average)
            .split("\n")[0]
            .split("=")[1]
        )
        gs.message("r.info done")

        # In Grass, aspect categories represent the number degrees of east and they increase
        # counterclockwise: 90deg is North, 180 is West, 270 is South 360 is East.
        # The aspect value 0 is used to indicate undefined aspect in flat areas with slope=0.
        # We calculate the number of degree from north, increasing counterclockwise.
        gs.mapcalc(
            "$r_aspect_mod = if($r_aspect == 0, 0, if($r_aspect > 90, 450 - $r_aspect, 90 - $r_aspect))",
            r_aspect=r_aspect,
            r_aspect_mod=r_aspect_mod,
        )
        gs.message("r.mapcalc done")

        # Centroid and mean slope
        baricenter_slope_baricenter = gs.read_command(
            "r.volume", input=r_slope, clump=r_basin
        )

        gs.message("r.volume done")

        baricenter_slope_baricenter = baricenter_slope_baricenter.split()
        mean_slope = baricenter_slope_baricenter[30]

        # Rectangle containing basin
        basin_east = baricenter_slope_baricenter[33]
        basin_north = baricenter_slope_baricenter[34]
        info_region_basin = gs.read_command("g.region", raster=r_basin, flags="m")

        gs.message("g.region done")
        dict_region_basin = dict(
            x.split("=", 1) for x in info_region_basin.split("\n") if "=" in x
        )
        basin_resolution = float(dict_region_basin["nsres"])
        #        x_massimo = float(dict_region_basin['n']) + (basin_resolution * 10)
        #        x_minimo = float(dict_region_basin['w']) - (basin_resolution * 10)
        #        y_massimo = float(dict_region_basin['e']) + (basin_resolution * 10)
        #        y_minimo = float(dict_region_basin['s']) - (basin_resolution * 10)
        nw = dict_region_basin["w"], dict_region_basin["n"]
        se = dict_region_basin["e"], dict_region_basin["s"]
        gs.message("Rectangle containing basin done")

        east1, north1 = coordinates.split(",")
        east = float(east1)
        north = float(north1)

        # Directing vector
        delta_x = abs(float(basin_east) - east)
        delta_y = abs(float(basin_north) - north)
        L_orienting_vect = math.sqrt((delta_x**2) + (delta_y**2)) / 1000
        gs.message("Directing vector done")

        # Prevalent orientation
        prevalent_orientation = math.atan(delta_y / delta_x)
        gs.message("Prevalent orientation done")

        # Compactness coefficient
        C_comp = perimeter_basin / (2 * math.sqrt(area_basin / math.pi))
        gs.message("Compactness coefficient done")

        # Circularity ratio
        R_c = (4 * math.pi * area_basin) / (perimeter_basin**2)
        gs.message("Circularity ratio done")

        # Mainchannel
        gs.mapcalc(
            "$r_mainchannel = if($r_hack==1,1,null())",
            r_hack=r_hack,
            r_mainchannel=r_mainchannel,
        )

        gs.run_command("r.thin", input=r_mainchannel, output=r_mainchannel + "_thin")
        gs.run_command(
            "r.to.vect",
            input=r_mainchannel + "_thin",
            output=v_mainchannel,
            type="line",
            verbose=True,
        )

        # Get coordinates of the outlet (belonging to stream network)

        gs.run_command("v.db.addtable", map=v_outlet_snap)

        gs.run_command(
            "v.db.addcolumn",
            map=v_outlet_snap,
            columns="x double precision,y double precision",
        )

        gs.run_command(
            "v.to.db", map=v_outlet_snap, option="coor", col="x,y", overwrite=True
        )

        namefile = os.path.join(directory, prefix + "_outlet_coors.txt")

        gs.run_command(
            "v.out.ascii", input=v_outlet_snap, output=namefile, cats=1, format="point"
        )

        f = open(namefile)
        east_o, north_o, cat = f.readline().split("|")

        param_mainchannel = gs.read_command(
            "v.what",
            map=v_mainchannel,
            coordinates="%s,%s" % (east_o, north_o),
            distance=5,
        )
        tmp = param_mainchannel.split("\n")[7]
        mainchannel = float(tmp.split()[1]) / 1000  # km

        # Topological Diameter
        gs.mapcalc(
            "$r_mainchannel_dim = -($r_mainchannel - $r_shreve) + 1",
            r_mainchannel_dim=r_mainchannel_dim,
            r_shreve=r_shreve,
            r_mainchannel=r_mainchannel,
        )
        gs.run_command(
            "r.thin", input=r_mainchannel_dim, output=r_mainchannel_dim + "_thin"
        )
        gs.run_command(
            "r.to.vect",
            input=r_mainchannel_dim + "_thin",
            output=v_mainchannel_dim,
            type="line",
            flags="v",
            verbose=True,
        )
        try:
            D_topo1 = gs.read_command(
                "v.info", map=v_mainchannel_dim, layer=1, flags="t"
            )
            D_topo = float(D_topo1.split("\n")[2].split("=")[1])
        except:
            D_topo = 1
            gs.message("Topological Diameter = WARNING")

        # Mean slope of mainchannel
        gs.message("doing v.to.points")
        gs.run_command(
            "v.to.points",
            input=v_mainchannel_dim,
            output=v_mainchannel_dim + "_point",
            type="line",
        )
        vertex = (
            gs.read_command(
                "v.out.ascii", verbose=True, input=v_mainchannel_dim + "_point"
            )
            .strip()
            .split("\n")
        )
        nodi = zeros((len(vertex), 4), float)
        pendenze = []

        for i in range(len(vertex)):
            x, y = float(vertex[i].split("|")[0]), float(vertex[i].split("|")[1])
            vertice1 = gs.read_command(
                "r.what",
                verbose=True,
                map="r_elevation_crop",
                coordinates="%s,%s" % (x, y),
            )
            vertice = vertice1.replace("\n", "").replace("||", "|").split("|")
            nodi[i, 0], nodi[i, 1], nodi[i, 2] = (
                float(vertice[0]),
                float(vertice[1]),
                float(vertice[2]),
            )

        for i in range(0, len(vertex) - 1, 2):
            dist = math.sqrt(
                math.fabs((nodi[i, 0] - nodi[i + 1, 0])) ** 2
                + math.fabs((nodi[i, 1] - nodi[i + 1, 1])) ** 2
            )
            deltaz = math.fabs(nodi[i, 2] - nodi[i + 1, 2])
            # Control to prevent float division by zero (dist=0)

            try:
                pendenza = deltaz / dist
                pendenze.append(pendenza)
                mainchannel_slope = sum(pendenze) / len(pendenze) * 100
            except:
                pass

        # Elongation Ratio
        R_al = (2 * math.sqrt(area_basin / math.pi)) / mainchannel

        # Shape factor
        S_f = area_basin / mainchannel

        # Characteristic altitudes
        height_basin_average = gs.read_command(
            "r.what",
            map=r_height_average,
            cache=500,
            coordinates="%s,%s" % (east_o, north_o),
        )
        height_basin_average = height_basin_average.replace("\n", "")
        height_basin_average = float(height_basin_average.split("|")[-1])
        minmax_height_basin = gs.read_command(
            "r.info", flags="r", map="r_elevation_crop"
        )
        minmax_height_basin = minmax_height_basin.strip().split("\n")
        min_height_basin, max_height_basin = (
            float(minmax_height_basin[0].split("=")[-1]),
            float(minmax_height_basin[1].split("=")[-1]),
        )
        H1 = max_height_basin
        H2 = min_height_basin
        HM = H1 - H2

        # Concentration time (Giandotti, 1934)
        t_c = ((4 * math.sqrt(area_basin)) + (1.5 * mainchannel)) / (
            0.8 * math.sqrt(HM)
        )

        # Mean hillslope length
        gs.run_command(
            "r.stats.zonal",
            cover=r_stream_e,
            base=r_mask,
            method="average",
            output=r_average_hillslope,
        )
        mean_hillslope_length = float(
            gs.read_command("r.info", flags="r", map=r_average_hillslope)
            .split("\n")[0]
            .split("=")[1]
        )

        # Magnitude
        gs.mapcalc(
            "$r_ord_1 = if($r_strahler==1,1,null())",
            r_ord_1=r_ord_1,
            r_strahler=r_strahler,
        )
        gs.run_command(
            "r.thin", input=r_ord_1, output=r_ord_1 + "_thin", iterations=200
        )
        gs.run_command(
            "r.to.vect", input=r_ord_1 + "_thin", output=v_ord_1, type="line", flags="v"
        )
        magnitudo = float(
            gs.read_command("v.info", map=v_ord_1, layer=1, flags="t")
            .split("\n")[2]
            .split("=")[1]
        )

        # First order stream frequency
        FSF = magnitudo / area_basin

        # Statistics

        stream_stats = gs.read_command(
            "r.stream.stats",
            stream_rast=r_strahler,
            direction=r_drainage_e,
            elevation="r_elevation_crop",
        )

        print(" ------------------------------ ")
        print("Output of r.stream.stats: ")
        print(stream_stats)

        stream_stats_summary = stream_stats.split("\n")[4].split("|")
        stream_stats_mom = stream_stats.split("\n")[8].split("|")
        Max_order, Num_streams, Len_streams, Stream_freq = (
            stream_stats_summary[0],
            stream_stats_summary[1],
            stream_stats_summary[2],
            stream_stats_summary[5],
        )
        Bif_ratio, Len_ratio, Area_ratio, Slope_ratio = (
            stream_stats_mom[0],
            stream_stats_mom[1],
            stream_stats_mom[2],
            stream_stats_mom[3],
        )
        drainage_density = float(Len_streams) / float(area_basin)

        # Cleaning up
        gs.run_command(
            "g.remove", flags="f", type="raster", name="r_elevation_crop", quiet=True
        )
        gs.run_command(
            "g.remove", flags="f", type="raster", name=r_height_average, quiet=True
        )
        gs.run_command(
            "g.remove", flags="f", type="raster", name=r_aspect_mod, quiet=True
        )
        gs.run_command(
            "g.remove", flags="f", type="raster", name=r_mainchannel, quiet=True
        )
        gs.run_command(
            "g.remove", flags="f", type="raster", name=r_stream_e, quiet=True
        )
        gs.run_command(
            "g.remove", flags="f", type="raster", name=r_drainage_e, quiet=True
        )
        gs.run_command("g.remove", flags="f", type="raster", name=r_mask, quiet=True)
        gs.run_command("g.remove", flags="f", type="raster", name=r_ord_1, quiet=True)
        gs.run_command(
            "g.remove", flags="f", type="raster", name=r_average_hillslope, quiet=True
        )
        gs.run_command(
            "g.remove", flags="f", type="raster", name=r_mainchannel_dim, quiet=True
        )
        gs.run_command("g.remove", flags="f", type="raster", name=r_outlet, quiet=True)
        gs.run_command("g.remove", flags="f", type="raster", name=r_basin, quiet=True)
        gs.run_command(
            "g.remove",
            flags="f",
            type="raster",
            name=prefix + "_mainchannel_thin",
            quiet=True,
        )
        gs.run_command(
            "g.remove",
            flags="f",
            type="raster",
            name=prefix + "_mainchannel_dim_thin",
            quiet=True,
        )
        gs.run_command(
            "g.remove",
            flags="f",
            type="raster",
            name=prefix + "_ord_1_thin",
            quiet=True,
        )
        gs.run_command(
            "g.remove",
            flags="f",
            type="raster",
            name=prefix + "_stream_e_thin",
            quiet=True,
        )
        gs.run_command(
            "g.remove",
            flags="f",
            type="vector",
            name=v_mainchannel_dim + "_point",
            quiet=True,
        )
        gs.run_command(
            "g.remove", flags="f", type="vector", name=v_mainchannel_dim, quiet=True
        )
        gs.run_command("g.remove", flags="f", type="vector", name=v_ord_1, quiet=True)

        if nomap:
            gs.run_command(
                "g.remove", flags="f", type="vector", name=v_outlet, quiet=True
            )
            gs.run_command(
                "g.remove", flags="f", type="vector", name=v_basin, quiet=True
            )
            gs.run_command(
                "g.remove", flags="f", type="vector", name=v_mainchannel, quiet=True
            )
            gs.run_command(
                "g.remove", flags="f", type="raster", name=r_accumulation, quiet=True
            )
            gs.run_command(
                "g.remove", flags="f", type="raster", name=r_drainage, quiet=True
            )
            gs.run_command(
                "g.remove", flags="f", type="raster", name=r_aspect, quiet=True
            )
            gs.run_command(
                "g.remove", flags="f", type="raster", name=r_strahler, quiet=True
            )
            gs.run_command(
                "g.remove", flags="f", type="raster", name=r_shreve, quiet=True
            )
            gs.run_command(
                "g.remove", flags="f", type="raster", name=r_horton, quiet=True
            )
            gs.run_command(
                "g.remove", flags="f", type="raster", name=r_hack, quiet=True
            )
            gs.run_command(
                "g.remove", flags="f", type="raster", name=r_distance, quiet=True
            )
            gs.run_command(
                "g.remove",
                flags="f",
                type="raster",
                name=r_hillslope_distance,
                quiet=True,
            )
            gs.run_command(
                "g.remove", flags="f", type="raster", name=r_slope, quiet=True
            )

        ####################################################

        parametri_bacino = {}
        parametri_bacino["mean_slope"] = float(mean_slope)
        parametri_bacino["mean_elev"] = float(mean_elev)
        parametri_bacino["basin_east"] = float(basin_east)
        parametri_bacino["basin_north"] = float(basin_north)
        parametri_bacino["basin_resolution"] = float(basin_resolution)
        parametri_bacino["nw"] = nw
        parametri_bacino["se"] = se
        parametri_bacino["area_basin"] = float(area_basin)
        parametri_bacino["perimeter_basin"] = float(perimeter_basin)
        parametri_bacino["L_orienting_vect"] = float(L_orienting_vect)
        parametri_bacino["prevalent_orientation"] = float(prevalent_orientation)
        parametri_bacino["C_comp"] = float(C_comp)
        parametri_bacino["R_c"] = float(R_c)
        parametri_bacino["mainchannel"] = float(mainchannel)
        parametri_bacino["D_topo"] = float(D_topo)
        parametri_bacino["mainchannel_slope"] = float(mainchannel_slope)
        parametri_bacino["R_al"] = float(R_al)
        parametri_bacino["S_f"] = float(S_f)
        parametri_bacino["H1"] = float(H1)
        parametri_bacino["H2"] = float(H2)
        parametri_bacino["HM"] = float(HM)
        parametri_bacino["t_c"] = float(t_c)
        parametri_bacino["mean_hillslope_length"] = float(mean_hillslope_length)
        parametri_bacino["magnitudo"] = float(magnitudo)
        parametri_bacino["Max_order"] = float(Max_order)
        parametri_bacino["Num_streams"] = float(Num_streams)
        parametri_bacino["Len_streams"] = float(Len_streams)
        parametri_bacino["Stream_freq"] = float(Stream_freq)
        parametri_bacino["Bif_ratio"] = float(Bif_ratio)
        parametri_bacino["Len_ratio"] = float(Len_ratio)
        parametri_bacino["Area_ratio"] = float(Area_ratio)
        parametri_bacino["Slope_ratio"] = float(Slope_ratio)
        parametri_bacino["drainage_density"] = float(drainage_density)
        parametri_bacino["FSF"] = float(FSF)

        # create .csv file
        csvfile = os.path.join(directory, prefix + "_parameters.csv")
        with open(csvfile, "w") as f:
            writer = csv.writer(f)
            writer.writerow(["Morphometric parameters of basin:"])
            writer.writerow([" "])
            writer.writerow(["Easting Centroid of basin"] + [basin_east])
            writer.writerow(["Northing Centroid of basin"] + [basin_north])
            writer.writerow(["Rectangle containing basin N-W"] + [nw])
            writer.writerow(["Rectangle containing basin S-E"] + [se])
            writer.writerow(["Area of basin [km^2]"] + [area_basin])
            writer.writerow(["Perimeter of basin [km]"] + [perimeter_basin])
            writer.writerow(["Max Elevation [m s.l.m.]"] + [H1])
            writer.writerow(["Min Elevation [m s.l.m.]"] + [H2])
            writer.writerow(["Elevation Difference [m]"] + [HM])
            writer.writerow(["Mean Elevation"] + [mean_elev])
            writer.writerow(["Mean Slope"] + [mean_slope])
            writer.writerow(["Length of Directing Vector [km]"] + [L_orienting_vect])
            writer.writerow(
                ["Prevalent Orientation [degree from north, counterclockwise]"]
                + [prevalent_orientation]
            )
            writer.writerow(["Compactness Coefficient"] + [C_comp])
            writer.writerow(["Circularity Ratio"] + [R_c])
            writer.writerow(["Topological Diameter"] + [D_topo])
            writer.writerow(["Elongation Ratio"] + [R_al])
            writer.writerow(["Shape Factor"] + [S_f])
            writer.writerow(["Concentration Time (Giandotti, 1934) [hr]"] + [t_c])
            writer.writerow(["Length of Mainchannel [km]"] + [mainchannel])
            writer.writerow(
                ["Mean slope of mainchannel [percent]"] + [mainchannel_slope]
            )
            writer.writerow(["Mean hillslope length [m]"] + [mean_hillslope_length])
            writer.writerow(["Magnitudo"] + [magnitudo])
            writer.writerow(["Max order (Strahler)"] + [Max_order])
            writer.writerow(["Number of streams"] + [Num_streams])
            writer.writerow(["Total Stream Length [km]"] + [Len_streams])
            writer.writerow(["First order stream frequency"] + [FSF])
            writer.writerow(["Drainage Density [km/km^2]"] + [drainage_density])
            writer.writerow(["Bifurcation Ratio (Horton)"] + [Bif_ratio])
            writer.writerow(["Length Ratio (Horton)"] + [Len_ratio])
            writer.writerow(["Area ratio (Horton)"] + [Area_ratio])
            writer.writerow(["Slope ratio (Horton)"] + [Slope_ratio])

        # Create summary (transposed)
        csvfileT = os.path.join(directory, prefix + "_parametersT.csv")  # transposed
        with open(csvfileT, "w") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["x"]
                + ["y"]
                + ["Easting_Centroid_basin"]
                + ["Northing_Centroid_basin"]
                + ["Rectangle_containing_basin_N_W"]
                + ["Rectangle_containing_basin_S_E"]
                + ["Area_of_basin_km2"]
                + ["Perimeter_of_basin_km"]
                + ["Max_Elevation"]
                + ["Min_Elevation"]
                + ["Elevation_Difference"]
                + ["Mean_Elevation"]
                + ["Mean_Slope"]
                + ["Length_of_Directing_Vector_km"]
                + ["Prevalent_Orientation_deg_from_north_ccw"]
                + ["Compactness_Coefficient"]
                + ["Circularity_Ratio"]
                + ["Topological_Diameter"]
                + ["Elongation_Ratio"]
                + ["Shape_Factor"]
                + ["Concentration_Time_hr"]
                + ["Length_of_Mainchannel_km"]
                + ["Mean_slope_of_mainchannel_percent"]
                + ["Mean_hillslope_length_m"]
                + ["Magnitudo"]
                + ["Max_order_Strahler"]
                + ["Number_of_streams"]
                + ["Total_Stream_Length_km"]
                + ["First_order_stream_frequency"]
                + ["Drainage_Density_km_over_km2"]
                + ["Bifurcation_Ratio_Horton"]
                + ["Length_Ratio_Horton"]
                + ["Area_ratio_Horton"]
                + ["Slope_ratio_Horton"]
            )
            writer.writerow(
                [east_o]
                + [north_o]
                + [basin_east]
                + [basin_north]
                + [nw]
                + [se]
                + [area_basin]
                + [perimeter_basin]
                + [H1]
                + [H2]
                + [HM]
                + [mean_elev]
                + [mean_slope]
                + [L_orienting_vect]
                + [prevalent_orientation]
                + [C_comp]
                + [R_c]
                + [D_topo]
                + [R_al]
                + [S_f]
                + [t_c]
                + [mainchannel]
                + [mainchannel_slope]
                + [mean_hillslope_length]
                + [magnitudo]
                + [Max_order]
                + [Num_streams]
                + [Len_streams]
                + [FSF]
                + [drainage_density]
                + [Bif_ratio]
                + [Len_ratio]
                + [Area_ratio]
                + [Slope_ratio]
            )

        # Import table "rbasin_summary", joins it to "outlet_snap", then drops it
        gs.message("db.in.ogr: importing CSV table <%s>..." % csvfileT)
        gs.run_command("db.in.ogr", input=csvfileT, output="rbasin_summary")

        gs.run_command(
            "v.db.join",
            map=v_outlet_snap,
            otable="rbasin_summary",
            column="y",
            ocolumn="y",
        )
        gs.run_command("db.droptable", table="rbasin_summary", flags="f")

        gs.message("\n")
        gs.message("----------------------------------")
        gs.message("Morphometric parameters of basin :")
        gs.message("----------------------------------\n")
        gs.message("Easting Centroid of basin : %s " % basin_east)
        gs.message("Northing Centroid of Basin : %s " % basin_north)
        gs.message("Rectangle containing basin N-W : %s , %s " % nw)
        gs.message("Rectangle containing basin S-E : %s , %s " % se)
        gs.message("Area of basin [km^2] : %s " % area_basin)
        gs.message("Perimeter of basin [km] : %s " % perimeter_basin)
        gs.message("Max Elevation [m s.l.m.] : %s " % H1)
        gs.message("Min Elevation [m s.l.m.]: %s " % H2)
        gs.message("Elevation Difference [m]: %s " % HM)
        gs.message("Mean Elevation [m s.l.m.]: %s " % mean_elev)
        gs.message("Mean Slope : %s " % mean_slope)
        gs.message("Length of Directing Vector [km] : %s " % L_orienting_vect)
        gs.message(
            "Prevalent Orientation [degree from north, counterclockwise] : %s "
            % prevalent_orientation
        )
        gs.message("Compactness Coefficient : %s " % C_comp)
        gs.message("Circularity Ratio : %s " % R_c)
        gs.message("Topological Diameter : %s " % D_topo)
        gs.message("Elongation Ratio : %s " % R_al)
        gs.message("Shape Factor : %s " % S_f)
        gs.message("Concentration Time (Giandotti, 1934) [hr] : %s " % t_c)
        gs.message("Length of Mainchannel [km] : %s " % mainchannel)
        gs.message("Mean slope of mainchannel [percent] : %f " % mainchannel_slope)
        gs.message("Mean hillslope length [m] : %s " % mean_hillslope_length)
        gs.message("Magnitudo : %s " % magnitudo)
        gs.message("Max order (Strahler) : %s " % Max_order)
        gs.message("Number of streams : %s " % Num_streams)
        gs.message("Total Stream Length [km] : %s " % Len_streams)
        gs.message("First order stream frequency : %s " % FSF)
        gs.message("Drainage Density [km/km^2] : %s " % drainage_density)
        gs.message("Bifurcation Ratio (Horton) : %s " % Bif_ratio)
        gs.message("Length Ratio (Horton) : %s " % Len_ratio)
        gs.message("Area ratio (Horton) : %s " % Area_ratio)
        gs.message("Slope ratio (Horton): %s " % Slope_ratio)
        gs.message("------------------------------")
        gs.message("\n")
        gs.message("Done!")

    except:
        gs.message("\n")
        gs.message("------------------------------")
        gs.message("\n")
        gs.message("An ERROR occurred running r.basin")
        gs.message(
            "Please check for error messages above or try with another pairs of outlet coordinates"
        )

    # Set region to original
    gs.read_command("g.region", flags="p", region="original")
    gs.run_command("g.remove", flags="f", type="region", name="original")


if __name__ == "__main__":
    options, flags = gs.parser()
    sys.exit(main())
