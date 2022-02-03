#!/usr/bin/env python


############################################################################
#
# MODULE:        i.modis.import
# AUTHOR(S):     Luca Delucchi
# PURPOSE:       i.modis.import is an interface to pyModis for import into
#                GRASS GIS level 3 MODIS produts
#
# COPYRIGHT:     (C) 2011-2020 by Luca Delucchi
#
#                This program is free software under the GNU General Public
#                License (>=v2). Read the file COPYING that comes with GRASS
#                for details.
#
#############################################################################
#
# REQUIREMENTS:
#   - either MRT tools, https://lpdaac.usgs.gov/lpdaac/tools/modis_reprojection_tool
#   - or GDAL
#
#############################################################################

# %module
# % description: Import single or multiple tiles of MODIS products using pyModis.
# % keyword: raster
# % keyword: import
# % keyword: MODIS
# %end
# %flag
# % key: m
# % description: Create a mosaic for each date
# % guisection: Import settings
# %end
# %flag
# % key: t
# % description: Preserve temporary files (TIF and HDF mosaic)
# % guisection: Import settings
# %end
# %flag
# % key: q
# % description: Ignore the QA map layer
# % guisection: Import settings
# %end
# %flag
# % key: w
# % description: Create a text file to use with t.register
# % guisection: Temporal
# %end
# %flag
# % key: a
# % description: Append new file to existing file to use with t.register
# % guisection: Temporal
# %end
# %flag
# % key: l
# % description: List more info about the supported MODIS products
# % guisection: Print
# %end
# %flag
# % key: g
# % description: Print output message in shell script style
# % guisection: Print
# %end
# %option G_OPT_F_BIN_INPUT
# % description: Full path to single HDF file
# % required: no
# % guisection: Input
# %end
# %option G_OPT_F_INPUT
# % key: files
# % description: Full path to file with list of HDF files
# % required: no
# % guisection: Input
# %end
# %option
# % key: method
# % type: string
# % key_desc: resampling
# % description: Name of spatial resampling method
# % options: nearest, bilinear, cubic
# % answer: nearest
# % required: no
# % guisection: Import settings
# %end
# %option G_OPT_M_DIR
# % key: mrtpath
# % description: Full path to MRT directory
# % required: no
# % guisection: Input
# %end
# %option
# % key: spectral
# % type: string
# % key_desc: spectral subset
# % description: String of the form "( 1 0 1 0 )" to choose a subset of HDF layers to import
# % required: no
# % guisection: Import settings
# %end
# %option G_OPT_F_OUTPUT
# % key: outfile
# % description: Full path to output file to use with t.register
# % required: no
# % guisection: Temporal
# %end

import os
import sys
import glob
import shutil
import tempfile
from datetime import datetime, timedelta

import grass.script as grass
from grass.pygrass.utils import get_lib_path
from grass.exceptions import CalledModuleError

path = get_lib_path(modname="i.modis", libname="libmodis")
if path is None:
    grass.fatal("Not able to find the modis library directory.")
sys.path.append(path)


class grassParseModis:
    """Class to reproduce parseModis class when VRT is used for mosaic

    :param str filename: the name of MODIS hdf file
    """

    def __init__(self, filename, date):
        self.hdfname = filename
        self.date = date

    def retRangeTime(self):
        return {"RangeBeginningDate": self.date}


def list_files(opt, mosaik=False):
    """If used in function single(): Return a list of HDF files from the file
    list. If used in function mosaic(): Return a dictionary with a list of HDF
    files for each day
    """
    # read the file with the list of HDF
    if opt["files"] != "":
        if os.path.exists(opt["files"]):
            if os.path.splitext(opt["files"])[-1].lower() == ".hdf":
                grass.fatal(
                    _(
                        "Option <{}> assumes file with list of HDF files. "
                        "Use option <{}> to import a single HDF file"
                    ).format("files", "input")
                )
            listoffile = open(opt["files"], "r")
            basedir = os.path.split(listoffile.name)[0]
        else:
            grass.fatal(_("File {name} does not exist".format(name=opt["files"])))
        # if mosaic create a dictionary
        if mosaik:
            filelist = {}
        # if not mosaic create a list
        else:
            filelist = []
        # append hdf files
        for line in listoffile:
            if line.find("xml") == -1 and mosaik is False:
                filelist.append(line.strip())
            # for mosaic create a list of hdf files for each day
            elif line.find("xml") == -1 and mosaik is True:
                day = line.split("/")[-1].split(".")[1]
                if day in filelist:
                    filelist[day].append(line.strip())
                else:
                    filelist[day] = [line.strip()]
        listoffile.close()
    # create a list for each file
    elif options["input"] != "":
        filelist = [options["input"]]
        basedir = os.path.split(filelist[0])[0]
    return filelist, basedir


def spectral(opts, prod, q, m=False):
    """Return spectral string"""
    # return the spectral set selected by the user
    if opts["spectral"] != "":
        spectr = opts["spectral"]
    # return the spectral by default
    else:
        if q:
            if prod["spec_qa"]:
                spectr = prod["spec_qa"]
            else:
                spectr = prod["spec"]
        else:
            spectr = prod["spec"]
        if m:
            spectr = spectr.replace(" 0", "")
    return str(spectr)


def confile(pm, opts, q, mosaik=False):
    """Create the configuration file for MRT software"""
    try:
        # try to import pymodis (modis) and some classes for i.modis.download
        from rmodislib import resampling, product, projection
    except ImportError as e:
        grass.fatal("Unable to load i.modis library: {}".format(e))
    # return projection and datum
    projObj = projection()
    proj = projObj.returned()
    dat = projObj.datum()
    if proj == "UTM":
        zone = projObj.utmzone()
    else:
        zone = None
    cod = os.path.split(pm.hdfname)[1].split(".")[0]
    prod = product().fromcode(cod)
    if mosaik:
        # if mosaic it remove all the 0 from the subset string to convert all
        # the right layer
        spectr = spectral(opts, prod, q, True)
    else:
        spectr = spectral(opts, prod, q)
    # out prefix
    pref = modis_prefix(pm.hdfname)
    # resampling
    resampl = resampling(opts["method"]).returned()
    # projpar
    projpar = projObj.return_params()
    if projpar != "( 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 )":
        dat = "NODATUM"
    # resolution
    if proj != "GEO":
        res = int(prod["res"]) * int(projObj.proj["meters"])
    else:
        res = None
    try:
        conf = pm.confResample(spectr, res, pref, dat, resampl, proj, zone, projpar)
        return conf
    except IOError as e:
        grass.fatal(e)


def metadata(pars, mapp):
    """Set metadata to the imported files"""
    # metadata
    grass.run_command(
        "r.support",
        quiet=True,
        map=mapp,
        source1="MODIS NASA",
        hist="Imported with i.modis.import",
    )
    # timestamp
    rangetime = pars.retRangeTime()
    data = rangetime["RangeBeginningDate"].split("-")
    dataobj = datetime(int(data[0]), int(data[1]), int(data[2]))
    grass.run_command(
        "r.timestamp", map=mapp, quiet=True, date=dataobj.strftime("%d %b %Y")
    )
    return dataobj
    # color


#    if string.find(mapp, 'QC') != -1 or string.find(mapp, 'Quality') != -1 or \
#    string.find(mapp, 'QA') != -1:
#        grass.run_command('r.colors', quiet=True, map=mapp, color=coll)
#    elif string.find(mapp, 'NDVI') != -1:
#        grass.run_command('r.colors', quiet=True, map=mapp, color=coll[0])
#    elif string.find(mapp, 'EVI') != -1:
#        grass.run_command('r.colors', quiet=True, map=mapp, color=coll[1])
#    elif string.find(mapp, 'LST') != -1:
#        grass.run_command('r.colors', quiet=True, map=mapp, color=coll[0])
#    elif string.find(mapp, 'Snow') != -1:
#        grass.run_command('r.colors', quiet=True, map=mapp, color=coll[0])


def modis_prefix(inp, mosaic=False):
    """return the modis prefix"""
    modlist = os.path.split(inp)[1].split(".")
    if mosaic:
        return ".".join(modlist[:2])
    else:
        return ".".join(modlist[:3])


def import_tif(basedir, rem, write, pm, prod, target=None, listfile=None):
    """Import TIF files"""
    # list of tif files
    pref = modis_prefix(pm.hdfname)
    tifiles = glob.glob1(basedir, "{pr}*.tif".format(pr=pref))
    if not tifiles:
        tifiles = glob.glob1(os.getcwd(), "{pr}*.tif".format(pr=pref))
    if not tifiles:
        grass.fatal(_("Error during the conversion"))
    outfile = []
    # for each file import it
    for t in tifiles:
        basename = os.path.splitext(t)[0]
        basename = basename.replace(" ", "_")
        name = os.path.join(basedir, t)
        if not os.path.exists(name):
            name = os.path.join(os.getcwd(), t)
        if not os.path.exists(name):
            grass.warning(_("File %s doesn't find" % name))
            continue
        filesize = int(os.path.getsize(name))
        if filesize < 1000:
            grass.warning(
                _(
                    "Probably some error occur during the conversion"
                    "for file <%s>. Escape import" % name
                )
            )
            continue
        try:
            basename = basename.replace('"', "").replace(" ", "_")
            grass.run_command(
                "r.in.gdal", input=name, output=basename, overwrite=write, quiet=True
            )
            outfile.append(basename)

            # check number of bands
            nbands = int(grass.read_command("r.in.gdal", input=name, flags="p"))
        except CalledModuleError as e:
            grass.warning(_("Error during import of {}".format(basename)))
            continue

        # process bands
        for b in range(nbands):
            if nbands > 1:
                mapname = "{}.{}".format(basename, b + 1)
            else:
                mapname = basename
            data = metadata(pm, mapname)

            if listfile:
                days = prod["days"]
                fdata = data + timedelta(days)
                if days == 31:
                    fdata = datetime(fdata.year, fdata.month, 1)
                if days != 1 and data.year != fdata.year:
                    fdata = datetime(fdata.year, fdata.month, 1)
                listfile.write(
                    "{name}|{sd}|{fd}\n".format(
                        name=mapname,
                        sd=data.strftime("%Y-%m-%d"),
                        fd=fdata.strftime("%Y-%m-%d"),
                    )
                )

        # handle temporary data
        if rem:
            os.remove(name)
        if target:
            if target != basedir:
                shutil.move(name, target)

    return outfile


def findfile(pref, suff):
    """Check if a file exists on mapset"""
    if grass.find_file(pref + suff)["file"]:
        return grass.find_file(pref + suff)
    else:
        grass.warning(_("Raster map <%s> not found") % (pref + suff))


def doy2date(modis):
    """From he MODIS code to YYYY-MM-DD string date"""
    year = modis[:4]
    doy = modis[-3:]
    dat = datetime.strptime("{ye} {doy}".format(ye=year, doy=doy), "%Y %j")
    return dat.strftime("%Y-%m-%d")


def single(options, remove, an, ow, fil):
    """Convert the HDF file to TIF and import it"""
    try:
        # try to import pymodis (modis) and some classes for i.modis.download
        from rmodislib import product, projection, get_proj
    except ImportError as e:
        grass.fatal("Unable to load i.modis library: {}".format(e))
    try:
        from pymodis.convertmodis import convertModis
        from pymodis.convertmodis_gdal import convertModisGDAL
        from pymodis.parsemodis import parseModis
    except ImportError as e:
        grass.fatal("Unable to import pymodis library: {}".format(e))
    listfile, basedir = list_files(options)
    if not listfile:
        grass.warning(_("No HDF files found"))
        return

    # for each file
    count = len(listfile)
    idx = 1
    for i in listfile:
        if os.path.exists(i):
            hdf = i
        else:
            # the full path to hdf file
            hdf = os.path.join(basedir, i)
            if not os.path.exists(hdf):
                grass.warning(_("%s not found" % i))
                continue

        grass.message(
            _("Proccessing <{f}> ({i}/{c})...").format(
                f=os.path.basename(hdf), i=idx, c=count
            )
        )
        grass.percent(idx, count, 5)
        idx += 1

        try:
            pm = parseModis(hdf)
        except OSError:
            grass.fatal(_("<{}> is not a HDF file").format(hdf))
            continue
        if options["mrtpath"]:
            # create conf file fro mrt tools
            confname = confile(pm, options, an)
            # create convertModis class and convert it in tif file
            execmodis = convertModis(hdf, confname, options["mrtpath"])
        else:
            projwkt = get_proj("w")
            projObj = projection()
            pref = i.split(os.path.sep)[-1]
            prod = product().fromcode(pref.split(".")[0])
            spectr = spectral(options, prod, an)
            if projObj.returned() != "GEO":
                res = int(prod["res"]) * int(projObj.proj["meters"])
            else:
                res = None
            outname = "%s.%s.%s.single" % (
                pref.split(".")[0],
                pref.split(".")[1],
                pref.split(".")[2],
            )
            outname = outname.replace(" ", "_")
            execmodis = convertModisGDAL(
                str(hdf), outname, spectr, res, wkt=str(projwkt)
            )

        # produce temporary files in input folder
        os.chdir(basedir)
        try:
            execmodis.run(quiet=True)
        except:
            execmodis.run()
        import_tif(
            basedir=basedir, rem=remove, write=ow, pm=pm, listfile=fil, prod=prod
        )
        if options["mrtpath"]:
            os.remove(confname)


def mosaic(options, remove, an, ow, fil):
    """Create a daily mosaic of HDF files convert to TIF and import it"""
    try:
        # try to import pymodis (modis) and some classes for i.modis.download
        from rmodislib import product, projection, get_proj
    except ImportError as e:
        grass.fatal("Unable to load i.modis library: {}".format(e))
    try:
        from pymodis.convertmodis import convertModis, createMosaic
        from pymodis.convertmodis_gdal import createMosaicGDAL, convertModisGDAL
        from pymodis.parsemodis import parseModis
    except ImportError as e:
        grass.fatal("Unable to import pymodis library: {}".format(e))
    dictfile, targetdir = list_files(options, True)
    pid = str(os.getpid())
    # for each day
    count = len(dictfile.keys())
    idx = 1
    for dat, listfiles in dictfile.items():
        grass.message(_("Processing <{d}> ({i}/{c})...").format(d=dat, i=idx, c=count))
        grass.percent(idx, count, 5)
        idx += 1

        pref = listfiles[0].split(os.path.sep)[-1]
        prod = product().fromcode(pref.split(".")[0])
        spectr = spectral(options, prod, an)
        spectr = spectr.lstrip("( ").rstrip(" )")
        outname = "%s.%s_mosaic" % (pref.split(".")[0], pref.split(".")[1])
        outname = outname.replace(" ", "_")
        # create mosaic
        if options["mrtpath"]:
            # create the file with the list of name
            tempfile = open(os.path.join(targetdir, pid), "w")
            tempfile.writelines(listfiles)
            tempfile.close()
            # basedir of tempfile, where hdf files are write
            basedir = os.path.split(tempfile.name)[0]
            # return the spectral subset in according mrtmosaic tool format
            cm = createMosaic(tempfile.name, outname, options["mrtpath"], spectr)
            cm.run()
            hdfiles = glob.glob1(basedir, outname + "*.hdf")
        else:
            basedir = targetdir
            listfiles = [os.path.join(basedir, i) for i in listfiles]
            cm = createMosaicGDAL(listfiles, spectr)
            try:
                cm.write_vrt(os.path.join(basedir, outname), quiet=True)
            except:
                cm.write_vrt(os.path.join(basedir, outname))
            hdfiles = glob.glob1(basedir, outname + "*.vrt")
        for i in hdfiles:
            # the full path to hdf file
            hdf = os.path.join(basedir, i)
            try:
                pm = parseModis(hdf)
            except:
                out = i.replace(".vrt", "")
                data = doy2date(dat[1:])
                pm = grassParseModis(out, data)
            # create convertModis class and convert it in tif file
            if options["mrtpath"]:
                # create conf file fro mrt tools
                confname = confile(pm, options, an, True)
                execmodis = convertModis(hdf, confname, options["mrtpath"])
            else:
                confname = None
                projwkt = get_proj("w")
                projObj = projection()
                if projObj.returned() != "GEO":
                    res = int(prod["res"]) * int(projObj.proj["meters"])
                else:
                    res = None
                execmodis = convertModisGDAL(
                    str(hdf), out, spectr, res, wkt=str(projwkt), vrt=True
                )

            # produce temporary files in input folder
            os.chdir(basedir)
            try:
                execmodis.run(quiet=True)
            except:
                execmodis.run()
            # remove hdf
            if remove:
                # import tif files
                import_tif(
                    basedir=basedir,
                    rem=remove,
                    write=ow,
                    pm=pm,
                    listfile=fil,
                    prod=prod,
                )
                try:
                    os.remove(hdf)
                    os.remove(hdf + ".xml")
                except OSError:
                    pass
            # move the hdf and hdf.xml to the dir where are the original files
            else:
                # import tif files
                import_tif(
                    basedir=basedir,
                    rem=remove,
                    write=ow,
                    pm=pm,
                    target=targetdir,
                    listfile=fil,
                    prod=prod,
                )
                if i not in os.listdir(targetdir):
                    try:
                        shutil.move(hdf, targetdir)
                        shutil.move(hdf + ".xml", targetdir)
                    except OSError:
                        pass
            # remove the conf file
            try:
                os.remove(confname)
            except (OSError, TypeError) as e:
                pass
        if options["mrtpath"]:
            grass.try_remove(tempfile.name)
        grass.try_remove(os.path.join(targetdir, "mosaic", pid))


def main():
    # check if you are in GRASS
    gisbase = os.getenv("GISBASE")
    if not gisbase:
        grass.fatal(_("$GISBASE not defined"))
        return 0
    if flags["l"]:
        try:
            from rmodislib import product
        except ImportError as e:
            grass.fatal("Unable to load i.modis library: {}".format(e))
        prod = product()
        prod.print_prods()
        return 0
    # return an error if q and spectral are set
    if not flags["q"] and options["spectral"] != "":
        grass.warning(
            _(
                'If no QA layer chosen in the "spectral" option'
                " the command will report an error"
            )
        )
    # return an error if both input and files option are set or not
    if options["input"] == "" and options["files"] == "":
        grass.fatal(_('Choose one of "input" or "files" options'))
        return 0
    elif options["input"] != "" and options["files"] != "":
        grass.fatal(_('It is not possible set "input" and "files"' " options together"))
        return 0
    # check the version
    version = grass.core.version()
    # this is would be set automatically
    if version["version"].find("7.") == -1:
        grass.fatal(_("GRASS GIS version 7 required"))
        return 0
    # check if remove the files or not
    if flags["t"]:
        remove = False
    else:
        remove = True
    if grass.overwrite():
        over = True
    else:
        over = False
    # check if do check quality, rescaling and setting of colors
    if flags["q"]:
        analyze = False
    else:
        analyze = True
    # return the number of select layer from HDF files
    if options["spectral"]:
        count = options["spectral"].strip("(").strip(")").split().count("1")
    else:
        count = 0

    outfile = None
    # check if file for t.register has to been created
    if options["outfile"]:
        if flags["a"]:
            outfile = open(options["outfile"], "a")
        else:
            outfile = open(options["outfile"], "w")
        if count > 1:
            grass.warning(
                "The spectral subsets are more than one so the "
                " output file will be renamed"
            )
    elif flags["w"] and not options["outfile"]:
        outfile = tempfile.NamedTemporaryFile(delete=False)

    # check if import simple file or mosaic
    if flags["m"] and options["input"] != "":
        grass.fatal(
            _("It is not possible to create a mosaic with a single" " HDF file")
        )
        return 0
    elif flags["m"]:
        mosaic(options, remove, analyze, over, outfile)
    else:
        single(options, remove, analyze, over, outfile)
    # if t.register file is create
    if outfile:
        outfile.close()
        tempdir = grass.tempdir()
        # one layer only
        if count == 1:
            if flags["g"]:
                grass.message(_("file={name}".format(name=outfile.name)))
            else:
                grass.message(
                    _(
                        "You can use temporal framework, registering"
                        " the maps using t.register input=your_strds "
                        "'file={name}'".format(name=outfile.name)
                    )
                )
        # for more layer create several files with only a subset for each layer
        elif count > 1:
            tfile = open(outfile.name)
            outfiles = {}
            lines = tfile.readlines()
            # get the codes from only one HDF
            for line in lines[:count]:
                if flags["m"]:
                    code = "_".join(line.split("|")[0].split("_")[2:])
                else:
                    code = line.split("|")[0].split(".")[-1]
                outfiles[code] = open(
                    os.path.join(tempdir, "{co}.txt".format(co=code)), "w"
                )
            # split the lines for each code
            for line in lines:
                if flags["m"]:
                    code = "_".join(line.split("|")[0].split("_")[2:])
                else:
                    code = line.split("|")[0].split(".")[-1]
                outfiles[code].write(line)
            for k, v in outfiles.items():
                v.close()
            if flags["g"]:
                message = ""
            else:
                message = (
                    "You can use temporal framework, registering the "
                    "maps  in different temporal datasets using "
                    "t.register and \n"
                )
            tfile.close()
            for fil in outfiles.values():
                message += "'file={name}'\n".format(name=fil.name)
            grass.message(_(message))


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
