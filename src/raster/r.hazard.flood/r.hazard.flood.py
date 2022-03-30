#!/usr/bin/env python

############################################################################
#
# MODULE:      r.hazard.flood.py
# AUTHOR(S):   Margherita Di Leo
# PURPOSE:     Fast procedure to detect flood prone areas on the basis of a
#              topographic index
# COPYRIGHT:   (C) 2010 by Margherita Di Leo
#              dileomargherita@gmail.com
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
# TODO: add overwrite check for resulting flood/mti maps
#############################################################################

# %module
# % description: Fast procedure to detect flood prone areas.
# % keyword: raster
# % keyword: hydrology
# %end
# %option
# % key: map
# % type: string
# % gisprompt: old,raster,raster
# % key_desc: elevation
# % description: Name of elevation raster map
# % required: yes
# %end
# %option
# % key: flood
# % type: string
# % gisprompt: new,raster,raster
# % key_desc: flood
# % description: Name of output flood raster map
# % required: yes
# %end
# %option
# % key: mti
# % type: string
# % gisprompt: new,raster,raster
# % key_desc: MTI
# % label: Name of output MTI raster map
# % description: Name of the output Modified Topographic Index (MTI) raster map
# % required: yes
# %END

import sys
import os

try:
    import grass.script as grass
except:
    try:
        from grass.script import core as grass
    except:
        sys.exit("grass.script can't be imported.")


def main():

    #### check if we have the r.area addon
    if not grass.find_program("r.area", "--help"):
        grass.fatal(
            _("The 'r.area' module was not found, install it first:")
            + "\n"
            + "g.extension r.area"
        )

    # are we in LatLong location?
    s = grass.read_command("g.proj", flags="j")
    kv = grass.parse_key_val(s)
    if kv["+proj"] == "longlat":
        grass.fatal(_("This module does not operate in LatLong locations"))

    r_elevation = options["map"].split("@")[0]
    mapname = options["map"].replace("@", " ")
    mapname = mapname.split()
    mapname[0] = mapname[0].replace(".", "_")
    r_flood_map = options["flood"]
    r_mti = options["mti"]

    # Detect cellsize of the DEM
    info_region = grass.read_command("g.region", flags="p")
    dict_region = grass.parse_key_val(info_region, ":")
    resolution = (float(dict_region["nsres"]) + float(dict_region["ewres"])) / 2
    grass.message("Cellsize : %s " % resolution)

    # Flow accumulation map MFD
    grass.run_command(
        "r.watershed",
        elevation=r_elevation,
        accumulation="r_accumulation",
        convergence=5,
        flags="a",
    )
    grass.message("Flow accumulation done. ")

    # Slope map
    grass.run_command("r.slope.aspect", elevation=r_elevation, slope="r_slope")
    grass.message("Slope map done. ")

    # n exponent
    n = 0.016 * (resolution**0.46)
    grass.message("Exponent : %s " % n)

    # MTI threshold
    mti_th = 10.89 * n + 2.282
    grass.message("MTI threshold : %s " % mti_th)

    # MTI map
    grass.message("Calculating MTI raster map.. ")
    grass.mapcalc(
        "$r_mti = log((exp((($rast1+1)*$resolution) , $n)) / (tan($rast2+0.001)))",
        r_mti=r_mti,
        rast1="r_accumulation",
        resolution=resolution,
        rast2="r_slope",
        n=n,
    )

    # Cleaning up
    grass.message("Cleaning up.. ")
    grass.run_command(
        "g.remove", quiet=True, flags="f", type="raster", name="r_accumulation"
    )
    grass.run_command("g.remove", quiet=True, flags="f", type="raster", name="r_slope")

    # flood map
    grass.message("Calculating flood raster map.. ")
    grass.mapcalc("r_flood = if($rast1 >  $mti_th, 1, 0)", rast1=r_mti, mti_th=mti_th)

    ## # Deleting isolated pixels
    # Recategorizes data in a raster map by grouping cells that form physically discrete areas into unique categories (preliminar to r.area)
    grass.message("Running r.clump.. ")
    grass.run_command("r.clump", input="r_flood", output="r_clump", overwrite="True")

    # Delete areas of less than a threshold of cells (corresponding to 1 square kilometer)
    # Calculating threshold
    th = int(1000000 / resolution**2)
    grass.message("Deleting areas of less than %s cells.. " % th)
    grass.run_command(
        "r.area", input="r_clump", output="r_flood_th", lesser=th, flags="b"
    )

    # New flood map
    grass.mapcalc(
        "$r_flood_map = $rast1 / $rast1", r_flood_map=r_flood_map, rast1="r_flood_th"
    )

    # Cleaning up
    grass.message("Cleaning up.. ")
    grass.run_command("g.remove", flags="f", type="raster", name="r_clump", quiet=True)
    grass.run_command(
        "g.remove", flags="f", type="raster", name="r_flood_th", quiet=True
    )
    grass.run_command("g.remove", flags="f", type="raster", name="r_flood", quiet=True)

    grass.message(_("Raster maps <%s> and <%s> calculated") % (r_mti, r_flood_map))


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
