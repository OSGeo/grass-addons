#!/usr/bin/env python3

#
########################################################################
#
# MODULE:       r.vif
# AUTHOR(S):    Paulo van Breugel <paulo ecodiv earth>
# PURPOSE:      Calculate the variance inflation factor of set of
#               variables. The computation is done using an user defined number
#               (or percentage) of random cells (default 10.000) as input.
#               The user can set a maximum VIF, in wich case the VIF will
#               calculated again after removing the variables with the highest
#               VIF. This will be repeated till the VIF falls below the user
#               defined VIF threshold value.
#
# COPYRIGHT: (C) 2015 - 2026 Paulo van Breugel and the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
#
########################################################################
#
# %Module
# % description: To calculate the stepwise variance inflation factor.
# % keyword: raster
# % keyword: variance inflation factor
# % keyword: VIF
# %End

# %option
# % key: maps
# % type: string
# % gisprompt: old,cell,raster
# % description: variables
# % required: yes
# % multiple: yes
# % guisection: Input
# %end

# %option
# % key: retain
# % type: string
# % gisprompt: old,cell,raster
# % description: variables
# % required: no
# % multiple: yes
# % guisection: Input
# %end

# %option
# % key: maxvif
# % type: double
# % description: Maximum vif
# % key_desc: number
# % guisection: Input
# %end

# %option G_OPT_F_OUTPUT
# % key:file
# % description: Name of output text file
# % required: no
# % guisection: Input
# %end

# %option
# % key: n
# % type: string
# % description: number of sample points (number or percentage)
# % key_desc: number
# % guisection: Sample options
# %end

# %option
# % key: seed
# % type: integer
# % description: Seed for rand() function
# % required: no
# % guisection: Sample options
# %end

# %flag
# % key: s
# % description: Generate random seed (result is non-deterministic)
# % guisection: Sample options
# %end

# %flag
# % key: v
# % description: Only print selected variables to screen
# %end

# %flag
# % key: f
# % description: low-memory option (will use full raster layers)
# %end

# %rules
# %requires: n,-s,seed
# %end

# %rules
# %excludes: -s,seed
# %end

# %rules
# %requires_all: -v,maxvif
# %end

# import libraries
import os
import sys
import math
import uuid
import atexit
import numpy as np

try:
    from io import StringIO
except ImportError:
    from cStringIO import StringIO
import grass.script as gs

try:
    from grass.script import MaskManager

    HAS_MASK_MANAGER = True
except ImportError:
    HAS_MASK_MANAGER = False


# Functions
def prRed(skk):
    print("\033[91m {}\033[00m".format(skk))


def prGreen(skk):
    print("\033[92m {}\033[00m".format(skk))


CLEAN_RAST = []

mask_backup_name = None


def restore_mask_backup():
    """Best-effort restore of MASK from the tracked backup.

    If a MASK already exists, it is one r.vif created internally (the script
    held control throughout, so the user could not have set one). Remove it
    before renaming the backup back. On success, clears mask_backup_name.
    On failure, leaves it set and emits a warning with the backup name so the
    user can restore manually. Never raises.
    """
    global mask_backup_name
    if mask_backup_name is None:
        return
    mapset = gs.gisenv()["MAPSET"]
    found_backup = gs.find_file(name=mask_backup_name, element="cell", mapset=mapset)
    if not found_backup["fullname"]:
        mask_backup_name = None
        return
    found_mask = gs.find_file(name="MASK", element="cell", mapset=mapset)
    if found_mask["fullname"]:
        try:
            gs.run_command("r.mask", flags="r", quiet=True)
        except Exception:
            pass  # best effort; the rename below will fail with a clear warning
    try:
        gs.run_command("g.rename", raster=[mask_backup_name, "MASK"], quiet=True)
        mask_backup_name = None
    except Exception as exc:
        gs.warning(
            _(
                "Failed to restore MASK from backup <{name}>: {err}. "
                "Restore manually with: g.rename raster={name},MASK"
            ).format(name=mask_backup_name, err=exc)
        )


def cleanup():
    """Restore the original MASK if needed, then remove temporary maps."""
    restore_mask_backup()
    cleanrast = list(reversed(CLEAN_RAST))
    for rast in cleanrast:
        gs.run_command("g.remove", flags="f", type="all", name=rast, quiet=True)


def create_unique_name(name):
    """Generate a tmp name which contains prefix
    Store the name in the global list.
    """
    return name + str(uuid.uuid4().hex)


def tmpname(prefix):
    tmpf = create_unique_name(prefix)
    CLEAN_RAST.append(tmpf)
    return tmpf


def check_layer(envlay):
    """Check if the input layers exist. If not, exit with warning"""
    for chl, _ in enumerate(envlay):
        ffile = gs.find_file(envlay[chl], element="cell")
        if ffile["fullname"] == "":
            gs.fatal("The layer " + envlay[chl] + " does not exist.")


def read_data(raster, n, flag_s, seed):
    """Read in the raster layers as a numpy array."""
    global mask_backup_name
    gs.message("Reading in the data ...")

    def read_sampled():
        """Read the raster values at the currently unmasked cells."""
        tmpcov = StringIO(
            gs.read_command(
                "r.stats", flags="1n", input=raster, quiet=True, separator="comma"
            ).rstrip("\n")
        )
        return np.loadtxt(tmpcov, skiprows=0, delimiter=",")

    def random_sample(out):
        """Write a raster of n random sample points from raster[0] to <out>."""
        kwargs = {"input": raster[0], "npoints": n, "raster": out, "quiet": True}
        if flag_s:
            kwargs["flags"] = "s"
        else:
            kwargs["seed"] = seed
        gs.run_command("r.random", **kwargs)

    if not n:
        return read_sampled()

    if HAS_MASK_MANAGER:
        # GRASS 8.5+: draw the sample first so it respects any active user MASK
        # (as on 8.4), then let MaskManager apply the sample as the mask for
        # reading and restore the user's MASK automatically on exit, including
        # on error. No manual backup or rename is needed.
        sample = tmpname("rvif")
        random_sample(sample)
        with MaskManager() as manager:
            gs.mapcalc(
                "{m} = if(isnull({s}), null(), 1)".format(
                    m=manager.mask_name, s=sample
                ),
                quiet=True,
            )
            return read_sampled()

    # GRASS 8.4: no MaskManager. Back up the user's MASK, apply the sample
    # mask, and restore it in the finally block (with the atexit cleanup() as
    # a backstop if the process is killed).
    sample = tmpname("rvif")
    random_sample(sample)
    exist_mask = gs.find_file(name="MASK", element="cell", mapset=gs.gisenv()["MAPSET"])
    if exist_mask["fullname"]:
        # Track the backup in mask_backup_name (NOT CLEAN_RAST) so cleanup()
        # can restore it. Set only after a successful rename.
        backup = create_unique_name("rvifoldmask")
        gs.run_command("g.rename", raster=["MASK", backup], quiet=True)
        mask_backup_name = backup
    try:
        gs.run_command("r.mask", raster=sample, quiet=True)
        return read_sampled()
    finally:
        try:
            gs.run_command("r.mask", flags="r", quiet=True)
        except Exception:
            pass
        if exist_mask["fullname"]:
            restore_mask_backup()


def compute_vif(mapx, mapy):
    """Compute rsqr of linear regression between layers mapx and mapy."""
    x_i = np.hstack((mapx, np.ones((mapx.shape[0], 1))))
    unused, resid = np.linalg.lstsq(x_i, mapy, rcond=None)[:2]
    if resid.size == 0:
        resid_value = 0
    else:
        resid_value = resid[0]
    r2 = float(1 - resid_value / (mapy.size * mapy.var()))
    if float(r2) > 0.9999999999:
        vif = float("inf")
        sqrtvif = float("inf")
    else:
        vif = 1 / (1 - r2)
        sqrtvif = math.sqrt(vif)
    return [vif, sqrtvif]


def compute_vif2(mapx, mapy):
    vifstat = gs.read_command(
        "r.regression.multi", flags="g", quiet=True, mapx=mapx, mapy=mapy
    )
    vifstat = vifstat.split("\n")
    vifstat = [i.split("=") for i in vifstat]
    if float(vifstat[1][1]) > 0.9999999999:
        vif = float("inf")
        sqrtvif = float("inf")
    else:
        rsqr = float(vifstat[1][1])
        vif = 1 / (1 - rsqr)
        sqrtvif = math.sqrt(vif)
    return [vif, sqrtvif]


# main function
def main(options, flags):
    """Main function, called at execution time."""

    # Variables
    input_maps = options["maps"].split(",")
    retain_maps = options["retain"].split(",")
    if options["retain"]:
        check_layer(retain_maps)
        input_map_bases = [m.split("@")[0] for m in input_maps]
        for retain_map in retain_maps:
            if retain_map.split("@")[0] not in input_map_bases:
                gs.fatal(
                    _(
                        "Retained layer '{}' is not present in the maps list. "
                        "All layers specified in 'retain' must also be listed "
                        "in 'maps'. If the layer does exist in your maps list, "
                        "check that the mapset name matches (e.g., 'layer@mapset' "
                        "vs 'layer')."
                    ).format(retain_map)
                )
    input_map_names = [i.split("@")[0] for i in input_maps]
    retain_map_names = [i.split("@")[0] for i in retain_maps]
    max_vif = options["maxvif"]
    if max_vif:
        max_vif = float(max_vif)
    output_file = options["file"]
    number_points = options["n"]
    seed = options["seed"]
    if seed:
        int(seed)
    flag_v = flags["v"]
    flag_f = flags["f"]
    flag_s = flags["s"]

    # Determine maximum width of the columns to be printed to std output
    name_lengths = []
    for i in input_maps:
        name_lengths.append(len(i))
    nlength = max(name_lengths)

    # Read in data
    if not flag_f:
        p = read_data(raster=input_maps, n=number_points, flag_s=flag_s, seed=seed)

    # Create arrays to hold results (which will be written to file at end)
    out_vif = []
    out_sqrt = []
    out_variable = []

    # VIF is computed once only
    if max_vif == "":
        # Print header of table to std output
        print(
            "{0[0]:{1}s} {0[1]:8s} {0[2]:8s}".format(
                ["variable", "vif", "sqrtvif"], nlength
            )
        )

        # Compute the VIF
        for i, e in enumerate(input_map_names):
            # Compute vif using full rasters
            if flag_f:
                y = input_maps[i]
                x = input_maps[:]
                del x[i]
                vifstat = compute_vif2(x, y)
            # Compute vif using sample
            else:
                y = p[:, i]
                x = np.delete(p, i, axis=1)
                vifstat = compute_vif(x, y)
            # Write stats to arrays
            out_vif.append(vifstat[0])
            out_sqrt.append(vifstat[1])
            out_variable.append(e)
            print(
                "{0[0]:{1}s} {0[1]:8.2f} {0[2]:8.2f}".format(
                    [input_map_names[i], vifstat[0], vifstat[1]], nlength
                )
            )
        if len(output_file) > 0:
            print("Statistics are written to {}\n".format(output_file))

    # The VIF stepwise variable selection procedure
    else:
        rvifmx = max_vif + 1
        m = 0
        remove_variable = "none"
        out_removed = []
        out_round = []

        # The VIF will be computed across all variables. Next, the variable
        # with highest vif is removed and the procedure is repeated. This
        # continuous till the maximum vif across the variables > maxvif

        if flag_v:
            gs.message("Computing statistics ...")

        while max_vif < rvifmx:
            m += 1
            # all_vif holds the VIF of every variable and is used to decide
            # when to stop (all VIFs, including those of retained variables,
            # must drop below maxvif). rvif is a copy in which retained
            # variables are set to -9999 so they are never chosen for removal.
            all_vif = np.zeros(len(input_maps))
            rvif = np.zeros(len(input_maps))

            # print the header of the output table to the console
            if not flag_v:
                print("\nVIF round " + str(m))
                print("--------------------------------------")
                print(
                    "{0[0]:{1}s} {0[1]:>8s} {0[2]:>8s}".format(
                        ["variable", "vif", "sqrtvif"], nlength
                    )
                )

            # Compute the VIF and sqrt(vif) for all variables in this round
            for k, e in enumerate(input_map_names):
                # Compute vif using full rasters
                if flag_f:
                    y = input_maps[k]
                    x = input_maps[:]
                    del x[k]
                    vifstat = compute_vif2(x, y)
                else:
                    # Compute vif using sample
                    try:
                        y = p[:, k]
                    except IndexError as e:
                        prRed(f"An error occurred: {str(e)}")
                        prGreen(
                            "Tip: check if all input rasters have values within the computation region."
                        )
                    x = np.delete(p, k, axis=1)
                    vifstat = compute_vif(x, y)

                # Write results to arrays
                out_vif.append(vifstat[0])
                out_sqrt.append(vifstat[1])
                out_variable.append(e)
                out_round.append(m)
                out_removed.append(remove_variable)

                # print result to console
                if not flag_v:
                    print(
                        "{0[0]:{1}s} {0[1]:8.2f} {0[2]:8.2f}".format(
                            [input_map_names[k], vifstat[0], vifstat[1]], nlength
                        )
                    )

                # Record the VIF of every variable for the stop criterion. If
                # the variable is set to be retained by the user, its entry in
                # rvif is set to -9999 to ensure it is never selected for
                # removal (but it still counts towards the stop criterion).
                all_vif[k] = vifstat[0]
                if input_map_names[k] in retain_map_names:
                    rvif[k] = -9999
                else:
                    rvif[k] = vifstat[0]

            # Stop when the maximum VIF across all variables (including
            # retained ones) drops below maxvif.
            rvifmx = max(all_vif)
            if rvifmx >= max_vif:
                # Only non-retained variables may be removed. If every variable
                # still above the threshold is retained, no removal can lower
                # the VIF further, so stop and warn the user.
                if max(rvif) == -9999:
                    gs.warning(
                        _(
                            "The maximum VIF ({vif:.2f}) still exceeds the "
                            "threshold ({thr}), but all remaining variables at "
                            "or above the threshold are retained. Stopping the "
                            "selection procedure."
                        ).format(vif=rvifmx, thr=max_vif)
                    )
                    break
                rvifindex = np.argmax(rvif, axis=None)
                remove_variable = input_map_names[rvifindex]
                del input_maps[rvifindex]
                del input_map_names[rvifindex]
                if not flag_f:
                    p = np.delete(p, rvifindex, axis=1)

        # Write final selected variables to std output
        if not flag_v:
            print("\nselected variables are: ")
            print("--------------------------------------")
            print(", ".join(input_map_names))
        else:
            print(",".join(input_map_names))

    if len(output_file) > 0:
        try:
            text_file = open(output_file, "w")
            if max_vif == "":
                text_file.write("variable,vif,sqrtvif\n")
                for i in range(len(out_vif)):
                    text_file.write(
                        "{0:s},{1:.6f},{2:.6f}\n".format(
                            out_variable[i], out_vif[i], out_sqrt[i]
                        )
                    )
            else:
                text_file.write("round,removed,variable,vif,sqrtvif\n")
                for i in range(len(out_vif)):
                    text_file.write(
                        "{0:d},{1:s},{2:s},{3:.6f},{4:.6f}\n".format(
                            out_round[i],
                            out_removed[i],
                            out_variable[i],
                            out_vif[i],
                            out_sqrt[i],
                        )
                    )
        finally:
            text_file.close()
            gs.message("\nStatistics are written to {}\n".format(output_file))


if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main(*gs.parser()))
