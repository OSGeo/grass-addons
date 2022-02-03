#!/usr/bin/env python

"""
MODULE:    i.pysptools.unmix

AUTHOR(S): Stefan Blumentrath < stefan.blumentrath AT nina.no>
           Zofie Cimburova < zofie.cimburova AT nina.no>

PURPOSE:   Extract endmembers from imagery group and perform spectral unmixing
           using pysptools
           Depends on pysptools and scikit-learn

COPYRIGHT: (C) 2018 by the GRASS GIS Development Team,
                           Norwegian Institute for Nature Research (NINA)

           This program is free software under the GNU General Public
           License (>=v2). Read the file COPYING that comes with GRASS
           for details.
"""

# %module
# % description: Extract endmembers from imagery group and perform spectral unmixing using pysptools
# % keyword: imagery
# % keyword: endmember
# % keyword: spectral unmixing
# %end

# %option G_OPT_I_GROUP
# % key: input
# % description: Input imagery group
# % required : yes
# %end

# %option G_OPT_F_OUTPUT
# % key: output
# % guisection: output
# % description: Text file storing endmember information for i.spec.unmix
# % required : no
# %end

# %option
# % key: prefix
# % description: Prefix for resulting raster maps
# % guisection: output
# % required : no
# %end

# %option G_OPT_V_OUTPUT
# % key: endmembers
# % description: Vector map representing identified endmembers
# % guisection: output
# % required : no
# %end

# %option
# % key: endmember_n
# % type: integer
# % description: Number of endmembers to identify
# % required: yes
# %end

# %option
# % key: extraction_method
# % type: string
# % description: Method for endmember extraction
# % options: FIPPI,PPI,NFINDR
# % answer: NFINDR
# %end

# %option
# % key: unmixing_method
# % type: string
# % description: Algorithm for spectral unmixing
# % options: FCLS,UCLS,NNLS
# % answer: FCLS
# %end

# %option
# % key: maxit
# % type: integer
# % description: Maximal number of iterations for endmember extraction (default=3*number of bands)
# % required: no
# %end

# %flag
# % key: n
# % description: Do not use Automatic Target Generation Process (ATGP)
# %end

# %rules
# % required: output,prefix
# %end

import os
import sys
import numpy as np
from grass.pygrass import raster as r
from grass.pygrass.utils import getenv
import grass.script as gs

if "GISBASE" not in os.environ.keys():
    gs.message("You must be in GRASS GIS to run this program.")
    sys.exit(1)


def get_rastertype(raster):

    if not isinstance(raster[0, 0], np.float32) and not isinstance(
        raster[0, 0], np.float64
    ):
        map_type = u"INTEGER"
    else:
        map_type = u"REAL"

    return map_type


def mask_rasternd(raster):
    if not isinstance(raster[0, 0], np.float32) and not isinstance(
        raster[0, 0], np.float64
    ):
        mask = raster != -2147483648
    else:
        mask = np.isnan(raster) == False

    return mask


def main():

    try:
        import pysptools.eea as eea
    except ImportError:
        gs.fatal(
            _(
                "Cannot import pysptools \
                      (https://pypi.python.org/pypi/pysptools) library."
                " Please install it (pip install pysptools)"
                " or ensure that it is on path"
                " (use PYTHONPATH variable)."
            )
        )

    try:
        # sklearn is a dependency of used pysptools functionality
        import sklearn
    except ImportError:
        gs.fatal(
            _(
                "Cannot import sklearn \
                      (https://pypi.python.org/pypi/scikit-learn) library."
                " Please install it (pip install scikit-learn)"
                " or ensure that it is on path"
                " (use PYTHONPATH variable)."
            )
        )

    try:
        from cvxopt import solvers, matrix
    except ImportError:
        gs.fatal(
            _(
                "Cannot import cvxopt \
                      (https://pypi.python.org/pypi/cvxopt) library."
                " Please install it (pip install cvxopt)"
                " or ensure that it is on path"
                " (use PYTHONPATH variable)."
            )
        )

    # Parse input options
    input = options["input"]
    output = options["output"]
    prefix = options["prefix"]
    endmember_n = int(options["endmember_n"])
    endmembers = options["endmembers"]
    if options["maxit"]:
        maxit = options["maxit"]
    else:
        maxit = 0
    extraction_method = options["extraction_method"]
    unmixing_method = options["unmixing_method"]
    atgp_init = True if not flags["n"] else False
    overwrite = gs.overwrite()

    # List maps in imagery group
    try:
        maps = (
            gs.read_command("i.group", flags="g", group=input, quiet=True)
            .rstrip("\n")
            .split("\n")
        )
    except:
        pass

    # Validate input
    # q and maxit can be None according to manual, but does not work in current pysptools version
    if endmember_n <= 0:
        gs.fatal("Number of endmembers has to be > 0")
        """if (extraction_method == 'PPI' or
            extraction_method == 'NFINDR'):
            gs.fatal('Extraction methods PPI and NFINDR require endmember_n >= 2')
        endmember_n = None"""

    if maxit <= 0:
        maxit = 3 * len(maps)

    if endmember_n > len(maps) + 1:
        gs.warning(
            "More endmembers ({}) requested than bands in \
                   input imagery group ({})".format(
                endmember_n, len(maps)
            )
        )
        if extraction_method != "PPI":
            gs.fatal(
                "Only PPI method can extract more endmembers than number \
                     of bands in the imagery group"
            )

    if not atgp_init and extraction_method != "NFINDR":
        gs.verbose(
            "ATGP is only taken into account in \
                   NFINDR extraction method..."
        )

    # Get metainformation from input bands
    band_types = {}
    img = None
    n = 0
    gs.verbose("Reading imagery group...")
    for m in maps:
        map = m.split("@")

        # Build numpy stack from imagery group
        raster = r.raster2numpy(map[0], mapset=map[1])
        if raster == np.float64:
            raster = float32(raster)
            gs.warning(
                "{} is of type Float64.\
                        Float64 is currently not supported.\
                        Reducing precision to Float32".format(
                    raster
                )
            )

        # Determine map type
        band_types[map[0]] = get_rastertype(raster)

        # Create cube and mask from GRASS internal NoData value
        if n == 0:
            img = raster
            # Create mask from GRASS internal NoData value
            mask = mask_rasternd(raster)
        else:
            img = np.dstack((img, raster))
            mask = np.logical_and((mask_rasternd(raster)), mask)

        n = n + 1

    # Read a mask if present and give waringing if not
    # Note that otherwise NoData is read as values
    gs.verbose("Checking for MASK...")
    try:
        MASK = r.raster2numpy("MASK", mapset=getenv("MAPSET")) == 1
        mask = np.logical_and(MASK, mask)
        MASK = None
    except:
        pass

    if extraction_method == "NFINDR":
        # Extract endmembers from valid pixels using NFINDR function from pysptools
        gs.verbose("Extracting endmembers using NFINDR...")
        nfindr = eea.NFINDR()
        E = nfindr.extract(
            img,
            endmember_n,
            maxit=maxit,
            normalize=False,
            ATGP_init=atgp_init,
            mask=mask,
        )
    elif extraction_method == "PPI":
        # Extract endmembers from valid pixels using PPI function from pysptools
        gs.verbose("Extracting endmembers using PPI...")
        ppi = eea.PPI()
        E = ppi.extract(img, endmember_n, numSkewers=10000, normalize=False, mask=mask)
    elif extraction_method == "FIPPI":
        # Extract endmembers from valid pixels using FIPPI function from pysptools
        gs.verbose("Extracting endmembers using FIPPI...")
        fippi = eea.FIPPI()
        # q and maxit can be None according to manual, but does not work
        """if not maxit and not endmember_n:
            E = fippi.extract(img, q=None, normalize=False, mask=mask)
        if not maxit:
            E = fippi.extract(img, q=endmember_n, normalize=False, mask=mask)
        if not endmember_n:
            E = fippi.extract(img, q=int(), maxit=maxit, normalize=False,
                              mask=mask)
        else:
            E = fippi.extract(img, q=endmember_n, maxit=maxit, normalize=False,
                              mask=mask)"""
        E = fippi.extract(img, q=endmember_n, maxit=maxit, normalize=False, mask=mask)

    # Write output file in format required for i.spec.unmix addon
    if output:
        gs.verbose("Writing spectra file...")
        n = 0
        with open(output, "w") as o:
            o.write("# Channels: {}\n".format("\t".join(band_types.keys())))
            o.write("# Wrote {} spectra line wise.\n#\n".format(endmember_n))
            o.write("Matrix: {0} by {1}\n".format(endmember_n, len(maps)))
            for e in E:
                o.write("row{0}: {1}\n".format(n, "\t".join([str(i) for i in e])))
                n = n + 1

    # Write vector map with endmember information if requested
    if endmembers:
        gs.verbose("Writing vector map with endmembers...")
        from grass.pygrass import utils as u
        from grass.pygrass.gis.region import Region
        from grass.pygrass.vector import Vector
        from grass.pygrass.vector import VectorTopo
        from grass.pygrass.vector.geometry import Point

        # Build attribute table
        # Deinfe columns for attribute table
        cols = [(u"cat", "INTEGER PRIMARY KEY")]
        for b in band_types.keys():
            cols.append((b.replace(".", "_"), band_types[b]))

        # Get region information
        reg = Region()

        # Create vector map
        new = Vector(endmembers)
        new.open("w", tab_name=endmembers, tab_cols=cols)

        cat = 1
        for e in E:
            # Get indices
            idx = np.where((img[:, :] == e).all(-1))

            # Numpy array is ordered rows, columns (y,x)
            if len(idx[0]) == 0 or len(idx[1]) == 0:
                gs.warning(
                    "Could not compute coordinated for endmember {}. \
                            Please consider rescaling your data to integer".format(
                        cat
                    )
                )
                cat = cat + 1
                continue

            coords = u.pixel2coor((idx[1][0], idx[0][0]), reg)
            point = Point(coords[1] + reg.ewres / 2.0, coords[0] - reg.nsres / 2.0)

            # Get attributes
            n = 0
            attr = []
            for b in band_types.keys():
                if band_types[b] == u"INTEGER":
                    attr.append(int(e[n]))
                else:
                    attr.append(float(e[n]))
                n = n + 1

            # Write geometry with attributes
            new.write(point, cat=cat, attrs=tuple(attr))
            cat = cat + 1

        # Close vector map
        new.table.conn.commit()
        new.close(build=True)

    if prefix:
        # Run spectral unmixing
        import pysptools.abundance_maps as amaps

        if unmixing_method == "FCLS":
            fcls = amaps.FCLS()
            result = fcls.map(img, E, normalize=False, mask=mask)
        elif unmixing_method == "NNLS":
            nnls = amaps.NNLS()
            result = nnls.map(img, E, normalize=False, mask=mask)
        elif unmixing_method == "UCLS":
            ucls = amaps.UCLS()
            result = ucls.map(img, E, normalize=False, mask=mask)

        # Write results
        for l in range(endmember_n):
            rastname = "{0}_{1}".format(prefix, l + 1)
            r.numpy2raster(result[:, :, l], "FCELL", rastname, overwrite=overwrite)


# Run the module
if __name__ == "__main__":
    options, flags = gs.parser()
    sys.exit(main())
