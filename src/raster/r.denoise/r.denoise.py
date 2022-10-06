#!/usr/bin/env python
#
############################################################################
#
# MODULE:       r.denoise.py
# AUTHOR(S):    John A Stevenson
#               Converted to Python by Carlos H. Grohmann
# PURPOSE:      Run Sun's denoising algorithm from within GRASS
# COPYRIGHT:    (C) 2009 GRASS Development Team/John A Stevenson
#
# NOTES:    Requires Sun's denoising algorithm executable (mdenoise).
#       Instructions for installation of mdenoise are given on the
#       html manual page (g.manual r.denoise).
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# MINOR FIXES:     Alexander Muriy (amuriy AT gmail DOT com), 01.2012
#
#############################################################################

# %Module
# %  description: r.denoise - denoise topographic data
# %End
# %option
# % key: input
# % type: string
# % gisprompt: old,cell,raster
# % description: Raster input map
# % required : yes
# %end
# %option
# % key: output
# % type: string
# % gisprompt: new,cell,raster
# % description: Denoised raster output map
# % required : yes
# %end
# %option
# % key: iterations
# % type: integer
# % description: Number of normal-updating iterations
# % answer: 5
# % options: 1-50
# % required : no
# %end
# %option
# % key: threshold
# % type: double
# % description: Edge-sharpness threshold
# % answer: 0.93
# % options: 0.0-1.0
# % required : no
# %end
# %option
# % key: epsg
# % type: integer
# % description: EPSG projection code (required if current location is not projected)
# % required : no
# %end

import os
import atexit

try:
    from itertools import izip as zip
except ImportError:  # included in py 3.x series
    pass
import grass.script as grass

# pyproj lazy imported at the end of the file

# PID for temporary files
tmp_rmaps = []


# what to do in case of user break:
def cleanup():
    # delete any TMP files:
    grass.message(_("Removing temporary files..."))
    global tmp_rmaps
    try:
        for fname in tmp_rmaps:
            os.remove(fname)
    except OSError:
        pass


# test if requirements are present
def check_requirements():
    # mdenoise
    if not grass.find_program("mdenoise"):
        grass.fatal(
            _(
                "mdenoise required. Follow instructions in html manual page to install it (g.manual r.denoise)."
            )
        )


# reproject data
def do_proj(xyz_in, xyz_out, epsg_code):
    grass.message(_("Projecting..."))
    # lazy import
    # TODO: replace by pure GRASS GIS if pyproj not available
    try:
        import pyproj
    except ImportError:
        grass.fatal(
            _(
                "pyproj not found, install it first, e.g.:"
                " pip install pyproj"
                " (https://jswhit.github.io/pyproj)"
            )
        )
    # define projections
    loc_proj = grass.read_command("g.proj", flags="jf")
    loc_proj = pyproj.Proj(loc_proj.strip())
    epsg_proj = pyproj.Proj("epsg:" + str(epsg_code))
    # Create transformation object
    transformer = pyproj.Transformer.from_proj(loc_proj, epsg_proj)
    # open files
    f_in = open(xyz_in, "r")
    f_out = open(xyz_out, "w")
    # read input coordinates file
    for line in f_in.readlines():
        # do the projection
        for pnt in transformer.itransform([list(map(float, [line.split()]))]):
            # write output to file
            f_out.write("{} {} {}\n".format(*pnt))
    # close files
    f_in.close()
    f_out.close()


def main():
    global tmp_rmaps

    # user keys
    in_raster = options["input"]  # in_raster = 'srtm_1sec_amazonia'
    out_raster = options["output"]  # out_raster = 'teste_dnoise'
    iterations = options["iterations"]
    threshold = options["threshold"]
    epsg = options["epsg"]

    # check if input file exists
    if not grass.find_file(in_raster)["file"]:
        grass.fatal(_("Raster map <%s> not found") % in_raster)

    # name the files
    tmp_xyz = "{}.xyz".format(grass.tempfile())
    tmp_xyz_proj = "{}.xyz".format(grass.tempfile())
    tmp_out_dnoise = "{}.xyz".format(grass.tempfile())
    tmp_xyz_merge = "{}.xyz".format(grass.tempfile())
    # list for cleanup
    tmp_rmaps = [tmp_xyz, tmp_xyz_proj, tmp_out_dnoise, tmp_xyz_merge]

    # check if current location is in a projected coordinate system
    reproject = grass.locn_is_latlong()

    # Export the map to xyz points.
    grass.message(_("Exporting points..."))
    grass.run_command(
        "r.out.xyz", input=in_raster, output=tmp_xyz, separator="space", overwrite=True
    )

    # Reproject if necessary
    if reproject:
        do_proj(tmp_xyz, tmp_xyz_proj, epsg)
        tmp_xyz = tmp_xyz_proj

    # Denoise.  The -z flag preserves the xy positions of the points.
    grass.message(_("Denoising..."))
    cmd = (
        ["mdenoise"]
        + ["-i"]
        + [tmp_xyz]
        + ["-t"]
        + [str(threshold)]
        + ["-n"]
        + [str(iterations)]
        + ["-z"]
        + ["-o"]
        + [tmp_out_dnoise]
    )
    grass.call(cmd)

    # As only the z coordinates have changed in denoising,
    # the new z coordinates are combined with the original xy coordinates.
    f_merged = open(tmp_xyz_merge, "w")  # new, merged
    # read input coordinates file

    with open(tmp_out_dnoise) as f_dnoise, open(tmp_xyz) as f_orig:
        for line_dnoise, line_orig in zip(f_dnoise, f_orig):
            xyz_dnoise = line_dnoise.split()  # denoised
            xyz_orig = line_orig.split()  # original
            f_merged.write("%s %s %s\n" % (xyz_orig[0], xyz_orig[1], xyz_dnoise[2]))

    # close files
    f_merged.close()

    # Reload data
    grass.message(_("Reloading data..."))
    grass.run_command(
        "r.in.xyz",
        flags="i",
        input=tmp_xyz_merge,
        output=out_raster,
        method="min",
        x=1,
        y=2,
        z=3,
        separator="space",
        overwrite=True,
    )

    # Edit metadata to record denoising parameters
    grass.run_command(
        "r.support", map=out_raster, title="A denoised version of <%s>" % in_raster
    )
    grass.run_command(
        "r.support",
        map=out_raster,
        history="Generated by: r.denoise %s iterations=%s threshold=%s"
        % (in_raster, str(threshold), str(iterations)),
    )


# run the module
if __name__ == "__main__":
    options, flags = grass.parser()

    atexit.register(cleanup)
    check_requirements()
    main()
