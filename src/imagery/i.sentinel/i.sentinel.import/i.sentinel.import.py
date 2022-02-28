#!/usr/bin/env python3
#
############################################################################
#
# MODULE:      i.sentinel.import
# AUTHOR(S):   Martin Landa, Felix Kröber
# PURPOSE:     Imports Sentinel data downloaded from Copernicus Open Access Hub
#              using i.sentinel.download.
# COPYRIGHT:   (C) 2018-2021 by Martin Landa, and the GRASS development team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################

#%Module
#% description: Imports Sentinel satellite data downloaded from Copernicus Open Access Hub using i.sentinel.download.
#% keyword: imagery
#% keyword: satellite
#% keyword: Sentinel
#% keyword: import
#%end
#%option G_OPT_M_DIR
#% key: input
#% description: Name of input directory with downloaded Sentinel data
#% required: yes
#%end
#%option G_OPT_M_DIR
#% key: unzip_dir
#% description: Name of directory into which Sentinel zip-files are extracted (default=input)
#% required: no
#%end
#%option
#% key: pattern
#% description: Band name pattern to import
#% guisection: Filter
#%end
#%option
#% key: pattern_file
#% description: File name pattern to import
#% guisection: Filter
#%end
#%option
#% key: extent
#% type: string
#% required: no
#% multiple: no
#% options: input,region
#% answer: input
#% description: Output raster map extent
#% descriptions: region;extent of current region;input;extent of input map
#% guisection: Filter
#%end
#%option
#% key: memory
#% type: integer
#% required: no
#% multiple: no
#% label: Maximum memory to be used (in MB)
#% description: Cache size for raster rows
#% answer: 300
#%end
#%option G_OPT_F_OUTPUT
#% key: register_output
#% description: Name for output file to use with t.register
#% required: no
#%end
#%option G_OPT_M_DIR
#% key: metadata
#% description: Name of directory into which Sentinel metadata json dumps are saved
#% required: no
#%end
#%option
#% key: cloud_area_threshold
#% description: Threshold above which areas of clouds and/or cloud shadows will be masked (in hectares)
#% type: double
#% required: no
#% answer: 1
#%end
#%option
#% key: cloud_probability_threshold
#% description: Minimum cloud probability for pixels to be masked
#% type: integer
#% required: no
#% options: 0-100
#% answer: 65
#%end
#%option
#% key: cloud_output
#% type: string
#% required: no
#% multiple: no
#% options: vector,raster
#% answer: vector
#% label: Create cloud mask as raster or vector map
#%end
#%flag
#% key: r
#% description: Reproject raster data using r.import if needed
#% guisection: Settings
#%end
#%flag
#% key: l
#% description: Link raster data instead of importing
#% guisection: Settings
#%end
#%flag
#% key: o
#% description: Override projection check (use current location's projection)
#% guisection: Settings
#%end
#%flag
#% key: c
#% description: Import cloud masks
#% guisection: Settings
#%end
#%flag
#% key: s
#% description: Import cloud shadow masks
#% guisection: Settings
#%end
#%flag
#% key: n
#% description: Do not unzip SAFE-files if they are already extracted
#% guisection: Settings
#%end
#%flag
#% key: p
#% description: Print raster data to be imported and exit
#% guisection: Print
#%end
#%flag
#% key: j
#% description: Write meta data json for each band to LOCATION/MAPSET/cell_misc/BAND/description.json
#% guisection: Print
#%end
#%rules
#% exclusive: -l,-r,-p
#% exclusive: -o,-r
#% exclusive: extent,-l
#% exclusive: metadata,-j
#% requires: -s,-c
#%end

import os
import sys
import re
import glob
import shutil
import io
import json
from zipfile import ZipFile

import grass.script as gs
from grass.exceptions import CalledModuleError


class SentinelImporter(object):
    def __init__(self, input_dir, unzip_dir):
        # list of directories & maps to cleanup
        self._dir_list = []
        self._map_list = []

        # check if input dir exists
        self.input_dir = input_dir
        if not os.path.exists(input_dir):
            gs.fatal(_("Input directory <{}> does not exist").format(input_dir))

        # check if unzip dir exists
        if unzip_dir is None or unzip_dir == "":
            unzip_dir = input_dir

        self.unzip_dir = unzip_dir
        if not os.path.exists(unzip_dir):
            gs.fatal(_("Directory <{}> does not exist").format(unzip_dir))

    def __del__(self):
        # remove temporary maps
        for map in self._map_list:
            if gs.find_file(map, element="cell")["file"]:
                gs.run_command(
                    "g.remove", flags="fb", type="raster", name=map, quiet=True
                )
            if gs.find_file(map, element="vector")["file"]:
                gs.run_command(
                    "g.remove", flags="f", type="vector", name=map, quiet=True
                )

        if flags["l"]:
            # unzipped files are required when linking
            return

        # otherwise unzipped directory can be removed (?)
        for dirname in self._dir_list:
            dirpath = os.path.join(self.unzip_dir, dirname)
            gs.debug("Removing <{}>".format(dirpath))
            try:
                shutil.rmtree(dirpath)
            except OSError:
                pass

    def filter(self, pattern=None):
        if pattern:
            filter_p = r".*{}.*.jp2$".format(pattern)
        else:
            filter_p = r".*_B.*.jp2$|.*_SCL*.jp2$"

        gs.debug("Filter: {}".format(filter_p), 1)
        self.files = self._filter(filter_p, force_unzip=not flags["n"])

    """
    No longer used
    @staticmethod
    def _read_zip_file(filepath):
        # scan zip file, return first member (root directory)
        with ZipFile(filepath) as fd:
            file_list = fd.namelist()

        return file_list
    """

    def _unzip(self, force=False):
        # extract all zip files from input directory
        if options["pattern_file"]:
            filter_f = "*" + options["pattern_file"] + "*.zip"
        else:
            filter_f = "*.zip"

        input_files = glob.glob(os.path.join(self.input_dir, filter_f))
        filter_s = filter_f.replace(".zip", ".SAFE")
        unziped_files = glob.glob(
            os.path.join(self.unzip_dir, filter_s), recursive=False
        )
        if len(unziped_files) > 0:
            unziped_files = [os.path.basename(safe) for safe in unziped_files]
        for filepath in input_files:
            safe = os.path.basename(filepath.replace(".zip", ".SAFE"))
            if safe not in unziped_files or force:
                gs.message("Reading <{}>...".format(filepath))

                with ZipFile(filepath) as fd:
                    fd.extractall(path=self.unzip_dir)

                self._dir_list.append(os.path.join(self.unzip_dir, safe))

    def _filter(self, filter_p, force_unzip=False):
        # unzip archives before filtering
        self._unzip(force=force_unzip)

        if options["pattern_file"]:
            filter_f = "*" + options["pattern_file"] + "*.SAFE"
        else:
            filter_f = "*.SAFE"

        pattern = re.compile(filter_p)
        files = []
        safes = glob.glob(os.path.join(self.unzip_dir, filter_f))
        if len(safes) < 1:
            gs.fatal(
                _(
                    "Nothing found to import. Please check input and pattern_file options."
                )
            )

        for safe in safes:
            for rec in os.walk(safe):
                if not rec[-1]:
                    continue

                match = filter(pattern.match, rec[-1])
                if match is None:
                    continue

                for f in match:
                    files.append(os.path.join(rec[0], f))

        return files

    def import_products(self, reproject=False, link=False, override=False):
        self._args = {}
        if link:
            module = "r.external"
            self._args["flags"] = "o" if override else None
        else:
            self._args["memory"] = options["memory"]
            if reproject:
                module = "r.import"
                self._args["resample"] = "bilinear"
                self._args["resolution"] = "value"
                self._args["extent"] = options["extent"]
            else:
                module = "r.in.gdal"
                self._args["flags"] = "o" if override else None
                if options["extent"] == "region":
                    if self._args["flags"]:
                        self._args["flags"] += "r"
                    else:
                        self._args["flags"] = "r"
        for f in self.files:
            if not override and (link or (not link and not reproject)):
                if not self._check_projection(f):
                    gs.fatal(
                        _(
                            "Projection of dataset does not appear to match current location. "
                            "Force reprojecting dataset by -r flag."
                        )
                    )

            self._import_file(f, module, self._args)

    def _check_projection(self, filename):
        try:
            with open(os.devnull) as null:
                gs.run_command(
                    "r.in.gdal", flags="j", input=filename, quiet=True, stderr=null
                )
        except CalledModuleError as e:
            return False

        return True

    def _raster_resolution(self, filename):
        try:
            from osgeo import gdal
        except ImportError as e:
            gs.fatal(_("Flag -r requires GDAL library: {}").format(e))
        dsn = gdal.Open(filename)
        trans = dsn.GetGeoTransform()

        ret = int(trans[1])
        dsn = None

        return ret

    def _raster_epsg(self, filename):
        try:
            from osgeo import gdal, osr
        except ImportError as e:
            gs.fatal(_("Flag -r requires GDAL library: {}").format(e))
        dsn = gdal.Open(filename)

        srs = osr.SpatialReference()
        srs.ImportFromWkt(dsn.GetProjectionRef())

        ret = srs.GetAuthorityCode(None)
        dsn = None

        return ret

    @staticmethod
    def _map_name(filename):
        return os.path.splitext(os.path.basename(filename))[0]

    def _import_file(self, filename, module, args):
        mapname = self._map_name(filename)
        gs.message(_("Processing <{}>...").format(mapname))
        if module == "r.import":
            self._args["resolution_value"] = self._raster_resolution(filename)
        try:
            gs.run_command(module, input=filename, output=mapname, **self._args)
            if gs.raster_info(mapname)["datatype"] in ("FCELL", "DCELL"):
                gs.message("Rounding to integer after reprojection")
                gs.use_temp_region()
                gs.run_command("g.region", raster=mapname)
                gs.run_command(
                    "r.mapcalc",
                    quiet=True,
                    expression="tmp_%s = round(%s)" % (mapname, mapname),
                )
                gs.run_command(
                    "g.rename",
                    quiet=True,
                    overwrite=True,
                    raster="tmp_%s,%s" % (mapname, mapname),
                )
                gs.del_temp_region()
            gs.raster_history(mapname)
        except CalledModuleError as e:
            pass  # error already printed

    def import_cloud_masks(
        self, area_threshold, prob_threshold, output, shadows, reproject
    ):
        try:
            if os.environ["GRASS_OVERWRITE"] == "1":
                overwrite = True
        except Exception as e:
            overwrite = False

        # Import cloud masks for L2A products
        files_L2A = self._filter("MSK_CLDPRB_20m.jp2")

        for f in files_L2A:
            safe_dir = os.path.dirname(f).split(os.path.sep)[-4]
            items = safe_dir.split("_")

            # Define names of final & temporary maps
            map_name = "_".join([items[5], items[2], "MSK", "CLOUDS"])
            clouds_imported = "_".join([items[5], items[2], "cloudprob"])
            clouds_selected = "_".join([items[5], items[2], "clouds_selected"])
            shadows_imported = "_".join([items[5], items[2], "shadows"])
            shadows_selected = "_".join([items[5], items[2], "shadows_selected"])
            mask_selected = "_".join([items[5], items[2], "mask_selected"])
            mask_cleaned = "_".join([items[5], items[2], "mask_cleaned"])

            self._map_list.extend(
                [
                    clouds_imported,
                    clouds_selected,
                    shadows_imported,
                    shadows_selected,
                    mask_selected,
                    mask_cleaned,
                ]
            )

            # check if mask alrady exist
            if gs.find_file(name=map_name, element=output)["file"] and not overwrite:
                gs.message(
                    _(
                        "option <output>: <{}> exists. To overwrite, use the --overwrite flag".format(
                            map_name
                        )
                    )
                )
                continue

            try:
                # Import & Threshold cloud probability layer
                gs.message(
                    _("Importing cloud mask for {}").format(
                        "_".join([items[5], items[2]])
                    )
                )
                if reproject:
                    self._args["resolution_value"] = self._raster_resolution(f)
                    self._args["resample"] = "bilinear"
                    gs.run_command(
                        "r.import", input=f, output=clouds_imported, **self._args
                    )
                else:
                    gs.run_command(
                        "r.in.gdal", input=f, output=clouds_imported, **self._args
                    )
                gs.use_temp_region()
                gs.run_command("g.region", raster=clouds_imported)
                gs.mapcalc(
                    f"{clouds_selected} = if({clouds_imported} >= {prob_threshold}, 1, 0)"
                )
                gs.del_temp_region()

                # Add shadow mask
                if shadows:
                    try:
                        shadow_file = self._filter(
                            "_".join([items[5], items[2], "SCL_20m.jp2"])
                        )
                        if reproject:
                            self._args["resolution_value"] = self._raster_resolution(
                                shadow_file[0]
                            )
                            self._args["resample"] = "nearest"
                            gs.run_command(
                                "r.import",
                                input=shadow_file,
                                output=shadows_imported,
                                **self._args,
                            )
                        else:
                            gs.run_command(
                                "r.in.gdal",
                                input=shadow_file,
                                output=shadows_imported,
                                **self._args,
                            )

                        gs.use_temp_region()
                        gs.run_command("g.region", raster=shadows_imported)
                        gs.mapcalc(
                            f"{shadows_selected} = if({shadows_imported} == 3, 2, 0)"
                        )
                        gs.mapcalc(
                            f"{mask_selected} = max({shadows_selected},{clouds_selected})"
                        )
                        gs.del_temp_region()
                    except Exception as e:
                        gs.warning(
                            _("Unable to import shadows for {}. Error: {}").format(
                                "_".join([items[5], items[2]]), e
                            )
                        )

                else:
                    gs.run_command(
                        "g.rename", quiet=True, raster=(clouds_selected, mask_selected)
                    )

                gs.use_temp_region()
                gs.run_command("g.region", raster=mask_selected)

                # Cleaning small patches
                try:
                    gs.run_command(
                        "r.reclass.area",
                        input=mask_selected,
                        output=mask_cleaned,
                        value=area_threshold,
                        mode="greater",
                    )
                except Exception as e:
                    pass  # error already printed

                # Extract & Label clouds (and shadows)
                gs.run_command("r.null", map=mask_cleaned, setnull="0")

                labels = ["1:clouds", "2:shadows"]
                labelling = gs.feed_command(
                    "r.category", map=mask_cleaned, separator=":", rules="-"
                )
                labelling.stdin.write("\n".join(labels).encode())
                labelling.stdin.close()
                labelling.wait()

                info_stats = gs.parse_command("r.stats", input=mask_cleaned, flags="p")

                # Create final cloud (and shadow) mask & display areal statistics
                if output == "vector":
                    gs.run_command(
                        "r.to.vect",
                        input=mask_cleaned,
                        output=map_name,
                        type="area",
                        flags="s",
                    )
                    colours = ["1 230:230:230", "2 60:60:60"]
                    colourise = gs.feed_command(
                        "v.colors",
                        map=map_name,
                        use="attr",
                        column="value",
                        rules="-",
                        quiet=True,
                    )
                    colourise.stdin.write("\n".join(colours).encode())
                    colourise.stdin.close()
                    colourise.wait()
                    gs.vector_history(map_name)

                else:
                    gs.run_command(
                        "g.rename", quiet=True, raster=(mask_cleaned, map_name)
                    )
                    colours = ["1 230:230:230", "2 60:60:60"]
                    colourise = gs.feed_command(
                        "r.colors", map=map_name, rules="-", quiet=True
                    )
                    colourise.stdin.write("\n".join(colours).encode())
                    colourise.stdin.close()
                    colourise.wait()
                    gs.raster_history(map_name)

                gs.message(
                    _("Areal proportion of masked clouds:{}").format(
                        [key.split()[1] for key in info_stats][0]
                    )
                )
                if shadows:
                    if len(info_stats) > 2:
                        gs.message(
                            _("Areal proportion of masked shadows:{}").format(
                                [key.split()[1] for key in info_stats][1]
                            )
                        )
                    else:
                        gs.message(_("Areal proportion of masked shadows:0%"))

                gs.del_temp_region()

            except Exception as e:
                gs.del_temp_region()
                gs.warning(
                    _("Unable to import cloud mask for {}. Error: {}").format(
                        "_".join([items[5], items[2]]), e
                    )
                )

        # Import of simplified cloud masks for Level-1C products
        all_files = self._filter("MSK_CLOUDS_B00.gml")
        files_L1C = []

        for f in all_files:
            safe_dir = os.path.dirname(f).split(os.path.sep)[-4]
            if safe_dir not in [
                os.path.dirname(file).split(os.path.sep)[-4] for file in files_L2A
            ]:
                files_L1C.append(f)

        if len(files_L1C) > 0:
            from osgeo import ogr

            for f in files_L1C:
                safe_dir = os.path.dirname(f).split(os.path.sep)[-4]
                items = safe_dir.split("_")

                # Define names of final & temporary maps
                map_name = "_".join([items[5], items[2], "MSK", "CLOUDS"])
                clouds_imported = "_".join([items[5], items[2], "clouds_imported"])
                mask_cleaned = "_".join([items[5], items[2], "mask_cleaned"])
                self._map_list.extend([clouds_imported, mask_cleaned])

                # check if mask alrady exist
                if (
                    gs.find_file(name=map_name, element=output)["file"]
                    and not overwrite
                ):
                    gs.fatal(
                        _(
                            "option <output>: <{}> exists. To overwrite, use the --overwrite flag".format(
                                map_name
                            )
                        )
                    )
                    continue

                # check if any OGR layer
                dsn = ogr.Open(f)
                layer_count = dsn.GetLayerCount()
                dsn.Destroy()
                if layer_count < 1:
                    gs.info("No clouds layer found in <{}>. Import skipped".format(f))
                    continue

                # Import cloud layer
                try:
                    gs.message(
                        _("Importing cloud mask for {}").format(
                            "_".join([items[5], items[2]])
                        )
                    )
                    gs.run_command(
                        "v.import",
                        input=f,
                        output=clouds_imported,
                        extent=options["extent"],
                        flags="o" if flags["o"] else None,
                        quiet=True,
                    )

                    gs.use_temp_region()
                    gs.run_command("g.region", vector=clouds_imported)

                    # Cleaning small patches
                    gs.run_command(
                        "v.clean",
                        input=clouds_imported,
                        output=mask_cleaned,
                        tool="rmarea",
                        threshold=area_threshold,
                    )

                    # Calculating info stats
                    gs.run_command(
                        "v.db.addcolumn", map=mask_cleaned, columns="value_num INT"
                    )
                    gs.run_command(
                        "v.db.update", map=mask_cleaned, column="value_num", value=1
                    )
                    gs.run_command(
                        "v.to.rast",
                        input=mask_cleaned,
                        output=mask_cleaned,
                        use="attr",
                        attribute_column="value_num",
                        quiet=True,
                    )
                    info_stats = gs.parse_command(
                        "r.stats", input=mask_cleaned, flags="p"
                    )

                    # Create final cloud mask output
                    if output == "vector":
                        gs.run_command(
                            "g.rename", quiet=True, vector=(mask_cleaned, map_name)
                        )
                        colours = ["1 230:230:230"]
                        colourise = gs.feed_command(
                            "v.colors",
                            map=map_name,
                            use="attr",
                            column="value_num",
                            rules="-",
                            quiet=True,
                        )
                        colourise.stdin.write("\n".join(colours).encode())
                        colourise.stdin.close()
                        colourise.wait()
                        gs.vector_history(map_name)

                    else:
                        gs.run_command(
                            "g.rename", quiet=True, raster=(mask_cleaned, map_name)
                        )
                        colours = ["1 230:230:230"]
                        colourise = gs.feed_command(
                            "r.colors", map=map_name, rules="-", quiet=True
                        )
                        colourise.stdin.write("\n".join(colours).encode())
                        colourise.stdin.close()
                        colourise.wait()
                        gs.raster_history(map_name)

                    # Display messages & statistics
                    if shadows:
                        gs.warning(
                            _("Level1 product: No shadow mask for {}").format(
                                "_".join([items[5], items[2]])
                            )
                        )

                    gs.message(
                        _("Areal proportion of masked clouds:{}").format(
                            [key.split()[1] for key in info_stats][0]
                        )
                    )

                    gs.del_temp_region()

                except Exception as e:
                    gs.del_temp_region()
                    gs.warning(
                        _("Unable to import cloud mask for {}. Error: {}").format(
                            "_".join([items[5], items[2]]), e
                        )
                    )

    def print_products(self):
        for f in self.files:
            sys.stdout.write(
                "{} {} (EPSG: {}){}".format(
                    f,
                    "1" if self._check_projection(f) else "0",
                    self._raster_epsg(f),
                    os.linesep,
                )
            )

    @staticmethod
    def _parse_mtd_file(mtd_file):
        # Lazy import
        import numpy as np

        try:
            from xml.etree import ElementTree
            from datetime import datetime
        except ImportError as e:
            gs.fatal(_("Unable to parse metadata file. {}").format(e))

        meta = {}
        meta["timestamp"] = None
        with io.open(mtd_file, encoding="utf-8") as fd:
            root = ElementTree.fromstring(fd.read())
            nsPrefix = root.tag[: root.tag.index("}") + 1]
            nsDict = {"n1": nsPrefix[1:-1]}
            node = root.find("n1:General_Info", nsDict)
            if node is not None:
                tile_id = (
                    node.find("TILE_ID").text
                    if node.find("TILE_ID") is not None
                    else ""
                )
                if not tile_id.startswith("S2"):
                    gs.fatal(
                        _("Register file can be created only for Sentinel-2 data.")
                    )

                meta["SATELLITE"] = tile_id.split("_")[0]

                # get timestamp
                ts_str = node.find("SENSING_TIME", nsDict).text
                meta["timestamp"] = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%S.%fZ")

            # Get Quality metadata
            node = root.find("n1:Quality_Indicators_Info", nsDict)
            image_qi = node.find("Image_Content_QI")
            if image_qi:
                for qi in list(image_qi):
                    meta[qi.tag] = qi.text

            # Get Geometric metadata
            node = root.find("n1:Geometric_Info", nsDict)
            tile_angles = node.find("Tile_Angles")
            if tile_angles is not None:
                # In L1C products it can be necessary to compute angles from grid
                va_list = tile_angles.find("Mean_Viewing_Incidence_Angle_List")
                if va_list is not None:
                    for it in list(va_list):
                        band = it.attrib["bandId"]
                        for i in list(it):
                            if "ZENITH_ANGLE" in i.tag or "AZIMUTH_ANGLE" in i.tag:
                                meta[i.tag + "_" + band] = i.text
                    sa_grid = tile_angles.find("Sun_Angles_Grid")
                    if sa_grid is not None:
                        for ssn in list(sa_grid):
                            if ssn.tag == "Zenith":
                                for sssn in list(ssn):
                                    if sssn.tag == "Values_List":
                                        mean_zenith = np.mean(
                                            np.array(
                                                [
                                                    np.array(
                                                        ssssn.text.split(" "),
                                                        dtype=np.float,
                                                    )
                                                    for ssssn in list(sssn)
                                                ],
                                                dtype=np.float,
                                            )
                                        )
                                        meta["MEAN_SUN_ZENITH_GRID_ANGLE"] = mean_zenith
                            elif ssn.tag == "Azimuth":
                                for sssn in list(ssn):
                                    if sssn.tag == "Values_List":
                                        mean_azimuth = np.mean(
                                            np.array(
                                                [
                                                    np.array(
                                                        ssssn.text.split(" "),
                                                        dtype=np.float,
                                                    )
                                                    for ssssn in list(sssn)
                                                ],
                                                dtype=np.float,
                                            )
                                        )
                                        meta[
                                            "MEAN_SUN_AZIMUTH_GRID_ANGLE"
                                        ] = mean_azimuth
                    sa_mean = tile_angles.find("Mean_Sun_Angle")
                    if sa_mean is not None:
                        for it in list(sa_mean):
                            if it.tag == "ZENITH_ANGLE" or it.tag == "AZIMUTH_ANGLE":
                                meta["MEAN_SUN_" + it.tag] = it.text
            else:
                gs.warning("Unable to extract tile angles from <{}>".format(mtd_file))
        if not meta["timestamp"]:
            gs.error(_("Unable to determine timestamp from <{}>").format(mtd_file))

        return meta

    @staticmethod
    def _ip_from_path(path):
        return os.path.basename(path[: path.find(".SAFE")])

    def write_metadata(self):
        gs.message(_("Writing metadata to maps..."))
        ip_meta = {}
        for mtd_file in self._filter("MTD_TL.xml"):
            ip = self._ip_from_path(mtd_file)
            ip_meta[ip] = self._parse_mtd_file(mtd_file)

        if not ip_meta:
            gs.warning(_("Unable to determine timestamps. No metadata file found"))

        for img_file in self.files:
            map_name = self._map_name(img_file)
            ip = self._ip_from_path(img_file)
            meta = ip_meta[ip]
            if meta:
                bn = map_name.split("_")[2].lstrip("B").rstrip("A")
                if bn.isnumeric():
                    bn = int(bn)
                else:
                    continue

                timestamp = meta["timestamp"]
                timestamp_str = timestamp.strftime("%d %b %Y %H:%M:%S.%f")
                descr_list = []
                for dkey in meta.keys():
                    if dkey != "timestamp":
                        if "TH_ANGLE_" in dkey:
                            if dkey.endswith("TH_ANGLE_{}".format(bn)):
                                descr_list.append("{}={}".format(dkey, meta[dkey]))
                        else:
                            descr_list.append("{}={}".format(dkey, meta[dkey]))
                descr = "\n".join(descr_list)
                bands = (
                    gs.read_command(
                        "g.list",
                        type="raster",
                        mapset=".",
                        pattern="{}*".format(map_name),
                    )
                    .rstrip("\n")
                    .split("\n")
                )

                descr_dict = {dl.split("=")[0]: dl.split("=")[1] for dl in descr_list}
                env = gs.gisenv()
                json_standard_folder = os.path.join(
                    env["GISDBASE"], env["LOCATION_NAME"], env["MAPSET"], "cell_misc"
                )
                if flags["j"] and not os.path.isdir(json_standard_folder):
                    os.makedirs(json_standard_folder)
                for band in bands:
                    gs.run_command(
                        "r.support",
                        map=map_name,
                        source1=ip,
                        source2=img_file,
                        history=descr,
                    )
                    gs.run_command("r.timestamp", map=map_name, date=timestamp_str)
                    if flags["j"]:
                        metadatajson = os.path.join(
                            json_standard_folder, map_name, "description.json"
                        )
                    elif options["metadata"]:
                        metadatajson = os.path.join(
                            options["metadata"], map_name, "description.json"
                        )
                    if flags["j"] or options["metadata"]:
                        if not os.path.isdir(os.path.dirname(metadatajson)):
                            os.makedirs(os.path.dirname(metadatajson))
                        with open(metadatajson, "w") as outfile:
                            json.dump(descr_dict, outfile)

    def create_register_file(self, filename):
        gs.message(_("Creating register file <{}>...").format(filename))
        ip_timestamp = {}
        for mtd_file in self._filter("MTD_TL.xml"):
            ip = self._ip_from_path(mtd_file)
            ip_timestamp[ip] = self._parse_mtd_file(mtd_file)["timestamp"]

        if not ip_timestamp:
            gs.warning(_("Unable to determine timestamps. No metadata file found"))
        has_band_ref = float(gs.version()["version"][0:3]) >= 7.9
        sep = "|"
        with open(filename, "w") as fd:
            for img_file in self.files:
                map_name = self._map_name(img_file)
                ip = self._ip_from_path(img_file)
                timestamp = ip_timestamp[ip]
                if timestamp:
                    timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")
                else:
                    timestamp_str = ""
                fd.write(
                    "{img}{sep}{ts}".format(img=map_name, sep=sep, ts=timestamp_str)
                )
                if has_band_ref:
                    try:
                        band_ref = re.match(
                            r".*_B([0-18][0-9A]).*|.*_([S][C][L])_.*", map_name
                        ).groups()
                        band_ref = band_ref[0] if band_ref[0] else band_ref[1]
                        band_ref = band_ref.lstrip("0")
                    except AttributeError:
                        gs.warning(
                            _("Unable to determine band reference for <{}>").format(
                                map_name
                            )
                        )
                        continue
                    fd.write("{sep}{br}".format(sep=sep, br="S2_{}".format(band_ref)))
                fd.write(os.linesep)


def main():
    importer = SentinelImporter(options["input"], options["unzip_dir"])

    importer.filter(options["pattern"])
    if len(importer.files) < 1:
        gs.fatal(_("Nothing found to import. Please check input and pattern options."))

    if flags["p"]:
        if options["register_output"]:
            gs.warning(
                _(
                    "Register output file name is not created " "when -{} flag given"
                ).format("p")
            )
        importer.print_products()
        return 0

    importer.import_products(flags["r"], flags["l"], flags["o"])
    importer.write_metadata()

    if flags["c"]:
        # import cloud mask if requested
        importer.import_cloud_masks(
            options["cloud_area_threshold"],
            options["cloud_probability_threshold"],
            options["cloud_output"],
            flags["s"],
            flags["r"],
        )

    if options["register_output"]:
        # create t.register file if requested
        importer.create_register_file(options["register_output"])

    return 0


if __name__ == "__main__":
    options, flags = gs.parser()
    sys.exit(main())
