#!/usr/bin/env python

############################################################################
#
# MODULE:       r.null.all
# AUTHOR(S):    Vaclav Petras <wenzeslaus gmail com>
#
# PURPOSE:      Manage null values for all raster maps in a mapset
# COPYRIGHT:    (C) 2019 by Vaclav Petras and the GRASS Development Team
#
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################

# %module
# % description: Manages NULL values of raster maps in a mapset or their subset.
# % keyword: raster
# % keyword: map management
# % keyword: null data
# % keyword: no-data
# %end
# %flag
# % key: f
# % description: Only do the work if the map is floating-point
# % guisection: Check
# %end
# %flag
# % key: i
# % description: Only do the work if the map is integer
# % guisection: Check
# %end
# %flag
# % key: n
# % description: Only do the work if the map doesn't have a NULL-value bitmap file
# % guisection: Check
# %end
# %flag
# % key: c
# % description: Create NULL-value bitmap file validating all data cells
# %end
# %flag
# % key: r
# % description: Remove NULL-value bitmap file
# % guisection: Remove
# %end
# %flag
# % key: z
# % description: Re-create NULL-value bitmap file (to compress or uncompress)
# %end
# %flag
# % key: d
# % label: Dry run
# % description: Map names to be checked or processed will be printed (does not take into account other flags)
# %end
# %option
# % key: setnull
# % type: string
# % required: no
# % multiple: yes
# % key_desc: val[-val]
# % description: List of cell values to be set to NULL
# % guisection: Modify
# %end
# %option
# % key: null
# % type: double
# % required: no
# % multiple: no
# % description: The value to replace the null value by
# % guisection: Modify
# %end
# %option
# % key: pattern
# % type: string
# % required: no
# % multiple: yes
# % key_desc: expression
# % label: Map name search pattern (default: all)
# % guisection: Pattern
# %end
# %option
# % key: exclude
# % type: string
# % required: no
# % multiple: yes
# % label: Map name exclusion pattern (default: none)
# % guisection: Pattern
# %end
# %option
# % key: matching
# % type: string
# % required: no
# % multiple: no
# % label: Search pattern syntax
# % options: all,wildcards,basic,extended
# % descriptions: all;Match all (no pattern needed);wildcards;Use wildcards (glob pattern);basic;Use basic regular expressions;extended;Use extended regular expressions
# % answer: all
# % guisection: Pattern
# %end
# %rules
# % required: setnull, null
# %end


import grass.script as gs


def main():
    options, flags = gs.parser()
    pattern = options["pattern"]
    exclude = options["exclude"]
    expression_type = options["matching"]
    setnull = options["setnull"]  # value(s) to null
    null = options["null"]  # null to value
    dry_run = flags["d"]

    null_flags = ""
    for flag, value in flags.items():
        if value and flag in "fincrz":
            null_flags += flag

    if expression_type == "all" and pattern:
        gs.fatal(_("Option pattern is not allowed with matching=all"))
    if expression_type == "all" and exclude:
        gs.fatal(_("Option exclude is not allowed with matching=all"))

    # we need to set pattern for all
    # and for exclude only input with wildcards
    if not pattern:
        if expression_type == "all":
            pattern = "*"
            exclude = None
            expression_type = "wildcards"
        elif expression_type == "wildcards":
            pattern = "*"
        elif expression_type in ("basic", "extended"):
            pattern = ".*"

    # a proper None is needed
    # ("" and not setting the value is different for g.list)
    if not exclude:
        exclude = None

    if expression_type == "wildcards":
        expression_type_flag = ""
    elif expression_type == "basic":
        expression_type_flag = "r"
    else:
        # expression_type == "extended" case
        expression_type_flag = "e"

    type = "raster"
    mapset = "."  # current
    try:
        maps = gs.list_strings(
            type=type,
            mapset=mapset,
            pattern=pattern,
            exclude=exclude,
            flag=expression_type_flag,
        )
    except gs.CalledModuleError:
        # the previous error is appropriate (assuming g.list error)
        import sys

        sys.exit(1)

    if dry_run and maps:
        gs.message(
            _(
                "With inclusion pattern <{pattern}>"
                " and exclusion pattern <{exclude}>"
                " using syntax <{expression_type}>"
                " these raster maps were identified"
            ).format(**locals())
        )
    elif dry_run:
        gs.message(
            _(
                "No raster maps were identified"
                " with inclusion pattern <{pattern}>"
                " and exclusion pattern <{exclude}>"
                " using syntax <{expression_type}>"
            ).format(**locals())
        )

    for map in maps:
        # TODO: option copy with prefix/suffix before setting nulls
        if dry_run:
            # TODO: apply the further selection flags
            # (or add dry run to r.null)
            print(map)
        else:
            gs.run_command(
                "r.null", map=map, setnull=setnull, null=null, flags=null_flags
            )


if __name__ == "__main__":
    main()
