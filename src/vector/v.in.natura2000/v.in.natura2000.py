#!/usr/bin/env python

"""
MODULE:    v.in.natura2000

AUTHOR(S): Helmut Kudrnovsky <alectoria AT gmx at>

PURPOSE:   Imports Natura 2000 spatial data of protected areas

COPYRIGHT: (C) 2015 by the GRASS Development Team

           This program is free software under the GNU General Public
           License (>=v2). Read the file COPYING that comes with GRASS
           for details.
"""

# %module
# % description: importing of Natura 2000 spatial data of protected areas
# % keyword: vector
# % keyword: geometry
# %end

# %option G_OPT_F_BIN_INPUT
# % key: input
# % required: yes
# %end

# %option G_OPT_V_OUTPUT
# % key: output
# % description: name of imported spatial data set
# % required : no
# % guisection: output
# %end

# %option sitetype
# % key: sitetype
# % description: Select site type of input (A, B or C)
# % required : no
# % guisection: selection
# %end

# %option habitat_code
# % key: habitat_code
# % description: Select habitat code of input
# % required : no
# % guisection: selection
# %end

# %option species_code
# % key: species_code
# % description: Select species of input
# % required : no
# % guisection: selection
# %end

# %option biogeographic_region
# % key: biogeographic_region
# % description: Select biogeographic region of input
# % required : no
# % guisection: selection
# %end

# %option member_state
# % key: member_state
# % description: Select member state of input
# % required : no
# % guisection: selection
# %end

# %option existing_layer
# % key: existing_layer
# % description: Import of existing layer
# % required : no
# % guisection: layer
# %end

# %flag
# % key: l
# % description: Print available layer
# % guisection: layer
# %end

# %flag
# % key: b
# % description: Print list of biogeographic regions
# % guisection: print
# %end

# %flag
# % key: m
# % description: Print list of EU member states codes
# % guisection: print
# %end

# %flag
# % key: h
# % description: Print list of habitats of community interest
# % guisection: print
# %end

# %flag
# % key: s
# % description: Print list of species of community interest
# % guisection: print
# %end

# %flag
# % key: t
# % description: Print list of protected area site types
# % guisection: print
# %end

import sys
import os
import csv
import math
import shutil
import tempfile
import grass.script as grass


def main():

    n2k_input = options["input"]
    n2k_output = options["output"]
    pa_sitetype_input = options["sitetype"]
    habitat_code_input = options["habitat_code"]
    species_code_input = options["species_code"]
    biogeoreg_long = options["biogeographic_region"]
    biogeoreg_long2 = biogeoreg_long.replace(" ", "_")
    biogeoreg_long_quoted = '"' + biogeoreg_long + '"'
    habitat_view = "v" + habitat_code_input
    habitat_spatial_view = "sv" + habitat_code_input
    species_view = "v" + species_code_input
    species_spatial_view = "sv" + species_code_input
    biogeoreg_view = "v" + biogeoreg_long2
    biogeoreg_spatial_view = "sv" + biogeoreg_long2
    ms_input = options["member_state"]
    layer_exist = options["existing_layer"]
    list_n2k_layer = flags["l"]
    list_bg_reg = flags["b"]
    list_ms = flags["m"]
    list_habitats = flags["h"]
    list_species = flags["s"]
    list_site_type = flags["t"]
    global tmp

    try:
        import pyspatialite.dbapi2 as db
    except:
        grass.fatal(
            "pyspatialite is needed to run this script.\n"
            "source: https://pypi.python.org/pypi/pyspatialite \n"
            "Please activate/install it in your python stack."
        )

    if list_n2k_layer:
        grass.message("Available data layer(s):")
        grass.message("may take some time ...")
        grass.message("...")
        grass.run_command("v.in.ogr", input=n2k_input, flags="l")

    if list_bg_reg:
        grass.message("Biogeographic regions:")
        conn = db.connect("%s" % n2k_input)
        c = conn.cursor()
        for row in c.execute(
            "SELECT BIOGEFRAPHICREG FROM BIOREGION GROUP BY BIOGEFRAPHICREG"
        ):
            grass.message(row)
        conn.close()

    if list_ms:
        grass.message("EU member states:")
        conn = db.connect("%s" % n2k_input)
        c = conn.cursor()
        for row in c.execute("SELECT MS FROM Natura2000polygon GROUP BY MS"):
            grass.message(row)
        conn.close()

    if list_habitats:
        grass.message("habitat codes of EU community interest:")
        conn = db.connect("%s" % n2k_input)
        c = conn.cursor()
        try:
            for row in c.execute(
                "SELECT HABITATCODE, DESCRIPTION FROM HABITATS GROUP BY HABITATCODE"
            ):
                grass.message(row)
        except:
            pass
            grass.warning(
                "Some problems querying habitat code or names occurred."
                " Please check columns HABITATCODE and DESCRIPTION of table HABITATS in the sqlite database."
            )
        conn.close()

    if list_species:
        grass.message("species codes of EU community interest:")
        conn = db.connect("%s" % n2k_input)
        c = conn.cursor()
        try:
            for row in c.execute(
                "SELECT SPECIESCODE, SPECIESNAME FROM SPECIES GROUP BY SPECIESCODE"
            ):
                grass.message(row)
        except:
            pass
            grass.warning(
                "Some problems querying species code or names occurred."
                " Please check columns SPECIESCODE and SPECIESNAME of table SPECIES in the sqlite database."
            )
        conn.close()

    if list_site_type:
        grass.message("site types:")
        conn = db.connect("%s" % n2k_input)
        c = conn.cursor()
        for row in c.execute("SELECT SITETYPE FROM NATURA2000SITES GROUP BY SITETYPE"):
            grass.message(row)
        conn.close()

    if pa_sitetype_input:
        grass.message("importing protected areas of site type: %s" % pa_sitetype_input)
        grass.message("may take some time ...")
        grass.run_command(
            "v.in.ogr",
            input="%s" % (n2k_input),
            layer="natura2000polygon",
            output=n2k_output,
            where="SITETYPE = '%s'" % (pa_sitetype_input),
            quiet=False,
        )

    if ms_input:
        grass.message("importing protected areas of member state: %s" % ms_input)
        grass.message("may take some time ...")
        grass.run_command(
            "v.in.ogr",
            input="%s" % (n2k_input),
            layer="natura2000polygon",
            output=n2k_output,
            where="MS = '%s'" % (ms_input),
            quiet=False,
        )

    if habitat_code_input:
        grass.message(
            "importing protected areas with habitat (code): %s" % habitat_code_input
        )
        grass.message("preparing (spatial) views in the sqlite/spatialite database:")
        conn = db.connect("%s" % n2k_input)
        c = conn.cursor()
        # create view of defined habitat
        grass.message("view: %s" % habitat_view)
        sqlhabitat = 'CREATE VIEW "%s" AS ' % (habitat_view)
        sqlhabitat += "SELECT * FROM HABITATS "
        sqlhabitat += 'WHERE HABITATCODE = "%s" ' % (habitat_code_input)
        sqlhabitat += 'ORDER BY "SITECODE"'
        grass.message(sqlhabitat)
        c.execute(sqlhabitat)
        # create spatial view of defined habitat - part 1
        grass.message("spatial view: %s" % habitat_spatial_view)
        sqlhabitatspatial1 = 'CREATE VIEW "%s" AS ' % (habitat_spatial_view)
        sqlhabitatspatial1 += (
            'SELECT "a"."ROWID" AS "ROWID", "a"."PK_UID" AS "PK_UID", '
        )
        sqlhabitatspatial1 += (
            '"a"."SITECODE" AS "SITECODE", "a"."SITENAME" AS "SITENAME", '
        )
        sqlhabitatspatial1 += '"a"."RELEASE_DA" AS "RELEASE_DA", "a"."MS" AS "MS", '
        sqlhabitatspatial1 += (
            '"a"."SITETYPE" AS "SITETYPE", "a"."Geometry" AS "Geometry", '
        )
        sqlhabitatspatial1 += '"b"."SITECODE" AS "SITECODE_1", "b"."HABITATCODE" AS "HABITATCODE", "b"."DESCRIPTION" AS "DESCRIPTION", '
        sqlhabitatspatial1 += '"b"."COVER_HA" AS "COVER_HA", "b"."CAVES" AS "CAVES", "b"."REPRESENTATIVITY" AS "REPRESENTATIVITY", '
        sqlhabitatspatial1 += (
            '"b"."RELSURFACE" AS "RELSURFACE", "b"."CONSERVATION" AS "CONSERVATION", '
        )
        sqlhabitatspatial1 += '"b"."GLOBAL_ASSESMENT" AS "GLOBAL_ASSESMENT", "b"."DATAQUALITY" AS "DATAQUALITY", '
        sqlhabitatspatial1 += '"b"."PERCENTAGECOVER" AS "PERCENTAGECOVER" '
        sqlhabitatspatial1 += 'FROM "Natura2000polygon" AS "a" '
        sqlhabitatspatial1 += 'JOIN %s AS "b" USING ("SITECODE") ' % (habitat_view)
        sqlhabitatspatial1 += 'ORDER BY "a"."SITECODE";'
        grass.message(sqlhabitatspatial1)
        c.execute(sqlhabitatspatial1)
        # create spatial view of defined habitat - part 2
        sqlhabitatspatial2 = "INSERT INTO views_geometry_columns "
        sqlhabitatspatial2 += "(view_name, view_geometry, view_rowid, f_table_name, f_geometry_column, read_only) "
        sqlhabitatspatial2 += (
            'VALUES ("%s", "geometry", "rowid", "natura2000polygon", "geometry", 1);'
            % (habitat_spatial_view.lower())
        )
        grass.message(sqlhabitatspatial2)
        # execute spatial vieww
        c.execute(sqlhabitatspatial2)
        conn.commit()
        conn.close()
        # import spatial view
        grass.message("importing data...")
        grass.message("may take some time...")
        grass.run_command(
            "v.in.ogr",
            input="%s" % (n2k_input),
            layer="%s" % (habitat_spatial_view),
            output=n2k_output,
            quiet=False,
        )

    if species_code_input:
        grass.message(
            "importing protected areas with species (code): %s" % species_code_input
        )
        grass.message("preparing (spatial) views in the sqlite/spatialite database:")
        conn = db.connect("%s" % n2k_input)
        c = conn.cursor()
        # create view of defined species
        grass.message("view: %s" % species_view)
        sqlspecies = 'CREATE VIEW "%s" AS ' % (species_view)
        sqlspecies += "SELECT * FROM SPECIES "
        sqlspecies += 'WHERE SPECIESCODE = "%s" ' % (species_code_input)
        sqlspecies += 'ORDER BY "SITECODE"'
        grass.message(sqlspecies)
        c.execute(sqlspecies)
        # create spatial view of defined species - part 1
        grass.message("spatial view: %s" % species_spatial_view)
        sqlspeciesspatial1 = 'CREATE VIEW "%s" AS ' % (species_spatial_view)
        sqlspeciesspatial1 += (
            'SELECT "a"."ROWID" AS "ROWID", "a"."PK_UID" AS "PK_UID", '
        )
        sqlspeciesspatial1 += (
            '"a"."SITECODE" AS "SITECODE", "a"."SITENAME" AS "SITENAME", '
        )
        sqlspeciesspatial1 += '"a"."RELEASE_DA" AS "RELEASE_DA", "a"."MS" AS "MS", '
        sqlspeciesspatial1 += (
            '"a"."SITETYPE" AS "SITETYPE", "a"."Geometry" AS "Geometry", '
        )
        sqlspeciesspatial1 += (
            '"b"."COUNTRY_CODE" AS "COUNTRY_CODE", "b"."SITECODE" AS "SITECODE_1", '
        )
        sqlspeciesspatial1 += (
            '"b"."SPECIESNAME" AS "SPECIESNAME", "b"."SPECIESCODE" AS "SPECIESCODE", '
        )
        sqlspeciesspatial1 += (
            '"b"."REF_SPGROUP" AS "REF_SPGROUP", "b"."SPGROUP" AS "SPGROUP", '
        )
        sqlspeciesspatial1 += '"b"."SENSITIVE" AS "SENSITIVE", "b"."NONPRESENCEINSITE" AS "NONPRESENCEINSITE", '
        sqlspeciesspatial1 += '"b"."POPULATION_TYPE" AS "POPULATION_TYPE", "b"."LOWERBOUND" AS "LOWERBOUND", '
        sqlspeciesspatial1 += (
            '"b"."UPPERBOUND" AS "UPPERBOUND", "b"."COUNTING_UNIT" AS "COUNTING_UNIT", '
        )
        sqlspeciesspatial1 += '"b"."ABUNDANCE_CATEGORY" AS "ABUNDANCE_CATEGORY", '
        sqlspeciesspatial1 += (
            '"b"."DATAQUALITY" AS "DATAQUALITY", "b"."POPULATION" AS "POPULATION", '
        )
        sqlspeciesspatial1 += (
            '"b"."CONSERVATION" AS "CONSERVATION", "b"."ISOLATION" AS "ISOLATION", '
        )
        sqlspeciesspatial1 += '"b"."GLOBAL" AS "GLOBAL" '
        sqlspeciesspatial1 += 'FROM "Natura2000polygon" AS "a" '
        sqlspeciesspatial1 += 'JOIN %s AS "b" USING ("SITECODE") ' % (species_view)
        sqlspeciesspatial1 += 'ORDER BY "a"."SITECODE";'
        grass.message(sqlspeciesspatial1)
        c.execute(sqlspeciesspatial1)
        # create spatial view of defined habitat - part 2
        sqlspeciesspatial2 = "INSERT INTO views_geometry_columns "
        sqlspeciesspatial2 += "(view_name, view_geometry, view_rowid, f_table_name, f_geometry_column, read_only) "
        sqlspeciesspatial2 += (
            'VALUES ("%s", "geometry", "rowid", "natura2000polygon", "geometry", 1);'
            % (species_spatial_view.lower())
        )
        grass.message(sqlspeciesspatial2)
        # execute spatial view
        c.execute(sqlspeciesspatial2)
        conn.commit()
        conn.close()
        # import spatial view
        grass.message("importing data...")
        grass.message("may take some time...")
        grass.run_command(
            "v.in.ogr",
            input="%s" % (n2k_input),
            layer="%s" % (species_spatial_view),
            output=n2k_output,
            quiet=False,
        )

    if biogeoreg_long:
        grass.message(
            "importing protected areas of biogeographic region: %s" % biogeoreg_long
        )
        grass.message("preparing (spatial) views in the sqlite/spatialite database:")
        conn = db.connect("%s" % n2k_input)
        c = conn.cursor()
        # create view of defined biogeographic region
        grass.message("view: %s" % biogeoreg_view)
        sqlbioreg = 'CREATE VIEW "%s" AS ' % (biogeoreg_view)
        sqlbioreg += "SELECT * FROM BIOREGION "
        sqlbioreg += 'WHERE BIOGEFRAPHICREG = "%s" ' % (biogeoreg_long)
        sqlbioreg += 'ORDER BY "SITECODE"'
        grass.message(sqlbioreg)
        c.execute(sqlbioreg)
        # create spatial view of defined biogeographical region - part 1
        grass.message("spatial view: %s" % biogeoreg_spatial_view)
        sqlbioregspatial1 = 'CREATE VIEW "%s" AS ' % (biogeoreg_spatial_view)
        sqlbioregspatial1 += 'SELECT "a"."ROWID" AS "ROWID", "a"."PK_UID" AS "PK_UID", '
        sqlbioregspatial1 += '"a"."RELEASE_DA" AS "RELEASE_DA", "a"."MS" AS "MS", '
        sqlbioregspatial1 += (
            '"a"."SITETYPE" AS "SITETYPE", "a"."Geometry" AS "Geometry", '
        )
        sqlbioregspatial1 += '"b"."SITECODE" AS "SITECODE_1", "b"."BIOGEFRAPHICREG" AS "BIOGEFRAPHICREG", '
        sqlbioregspatial1 += '"b"."PERCENTAGE" AS "PERCENTAGE" '
        sqlbioregspatial1 += 'FROM "Natura2000polygon" AS "a" '
        sqlbioregspatial1 += 'JOIN %s AS "b" USING ("SITECODE") ' % (biogeoreg_view)
        sqlbioregspatial1 += 'ORDER BY "a"."SITECODE";'
        grass.message(sqlbioregspatial1)
        c.execute(sqlbioregspatial1)
        # create spatial view of defined biogeographical region - part 2
        sqlbioregspatial2 = "INSERT INTO views_geometry_columns "
        sqlbioregspatial2 += "(view_name, view_geometry, view_rowid, f_table_name, f_geometry_column, read_only) "
        sqlbioregspatial2 += (
            'VALUES ("%s", "geometry", "rowid", "natura2000polygon", "geometry", 1);'
            % (biogeoreg_spatial_view.lower())
        )
        grass.message(sqlbioregspatial2)
        # execute spatial view
        c.execute(sqlbioregspatial2)
        conn.commit()
        conn.close()
        # import spatial view
        grass.message("importing data...")
        grass.message("may take some time...")
        grass.run_command(
            "v.in.ogr",
            input="%s" % (n2k_input),
            layer="%s" % (biogeoreg_spatial_view),
            output=n2k_output,
            quiet=False,
        )

    if layer_exist:
        grass.message(
            "importing existing spatial layer %s of the dataset" % layer_exist
        )
        grass.run_command(
            "v.in.ogr",
            input="%s" % (n2k_input),
            layer="%s" % (layer_exist),
            output=n2k_output,
            quiet=False,
        )


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
