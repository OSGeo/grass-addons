#!/usr/bin/env python

############################################################################
#
# MODULE:       db.join
# AUTHOR(S):    Markus Neteler
#               Derived from v.db.join
# PURPOSE:      Join a table to another table
# COPYRIGHT:    (C) 2016 by Markus Neteler and the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
# TODO: use "BEGIN TRANSACTION"
#            or f.write("{}\n".format(grass.db_begin_transaction(fi['driver']))) ?
#############################################################################

# %module
# % description: Joins a database table to another database table.
# % keyword: database
# % keyword: attribute table
# %end

# %option G_OPT_DB_TABLE
# % description: Table to which to join other table
# % required : yes
# %end

# %option G_OPT_DB_COLUMN
# % description: Identifier column (e.g.: cat) in the table to be used for join
# % required : yes
# %end

# %option G_OPT_DB_DATABASE
# %end

# %option G_OPT_DB_DRIVER
# % options: dbf,odbc,ogr,sqlite,pg
# %end

# %option G_OPT_DB_TABLE
# % key: other_table
# % description: Other table name
# % required: yes
# % guidependency: ocolumn,scolumns
# %end

# %option G_OPT_DB_COLUMN
# % key: other_column
# % description: Identifier column (e.g.: id) in the other table used for join
# % required: yes
# %end

# %option G_OPT_DB_COLUMN
# % key: subset_columns
# % multiple: yes
# % required: no
# % description: Subset of columns from the other table
# %end

import sys
import string
import grass.script as grass
from grass.exceptions import CalledModuleError


def main():
    table = options["table"]
    column = options["column"]
    otable = options["other_table"]
    ocolumn = options["other_column"]
    if options["subset_columns"]:
        scolumns = options["subset_columns"].split(",")
    else:
        scolumns = None

    database = options["database"]
    driver = options["driver"]

    # this error handling is completely different among th db.* scripts - FIX
    if not database:
        database = None
    if not driver:
        driver = None

    if driver == "dbf":
        grass.fatal(_("JOIN is not supported for tables stored in DBF format"))

    # describe input table
    all_cols_tt = grass.db_describe(table, driver=driver, database=database)["cols"]
    if not all_cols_tt:
        grass.fatal(_("Unable to describe table <%s>") % table)
    found = False

    # check if column is in input table
    if column not in [col[0] for col in all_cols_tt]:
        grass.fatal(_("Column <%s> not found in table <%s>") % (column, table))

    # describe other table
    all_cols_ot = grass.db_describe(otable, driver=driver, database=database)["cols"]

    # check if ocolumn is in other table
    if ocolumn not in [ocol[0] for ocol in all_cols_ot]:
        grass.fatal(_("Column <%s> not found in table <%s>") % (ocolumn, otable))

    # determine columns subset from other table
    if not scolumns:
        # select all columns from other table
        cols_to_add = all_cols_ot
    else:
        cols_to_add = []
        # check if scolumns exists in the other table
        for scol in scolumns:
            found = False
            for col_ot in all_cols_ot:
                if scol == col_ot[0]:
                    found = True
                    cols_to_add.append(col_ot)
                    break
            if not found:
                grass.warning(_("Column <%s> not found in table <%s>") % (scol, otable))

    select = "SELECT $colname FROM $otable WHERE $otable.$ocolumn=$table.$column"
    template = string.Template("UPDATE $table SET $colname=(%s);" % select)

    for col in cols_to_add:
        # skip the vector column which is used for join
        colname = col[0]
        if colname == column:
            continue

        use_len = False
        if len(col) > 2:
            use_len = True
            # Sqlite 3 does not support the precision number any more
            if driver == "sqlite":
                use_len = False
            # MySQL - expect format DOUBLE PRECISION(M,D), see #2792
            elif driver == "mysql" and col[1] == "DOUBLE PRECISION":
                use_len = False

        if use_len:
            coltype = "%s(%s)" % (col[1], col[2])
        else:
            coltype = "%s" % col[1]

        colspec = "%s %s" % (colname, coltype)

        # add only the new column to the table
        if colname not in all_cols_tt:
            p = grass.feed_command(
                "db.execute", input="-", database=database, driver=driver
            )
            p.stdin.write("ALTER TABLE %s ADD COLUMN %s" % (table, colspec))
            grass.debug("ALTER TABLE %s ADD COLUMN %s" % (table, colspec))
            p.stdin.close()
            if p.wait() != 0:
                grass.fatal(_("Unable to add column <%s>.") % colname)

        stmt = template.substitute(
            table=table, column=column, otable=otable, ocolumn=ocolumn, colname=colname
        )
        grass.debug(stmt, 1)
        grass.verbose(_("Updating column <%s> of table <%s>...") % (colname, table))
        try:
            grass.write_command(
                "db.execute", stdin=stmt, input="-", database=database, driver=driver
            )
        except CalledModuleError:
            grass.fatal(_("Error filling column <%s>") % colname)

    return 0


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
