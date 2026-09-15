#!/usr/bin/env python
"""
MODULE:    r.in.ogc.coverages

AUTHOR(S): Luca Delucchi <lucadeluge AT gmail.com>

PURPOSE:   Downloads and imports data from OGC API Coverages server.

COPYRIGHT: (C) 2021 Luca Delucchi, and by the GRASS Development Team

This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.
"""

# %module
# % description: Downloads and imports data from OGC API Coverages server.
# % keyword: raster
# % keyword: import
# % keyword: ogc
# % keyword: coverages
# %end

# %option
# % key: url
# % type: string
# % description: URL of OGC API Coverages server
# % required: yes
# %end

# %option
# % key: layer
# % type: string
# % description: Layer to request from server
# %end

# %option G_OPT_R_OUTPUT
# % description: Name for output raster map
# % required: no
# %end

# %flag
# % key: l
# % description: Get layers from the server
# %end
import sys
import grass.script as gs


def main():
    try:
        from owslib.ogcapi.coverages import Coverages
    except:
        gs.fatal(
            _(
                "OSWLib was not found. Install OSWLib (https://github.com/geopython/OWSLib)."
            )
        )

    feats = Coverages(options["url"])
    collections = feats.coverages()
    if flags["l"]:
        for coll in collections:
            print("{}".format(coll))
        return
    if not options["layer"]:
        gs.fatal(
            _("Required parameter <layer> not set: (Name for input vector map layer)")
        )
    elif options["layer"] not in collections:
        gs.fatal(_("Layer {} is not a Coverage layer"))

    if not options["output"]:
        gs.fatal(_("Required parameter <output> not set: (Name for output vector map)"))
    try:
        layer = feats.coverage(options["layer"])
    except Exception as e:
        gs.fatal(
            _("Problem retrieving data from the server. The error was: {}").format(e)
        )
    tmpfile = gs.tempfile()
    with open(tmpfile, "wb") as f:
        f.write(layer.getbuffer())
    gs.run_command("r.import", input=tmpfile, output=options["output"])


if __name__ == "__main__":
    options, flags = gs.parser()
    sys.exit(main())
