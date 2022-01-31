#!/usr/bin/env python
############################################################################
#
# MODULE:       v.build.pg
# AUTHOR(S):    Martin Landa
# PURPOSE:      Builds PostGIS topology for PG-linked vector map.
# COPYRIGHT:    (C) 2012 by Martin Landa, and the GRASS Development Team
#
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################

# %module
# % description: Builds PostGIS topology for vector map linked via v.external.
# % keyword: vector
# % keyword: external
# % keyword: PostGIS
# % keyword: topology
# % overwrite: yes
# %end
# %option G_OPT_V_MAP
# % description:
# %end
# %option
# % key: topo_schema
# % label: Name of schema where to build PostGIS topology
# % description: Default: topo_<map>
# % key_desc: name
# %end
# %option
# % key: topo_column
# % description: Name of topology column
# % key_desc: name
# % required: yes
# % answer: topo
# %end
# %option
# % key: tolerance
# % description: Tolerance to snap input geometry to existing primitives
# % type: double
# % answer: 1
# %end
# %flag
# % key: p
# % description: Don't execute SQL statements, just print them and exit
# %end

import os
import sys

import grass.script as grass
from grass.exceptions import CalledModuleError


def execute(sql, msg=None, useSelect=True):
    if useSelect:
        cmd = "select"
    else:
        cmd = "execute"

    if flags["p"]:
        sys.stdout.write("\n%s\n\n" % sql)
        return

    try:
        grass.run_command("db.%s" % cmd, sql=sql, **pg_conn)
    except CalledModuleError:
        if msg:
            grass.fatal(msg)
        else:
            grass.fatal(_("Unable to build PostGIS topology"))


def main():
    vmap = options["map"]
    curr_mapset = grass.gisenv()["MAPSET"]
    mapset = grass.find_file(name=vmap, element="vector")["mapset"]

    # check if map exists in the current mapset
    if not mapset:
        grass.fatal(_("Vector map <%s> not found") % vmap)
    if mapset != curr_mapset:
        grass.fatal(_("Vector map <%s> not found in the current mapset") % vmap)

    # check for format
    vInfo = grass.vector_info(vmap)
    if vInfo["format"] != "PostGIS,PostgreSQL":
        grass.fatal(_("Vector map <%s> is not a PG-link") % vmap)

    # default connection
    global pg_conn
    pg_conn = {"driver": "pg", "database": vInfo["pg_dbname"]}

    # default topo schema
    if not options["topo_schema"]:
        options["topo_schema"] = "topo_%s" % options["map"]

    # check if topology schema already exists
    topo_found = False
    ret = grass.db_select(
        sql="SELECT COUNT(*) FROM topology.topology "
        "WHERE name = '%s'" % options["topo_schema"],
        **pg_conn
    )

    if not ret or int(ret[0][0]) == 1:
        topo_found = True

    if topo_found:
        if int(os.getenv("GRASS_OVERWRITE", "0")) == 1:
            # -> overwrite
            grass.warning(
                _("Topology schema <%s> already exists and will be overwritten")
                % options["topo_schema"]
            )
        else:
            grass.fatal(
                _("option <%s>: <%s> exists.") % ("topo_schema", options["topo_schema"])
            )

        # drop topo schema if exists
        execute(
            sql="SELECT topology.DropTopology('%s')" % options["topo_schema"],
            msg=_("Unable to remove topology schema"),
        )

    # create topo schema
    schema, table = vInfo["pg_table"].split(".")
    grass.message(_("Creating new topology schema..."))
    execute(
        "SELECT topology.createtopology('%s', find_srid('%s', '%s', '%s'), %s)"
        % (
            options["topo_schema"],
            schema,
            table,
            vInfo["geometry_column"],
            options["tolerance"],
        )
    )

    # add topo column to the feature table
    grass.message(_("Adding new topology column..."))
    execute(
        "SELECT topology.AddTopoGeometryColumn('%s', '%s', '%s', '%s', '%s')"
        % (
            options["topo_schema"],
            schema,
            table,
            options["topo_column"],
            vInfo["feature_type"],
        )
    )

    # build topology
    grass.message(_("Building PostGIS topology..."))
    execute(
        "UPDATE %s.%s SET %s = topology.toTopoGeom(%s, '%s', 1, %s)"
        % (
            schema,
            table,
            options["topo_column"],
            vInfo["geometry_column"],
            options["topo_schema"],
            options["tolerance"],
        ),
        useSelect=False,
    )

    # report summary
    execute("SELECT topology.TopologySummary('%s')" % options["topo_schema"])

    return 0


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
