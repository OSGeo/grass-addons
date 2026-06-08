#!/usr/bin/env python3

############################################################################
#
# MODULE:       t.strds.copy
# AUTHOR(S):    Paulo van Breugel
# PURPOSE:      Copy a space time raster dataset (STRDS) and its registered
#               raster maps from one mapset into the current mapset,
#               preserving timestamps.
# COPYRIGHT:    (C) 2026 by Paulo van Breugel and the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
############################################################################

# %module
# % description: Copies a space time raster dataset and its maps into the current mapset.
# % keyword: temporal
# % keyword: copy
# % keyword: raster
# % keyword: time
# %end

# %option G_OPT_STRDS_INPUT
# % key: input
# % label: Name source strds
# % description: Name of the source space time raster dataset (use name@mapset)
# %end

# %option G_OPT_STRDS_OUTPUT
# % key: output
# % label: Name destination strds
# % required: no
# % description: Name of the output STRDS in the current mapset (default: same as input name)
# %end

import os

import grass.script as gs


def main():
    options = gs.parser()[0]

    src = options["input"]
    dst = options["output"]
    overwrite = gs.overwrite()

    import grass.temporal as tgis

    tgis.init()

    # Resolve source name and mapset
    if "@" in src:
        src_name, src_mapset = src.split("@", 1)
    else:
        src_name = src
        src_mapset = None  # search path resolution

    # The destination must live in the current mapset. Default to the source
    # name when no output is given.
    cur_mapset = gs.gisenv()["MAPSET"]
    dst_name = dst.split("@", 1)[0] if dst else src_name

    # Check if output STRDS already exists, stop if so
    existing = gs.read_command(
        "t.list",
        type="strds",
        where="mapset = '{}'".format(cur_mapset),
        quiet=True,
    ).splitlines()
    existing = {e.split("@", 1)[0] for e in existing if e.strip()}
    if dst_name in existing and not overwrite:
        gs.fatal(
            _(
                "Output STRDS <{}> already exists in mapset <{}>. "
                "Use --overwrite to replace it."
            ).format(dst_name, cur_mapset)
        )

    # Make sure the source STRDS is found
    sp = tgis.open_old_stds(src, "strds")

    # Guard against copying a dataset onto itself
    if sp.get_mapset() == cur_mapset and dst_name == src_name:
        gs.fatal(
            _(
                "Source and output refer to the same STRDS <{}> in mapset "
                "<{}>. Choose a different output name."
            ).format(src_name, cur_mapset)
        )
    src_temporal_type = sp.get_temporal_type()
    src_title = sp.metadata.get_title()
    src_description = sp.metadata.get_description()
    # Relative-time datasets need the time unit for t.register; None if absolute
    src_unit = sp.get_relative_time_unit()

    # Pull the registered maps with their timestamps
    out = gs.read_command(
        "t.rast.list",
        input=src,
        columns="name,mapset,start_time,end_time",
        separator="pipe",
        flags="u",
    )
    rows = [r for r in out.splitlines() if r.strip()]
    if not rows:
        gs.fatal(_("Source STRDS <{}> contains no registered maps.").format(src))

    # Parse rows once into (name, mapset, start, end) tuples
    maps = []
    for row in rows:
        parts = row.split("|")
        name = parts[0]
        mapset = parts[1] if len(parts) > 1 and parts[1] else src_mapset
        start = parts[2] if len(parts) > 2 else ""
        end = parts[3] if len(parts) > 3 else ""
        maps.append((name, mapset, start, end))

    # Stop if any target raster name already exists in the current mapset.
    if not overwrite:
        grouped = gs.list_grouped(type="raster", check_search_path=False)
        present = set(grouped.get(cur_mapset, []))
        clashes = sorted(n for n, _m, _s, _e in maps if n in present)
        if clashes:
            gs.fatal(
                _(
                    "The following raster map(s) already exist in mapset "
                    "<{}>: {}. Use --overwrite to replace them."
                ).format(cur_mapset, ", ".join(clashes))
            )

    reg_path = gs.tempfile()
    n_maps = 0
    with open(reg_path, "w") as reg:
        for name, mapset, start, end in maps:
            fqname = f"{name}@{mapset}" if mapset else name
            gs.run_command(
                "g.copy",
                raster=f"{fqname},{name}",
                overwrite=overwrite,
                quiet=True,
            )

            # Build register line: name[|start[|end]]
            if start and end and end != "None":
                line = f"{name}|{start}|{end}"
            elif start and start != "None":
                line = f"{name}|{start}"
            else:
                line = name
            reg.write(line + "\n")
            n_maps += 1

    gs.message(_("Processed {} raster map(s).").format(n_maps))

    # Create the destination STRDS in the current mapset.
    title = src_title if src_title else f"Copy of {src_name}"
    description = (
        src_description
        if src_description
        else f"Copied from {src} into mapset {cur_mapset}"
    )

    gs.run_command(
        "t.create",
        type="strds",
        temporaltype=src_temporal_type,
        output=dst_name,
        title=title,
        description=description,
        overwrite=overwrite,
    )

    # Register the maps with their original timestamps. Relative-time datasets
    # require the time unit to be passed explicitly.
    reg_kwargs = dict(input=dst_name, file=reg_path, overwrite=overwrite)
    if src_temporal_type == "relative":
        reg_kwargs["unit"] = src_unit
    gs.run_command("t.register", **reg_kwargs)

    try:
        os.remove(reg_path)
    except OSError:
        pass

    gs.message(
        _("STRDS <{}> successfully copied to <{}@{}>.").format(
            src, dst_name, cur_mapset
        )
    )


if __name__ == "__main__":
    main()
