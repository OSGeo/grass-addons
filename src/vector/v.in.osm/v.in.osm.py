#!/usr/bin/env python
"""
MODULE:    v.in.osm

AUTHOR(S): Stepan Turek <stepan.turek AT seznam.cz>

PURPOSE:   Imports OpenStreetMap data into GRASS GIS.

COPYRIGHT: (C) 2016 Stepan Turek, and by the GRASS Development Team
            - list layers (-l) support and minor tweaks for OSM .pbf import by Markus Neteler

This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.
"""

# %module
# % description: Imports OpenStreetMap data into GRASS GIS.
# % keyword: osm
# % keyword: vector
# % keyword: import
# %end

# %option G_OPT_F_BIN_INPUT
# % description: Table file to be imported or DB connection string
# %end

# %option G_OPT_V_OUTPUT
# % description: Name for output vector map
# % required: no
# %end

# %option G_OPT_DB_WHERE
# %end

# %option G_OPT_V_TYPE
# % description: Name for output vector map
# % options: point,line,boundary,centroid
# % answer: point,line,boundary,centroid
# % required: no
# %end

# %option G_OPT_DB_TABLE
# %end

# %flag
# % key: o
# % label: Override projection check (use current project's projection)
# % description: Assume that the dataset has the same projection as the current project; without this flag the data are reprojected to the current project's CRS
# %end

# %flag
# % key: l
# % label: List available OGR layers in data source and exit
# %end

import os
import sys
import atexit
from grass.script.utils import try_rmdir
import grass.script as gs
from grass.exceptions import CalledModuleError


class OsmImporter:
    def __init__(self):
        self.tmp_vects = []
        self.tmp_files = []
        self.tmp_opid = str(os.getpid())

    def cleanup(self):
        for tmp in self.tmp_vects:
            gs.run_command("g.remove", flags="f", type="vector", name=tmp, quiet=True)
        for tmp in self.tmp_files:
            if os.path.exists(tmp):
                os.remove(tmp)

    def _getTmpName(self, name):
        return name + "_" + self.tmp_opid

    def getNewTmp(self, name):
        tmp = self._getTmpName(name)

        self.tmp_vects.append(tmp)

        return tmp

    def getTmp(self, name):
        return self._getTmpName(name)

    def _layerIsPolygon(self, input_, table):
        """Return True if the OGR layer holds (multi)polygons."""
        from osgeo import ogr

        ogr.UseExceptions()
        try:
            ds = ogr.Open(input_)
            layer = ds.GetLayerByName(table)
        except RuntimeError as e:
            gs.fatal(_("Unable to open <{}>: {}").format(input_, e))
        if layer is None:
            gs.fatal(
                _("Layer <{}> not found in <{}> (list layers with -l)").format(
                    table, input_
                )
            )
        geom_type = ogr.GT_Flatten(layer.GetGeomType())
        return geom_type in (ogr.wkbPolygon, ogr.wkbMultiPolygon)

    def _projectWkt(self):
        """Return the CRS of the current project as WKT."""
        try:
            return gs.read_command("g.proj", flags="p", format="wkt")
        except CalledModuleError:
            # GRASS versions without the format option.
            return gs.read_command("g.proj", flags="wf")

    def _reproject(self, input_, table, where):
        """Extract the layer (with the attribute filter) into a temporary
        GeoPackage in the current project's CRS; return its path."""
        from osgeo import gdal

        gdal.UseExceptions()
        gpkg = gs.tempfile(create=False) + ".gpkg"
        self.tmp_files.append(gpkg)
        try:
            gdal.VectorTranslate(
                gpkg,
                input_,
                format="GPKG",
                layers=[table],
                layerName=table,
                where=where or None,
                dstSRS=self._projectWkt(),
                reproject=True,
            )
        except RuntimeError as e:
            gs.fatal(_("Reprojection of layer <{}> failed: {}").format(table, e))
        return gpkg

    def main(self, options, flags):
        # just get the layer names
        if flags["l"]:
            try:
                gs.run_command(
                    "v.in.ogr", quiet=True, input=options["input"], flags="l"
                )
                sys.exit()
            except CalledModuleError:
                gs.fatal(_("%s failed") % "v.in.ogr")
        else:
            if not options["table"]:
                gs.fatal(_("Required parameter <%s> not set") % "table")
            if not options["output"]:
                gs.fatal(_("Required parameter <%s> not set") % "output")

        # https://gdal.org/drivers/vector/osm.html
        os.environ["OGR_INTERLEAVED_READING"] = "YES"

        # Keep only the feature types matching the layer geometry: v.in.ogr
        # would otherwise turn polygon rings into lines, or linestrings into
        # boundaries.
        types = options["type"].split(",")
        is_polygon = self._layerIsPolygon(options["input"], options["table"])
        wanted = ("boundary", "centroid") if is_polygon else ("point", "line")
        types = [t for t in types if t in wanted]
        if not types:
            gs.fatal(
                _("Layer <{}> contains {}: <type> must include {}").format(
                    options["table"],
                    _("polygons") if is_polygon else _("points or lines"),
                    " and/or ".join(wanted),
                )
            )

        source, where = options["input"], options["where"]
        if not flags["o"]:
            gs.message(
                _("Reprojecting <{}> to the current project...").format(
                    options["table"]
                )
            )
            source = self._reproject(options["input"], options["table"], where)
            where = ""

        # process
        try:
            gs.debug("Step 1/3: v.in.ogr...", 2)
            gs.run_command(
                "v.in.ogr",
                quiet=True,
                input=source,
                output=options["output"] if is_polygon else self.getNewTmp("ogr"),
                layer=options["table"],
                where=where,
                type=",".join(types),
                flags="o" if flags["o"] else None,
            )
        except CalledModuleError:
            gs.fatal(_("%s failed") % "v.in.ogr")

        if is_polygon:
            return

        try:
            gs.debug("Step 2/3: v.split...", 2)
            gs.run_command(
                "v.split",
                quiet=True,
                input=self.getTmp("ogr"),
                output=self.getNewTmp("split"),
                vertices=2,
            )
        except CalledModuleError:
            gs.fatal(_("%s failed") % "v.split")

        try:
            gs.debug("Step 3/3: v.build.polylines...", 2)
            gs.run_command(
                "v.build.polylines",
                quiet=True,
                input=self.getNewTmp("split"),
                output=options["output"],
                cats="same",
            )
        except CalledModuleError:
            gs.fatal(_("%s failed") % "v.build.polylines")


if __name__ == "__main__":
    options, flags = gs.parser()

    osm_imp = OsmImporter()
    atexit.register(osm_imp.cleanup)

    osm_imp.main(options, flags)
