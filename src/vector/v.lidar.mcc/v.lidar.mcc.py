#!/usr/bin/env python
############################################################################
#
# MODULE:       v.lidar.mcc
# AUTHOR:       Stefan Blumentrath, Norwegian Institute for Nature Research (NINA),
#               Oslo
# PURPOSE:      Reclassify points of a LiDAR point cloud as ground / non-ground
#               using a multiscale curvature based classification algorithm
# COPYRIGHT:    (c) 2013 Stefan Blumentrath, NINA, and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

# %module
# % description: Reclassifies points of a LiDAR point cloud as ground / non-ground using a multiscale curvature based classification algorithm.
# % keyword: vector
# % keyword: lidar
# % keyword: classification
# %end
# %flag
# % key: n
# % description: Filter negative outliers (default is positive)
# %end
# %option G_OPT_V_INPUT
# % description: Input vector point map
# % label: Input point layer
# % required: yes
# %end
# %option G_OPT_V_OUTPUT
# % key: ground
# % label: Output ground return points
# % description: Output vector point map containing points classified as ground return
# % required: yes
# %end
# %option G_OPT_V_OUTPUT
# % key: nonground
# % label: Output non-ground return points
# % description: Output vector point map containing points NOT classified as ground return
# % required: yes
# %end
# %option nl
# % key: nl
# % label: Number of scale domains (nl)
# % description: nl
# % type: integer
# % required: no
# % answer : 3
# %end
# %option t
# % key: t
# % type: double
# % label: Curvature tolerance threshold (t)
# % required: no
# % answer : 0.3
# %end
# %option j
# % key: j
# % label: Convergence threshold (j)
# % type: double
# % required: no
# % answer : 0.1
# %end
# %option f
# % key: f
# % label: Tension parameter (f)
# % type: double
# % required: no
# % answer : 2
# %end
# %option s
# % key: s
# % label: Spline steps parameter (s)
# % type: integer
# % required: no
# % answer : 10
# %end

import sys
import os
import atexit

# GRASS binding
try:
    import grass.script as grass
except ImportError:
    sys.exit(_("No GRASS-python library found"))

GUIModulesPath = os.path.join(os.getenv("GISBASE"), "etc", "gui", "wxpython")
sys.path.append(GUIModulesPath)

GUIPath = os.path.join(os.getenv("GISBASE"), "etc", "gui", "wxpython", "scripts")
sys.path.append(GUIPath)

# i18N
import gettext

gettext.install("grassmods", os.path.join(os.getenv("GISBASE"), "locale"))


def cleanup():
    nuldev = open(os.devnull, "w")
    grass.run_command(
        "g.remove",
        flags="f",
        type="vector",
        name="%s,%s,%s" % (temp_ng, temp_ncin, temp_ncout),
        quiet=True,
        stderr=nuldev,
    )


def main():
    global temp_ng, temp_ncin, temp_ncout

    # we discard stderrs when not debugging
    # ideally stderrs should be printed when an exception was raised
    # this would be done easily with StringIO
    # but it doesn't work with subprocess
    if not grass.debug_level():
        nuldev = open(os.devnull, "w")
    else:
        nuldev = sys.stderr

    # Initalise temporary verctor map names
    temp_ng = "v_lidar_mcc_tmp_ng_" + str(os.getpid())
    temp_ncin = "v_lidar_mcc_tmp_ncin_" + str(os.getpid())
    temp_ncout = "v_lidar_mcc_tmp_ncout_" + str(os.getpid())

    input = options["input"]
    g_output = options["ground"]
    ng_output = options["nonground"]

    # does map exist?
    if not grass.find_file(input, element="vector")["file"]:
        grass.fatal(_("Vector map <%s> not found") % input)

    # Count points in input map
    n_input = grass.vector_info(input)["points"]

    # does map contain points ?
    if not (n_input > 0):
        grass.fatal(_("Vector map <%s> does not contain points") % input)

    flag_n = flags["n"]

    ### Scale domain (l)
    # Evans & Hudak 2007 used scale domains 1 to 3
    l = int(1)
    l_stop = int(options["nl"])
    if l_stop < 1:
        grass.fatal("The minimum number of scale domains is 1.")

    ### Curvature tolerance threshold (t)
    # Evans & Hudak 2007 used a t-value of 0.3
    t = float(options["t"])
    ###Increase of curvature tolerance threshold for each
    ti = t / 3.0

    ### Convergence threshold (j)
    # Evans & Hudak 2007 used a convergence threshold of 0.3
    j = float(options["j"])
    if j <= 0:
        grass.fatal("The convergence threshold has to be > 0.")

    ### Tension parameter (f)
    # Evans & Hudak 2007 used a tension parameter 1.5
    f = float(options["f"])
    if f <= 0:
        grass.fatal("The tension parameter has to be > 0.")

    ### Spline steps parameter (s)
    # Evans & Hudak 2007 used the 12 nearest neighbors
    # (used spline steps $res * 5 before)
    s = int(options["s"])
    if s <= 0:
        grass.fatal("The spline step parameter has to be > 0.")

    ###Read desired resolution from region
    # Evans & Hudak 2007 used a desired resolution (delta) of 1.5
    gregion = grass.region()
    x_res_fin = gregion["ewres"]
    y_res_fin = gregion["nsres"]

    # Defineresolution steps in iteration
    n_res_steps = (l_stop + 1) / 2

    # Pass ame of input map to v.outlier
    nc_points = input

    # controls first creation of the output map before patching
    ng_output_exists = False
    # append and do not build topology
    vpatch_flags = "ab"

    # 7.x requires topology to see z coordinate
    # 7.1 v.patch has flags to use z even without topology
    # see #2433 on Trac and r66822 in Subversion
    build_before_patch = True
    unused, gver_minor, unused = grass.version()["version"].split(".")
    if int(gver_minor) >= 1:
        build_before_patch = False
        # do not expect topology and expect z
        vpatch_flags += "nz"

    # Loop through scale domaines
    while l <= l_stop:
        i = 1
        convergence = 100
        if l < ((l_stop + 1) / 2):
            xres = x_res_fin / (n_res_steps - (l - 1))
            yres = y_res_fin / (n_res_steps - (l - 1))
        elif l == ((l_stop + 1) / 2):
            xres = x_res_fin
            yres = y_res_fin
        else:
            xres = x_res_fin * ((l + 1) - n_res_steps)
            yres = y_res_fin * ((l + 1) - n_res_steps)

        grass.use_temp_region()
        grass.run_command(
            "g.region",
            s=gregion["s"],
            w=gregion["w"],
            nsres=yres,
            ewres=xres,
            flags="a",
        )
        xs_s = xres * s
        ys_s = yres * s
        grass.message("Processing scale domain " + str(l) + "...")
        # Repeat application of v.outlier until convergence level is reached
        while convergence > j:
            grass.verbose(
                "Number of input points in iteration " + str(i) + ": " + str(n_input)
            )
            # Run v.outlier
            if not flag_n:
                grass.run_command(
                    "v.outlier",
                    input=nc_points,
                    output=temp_ncout,
                    outlier=temp_ng,
                    ew_step=xs_s,
                    ns_step=ys_s,
                    lambda_=f,
                    threshold=t,
                    filter="positive",
                    overwrite=True,
                    quiet=True,
                    stderr=nuldev,
                )
            else:
                grass.run_command(
                    "v.outlier",
                    input=nc_points,
                    output=temp_ncout,
                    outlier=temp_ng,
                    ew_step=xs_s,
                    ns_step=ys_s,
                    lambda_=f,
                    threshold=t,
                    filter="negative",
                    overwrite=True,
                    quiet=True,
                    stderr=nuldev,
                )

            # Get information about results for calculating convergence level
            ng = grass.vector_info(temp_ng)["points"]
            nc = n_input - ng
            n_input = nc
            grass.run_command(
                "g.remove",
                flags="f",
                type="vector",
                name=temp_ncin,
                quiet=True,
                stderr=nuldev,
            )
            grass.run_command(
                "g.rename",
                vector=temp_ncout + "," + temp_ncin,
                quiet=True,
                stderr=nuldev,
            )
            nc_points = temp_ncin
            # Give information on process status
            grass.verbose(
                "Unclassified points after iteration " + str(i) + ": " + str(nc)
            )
            grass.verbose(
                "Points classified as non ground after iteration "
                + str(i)
                + ": "
                + str(ng)
            )
            # Set convergence level
            if nc > 0:
                convergence = float(float(ng) / float(nc))
                if build_before_patch:
                    grass.run_command("v.build", map=temp_ng, stderr=nuldev)
                # Patch non-ground points to non-ground output map
                if ng_output_exists:
                    grass.run_command(
                        "v.patch",
                        input=temp_ng,
                        output=ng_output,
                        flags=vpatch_flags,
                        overwrite=True,
                        quiet=True,
                        stderr=nuldev,
                    )
                else:
                    grass.run_command(
                        "g.copy", vector=(temp_ng, ng_output), stderr=nuldev
                    )
                    ng_output_exists = True
            else:
                convergence = 0
            # Give information on convergence level
            grass.verbose(
                "Convergence level after run "
                + str(i)
                + " in scale domain "
                + str(l)
                + ": "
                + str(round(convergence, 3))
            )
            # Increase iterator
            i = i + 1
        # Adjust curvature tolerance and reset scale domain
        t = t + ti
        l = l + 1
        # Delete temporary region
        grass.del_temp_region()

    # Rename temporary map of points whichhave not been classified as non-ground to output vector map containing ground points
    grass.run_command(
        "g.rename", vector=nc_points + "," + g_output, quiet=True, stderr=nuldev
    )


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())
