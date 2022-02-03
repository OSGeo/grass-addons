#!/usr/bin/env python3

############################################################################
#
# MODULE:       v.db.pyupdate
#
# AUTHOR(S):    Vaclav Petras
#
# PURPOSE:      Update a column values using Python expressions
#
# COPYRIGHT:    (C) 2020 by Vaclav Petras and the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

"""Update GRASS GIS vector attributes using Python expressions.

This executable script is a GRASS GIS module to run in a GRASS GIS session.
"""

# %module
# % description: Updates a column in a vector attribute table using Python code
# % keyword: vector
# % keyword: attribute table
# % keyword: database
# % keyword: attribute update
# % keyword: Python
# %end
# %option G_OPT_V_MAP
# %end
# %option G_OPT_V_FIELD
# % required: yes
# %end
# %option G_OPT_DB_WHERE
# % label: WHERE condition of the initial SQL statement
# % description: A standard SQL which will reduce the number of rows processed in Python
# %end
# %option G_OPT_DB_COLUMN
# % key: column
# % description: Name of attribute column to update
# % required: yes
# %end
# %option
# % key: expression
# % type: string
# % label: Python expression to compute the new value
# % description: Example: name.replace('-', ' ')
# % required: yes
# %end
# %option
# % key: condition
# % type: string
# % label: Python expression to select only subset of rows
# % description: Example: name.startswith('North')
# %end
# %option
# % key: packages
# % type: string
# % label: Python packages to import
# % description: The math package is always imported for convenience
# % multiple: yes
# %end
# %option G_OPT_F_INPUT
# % key: functions
# % label: Name of Python file defining functions for expression and condition
# % description: This file can contain imports and it will loaded before expression and condition are evaluated
# % required: no
# %end
# %flag
# % key: s
# % label: Import all functions from specificed packages
# % description: Packages will be additionally imported using star imports (from package import *)
# %end
# %flag
# % key: u
# % label: Do not provide the additional lower-cased column names
# % description: Attributes will be accessible only using the original (often uppercase) column name
# %end
# %rules
# % requires: -s,packages
# %end

import os
import json
import csv

# Importing so that it available to the expression.
import math  # noqa: F401 pylint: disable=unused-import

import grass.script as gs


SQL_INT_TYPES = [
    "INT",
    "INTEGER",
    "TINYINT",
    "SMALLINT",
    "MEDIUMINT",
    "BIGINT",
    "UNSIGNED BIG INT",
    "INT2",
    "INT8",
]
SQL_FLOAT_TYPES = [
    "REAL",
    "DOUBLE",
    "DOUBLE PRECISION",
    "FLOAT",
    "FLOATING POINT",
]


def python_to_transaction(
    table,
    table_contents,
    column,
    column_type,
    expression,
    expression_function,
    condition,
    condition_function,
    ensure_lowercase,
):
    """Apply Python functions and create SQL"""
    not_quoted_types = SQL_INT_TYPES + SQL_FLOAT_TYPES
    cmd = ["BEGIN TRANSACTION"]  # Makes execution significantly faster
    for row in table_contents:
        kwargs = {}
        for key, value in row.items():
            # Translate NULL representation to None
            # TODO: Is this just a workaround for a bug in v.db.select -j?
            if value == key:
                kwargs[key] = None
                if ensure_lowercase:
                    kwargs[key.lower()] = None
            else:
                # Type is determined through JSON, so assuming it is correct.
                kwargs[key] = value
                if ensure_lowercase:
                    kwargs[key.lower()] = value
            # TODO: fix variables which are Python keywords
        if condition and not condition_function(**kwargs):
            # No Python condition or condition evaluates as False
            continue
        # TODO: Add specific error handling for wrong column names?
        try:
            value = expression_function(**kwargs)
        except Exception as error:  # pylint: disable=broad-except
            attributes = []
            for key, value in kwargs.items():
                # Limit the number of attributes shown in the message.
                max_attrs_show = 3
                if len(attributes) >= max_attrs_show:
                    attributes.append("...")
                    break
                # Try to show the relevant attributes. The "relevant" does not
                # apply when they are misspelled.
                # TODO: Merge with the case for all misspelled where this won't show
                # any.
                if key in expression:
                    attributes.append(f"{key}={value}")
            if not attributes:
                # TODO: needs to be more systematic regarding number of items and format str/int/float
                attributes = [f"{key}={value}" for key, value in kwargs.items()][:3]
                attributes.append("...")
            gs.fatal(
                _(
                    "Evaluation of expression <{expression}...>"
                    " where {attributes} failed with: {error}"
                ).format(
                    expression=expression[:20],  # TODO: short expressions without ...
                    attributes=", ".join(attributes),
                    error=error,
                )
            )
        if value is None:
            # Translate None to SQL NULL
            value = "NULL"
        elif column_type.upper() not in not_quoted_types:
            # Quote strings
            # TODO: We need a robust SQL escape function here.
            value = f"'{value}'"
        cat_column = "cat"
        cat = row[cat_column]
        cmd.append(f"UPDATE {table} SET {column} = {value} WHERE {cat_column} = {cat};")
    cmd.append("END TRANSACTION")
    return cmd


def csv_loads(text, delimeter, quotechar='"', null=None):
    """Load CSV from a string

    Determines a type for each cell separatelly based on its content.
    If it can be converted to int, it is int. If to a float, it is float.
    Otherwise, it is str.

    Meant to be an equivalent of json.loads().
    """
    csv_reader = csv.DictReader(text.splitlines(), delimiter=delimeter)
    table = []
    for row in csv_reader:
        for key, value in row.items():
            try:
                value = int(value)
                row[key] = value
            except ValueError:
                try:
                    value = float(value)
                    row[key] = value
                except ValueError:
                    # It is a string.
                    pass
        table.append(row)
    return table


def main():
    """Process command line parameters and update the table"""
    options, flags = gs.parser()

    vector = options["map"]
    layer = options["layer"]
    where = options["where"]
    column = options["column"]
    expression = options["expression"]
    condition = options["condition"]
    functions_file = options["functions"]

    # Map needs to be in the current mapset
    mapset = gs.gisenv()["MAPSET"]
    if not gs.find_file(vector, element="vector", mapset=mapset)["file"]:
        gs.fatal(
            _(
                "Vector map <{vector}> does not exist or is not in the current mapset"
                "(<{mapset}>) and therefore it cannot be modified"
            ).format(**locals())
        )

    # Map+layer needs to have a table connected
    try:
        # TODO: Support @OGR vector maps? Probably not supported by db.execute anyway.
        db_info = gs.vector_db(vector)[int(layer)]
    except KeyError:
        gs.fatal(
            _(
                "There is no table connected to map <{vector}> (layer <{layer}>)."
                " Use v.db.connect or v.db.addtable to add it."
            ).format(**locals())
        )
    table = db_info["table"]
    database = db_info["database"]
    driver = db_info["driver"]
    columns = gs.vector_columns(vector, layer)

    # Check that column exists
    try:
        column_info = columns[column]
    except KeyError:
        gs.fatal(
            _("Column <{column}> not found. Use v.db.addcolumn to create it.").format(
                column=column
            )
        )
    column_type = column_info["type"]

    # Check that optional function file exists
    if functions_file:
        if not os.access(functions_file, os.R_OK):
            gs.fatal(_("File <{file}> not found").format(file=functions_file))

    # Define Python functions
    # Here we need the full-deal eval and exec functions and can't sue less
    # general alternatives such as ast.literal_eval.
    def expression_function(**kwargs):
        return eval(expression, globals(), kwargs)  # pylint: disable=eval-used

    def condition_function(**kwargs):
        return eval(condition, globals(), kwargs)  # pylint: disable=eval-used

    # TODO: Add error handling for failed imports.
    if options["packages"]:
        packages = options["packages"].split(",")
        for package in packages:
            # pylint: disable=exec-used
            exec(f"import {package}", globals(), globals())
            if flags["s"]:
                exec(f"from {package} import *", globals(), globals())

    # TODO: Add error handling for invalid syntax.
    if functions_file:
        with open(functions_file) as file:
            exec(file.read(), globals(), globals())  # pylint: disable=exec-used

    # Get table contents
    if not where:
        # The condition needs to be None, an empty string is passed through.
        where = None
    if gs.version()["version"] < "7.9":
        sep = "|"  # Only one char sep for Python csv package.
        null = "NULL"
        csv_text = gs.read_command(
            "v.db.select",
            map=vector,
            layer=layer,
            separator=sep,
            null=null,
            where=where,
        )
        table_contents = csv_loads(csv_text, delimeter=sep, null=null)
    else:
        # TODO: XXX is a workaround for a bug in v.db.select -j
        json_text = gs.read_command(
            "v.db.select", map=vector, layer=layer, flags="j", null="XXX", where=where
        )
        table_contents = json.loads(json_text)

    cmd = python_to_transaction(
        table=table,
        table_contents=table_contents,
        column=column,
        column_type=column_type,
        expression=expression,
        expression_function=expression_function,
        condition=condition,
        condition_function=condition_function,
        ensure_lowercase=not flags["u"],
    )

    # Messages
    if len(cmd) == 2:
        gs.message("No rows to update. Try a different SQL where or Python condition.")
    elif len(cmd) > 2:
        # First and last statement
        gs.verbose(f'Using SQL: "{cmd[1]}...{cmd[-2]}"')

    # The newline is needed for successful execution/reading of many statements.
    # TODO: Add error handling when there is a syntax error due to wrongly
    # generated SQL statement and/or sanitize the value in update more.
    gs.write_command(
        "db.execute", input="-", database=database, driver=driver, stdin="\n".join(cmd)
    )

    gs.vector_history(vector)


if __name__ == "__main__":
    main()
