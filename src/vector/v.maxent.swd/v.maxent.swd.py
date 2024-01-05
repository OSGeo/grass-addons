#!/usr/bin/env python3

#
############################################################################
#
# MODULE:       v.maxent.swd
# AUTHOR(S):    Paulo van Breugel
# PURPOSE:      Produce a set of text file (SWD file) which can be used as
#               input to MaxEnt 3.3.3. It may also provide the input data
#               presence and absence/background for other modeling tools
#               in e.g. R
#
#               The SWD file format is a simple CSV-like file file format as
#               described in Elith et al. 2011. Generally it looks like:
#
#               specie_name,X,Y,parameter_1,parameter_2,...
#               your_species,1.1,1.1,1,1,...
#
#               The first column always contains the name of a species (for
#               background data this column is ignored so any name can be used),
#               followed by two colums for the X- and Y-coordinates. Then each
#               column represents one environmental parameter.
#
#               Map names of the maps containing the environmental parameters
#               can be replaced by short names. Likewise, it is possible to
#               define aliases for the names of the species distribution layer
#
# COPYRIGHT:   (C) 2015-2024 Paulo van Breugel and the GRASS Development Team
#              http://ecodiv.earth
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################
#
# REQUIREMENTS:
# -
# %Module
# % description: Export raster values at given point locations as text file in SWD format for input in Maxent
# % keyword: vector
# % keyword: export
# % keyword: Maxent
# %End

# %option
# % key: species
# % type: string
# % description: vector map(s) of species occurence
# % required : no
# % multiple : yes
# % gisprompt: old,vector
# % guisection: point data
# %end

# %option
# % key: species_name
# % type: string
# % description: Alias-name(s) for species (default: map names).
# % required : no
# % guisection: point data
# %end

# %rules
# %requires: species_name,species
# %end

# %option
# % key: evp_maps
# % type: string
# % description: Environmental parameter map(s)
# % required : yes
# % multiple : yes
# % gisprompt: old,cell,raster
# % guisection: environment
# %end

# %option
# % key: alias_names
# % type: string
# % description: Alias names for environmental parameter(s)
# % required : no
# % guisection: environment
# %end

# %option
# % key: evp_cat
# % type: string
# % description: Categorial environmental parameter map(s)
# % required : no
# % multiple : yes
# % gisprompt: old,cell,raster
# % guisection: environment
# %end

# %option
# % key: alias_cat
# % type: string
# % description: Alias names for categorial parameter(s)
# % required : no
# % guisection: environment
# %end

# %option
# % key: nbgp
# % type: string
# % description: Number or percentage of background points
# % key_desc: number
# % answer : 10000
# % required: no
# % guisection: point data
# %end

# %option
# % key: bgp
# % type: string
# % description: Vector layer with background / absence points
# % required : no
# % multiple : no
# % gisprompt: old,vector
# % guisection: point data
# %end

# %rules
# %exclusive: nbgp,bgp
# %end

# %option G_OPT_F_OUTPUT
# % key: bgr_output
# % description: Background SWD file
# % required : yes
# % multiple: no
# % guisection: output
# %end

# %option G_OPT_F_OUTPUT
# % key: species_output
# % description: Species SWD file
# % required : no
# % multiple: no
# % guisection: output
# %end

# %rules
# %requires: species_output,species
# %end

# %option G_OPT_F_OUTPUT
# % key: alias_output
# % description: CSV file with alias and map names
# % guisection: output
# % required : no
# %end

# %option G_OPT_M_DIR
# % key: export_rasters
# % description: Folder where to export the predictor raster layers to
# % guisection: output
# % required : no
# %end

# %option
# % key: format
# % description: Raster data format to write (case sensitive, see r.out.gdal)
# % guisection: output
# % required: no
# % options: ascii,GeoTIFF
# %end


# %flag
# % key: h
# % description: skip header in csv
# %end

# %option
# % key: nodata
# % type: integer
# % description: nodata value in output files
# % key_desc: number
# % answer : -9999
# % required: no
# %end

# %option
# % key: seed
# % type: integer
# % required: no
# % multiple: no
# % answer: 1
# % description: Seed for generating random points
# %End


# ----------------------------------------------------------------------------
# Standard
# ----------------------------------------------------------------------------

# import libraries
import os
import sys
import tempfile
import atexit
import sys
import uuid
import grass.script as gs


CLEAN_LAY = []


def create_unique_name(name):
    """Generate a tmp name which contains prefix
    Store the name in the global list.
    Use only for raster maps.
    """
    return name + str(uuid.uuid4().hex)


def create_temporary_name(prefix):
    tmpf = create_unique_name(prefix)
    CLEAN_LAY.append(tmpf)
    return tmpf


def cleanup():
    """Remove temporary maps specified in the global list"""
    maps = reversed(CLEAN_LAY)
    mapset = gs.gisenv()["MAPSET"]
    for map_name in maps:
        for element in ("raster", "vector"):
            found = gs.find_file(
                name=map_name,
                element=element,
                mapset=mapset,
            )
            if found["file"]:
                gs.run_command(
                    "g.remove",
                    flags="f",
                    type=element,
                    name=map_name,
                    quiet=True,
                )


def CreateFileName(outputfile):
    flname = outputfile
    k = 0
    while os.path.isfile(flname):
        k = k + 1
        fn = flname.split(".")
        if len(fn) == 1:
            flname = fn[0] + "_" + str(k)
        else:
            flname = fn[0] + "_" + str(k) + "." + fn[1]
    return flname


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------


def main(options, flags):
    # variables
    evp = options["evp_maps"]
    evp = evp.split(",")
    evpn = options["alias_names"]
    alias_output = options["alias_output"]
    bgrout = options["bgr_output"]
    if os.path.isfile(bgrout):
        bgrout2 = CreateFileName(bgrout)
        gs.message(
            _("The file {} already exist. Using {} instead".format(bgrout, bgrout2))
        )
        bgrout = bgrout2
    bgpn = options["nbgp"]
    nodata = options["nodata"]
    flag_h = flags["h"]
    if flag_h:
        header = "c"
    else:
        header = ""

    # Create list with environmental layers and list with their (alias) names
    if evpn == "":
        evpn = [z.split("@")[0] for z in evp]
    else:
        evpn = evpn.split(",")
    if len(evp) != len(evpn):
        gs.fatal(_("Number of environmental layers does not match number of aliases"))
    evpc = options["evp_cat"]
    if evpc != "":
        evpc = evpc.split(",")
        for k in range(len(evpc)):
            laytype = gs.raster_info(evpc[k])["datatype"]
            if laytype != "CELL":
                gs.fatal(_("Categorical variables need to be of type CELL (integer)"))
        evpcn = options["alias_cat"]
        if evpcn == "":
            evpcn = [z.split("@")[0] for z in evpc]
        else:
            evpcn = evpcn.split(",")
        if len(evpc) != len(evpcn):
            gs.fatal(
                _("Number of environmental layers does not match number of aliases")
            )
        environmental_layers = evp + evpc
        env_vars = evpn + evpcn

    # Write alias output if requested
    if alias_output:
        gs.message(_("Creating alias file"))
        with open(alias_output, "w") as alias_out:
            for idx, name in enumerate(env_vars):
                alias_out.write("{},{}\n".format(name, environmental_layers[idx]))

    # --------------------------------------------------------------------------
    # Export environmental layers
    # --------------------------------------------------------------------------
    if bool(options["export_rasters"]):
        gs.message(_("Exporting environmental raster layers"))
        if options["format"] == "ascii":
            raster_format = "AAIGrid"
            raster_extension = "asc"
        elif options["format"] == "GeoTIFF":
            raster_format = "GTiff"
            raster_extension = "tif"
        else:
            gs.message(
                "Only ascii and geotif are supported. Exporting rasters as ascii"
            )
            raster_format = "AAIGrid"
            raster_extension = "asc"
        if len(evp) > 0:
            for idx, name in enumerate(evp):
                exporturl = os.path.join(
                    options["export_rasters"], f"{evpn[idx]}.{raster_extension}"
                )
                gs.run_command(
                    "r.out.gdal",
                    input=name,
                    output=exporturl,
                    format=raster_format,
                    nodata=int(options["nodata"]),
                    flags="c",
                    quiet=True,
                )
        if len(evpc) > 0:
            for idx, name in enumerate(evpc):
                exporturl = os.path.join(
                    options["export_rasters"], f"{evpcn[idx]}.{raster_extension}"
                )
                gs.run_command(
                    "r.out.gdal",
                    input=name,
                    output=exporturl,
                    format=raster_format,
                    flags="c",
                    type="Int16",
                    nodata=-9999,
                    quiet=True,
                )

    # --------------------------------------------------------------------------
    # Background points
    # --------------------------------------------------------------------------

    # Create / copy to tmp layer
    bgpname = create_temporary_name("bgp")
    gs.message(_("Creating SWD file with background points"))
    if bool(options["bgp"]):
        gs.run_command("g.copy", vector=[options["bgp"], bgpname], quiet=True)
    else:
        if bool(options["seed"]):
            gs.run_command(
                "r.random",
                input=environmental_layers[0],
                npoints=bgpn,
                vector=bgpname,
                quiet=True,
                seed=int(options["seed"]),
            )
        else:
            gs.run_command(
                "r.random",
                input=environmental_layers[0],
                npoints=bgpn,
                vector=bgpname,
                quiet=True,
                flags="s",
            )
        gs.run_command("v.db.droptable", flags="f", map=bgpname, quiet=True)
        gs.run_command("v.db.addtable", map=bgpname, table=bgpname, quiet=True)

    # Upload environmental values for point locations to attribute table
    for j in range(len(env_vars)):
        gs.run_command(
            "v.what.rast",
            map=bgpname,
            raster=environmental_layers[j],
            column=env_vars[j],
            quiet=True,
        )
        sqlst = (
            "update "
            + bgpname
            + " SET "
            + env_vars[j]
            + " = "
            + str(nodata)
            + " WHERE "
            + env_vars[j]
            + " ISNULL"
        )
        gs.run_command("db.execute", sql=sqlst, quiet=True)
    gs.run_command(
        "v.db.addcolumn", map=bgpname, columns="species VARCHAR(250)", quiet=True
    )
    sqlst = "update " + bgpname + " SET species = 'background'"
    gs.run_command("db.execute", sql=sqlst, quiet=True)

    # Upload x and y coordinates
    gs.run_command(
        "v.to.db",
        map=bgpname,
        option="coor",
        columns="Long,Lat",
        quiet=True,
    )

    # Export the data to csv file and remove temporary file
    cols = ["species", "Long", "Lat"] + env_vars
    gs.run_command(
        "v.db.select",
        flags=header,
        map=bgpname,
        columns=cols,
        separator=",",
        file=bgrout,
        quiet=True,
    )

    # --------------------------------------------------------------------------
    # Presence points
    # --------------------------------------------------------------------------
    if bool(options["species"]):
        gs.message(_("Creating SWD file with presence points"))
        bgrdir = tempfile.mkdtemp()

        # Get list with species names
        specs = options["species"]
        specs = specs.split(",")
        specsn = options["species_name"]
        if specsn == "":
            specsn = [z.split("@")[0] for z in specs]
        else:
            specsn = specsn.split(",")
        specout = options["species_output"]

        # Write for each species a temp swd file
        for i in range(len(specs)):
            # Upload environmental values for point locations to attribute table
            bgrtmp = os.path.join(bgrdir, "prespoints{}".format(i))
            specname = create_temporary_name("sp")
            gs.run_command("g.copy", vector=[specs[i], specname], quiet=True)
            for j in range(len(env_vars)):
                gs.run_command(
                    "v.what.rast",
                    map=specname,
                    raster=environmental_layers[j],
                    column=env_vars[j],
                    quiet=True,
                )
                sqlst = f"update {specname} SET {env_vars[j]} = {str(nodata)} WHERE {env_vars[j]} ISNULL"
                gs.run_command("db.execute", sql=sqlst, quiet=True)
            gs.run_command(
                "v.db.addcolumn",
                map=specname,
                columns="species VARCHAR(250)",
                quiet=True,
            )
            sqlst = f"update {specname} SET species = '{specsn[i]}'"
            gs.run_command("db.execute", sql=sqlst, quiet=True)

            # Upload x and y coordinates
            gs.run_command(
                "v.to.db",
                map=specname,
                option="coor",
                columns="Long,Lat",
                quiet=True,
            )

            # Export the data to csv file and remove temporary file
            if header == "" and i == 0:
                gs.run_command(
                    "v.db.select",
                    map=specname,
                    columns=cols,
                    separator=",",
                    file=bgrtmp,
                    quiet=True,
                )
            else:
                gs.run_command(
                    "v.db.select",
                    flags="c",
                    map=specname,
                    columns=cols,
                    separator=",",
                    file=bgrtmp,
                    quiet=True,
                )

        # Combine species swd files
        filenames = os.path.join(bgrdir, "prespoints")
        filenames = [filenames + str(i) for i in range(len(specs))]
        with open(specout, "w") as outfile:
            for fname in filenames:
                with open(fname) as infile:
                    outfile.write(infile.read().rstrip() + "\n")

        # Remove temporary text files
        for m in filenames:
            os.remove(m)


if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main(*gs.parser()))
