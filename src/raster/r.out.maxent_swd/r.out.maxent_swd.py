#!/usr/bin/env python

"""
MODULE:       r.out.maxent_swd
AUTHOR(S):    Stefan Blumentrath <stefan dot blumentrath at nina dot no >
PURPOSE:      Produce a set of SWD file as input to MaxEnt 3.3.3e using r.stats.

              The SWD file format is a simple CSV-like file file format as
              described in Elith et al. 2011. Generally it looks like:

              specie_name,X,Y,parameter_1,parameter_2,...
              your_specie,1.1,1.1,1,1,...

              The first column always contains the name of a species, followed by
              two columns for the X- and Y-coordinates. Then each column
              represents one environmental parameter. In contrast to r.stats
              only integer values are accepted to represent NO DATA.

              A background SWD file is always produced while specie output
              can be omitted.

              Multiple species can be processed, but each has to be in an
              individual raster map. Map names of the maps containing the
              environmental parameters can be replaced by short names,
              that should be used in MaxEnt 3.3.3.e.

              Results from MaxEnt can either be imported by r.in.xyz or
              calculated from MaxEnt lambdas file using the script
              r.maxent.lambdas.


COPYRIGHT:    (C) 2022 by the Norwegian Institute for Nature Research
              http://www.nina.no, Stefan Bluentrath and the GRASS GIS
              Development Team

              This program is free software under the GNU General Public
              License (>=v2). Read the file COPYING that comes with GRASS
              for details.

REQUIREMENTS:
 -
"""

# %Module
# % description: Exports map data as input to MaxEnt in SWD format
# % keyword: raster
# % keyword: export
# % keyword: maxent
# % keyword: ecology
# % keyword: niche
# %End
#
# %flag
# % key: z
# % description: Zoom computational region to species data (may speed up processing)
# % guisection: Species
# %end
#
# %option G_OPT_F_INPUT
# % key: alias_input
# % type: string
# % description: File containg map and alias name(s) for environmental parameter(s)
# % guisection: Background
# % required: no
# %end
#
# %option G_OPT_R_INPUTS
# % key: env_maps
# % description: Environmental parameter map(s)
# % guisection: Background
# % required : no
# %end
#
# %option
# % key: alias_names
# % type: string
# % description: Alias names for environmental parameter map(s)
# % guisection: Background
# % required : no
# %end
#
# %option G_OPT_F_OUTPUT
# % key: bgr_output
# % description: Output SWD file for the environmental data of the background landscape
# % guisection: Background
# % required : no
# %end
#
# %option G_OPT_F_OUTPUT
# % key: alias_output
# % description: CSV-like output file with alias names in first column and map names in second column, separated by comma
# % guisection: Background
# % required : no
# %end
#
# %option G_OPT_R_INPUT
# % key: bgr_mask
# % description: Map to be used as mask for the background landscape
# % guisection: Background
# % required : no
# %end
#
# %option G_OPT_R_INPUTS
# % key: species_masks
# % description: Raster map(s) of specie occurence
# % guisection: Species
# % required : no
# %end
#
# %option G_OPT_F_OUTPUT
# % key: species_output
# % description: Output SWD file for the specie(s) related environmental data
# % guisection: Output
# % required : no
# %end
#
# %option
# % key: species_names
# % type: string
# % description: Alias-name(s) for species to be used in MaxEnt SWD file instead of map names, separated by comma (default: map names).
# % guisection: Species
# % required : no
# %end
#
# %Option
# % key: null_value
# % type: integer
# % required: no
# % description: Integer representing NO DATA cell value (default: -9999)
# % guisection: Output
# % answer: -9999
# %end
#
# %rules
# % required: alias_input,env_maps
# % exclusive: alias_input,alias_output
# % requires: alias_output,alias_names
# % requires: species_names,species_masks
# % requires: species_output,species_masks
# %end

import atexit
import os

import grass.script as gscript
from grass.pygrass.gis import Mapset
from grass.pygrass.raster import RasterRow

TMP_NAME = gscript.tempname(12)


def cleanup():
    """Restore old mask if it existed"""
    if RasterRow("{}_MASK".format(TMP_NAME), Mapset().name).exist():
        gscript.verbose("Restoring old mask...")
        if RasterRow("MASK", Mapset().name).exist():
            gscript.run_command("r.mask", flags="r")
        gscript.run_command(
            "g.rename", rast="{}_MASK,MASK".format(TMP_NAME), quiet=True
        )
    if RasterRow("MASK", Mapset().name).exist():
        gscript.run_command("r.mask", flags="r")


def parse_bgr_input(alias_input, env_maps, alias_names):
    """Parse environmental background input"""
    if env_maps:
        env_maps = env_maps.split(",")

    if alias_names:
        alias_names = alias_names.split(",")

    if alias_input:
        if not os.access(alias_input, os.R_OK):
            gscript.fatal(
                _("The file containing alias names does not exist or is not readable.")
            )
        gscript.info(
            _(
                "Alias and map names are beeing read from file. Other input regarding environmental parameter(s) will be ignored..."
            )
        )
        with open(alias_input, "r") as alias_txt:
            lines = alias_txt.readlines()
            parameters = []
            alias = []
            for line in lines:
                if "," in line:
                    parameters.append(line.split(",")[1].strip())
                    alias.append(line.split(",")[0].strip())
    else:
        parameters = env_maps

        if alias_names:
            alias = alias_names
        else:
            alias = [param.split("@")[0] for param in parameters]

    # Check if number of alias names is identically with number of background maps
    if len(alias) != len(parameters):
        gscript.fatal(
            _("Number of provided background maps and alias names do not match.")
        )

    for param in parameters:
        # Check if environmental parameter map(s) exist
        if not RasterRow(param).exist():
            gscript.fatal(
                _(
                    "Could not find environmental parameter raster map <{}>".format(
                        param
                    )
                )
            )

    return alias, parameters


def parse_species_input(species_masks, species_names):
    """Parse species input"""

    species_dict = {}

    if species_masks:
        species_masks = species_masks.split(",")

    if species_names:
        species_names = species_names.split(",")

    # Check if number of specie names is identically with number of specie maps
    if species_names and species_masks:
        if len(species_names) != len(species_masks):
            gscript.fatal(
                _(
                    "Number of provided species input maps and species names do not match."
                )
            )

    if species_masks:
        for idx, species in enumerate(species_masks):
            # Check if species map exist
            species_map_name = species.split("@")
            species_name = species_names[idx] if species_names else species_map_name[0]
            species_map = RasterRow(*species_map_name)
            if not species_map.exist():
                gscript.fatal(
                    _(
                        "Could not find species raster map <{}> in mapset <{}>.".format(
                            *species_map_name
                        )
                    )
                )

            species_dict[species_name] = species_map_name

    return species_dict


def main():
    """Do the main work"""

    alias_output = options["alias_output"]

    bgr_mask = options["bgr_mask"]

    null_value = options["null_value"]

    bgr_output = options["bgr_output"]
    species_output = options["species_output"]

    alias, parameters = parse_bgr_input(
        options["alias_input"], options["env_maps"], options["alias_names"]
    )

    species_dict = parse_species_input(
        options["species_masks"], options["species_names"]
    )

    # Check if a mask file allready exists
    if RasterRow("MASK", Mapset().name).exist():
        gscript.verbose(
            _("A mask allready exists. Renaming existing mask to old_MASK...")
        )
        gscript.run_command(
            "g.rename", rast="MASK,{}_MASK".format(TMP_NAME), quiet=True
        )

    # Build parameter header if necessary
    header = ",".join(alias)

    # Write alias output if requested
    if alias_output:
        with open(alias_output, "w") as alias_out:
            for idx, name in enumerate(alias):
                alias_out.write("{},{}\n".format(name, parameters[idx]))

    # Check if specie output is requested and produce it
    if species_output and species_dict:
        # Write header to species output SWD file
        species_header = "species,X,Y,{}\n".format(header)

        with open(species_output, "w") as sp_out:
            sp_out.write(species_header)

        # Parse species input variables
        for species in species_dict:

            species_map = species_dict[species]
            # Zoom region to match specie map if requested
            if flags["z"]:
                gscript.verbose(
                    _("Zooming region to species {} temporarily.".format(species))
                )
                gscript.use_temp_region()
                gscript.run_command(
                    "g.region", align="@".join(species_map), zoom="@".join(species_map)
                )
            #
            # Apply specie mask
            gscript.run_command(
                "r.mask", raster="@".join(species_map), overwrite=True, quiet=True
            )

            # Export data using r.stats
            gscript.verbose(_("Producing output for species {}".format(species)))
            stats = gscript.pipe_command(
                "r.stats",
                flags="1gN",
                verbose=True,
                input=",".join(parameters),
                separator=",",
                null_value=null_value,
            )

            with open(species_output, "a") as sp_out:
                for row in stats.stdout:
                    sp_out.write("{},{}".format(species, gscript.decode(row)))

            # Redo zoom region to match specie map if it had been requested
            if flags["z"]:
                gscript.del_temp_region()
            # Remove mask
            gscript.run_command("r.mask", flags="r", quiet=True)

    # Write header to background output SWD file
    bgr_header = "bgr,X,Y,{}\n".format(",".join(alias))

    with open(bgr_output, "w") as bgr_out:
        bgr_out.write(bgr_header)

    # Process map data for background
    # Check if a mask file allready exists
    if bgr_mask:
        gscript.verbose(
            _("Using map {} as mask for the background landscape...".format(bgr_mask))
        )
        # Apply mask
        gscript.run_command("r.mask", raster=bgr_mask, overwrite=True, quiet=True)
    #
    # Export data using r.stats
    gscript.verbose(_("Producing output for background landscape"))
    stats = gscript.pipe_command(
        "r.stats",
        flags="1gN",
        input=",".join(parameters),
        separator=",",
        null_value=null_value,
    )

    with open(bgr_output, "a") as bgr_out:
        for row in stats.stdout:
            bgr_out.write("bgr,{}".format(gscript.decode(row)))

    cleanup()


if __name__ == "__main__":
    options, flags = gscript.parser()
    atexit.register(cleanup)
    main()
