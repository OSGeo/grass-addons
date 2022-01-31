#!/usr/bin/env python

"""Import CSV as vector points with attributes into GRASS GIS

Uses pyproj for CRS transformation, temporary file for the intermediate data,
and v.in.ascii for import.
"""

# %module
# % label: Import a CSV file using pyproj for CRS transformation
# % keyword: vector
# % keyword: import
# % keyword: projection
# % keyword: transformation
# % keyword: point
# % keyword: ASCII
# % keyword: CSV
# %end
# %option G_OPT_F_INPUT
# %end
# %option G_OPT_V_OUTPUT
# %end
# %option G_OPT_F_SEP
# % answer: comma
# % required: yes
# %end
# %option
# % key: latitude
# % type: string
# % required: yes
# % multiple: no
# % label: Name of column used as latitude
# %end
# %option
# % key: longitude
# % type: string
# % required: yes
# % multiple: no
# % label: Name of column used as longitude
# %end
# %option
# % key: crs
# % type: string
# % label: Coordinate reference system (CRS) of the coordinates
# % description: EPSG code (e.g. 4326 or EPSG:4326), WKT string, and PROJ string are recognized
# % required: yes
# % answer: EPSG:4326
# %end
# %option
# % key: limit
# % type: integer
# % label: Limit number of lines processed
# % required: no
# % options: 1-
# %end
# %option
# % key: int_columns
# % type: string
# % required: no
# % multiple: yes
# % label: Names of columns which are integers
# % guisection: Points
# %end
# %option
# % key: real_columns
# % type: string
# % required: no
# % multiple: yes
# % label: Names of columns which are double floating point numbers (floats)
# % guisection: Points
# %end

import os
import sys
import csv
import re
import tempfile
import atexit

import grass.script as gs

try:
    # GRASS GIS >= 8.0
    from grass.script import legalize_vector_name as make_name_sql_compliant
except ImportError:

    def make_name_sql_compliant(name, fallback_prefix="x"):
        """Make *name* usable for vectors, tables, and columns

        This is a simplified copy of the legalize_vector_name() function
        from the library (not available in 7.8).
        """
        if fallback_prefix and re.match("[^A-Za-z]", name[0], flags=re.ASCII):
            name = "{fallback_prefix}{name}".format(**locals())
        name = re.sub("[^A-Za-z0-9_]", "_", name, flags=re.ASCII)
        keywords = ["and", "or", "not"]
        if name in keywords:
            name = "{name}_".format(**locals())
        return name


def get_current_crs():
    """Get CRS of the current location"""
    # Note that EPSG as only authority and PROJ string is kind of old-style.
    to_g_proj = gs.parse_command("g.proj", flags="g")
    if "epsg" in to_g_proj:
        return "EPSG:{epsg}".format(epsg=to_g_proj["epsg"])
    return gs.read_command("g.proj", flags="jf")


def get_header_from_csv(input_filename, separator):
    """Get names of columns from the header of a CSV file"""
    fieldnames = []
    with open(input_filename) as infile:
        reader = csv.reader(infile, delimiter=separator)
        for i, row in enumerate(reader):
            if i == 0:
                for col in row:
                    fieldnames.append(col)
            else:
                break
    return fieldnames


def names_to_sql_columns(names, float_names, int_names):
    """Convert list of names to SQL column definition

    Creates definition of columns for an SQL statement.
    Non-compliant names are fixed.
    The original names are assumed to be unique.
    """
    sql_columns = []
    bad_name_prefix = "col_"

    for name in names:
        if name in float_names:
            sql_type = "REAL"
        elif name in int_names:
            sql_type = "INTEGER"
        else:
            sql_type = "TEXT"
        # Catch and fix SQL non-compliant names.
        old_name = name
        name = make_name_sql_compliant(name, fallback_prefix=bad_name_prefix)
        if name != old_name:
            gs.verbose(_("Renaming <{old_name}> to <{name}>").format(**locals()))
        sql_columns.append((name, sql_type))
    # Format as "name1 type1,name2 type2".
    sql_columns = [" ".join(column) for column in sql_columns]
    return ", ".join(sql_columns)


def get_tmp_file_name():
    """Get a name (full path) of a temporary file.

    Deletes the file at program exit which is appropriate for modules and scripts.
    """
    # We are responsible for deleting the file.
    tmp_file = tempfile.NamedTemporaryFile(delete=False)
    tmp_file.close()  # Closed but still exists.
    atexit.register(lambda: os.remove(tmp_file.name))
    return tmp_file.name


def main():
    """Import file according to the command line parameters"""
    # Allow more locals in the main.
    # pylint: disable=too-many-locals
    options, unused_flags = gs.parser()

    # Requires pyproj >= 2.2.0
    # Lazy importing pyproj because it is not a dependency of GRASS GIS.
    from pyproj import Transformer  # pylint: disable=import-outside-toplevel

    to_crs = get_current_crs()
    # We assign xy as result, so we need to keep the en ordering.
    transformer = Transformer.from_crs(
        options["crs"], to_crs, always_xy=True, skip_equivalent=True
    )

    input_filename = options["input"]
    output_map = options["output"]
    lat_name = options["latitude"]
    lon_name = options["longitude"]

    separator = gs.separator(options["separator"])

    integer_names = options["int_columns"].split(",")
    float_names = options["real_columns"].split(",")

    # Lat and lon as doubles because we require that anyway.
    float_names.extend([lat_name, lon_name])

    if options["limit"]:
        limit = int(options["limit"])
    else:
        limit = None
    assert limit is None or limit >= 1, "Check limit option definition"

    fieldnames = get_header_from_csv(input_filename, separator)
    if "X" not in fieldnames and "Y" not in fieldnames:
        # If there is X and Y, we will replace is content.
        fieldnames.extend(["X", "Y"])
        float_names.extend(["X", "Y"])
        y_index = len(fieldnames)  # One-based index in v.in.ascii
        x_index = y_index - 1
    else:
        y_index = fieldnames.index("Y") + 1
        x_index = fieldnames.index("X") + 1

    tmp_file = get_tmp_file_name()

    with open(input_filename) as infile, open(tmp_file, mode="w") as outfile:
        reader = csv.DictReader(infile, delimiter=separator)
        writer = csv.DictWriter(
            outfile,
            fieldnames=fieldnames,
            delimiter=separator,
            quotechar='"',
            lineterminator="\n",
        )
        writer.writeheader()
        for i, row in enumerate(reader):
            if limit and i >= limit:
                break
            lon = float(row[lon_name])
            lat = float(row[lat_name])
            x, y = transformer.transform(lon, lat)
            row["X"] = x
            row["Y"] = y
            writer.writerow(row)

    sql_columns = names_to_sql_columns(fieldnames, float_names, integer_names)

    gs.run_command(
        "v.in.ascii",
        input=tmp_file,
        output=output_map,
        format="point",
        separator=separator,
        text='"',
        skip=1,
        columns=sql_columns,
        x=x_index,
        y=y_index,
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
