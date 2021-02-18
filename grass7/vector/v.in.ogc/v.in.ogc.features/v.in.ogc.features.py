#!/usr/bin/env python
"""
MODULE:    v.in.ogc.features

AUTHOR(S): Luca Delucchi <lucadeluge AT gmail.com>

PURPOSE:   Downloads and imports data from OGC API Features server.

COPYRIGHT: (C) 2021 Luca Delucchi, and by the GRASS Development Team

This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.
"""

#%module
#% description: Downloads and imports data from OGC API Features server.
#% keyword: vector
#% keyword: import
#% keyword: ogc
#% keyword: features
#%end

#%option
#% key: url
#% type: string
#% description: URL of OGC API Features server
#% required: yes
#%end

#%option
#% key: layer
#% type: string
#% description: Layer to request from server
#%end

#%option G_OPT_V_OUTPUT
#% description: Name for output vector map
#% required: no
#%end

#%flag
#% key: l
#% description: Get layers from the server
#%end
import sys
import json
import grass.script as grass


def main():
    try:
        from owslib.ogcapi.features import Features
    except:
        grass.fatal(
            _(
                "OSWLib can not be found. Install OSWLib (http://geopython.github.com/OWSLib/)."
            )
        )

    feats = Features(options["url"])
    if flags["l"]:
        collections = feats.collections()
        for coll in collections["collections"]:
            if "layerDataType" in coll.keys():
                colltype = coll["layerDataType"]
            elif "itemType" in coll.keys():
                colltype = coll["itemType"]
            if colltype in ["Feature", "Vector"]:
                try:
                    print("{}: {}".format(coll["id"], coll["title"]))
                except:
                    print("{}: {}".format(coll["name"], coll["title"]))
        return
    if not options["layer"]:
        grass.fatal(
            _("Required parameter <layer> not set:" "(Name for input vector map layer)")
        )
    if not options["output"]:
        grass.fatal(
            _("Required parameter <output> not set:" "(Name for output vector map)")
        )
    coll = feats.collection(options["layer"])
    if "layerDataType" in coll.keys():
        colltype = coll["layerDataType"]
    elif "itemType" in coll.keys():
        colltype = coll["itemType"]
    if colltype not in ["Feature", "Vector"]:
        grass.warning("The layer '{}' could not be a Feature object")
    try:
        layer = feats.collection_items(options["layer"])
    except Exception as e:
        grass.fatal(
            _("Problem retriving data from the server. " "The error was: {}".format(e))
        )
    tmpfile = grass.tempfile()
    with open(tmpfile, "w") as f:
        json.dump(layer, f, indent=4)
    grass.run_command("v.import", input=tmpfile, output=options["output"])


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
