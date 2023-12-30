#!/usr/bin/env python

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
# COPYRIGHT:   (C) 2015-2019 Paulo van Breugel and the GRASS Development Team
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
# % required : yes
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

# %flag
# % key: e
# % description: include the original columns in input layers in export to swd file
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
# % required : yes
# % multiple: no
# % guisection: output
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

# ----------------------------------------------------------------------------
# Standard
# ----------------------------------------------------------------------------

# import libraries
import os
import sys
import grass.script as grass
import numpy as np
import string
import uuid
import atexit
import tempfile

# ----------------------------------------------------------------------------
# Standard
# ----------------------------------------------------------------------------

# create set to store names of temporary maps to be deleted upon exit
clean_rast = set()


def cleanup():
    for rast in clean_rast:
        grass.run_command("g.remove", type="rast", name=rast, quiet=True)


# ----------------------------------------------------------------------------
# Functions
# ----------------------------------------------------------------------------

# Create temporary name
def tmpname(name):
    tmpf = name + "_" + str(uuid.uuid4())
    tmpf = string.replace(tmpf, "-", "_")
    clean_rast.add(tmpf)
    return tmpf


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


def main():

    # options = {"species":"species1@plantspecies,species2","species_name":"", "evp_maps":"bio_1@climate,bio_2@climate,bio_3@climate", "alias_names":"BIO1,BIO2,bio3", "evp_cat":"tmpcategory@plantspecies","alias_cat":"categ","bgr_output":"swd_bgr.csv", "species_output":"swd_spec.csv", "nbgp":1000, "bgp":"", "nodata":-9999}
    # flags = {"e":False, "h":False}

    # --------------------------------------------------------------------------
    # Variables
    # --------------------------------------------------------------------------

    # variables
    specs = options["species"]
    specs = specs.split(",")
    specsn = options["species_name"]
    if specsn == "":
        specsn = [z.split("@")[0] for z in specs]
    else:
        specsn = specsn.split(",")
    evp = options["evp_maps"]
    evp = evp.split(",")
    evpn = options["alias_names"]
    bgrout = options["bgr_output"]
    if os.path.isfile(bgrout):
        bgrout2 = CreateFileName(bgrout)
        grass.message(
            "The file " + bgrout + " already exist. Using " + bgrout2 + " instead"
        )
        bgrout = bgrout2
    specout = options["species_output"]
    bgp = options["bgp"]
    bgpn = options["nbgp"]
    nodata = options["nodata"]
    flag_e = flags["e"]
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
        grass.fatal("Number of environmental layers does not match number of aliases")
    evp_cols = [s + " DOUBLE PRECISION" for s in evpn]
    evpc = options["evp_cat"]
    if evpc != "":
        evpc = evpc.split(",")
        for k in range(len(evpc)):
            laytype = grass.raster_info(evpc[k])["datatype"]
            if laytype != "CELL":
                grass.fatal("Categorical variables need to be of type CELL (integer)")
        evpcn = options["alias_cat"]
        if evpcn == "":
            evpcn = [z.split("@")[0] for z in evpc]
        else:
            evpcn = evpcn.split(",")
        evpcn = ["cat_" + s for s in evpcn]
        evpc_cols = [s + " INTEGER" for s in evpcn]
        evp = evp + evpc
        evpn = evpn + evpcn
        evp_cols = evp_cols + evpc_cols
    evp_cols = [
        "species VARCHAR(250)",
        "Long DOUBLE PRECISION",
        "Lat DOUBLE PRECISION",
    ] + evp_cols

    # --------------------------------------------------------------------------
    # Background points
    # --------------------------------------------------------------------------

    # Create / copy to tmp layer
    bgpname = tmpname("bgp")
    if bgp == "":
        grass.run_command(
            "r.random", input=evp[0], npoints=bgpn, vector=bgpname, quiet=True
        )
        grass.run_command("v.db.droptable", flags="f", map=bgpname, quiet=True)
        grass.run_command("v.db.addtable", map=bgpname, table=bgpname, quiet=True)
    else:
        grass.run_command("g.copy", vector=[bgpn, bgpname], quiet=True)
    grass.run_command("v.db.addcolumn", map=bgpname, columns=evp_cols, quiet=True)

    # Upload environmental values for point locations to attribute table
    for j in range(len(evpn)):
        grass.run_command(
            "v.what.rast", map=bgpname, raster=evp[j], column=evpn[j], quiet=True
        )
        sqlst = (
            "update "
            + bgpname
            + " SET "
            + evpn[j]
            + " = "
            + str(nodata)
            + " WHERE "
            + evpn[j]
            + " ISNULL"
        )
        grass.run_command("db.execute", sql=sqlst, quiet=True)
    sqlst = "update " + bgpname + " SET species = 'background'"
    grass.run_command("db.execute", sql=sqlst, quiet=True)

    # Upload x and y coordinates
    grass.run_command(
        "v.to.db", map=bgpname, option="coor", columns="Long,Lat", quiet=True
    )

    # Export the data to csv file and remove temporary file
    if flag_e:
        grass.run_command(
            "v.db.select",
            flags=header,
            map=bgpname,
            columns="*",
            separator=",",
            file=bgrout,
            quiet=True,
        )
    else:
        cols = ["Long", "Lat", "species"] + evpn
        grass.run_command(
            "v.db.select",
            flags=header,
            map=bgpname,
            columns=cols,
            separator=",",
            file=bgrout,
            quiet=True,
        )
    grass.run_command("g.remove", type="vector", name=bgpname, flags="f", quiet=True)

    # --------------------------------------------------------------------------
    # Presence points
    # --------------------------------------------------------------------------
    bgrdir = tempfile.mkdtemp()
    for i in range(len(specs)):
        specname = tmpname("sp")
        bgrtmp = bgrdir + "/prespoints" + str(i)
        grass.run_command("g.copy", vector=[specs[i], specname], quiet=True)
        grass.run_command("v.db.addcolumn", map=specname, columns=evp_cols, quiet=True)

        # Upload environmental values for point locations to attribute table
        for j in range(len(evpn)):
            grass.run_command(
                "v.what.rast", map=specname, raster=evp[j], column=evpn[j], quiet=True
            )
            sqlst = (
                "update "
                + specname
                + " SET "
                + evpn[j]
                + " = "
                + str(nodata)
                + " WHERE "
                + evpn[j]
                + " ISNULL"
            )
            grass.run_command("db.execute", sql=sqlst, quiet=True)
        sqlst = "update " + specname + " SET species = '" + specsn[i] + "'"
        grass.run_command("db.execute", sql=sqlst, quiet=True)

        # Upload x and y coordinates
        grass.run_command(
            "v.to.db", map=specname, option="coor", columns="Long,Lat", quiet=True
        )

        # Export the data to csv file and remove temporary file
        if flag_e:
            if flag_h and i == 0:
                grass.run_command(
                    "v.db.select",
                    map=specname,
                    columns="*",
                    separator=",",
                    file=bgrtmp,
                    quiet=True,
                )
            else:
                grass.run_command(
                    "v.db.select",
                    flags="c",
                    map=specname,
                    columns="*",
                    separator=",",
                    file=bgrtmp,
                    quiet=True,
                )
        else:
            cols = ["species"] + evpn
            if header == "" and i == 0:
                grass.run_command(
                    "v.db.select",
                    map=specname,
                    columns=cols,
                    separator=",",
                    file=bgrtmp,
                    quiet=True,
                )
            else:
                grass.run_command(
                    "v.db.select",
                    flags="c",
                    map=specname,
                    columns=cols,
                    separator=",",
                    file=bgrtmp,
                    quiet=True,
                )
        grass.run_command(
            "g.remove", type="vector", name=specname, flags="f", quiet=True
        )

    # Combine csv files
    filenames = bgrdir + "/prespoints"
    filenames = [filenames + str(i) for i in range(len(specs))]
    with open(specout, "w") as outfile:
        for fname in filenames:
            with open(fname) as infile:
                outfile.write(infile.read().rstrip() + "\n")

    # Remove temporary text files
    for m in filenames:
        os.remove(m)


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())
