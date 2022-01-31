#!/usr/bin/env python
"""
MODULE:    v.in.wfs2

AUTHOR(S): Stepan Turek <stepan.turek AT seznam.cz>

PURPOSE:   Downloads and imports data from WFS server.

COPYRIGHT: (C) 2012 Stepan Turek, and by the GRASS Development Team

This program is free software under the GNU General Public License
(>=v2). Read the file COPYING that comes with GRASS for details.
"""

# %module
# % description: Downloads and imports data from WFS server.
# % keyword: vector
# % keyword: import
# % keyword: wfs
# %end

# %option
# % key: url
# % type: string
# % description:URL of WFS server
# % required: yes
# %end

# %option
# % key: layers
# % type: string
# % description: Layers to request from server
# % multiple: yes
# % required: yes
# %end

# %option G_OPT_V_OUTPUT
# % description: Name for output vector map
# %end


# %option
# % key: srs
# % type: integer
# % description: EPSG number of source projection for request
# % answer:4326
# % guisection: Request properties
# %end

# %flag
# % key: r
# % description: Restrict fetch to features which touch the region
# % guisection: Request properties
# %end

# %option
# % key: region
# % type: string
# % description: Named region to request data for (only with r flag)
# % guisection: Request properties
# %end

# %option
# % key: wfs_version
# % type:string
# % description:WFS standard
# % options:1.1.0, 1.0.0
# % answer:1.1.0
# % guisection: Request properties
# %end

# %option
# % key: maximum_features
# % type: integer
# % label: Maximum number of features to download
# % description: (default: unlimited)
# % guisection: Request properties
# %end

# %option
# % key: urlparams
# % type:string
# % description: Addition query parameters for server (only with GRASS driver)
# % guisection: Request properties
# %end

# %flag
# % key: c
# % description: Get capabilities
# % guisection: Request properties
# % suppress_required: yes
# %end

# %option
# % key: driver
# % type:string
# % description:WFS driver
# % options:WFS_GRASS, WFS_OSWLib
# % answer:WFS_GRASS
# %end


import os
import sys

sys.path.insert(1, os.path.join(os.path.dirname(sys.path[0]), "etc", "v.in.wfs2"))

import grass.script as grass


def main():

    if options["driver"] == "WFS_GRASS":
        grass.debug("Using GRASS driver")
        from wfs_drv import WFSDrv

        wfs = WFSDrv()
    else:
        grass.debug("Using OSWLib driver")
        from wfs_owslib_drv import WFSOwsLibDrv

        wfs = WFSOwsLibDrv()

    if flags["c"]:
        wfs.GetCapabilities(options)
    else:
        wfs.GetFeature(options, flags)

    return 0


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
