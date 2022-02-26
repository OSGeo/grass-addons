#!/usr/bin/env python

############################################################################
#
# MODULE:       r.in.srtm.region
#
# AUTHOR(S):    Markus Metz
#               URL authenticaton added by Jonas Strobel, intern at mundialis and terrestris, Bonn
#
# PURPOSE:      Create a DEM from 3 arcsec SRTM v2.1 or 1 arcsec SRTM v3 tiles
#
# COPYRIGHT:    (C) 2011-2021 GRASS development team
#
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################

# %module
# % description: Creates a DEM from 3 arcsec SRTM v2.1 or 1 arcsec SRTM v3 tiles.
# % keyword: raster
# % keyword: import
# % keyword: SRTM
# %end
# %option G_OPT_R_OUTPUT
# % description: Name for output raster map
# % required: yes
# %end
# %option
# % key: username
# % description: Username for authentication
# % required: yes
# %end
# %option
# % key: password
# % description: Password for authentication
# % required: yes
# %end
# %option
# % key: url
# % description: Base URL to fetch SRTM tiles
# % required: no
# %end
# %option G_OPT_M_DIR
# % key: local
# % label: Local folder with SRTM tiles
# % description: Use local folder instead of URL to retrieve SRTM tiles
# % required: no
# %end
# %option
# % key: region
# % type: double
# % label: Import subregion only (default is current region)
# % description: Format: xmin,ymin,xmax,ymax - usually W,S,E,N
# % key_desc: xmin,ymin,xmax,ymax
# % multiple: no
# % required: no
# %end
# %option
# % key: memory
# % type: integer
# % description: Memory in MB for interpolation
# % answer: 300
# % required: no
# %end
# %option
# % key: method
# % type: string
# % required: no
# % multiple: no
# % options: nearest,bilinear,bicubic,lanczos,bilinear_f,bicubic_f,lanczos_f
# % description: Resampling method to use for reprojection (required if location projection not longlat)
# % descriptions: nearest;nearest neighbor;bilinear;bilinear interpolation;bicubic;bicubic interpolation;lanczos;lanczos filter;bilinear_f;bilinear interpolation with fallback;bicubic_f;bicubic interpolation with fallback;lanczos_f;lanczos filter with fallback
# % guisection: Output
# %end
# %option
# % key: resolution
# % type: double
# % required: no
# % multiple: no
# % description: Resolution of output raster map (required if location projection not longlat)
# % guisection: Output
# %end
# %flag
# %  key: n
# %  description: Fill null cells
# %end
# %flag
# %  key: 2
# %  label: Import SRTM v2 tiles
# %  description: Default: Import SRTM v3 tiles
# %end
# %flag
# % key: 1
# % description: Input is a 1-arcsec tile (default: 3-arcsec)
# %end
# %flag
# % key: z
# % description: Create zero elevation for missing tiles
# %end


# initialize global vars
TMPLOC = None
SRCGISRC = None
TGTGISRC = None
GISDBASE = None
proj = "".join(
    [
        "GEOGCS[",
        '"wgs84",',
        'DATUM["WGS_1984",SPHEROID["wgs84",6378137,298.257223563],TOWGS84[0.000000,0.000000,0.000000]],',
        'PRIMEM["Greenwich",0],',
        'UNIT["degree",0.0174532925199433]',
        "]",
    ]
)


import os
import atexit
import numpy as np
import subprocess
from six.moves.urllib import request as urllib2

try:
    from http.cookiejar import CookieJar
except ImportError:
    from cookielib import CookieJar
import time
import grass.script as grass
from grass.exceptions import CalledModuleError


def import_local_tile(tile, local, pid, srtmv3, one):
    output = tile + ".r.in.srtm.tmp." + str(pid)
    if srtmv3:
        if one:
            local_tile = str(tile) + ".SRTMGL1.hgt.zip"
        else:
            local_tile = str(tile) + ".SRTMGL3.hgt.zip"
    else:
        local_tile = str(tile) + ".hgt.zip"

    path = os.path.join(local, local_tile)
    if os.path.exists(path):
        path = os.path.join(local, local_tile)
        if one:
            grass.run_command(
                "r.in.srtm", input=path, output=output, flags="1", quiet=True
            )
        else:
            grass.run_command("r.in.srtm", input=path, output=output, quiet=True)
        return 1

    # SRTM subdirs: Africa, Australia, Eurasia, Islands, North_America, South_America
    for srtmdir in (
        "Africa",
        "Australia",
        "Eurasia",
        "Islands",
        "North_America",
        "South_America",
    ):
        path = os.path.join(local, srtmdir, local_tile)

        if os.path.exists(path):
            path = os.path.join(local, srtmdir, local_tile)
            if one:
                grass.run_command(
                    "r.in.srtm", input=path, output=output, flags="1", quiet=True
                )
            else:
                grass.run_command("r.in.srtm", input=path, output=output, quiet=True)
            return 1

    return 0


def download_tile(tile, url, pid, srtmv3, one, username, password):

    grass.debug("Download tile: %s" % tile, debug=1)
    output = tile + ".r.in.srtm.tmp." + str(pid)
    if srtmv3:
        if one:
            local_tile = str(tile) + ".SRTMGL1.hgt.zip"
        else:
            local_tile = str(tile) + ".SRTMGL3.hgt.zip"
    else:
        local_tile = str(tile) + ".hgt.zip"

    urllib2.urlcleanup()

    if srtmv3:
        remote_tile = str(url) + local_tile
        goturl = 1

        try:
            password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
            password_manager.add_password(
                None, "https://urs.earthdata.nasa.gov", username, password
            )

            cookie_jar = CookieJar()

            opener = urllib2.build_opener(
                urllib2.HTTPBasicAuthHandler(password_manager),
                # urllib2.HTTPHandler(debuglevel=1),    # Uncomment these two lines to see
                # urllib2.HTTPSHandler(debuglevel=1),   # details of the requests/responses
                urllib2.HTTPCookieProcessor(cookie_jar),
            )
            urllib2.install_opener(opener)

            request = urllib2.Request(remote_tile)
            response = urllib2.urlopen(request)

            fo = open(local_tile, "w+b")
            fo.write(response.read())
            fo.close
            time.sleep(0.5)
        except:
            goturl = 0
            pass

        return goturl

    # SRTM subdirs: Africa, Australia, Eurasia, Islands, North_America, South_America
    for srtmdir in (
        "Africa",
        "Australia",
        "Eurasia",
        "Islands",
        "North_America",
        "South_America",
    ):
        remote_tile = str(url) + str(srtmdir) + "/" + local_tile
        goturl = 1

        try:
            response = urllib2.urlopen(request)
            fo = open(local_tile, "w+b")
            fo.write(response.read())
            fo.close
            time.sleep(0.5)
            # does not work:
            # urllib.urlretrieve(remote_tile, local_tile, data = None)
        except:
            goturl = 0
            pass

        if goturl == 1:
            return 1

    return 0


def cleanup():
    if not in_temp:
        return
    os.chdir(currdir)
    if tmpregionname:
        grass.run_command("g.region", region=tmpregionname)
        grass.run_command(
            "g.remove", type="region", name=tmpregionname, flags="f", quiet=True
        )
    grass.try_rmdir(tmpdir)
    if TGTGISRC:
        os.environ["GISRC"] = str(TGTGISRC)
    # remove temp location
    if TMPLOC:
        grass.try_rmdir(os.path.join(GISDBASE, TMPLOC))
    if SRCGISRC:
        grass.try_remove(SRCGISRC)


def createTMPlocation(epsg=4326):
    SRCGISRC = grass.tempfile()
    TMPLOC = "temp_import_location_" + str(os.getpid())
    f = open(SRCGISRC, "w")
    f.write("MAPSET: PERMANENT\n")
    f.write("GISDBASE: %s\n" % GISDBASE)
    f.write("LOCATION_NAME: %s\n" % TMPLOC)
    f.write("GUI: text\n")
    f.close()

    # create temp location from input without import
    grass.verbose(_("Creating temporary location with EPSG:%d...") % epsg)
    grass.run_command("g.proj", flags="c", epsg=epsg, location=TMPLOC, quiet=True)

    # switch to temp location
    os.environ["GISRC"] = str(SRCGISRC)
    proj = grass.parse_command("g.proj", flags="g")
    if "epsg" in proj:
        currepsg = proj["epsg"]
    else:
        currepsg = proj["srid"].split("EPSG:")[1]

    currepsg = ":".join(srid.split(":")[-1:])
    if currepsg != str(epsg):
        grass.fatal("Creation of temporary location failed!")

    return SRCGISRC, TMPLOC


def main():

    global TMPLOC, SRCGISRC, TGTGISRC, GISDBASE
    global tile, tmpdir, in_temp, currdir, tmpregionname

    in_temp = False

    url = options["url"]
    username = options["username"]
    password = options["password"]
    local = options["local"]
    output = options["output"]
    memory = options["memory"]
    fillnulls = flags["n"]
    srtmv3 = flags["2"] == 0
    one = flags["1"]
    dozerotile = flags["z"]
    reproj_res = options["resolution"]

    overwrite = grass.overwrite()

    res = "00:00:03"
    if srtmv3:
        fillnulls = 0
        if one:
            res = "00:00:01"
    else:
        one = None

    if len(local) == 0:
        if len(url) == 0:
            if srtmv3:
                if one:
                    url = "https://e4ftl01.cr.usgs.gov/MEASURES/SRTMGL1.003/2000.02.11/"
                else:
                    url = "https://e4ftl01.cr.usgs.gov/MEASURES/SRTMGL3.003/2000.02.11/"
            else:
                url = "http://dds.cr.usgs.gov/srtm/version2_1/SRTM3/"

    if len(local) == 0:
        local = None

    # are we in LatLong location?
    s = grass.read_command("g.proj", flags="j")
    kv = grass.parse_key_val(s)

    if fillnulls == 1 and memory <= 0:
        grass.warning(
            _(
                "Amount of memory to use for interpolation must be positive, setting to 300 MB"
            )
        )
        memory = "300"

    # make a temporary directory
    tmpdir = grass.tempfile()
    grass.try_remove(tmpdir)
    os.mkdir(tmpdir)
    currdir = os.getcwd()
    pid = os.getpid()

    # change to temporary directory
    os.chdir(tmpdir)
    in_temp = True
    if local is None:
        local = tmpdir

    # save region
    tmpregionname = "r_in_srtm_tmp_region"
    grass.run_command("g.region", save=tmpregionname, overwrite=overwrite)

    # get extents
    if kv["+proj"] == "longlat":
        reg = grass.region()
    else:
        if not options["resolution"]:
            grass.fatal(
                _("The <resolution> must be set if the projection is not 'longlat'.")
            )
        reg2 = grass.parse_command("g.region", flags="uplg")
        north = [float(reg2["ne_lat"]), float(reg2["nw_lat"])]
        south = [float(reg2["se_lat"]), float(reg2["sw_lat"])]
        east = [float(reg2["ne_long"]), float(reg2["se_long"])]
        west = [float(reg2["nw_long"]), float(reg2["sw_long"])]
        reg = {}
        if np.mean(north) > np.mean(south):
            reg["n"] = max(north)
            reg["s"] = min(south)
        else:
            reg["n"] = min(north)
            reg["s"] = max(south)
        if np.mean(west) > np.mean(east):
            reg["w"] = max(west)
            reg["e"] = min(east)
        else:
            reg["w"] = min(west)
            reg["e"] = max(east)
        # get actual location, mapset, ...
        grassenv = grass.gisenv()
        tgtloc = grassenv["LOCATION_NAME"]
        tgtmapset = grassenv["MAPSET"]
        GISDBASE = grassenv["GISDBASE"]
        TGTGISRC = os.environ["GISRC"]

    if kv["+proj"] != "longlat":
        SRCGISRC, TMPLOC = createTMPlocation()
    if options["region"] is None or options["region"] == "":
        north = reg["n"]
        south = reg["s"]
        east = reg["e"]
        west = reg["w"]
    else:
        west, south, east, north = options["region"].split(",")
        west = float(west)
        south = float(south)
        east = float(east)
        north = float(north)

    # adjust extents to cover SRTM tiles: 1 degree bounds
    tmpint = int(north)
    if tmpint < north:
        north = tmpint + 1
    else:
        north = tmpint

    tmpint = int(south)
    if tmpint > south:
        south = tmpint - 1
    else:
        south = tmpint

    tmpint = int(east)
    if tmpint < east:
        east = tmpint + 1
    else:
        east = tmpint

    tmpint = int(west)
    if tmpint > west:
        west = tmpint - 1
    else:
        west = tmpint

    if north == south:
        north += 1
    if east == west:
        east += 1

    rows = abs(north - south)
    cols = abs(east - west)
    ntiles = rows * cols
    grass.message(_("Importing %d SRTM tiles...") % ntiles, flag="i")
    counter = 1

    srtmtiles = ""
    valid_tiles = 0
    for ndeg in range(south, north):
        for edeg in range(west, east):
            grass.percent(counter, ntiles, 1)
            counter += 1
            if ndeg < 0:
                tile = "S"
            else:
                tile = "N"
            tile = tile + "%02d" % abs(ndeg)
            if edeg < 0:
                tile = tile + "W"
            else:
                tile = tile + "E"
            tile = tile + "%03d" % abs(edeg)
            grass.debug("Tile: %s" % tile, debug=1)

            if local != tmpdir:
                gotit = import_local_tile(tile, local, pid, srtmv3, one)
            else:
                gotit = download_tile(tile, url, pid, srtmv3, one, username, password)
                if gotit == 1:
                    gotit = import_local_tile(tile, tmpdir, pid, srtmv3, one)
            if gotit == 1:
                grass.verbose(_("Tile %s successfully imported") % tile)
                valid_tiles += 1
            elif dozerotile:
                # create tile with zeros
                if one:
                    # north
                    if ndeg < -1:
                        tmpn = "%02d:59:59.5S" % (abs(ndeg) - 2)
                    else:
                        tmpn = "%02d:00:00.5N" % (ndeg + 1)
                    # south
                    if ndeg < 1:
                        tmps = "%02d:00:00.5S" % abs(ndeg)
                    else:
                        tmps = "%02d:59:59.5N" % (ndeg - 1)
                    # east
                    if edeg < -1:
                        tmpe = "%03d:59:59.5W" % (abs(edeg) - 2)
                    else:
                        tmpe = "%03d:00:00.5E" % (edeg + 1)
                    # west
                    if edeg < 1:
                        tmpw = "%03d:00:00.5W" % abs(edeg)
                    else:
                        tmpw = "%03d:59:59.5E" % (edeg - 1)
                else:
                    # north
                    if ndeg < -1:
                        tmpn = "%02d:59:58.5S" % (abs(ndeg) - 2)
                    else:
                        tmpn = "%02d:00:01.5N" % (ndeg + 1)
                    # south
                    if ndeg < 1:
                        tmps = "%02d:00:01.5S" % abs(ndeg)
                    else:
                        tmps = "%02d:59:58.5N" % (ndeg - 1)
                    # east
                    if edeg < -1:
                        tmpe = "%03d:59:58.5W" % (abs(edeg) - 2)
                    else:
                        tmpe = "%03d:00:01.5E" % (edeg + 1)
                    # west
                    if edeg < 1:
                        tmpw = "%03d:00:01.5W" % abs(edeg)
                    else:
                        tmpw = "%03d:59:58.5E" % (edeg - 1)

                grass.run_command("g.region", n=tmpn, s=tmps, e=tmpe, w=tmpw, res=res)
                grass.run_command(
                    "r.mapcalc",
                    expression="%s = 0" % (tile + ".r.in.srtm.tmp." + str(pid)),
                    quiet=True,
                )
                grass.run_command("g.region", region=tmpregionname)

    # g.list with sep = comma does not work ???
    pattern = "*.r.in.srtm.tmp.%d" % pid
    srtmtiles = grass.read_command(
        "g.list", type="raster", pattern=pattern, sep="newline", quiet=True
    )

    srtmtiles = srtmtiles.splitlines()
    srtmtiles = ",".join(srtmtiles)
    grass.debug("'List of Tiles: %s" % srtmtiles, debug=1)

    if valid_tiles == 0:
        grass.run_command(
            "g.remove", type="raster", name=str(srtmtiles), flags="f", quiet=True
        )
        grass.warning(_("No tiles imported"))
        if local != tmpdir:
            grass.fatal(_("Please check if local folder <%s> is correct.") % local)
        else:
            grass.fatal(
                _(
                    "Please check internet connection, credentials, and if url <%s> is correct."
                )
                % url
            )

    grass.run_command("g.region", raster=str(srtmtiles))

    grass.message(_("Patching tiles..."))
    if fillnulls == 0:
        if valid_tiles > 1:
            if kv["+proj"] != "longlat":
                grass.run_command("r.buildvrt", input=srtmtiles, output=output)
            else:
                grass.run_command("r.patch", input=srtmtiles, output=output)
        else:
            grass.run_command(
                "g.rename", raster="%s,%s" % (srtmtiles, output), quiet=True
            )
    else:
        ncells = grass.region()["cells"]
        if long(ncells) > 1000000000:
            grass.message(
                _("%s cells to interpolate, this will take some time") % str(ncells),
                flag="i",
            )
        if kv["+proj"] != "longlat":
            grass.run_command("r.buildvrt", input=srtmtiles, output=output + ".holes")
        else:
            grass.run_command("r.patch", input=srtmtiles, output=output + ".holes")
        mapstats = grass.parse_command(
            "r.univar", map=output + ".holes", flags="g", quiet=True
        )
        if mapstats["null_cells"] == "0":
            grass.run_command(
                "g.rename", raster="%s,%s" % (output + ".holes", output), quiet=True
            )
        else:
            grass.run_command(
                "r.resamp.bspline",
                input=output + ".holes",
                output=output + ".interp",
                se="0.0025",
                sn="0.0025",
                method="linear",
                memory=memory,
                flags="n",
            )
            grass.run_command(
                "r.patch",
                input="%s,%s" % (output + ".holes", output + ".interp"),
                output=output + ".float",
                flags="z",
            )
            grass.run_command(
                "r.mapcalc", expression="%s = round(%s)" % (output, output + ".float")
            )
            grass.run_command(
                "g.remove",
                type="raster",
                name="%s,%s,%s"
                % (output + ".holes", output + ".interp", output + ".float"),
                flags="f",
                quiet=True,
            )

    # switch to target location
    if kv["+proj"] != "longlat":
        os.environ["GISRC"] = str(TGTGISRC)
        # r.proj
        grass.message(_("Reprojecting <%s>...") % output)
        kwargs = {
            "location": TMPLOC,
            "mapset": "PERMANENT",
            "input": output,
            "memory": memory,
            "resolution": reproj_res,
        }
        if options["method"]:
            kwargs["method"] = options["method"]
        try:
            grass.run_command("r.proj", **kwargs)
        except CalledModuleError:
            grass.fatal(_("Unable to to reproject raster <%s>") % output)
    else:
        if fillnulls != 0:
            grass.run_command(
                "g.remove", type="raster", pattern=pattern, flags="f", quiet=True
            )

    # nice color table
    grass.run_command("r.colors", map=output, color="srtm", quiet=True)

    # write metadata:
    tmphist = grass.tempfile()
    f = open(tmphist, "w+")
    f.write(os.environ["CMDLINE"])
    f.close()
    if srtmv3:
        source1 = "SRTM V3"
    else:
        source1 = "SRTM V2.1"
    grass.run_command(
        "r.support",
        map=output,
        loadhistory=tmphist,
        description="generated by r.in.srtm.region",
        source1=source1,
        source2=(local if local != tmpdir else url),
    )
    grass.try_remove(tmphist)

    grass.message(_("Done: generated map <%s>") % output)


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    main()
