#!/usr/bin/env python

############################################################################
#
# MODULE:       r.in.nasadem
#
# AUTHOR(S):    Markus Metz
#               URL authenticaton added by Jonas Strobel, intern at mundialis and terrestris, Bonn
#
# PURPOSE:      Create a DEM from 1 arcsec NASADEM tiles
#
# COPYRIGHT:    (C) 2020-2021 GRASS development team
#
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################

# %module
# % description: Creates a DEM from 1 arcsec NASADEM tiles.
# % keyword: raster
# % keyword: import
# % keyword: SRTM
# %end
# %option
# % key: version
# % description: NASADEM version
# % options: NASADEM_HGT.001
# % answer: NASADEM_HGT.001
# % required: no
# %end
# %option
# % key: layer
# % description: NASADEM layer
# % options: hgt,num,swb
# % description: NASADEM layer to import
# % descriptions: hgt;Void-filled DEM;num;Number of scenes;swb;Updated SRTM water body data
# % answer: hgt
# % required: no
# %end
# %option G_OPT_R_OUTPUT
# % description: Name for output raster map
# % required: yes
# %end
# %option
# % key: username
# % description: Username for authentication
# % required: no
# %end
# %option
# % key: password
# % description: Password for authentication
# % required: no
# %end
# %option
# % key: url
# % description: Base URL to fetch NASADEM tiles
# % answer: https://e4ftl01.cr.usgs.gov/MEASURES
# % required: no
# %end
# %option G_OPT_M_DIR
# % key: local
# % label: Local folder with NASADEM tiles
# % description: Use local folder instead of URL to retrieve NASADEM tiles
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
# % key: method
# % type: string
# % required: no
# % multiple: no
# % options: nearest,bilinear,bicubic,lanczos,bilinear_f,bicubic_f,lanczos_f
# % description: Resampling method to use for reprojection (required if location projection not longlat)
# % descriptions: nearest;nearest neighbor;bilinear;bilinear interpolation;bicubic;bicubic interpolation;lanczos;lanczos filter;bilinear_f;bilinear interpolation with fallback;bicubic_f;bicubic interpolation with fallback;lanczos_f;lanczos filter with fallback
# % guisection: Output
# % answer: bilinear_f
# %end
# %option
# % key: resolution
# % type: double
# % required: no
# % multiple: no
# % description: Resolution of output raster map (required if location projection not longlat)
# % guisection: Output
# %end
# %option
# % key: memory
# % type: integer
# % required: no
# % multiple: no
# % label: Maximum memory to be used (in MB)
# % description: Cache size for raster rows
# % answer: 300
# %end
# %flag
# % key: z
# % description: Create zero elevation for missing tiles
# %end


import os
import atexit
import numpy as np
import shutil
import time
import zipfile as zfile
import subprocess
from six.moves.urllib import request as urllib2

try:
    from http.cookiejar import CookieJar
except ImportError:
    from cookielib import CookieJar
import grass.script as grass
from grass.exceptions import CalledModuleError

# initialize global vars
TMPLOC = None
SRCGISRC = None
TGTGISRC = None
GISDBASE = None

nd16bit1sec = """BYTEORDER M
LAYOUT BIL
NROWS 3601
NCOLS 3601
NBANDS 1
NBITS 16
BANDROWBYTES 7202
TOTALROWBYTES 7202
BANDGAPBYTES 0
PIXELTYPE SIGNEDINT
NODATA -32768
ULXMAP %s
ULYMAP %s
XDIM 0.000277777777777778
YDIM 0.000277777777777778
"""

nd8bit1sec = """BYTEORDER M
LAYOUT BIL
NROWS 3601
NCOLS 3601
NBANDS 1
NBITS 8
BANDROWBYTES 3601
TOTALROWBYTES 3601
BANDGAPBYTES 0
PIXELTYPE UNSIGNEDINT
ULXMAP %s
ULYMAP %s
XDIM 0.000277777777777778
YDIM 0.000277777777777778
"""

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


def import_local_tile(tile, local, pid, layer):
    # extract zip archive to current directory
    # create a bil file with associated files (hdr, prj)

    local_tile = "NASADEM_HGT_" + str(tile) + ".zip"
    output = tile + ".r.in.nasadem.tmp." + str(pid)

    suff = layer

    zipfile = local_tile
    layerfile = "{im}.{su}".format(im=tile, su=suff)

    if local is not None:
        zippath = os.path.join(local, zipfile)
        layerpath = os.path.join(local, layerfile)
    else:
        zippath = zipfile
        layerpath = layerfile

    if os.path.isfile(zippath):
        # really a ZIP file?
        if not zfile.is_zipfile(zippath):
            grass.fatal(_("'%s' does not appear to be a valid zip file.") % zipfile)

        is_zip = True
        if zippath != zipfile:
            shutil.copyfile(zippath, zipfile)
        # unzip & rename data file:
        try:
            zf = zfile.ZipFile(zipfile)
            zf.extractall()
        except:
            grass.fatal(_("Unable to unzip file."))

    if not os.path.isfile(layerfile):
        if local is None:
            return 0
        elif os.path.isfile(layerpath):
            shutil.copyfile(layerpath, layerfile)

    if not os.path.isfile(layerfile):
        return 0

    grass.verbose(_("Converting input file to BIL..."))
    bilfile = tile + ".bil"
    os.rename(layerfile, bilfile)

    north = tile[0]
    ll_latitude = int(tile[1:3])
    east = tile[3]
    ll_longitude = int(tile[4:7])

    # are we on the southern hemisphere? If yes, make LATITUDE negative.
    if north == "s":
        ll_latitude *= -1

    # are we west of Greenwich? If yes, make LONGITUDE negative.
    if east == "w":
        ll_longitude *= -1

    # Calculate Upper Left from Lower Left
    ulxmap = "%.1f" % ll_longitude
    # SRTM90 tile size is 1 deg:
    ulymap = "%.1f" % (ll_latitude + 1)

    grass.verbose(_("Attempting to import NASADEM %s data") % layer)
    if layer == "hgt":
        tmpl = nd16bit1sec
    elif layer == "num" or layer == "swb":
        tmpl = nd8bit1sec

    header = tmpl % (ulxmap, ulymap)
    hdrfile = tile + ".hdr"
    outf = open(hdrfile, "w")
    outf.write(header)
    outf.close()

    # create prj file: To be precise, we would need EGS96! But who really cares...
    prjfile = tile + ".prj"
    outf = open(prjfile, "w")
    outf.write(proj)
    outf.close()

    try:
        grass.run_command("r.in.gdal", input=bilfile, output=output, quiet=True)
    except:
        grass.fatal(_("Unable to import <%s>") % bilfile)

    return 1


def download_tile(tile, url, pid, version, username, password):

    grass.debug("Download tile: %s" % tile, debug=1)
    local_tile = "NASADEM_HGT_" + str(tile) + ".zip"

    urllib2.urlcleanup()

    remote_tile = str(url) + "/" + version + "/2000.02.11/" + local_tile
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

    if currepsg != str(epsg):
        grass.fatal("Creation of temporary location failed!")

    return SRCGISRC, TMPLOC


def main():

    global TMPLOC, SRCGISRC, TGTGISRC, GISDBASE
    global tile, tmpdir, in_temp, currdir, tmpregionname

    in_temp = False

    nasadem_version = options["version"]
    nasadem_layer = options["layer"]
    url = options["url"]
    username = options["username"]
    password = options["password"]
    local = options["local"]
    output = options["output"]
    dozerotile = flags["z"]
    reproj_res = options["resolution"]

    overwrite = grass.overwrite()

    tile = None
    tmpdir = None
    in_temp = None
    currdir = None
    tmpregionname = None

    if len(local) == 0:
        local = None
        if len(username) == 0 or len(password) == 0:
            grass.fatal(_("NASADEM download requires username and password."))

    # are we in LatLong location?
    s = grass.read_command("g.proj", flags="j")
    kv = grass.parse_key_val(s)

    # make a temporary directory
    tmpdir = grass.tempfile()
    grass.try_remove(tmpdir)
    os.mkdir(tmpdir)
    currdir = os.getcwd()
    pid = os.getpid()

    # change to temporary directory
    os.chdir(tmpdir)
    in_temp = True

    # save region
    tmpregionname = "r_in_nasadem_region_" + str(pid)
    grass.run_command("g.region", save=tmpregionname, overwrite=overwrite)

    # get extents
    if kv["+proj"] == "longlat":
        reg = grass.region()
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

    else:
        if not options["resolution"]:
            grass.fatal(
                _("The <resolution> must be set if the projection is not 'longlat'.")
            )
        if options["region"] is None or options["region"] == "":
            reg2 = grass.parse_command("g.region", flags="uplg")
            north_vals = [float(reg2["ne_lat"]), float(reg2["nw_lat"])]
            south_vals = [float(reg2["se_lat"]), float(reg2["sw_lat"])]
            east_vals = [float(reg2["ne_long"]), float(reg2["se_long"])]
            west_vals = [float(reg2["nw_long"]), float(reg2["sw_long"])]
            reg = {}
            if np.mean(north_vals) > np.mean(south_vals):
                north = max(north_vals)
                south = min(south_vals)
            else:
                north = min(north_vals)
                south = max(south_vals)
            if np.mean(west_vals) > np.mean(east_vals):
                west = max(west_vals)
                east = min(east_vals)
            else:
                west = min(west_vals)
                east = max(east_vals)
            # get actual location, mapset, ...
            grassenv = grass.gisenv()
            tgtloc = grassenv["LOCATION_NAME"]
            tgtmapset = grassenv["MAPSET"]
            GISDBASE = grassenv["GISDBASE"]
            TGTGISRC = os.environ["GISRC"]
        else:
            grass.fatal(
                _(
                    "The option <resolution> is only supported in the projection 'longlat'"
                )
            )

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

    # switch to longlat location
    if kv["+proj"] != "longlat":
        SRCGISRC, TMPLOC = createTMPlocation()

    rows = abs(north - south)
    cols = abs(east - west)
    ntiles = rows * cols
    grass.message(_("Importing %d NASADEM tiles...") % ntiles, flag="i")
    counter = 1

    srtmtiles = ""
    valid_tiles = 0
    for ndeg in range(south, north):
        for edeg in range(west, east):
            grass.percent(counter, ntiles, 1)
            counter += 1
            if ndeg < 0:
                tile = "s"
            else:
                tile = "n"
            tile = tile + "%02d" % abs(ndeg)
            if edeg < 0:
                tile = tile + "w"
            else:
                tile = tile + "e"
            tile = tile + "%03d" % abs(edeg)
            grass.debug("Tile: %s" % tile, debug=1)

            if local is None:
                download_tile(tile, url, pid, nasadem_version, username, password)

            gotit = import_local_tile(tile, local, pid, nasadem_layer)
            if gotit == 1:
                grass.verbose(_("Tile %s successfully imported") % tile)
                valid_tiles += 1
            elif dozerotile:
                # create tile with zeros
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

                grass.run_command("g.region", n=tmpn, s=tmps, e=tmpe, w=tmpw, res=res)
                grass.run_command(
                    "r.mapcalc",
                    expression="%s = 0" % (tile + ".r.in.nasadem.tmp." + str(pid)),
                    quiet=True,
                )
                grass.run_command("g.region", region=tmpregionname)

    # g.list with sep = comma does not work ???
    pattern = "*.r.in.nasadem.tmp.%d" % pid
    demtiles = grass.read_command(
        "g.list", type="raster", pattern=pattern, sep="newline", quiet=True
    )

    demtiles = demtiles.splitlines()
    demtiles = ",".join(demtiles)
    grass.debug("'List of Tiles: %s" % demtiles, debug=1)

    if valid_tiles == 0:
        grass.run_command(
            "g.remove", type="raster", name=str(demtiles), flags="f", quiet=True
        )
        grass.warning(_("No tiles imported"))
        if local is not None:
            grass.fatal(_("Please check if local folder <%s> is correct.") % local)
        else:
            grass.fatal(
                _(
                    "Please check internet connection, credentials, and if url <%s> is correct."
                )
                % url
            )

    grass.run_command("g.region", raster=str(demtiles))

    if valid_tiles > 1:
        grass.message(_("Patching tiles..."))
        if kv["+proj"] != "longlat":
            grass.run_command("r.buildvrt", input=demtiles, output=output)
        else:
            grass.run_command("r.patch", input=demtiles, output=output)
            grass.run_command(
                "g.remove", type="raster", name=str(demtiles), flags="f", quiet=True
            )
    else:
        grass.run_command("g.rename", raster="%s,%s" % (demtiles, output), quiet=True)

    # switch to target location and repoject nasadem
    if kv["+proj"] != "longlat":
        os.environ["GISRC"] = str(TGTGISRC)
        # r.proj
        grass.message(_("Reprojecting <%s>...") % output)
        kwargs = {
            "location": TMPLOC,
            "mapset": "PERMANENT",
            "input": output,
            "resolution": reproj_res,
        }
        if options["memory"]:
            kwargs["memory"] = options["memory"]
        if options["method"]:
            kwargs["method"] = options["method"]
        try:
            grass.run_command("r.proj", **kwargs)
        except CalledModuleError:
            grass.fatal(_("Unable to to reproject raster <%s>") % output)

    # nice color table
    grass.run_command("r.colors", map=output, color="srtm", quiet=True)

    # write metadata:
    tmphist = grass.tempfile()
    f = open(tmphist, "w+")
    # hide username and password
    cmdline = os.environ["CMDLINE"]
    if username is not None and len(username) > 0:
        cmdline = cmdline.replace("=" + username, "=xxx")
    if password is not None and len(password) > 0:
        cmdline = cmdline.replace("=" + password, "=xxx")

    f.write(cmdline)
    f.close()
    source1 = nasadem_version
    grass.run_command(
        "r.support",
        map=output,
        loadhistory=tmphist,
        description="generated by r.in.nasadem",
        source1=source1,
        source2=(local if local != tmpdir else url),
    )
    grass.try_remove(tmphist)

    grass.message(_("Done: generated map <%s>") % output)


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    main()
