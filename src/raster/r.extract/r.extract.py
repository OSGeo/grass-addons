#!/usr/bin/env python

############################################################################
#
# MODULE:       r.extract
# AUTHOR(S):    Anna Petrasova
# PURPOSE:      Extracts specified categories of an integer input map.
# COPYRIGHT:    (c) 2021 by Anna Petrasova and the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

# %module
# % description: Extracts specified categories of an integer input map.
# % keyword: raster
# % keyword: extract
# % keyword: extent
# % keyword: category
# %end
# %option G_OPT_R_INPUT
# %end
# %option G_OPT_R_OUTPUT
# %end
# %option
# % key: cats
# % type: string
# % required: yes
# % multiple: no
# % key_desc: range
# % label: Category values
# % description: Example: 1,3,7-9,13
# % gisprompt: old,cats,cats
# %end
# %flag
# % key: c
# % description: Clip to minimum extent
# %end
# %flag
# % key: s
# % description: Output reclassified map instead of true map
# %end

import sys
import atexit

import grass.script as gs

try:
    from grass.script.utils import append_random
except ImportError:
    import random
    import string

    def append_random(name, suffix_length=None, total_length=None):
        """Add a random part to of a specified length to a name (string)

        >>> append_random("tmp", 8)
        >>> append_random("tmp", total_length=16)

        ..note::

            This function is copied from grass79.
        """
        if suffix_length and total_length:
            raise ValueError(
                "Either suffix_length or total_length can be provided, not both"
            )
        if not suffix_length and not total_length:
            raise ValueError("suffix_length or total_length has to be provided")
        if total_length:
            # remove len of name and one underscore
            name_length = len(name)
            suffix_length = total_length - name_length - 1
            if suffix_length <= 0:
                raise ValueError(
                    "No characters left for the suffix:"
                    " total_length <{total_length}> is too small"
                    " or name <{name}> ({name_length}) is too long".format(**locals())
                )
        # We don't do lower and upper case because that could cause conflicts in
        # contexts which are case-insensitive.
        # We use lowercase because that's what is in UUID4 hex string.
        allowed_chars = string.ascii_lowercase + string.digits
        # The following can be shorter with random.choices from Python 3.6.
        suffix = "".join(random.choice(allowed_chars) for _ in range(suffix_length))
        return "{name}_{suffix}".format(**locals())


TMP = []


def cleanup():
    if TMP:
        gs.run_command("g.remove", type="raster", name=TMP, flags="f", quiet=True)


def parse(raster, values):
    info = gs.raster_info(raster)
    if info["datatype"] != "CELL":
        gs.fatal(_("Input raster map must be of type CELL"))
    rules = []
    vals = values.split(",")
    for val in vals:
        if "-" in val:
            a, b = val.split("-")
            if not a:
                a = info["min"]
            if not b:
                b = info["max"]
            for i in range(int(a), int(b) + 1):
                rules.append("{v} = {v}".format(v=i))
        else:
            rules.append("{v} = {v}".format(v=val))
    return rules


def reclass(input, out, rules):
    gs.write_command(
        "r.reclass", input=input, output=out, rules="-", stdin="\n".join(rules)
    )


def main():
    options, flags = gs.parser()
    original = options["input"]
    output = options["output"]
    cats = options["cats"]

    rules = parse(original, cats)
    if flags["c"] and flags["s"]:
        gs.warning(_("The extent of the output reclassified raster cannot be changed"))

    if flags["s"]:
        reclass(original, output, rules)
    else:
        output_tmp = append_random("tmp", 8)
        TMP.append(output_tmp)
        reclass(original, output_tmp, rules)
        if flags["c"]:
            gs.use_temp_region()
            atexit.register(gs.del_temp_region)
            gs.run_command("g.region", zoom=output_tmp)
        gs.mapcalc(output + " = " + output_tmp)

    gs.run_command("r.colors", map=output, raster=original, quiet=True)
    gs.raster_history(output)


if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main())
