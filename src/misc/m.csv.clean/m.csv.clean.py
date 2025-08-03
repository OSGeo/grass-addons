#!/usr/bin/env python3

# AUTHOR(S): Vaclav Petras <wenzeslaus gmail com>
#
# COPYRIGHT: (C) 2020 Vaclav Petras and by the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.

# %module
# % label: Creates a cleaned-up copy a CSV files
# % description: Creates CSV files which are ready to used in GRASS GIS
# % keyword: miscellaneous
# % keyword: CSV
# % keyword: ASCII
# %end

# %option G_OPT_F_INPUT
# % label: Input CSV file to clean up
# % required: yes
# %end

# %option G_OPT_F_SEP
# % answer: comma
# % required: yes
# %end

# %option G_OPT_F_OUTPUT
# % label: Clean CSV output file
# % required: yes
# %end

# %option
# % key: prefix
# % label: Prefix for columns which don't start with a letter
# % description: Prefix itself must start with a letter of English alphabeth
# % type: string
# % required: yes
# % answer: col_
# %end

# %option
# % key: recognized_date
# % label: Recognized date formats (e.g., %m/%d/%y)
# % description: For example, %m/%d/%Y,%m/%d/%y matches 7/30/2021 and 7/30/21
# % type: string
# % required: no
# % multiple: yes
# % guisection: Date
# %end

# %option
# % key: clean_date
# % label: Format for new clean-up date
# % description: For example, %Y-%m-%d for 2021-07-30
# % type: string
# % required: no
# % answer: date_%Y-%m-%d
# % guisection: Date
# %end

# %option
# % key: missing_names
# % label: Names for the columns without a name in the header
# % description: If only one is provided, but more than one is need, underscore and column number is added
# % type: string
# % required: yes
# % answer: column
# %end

# %option
# % key: cell_clean
# % label: Operations to apply to non-header cells in the body of the document
# % description: If only one is provided, but more than one is need, underscore and column number is added
# % type: string
# % required: no
# % multiple: yes
# % options: strip_whitespace,collapse_whitespace,date_format,none
# % answer: strip_whitespace,collapse_whitespace
# %end

import sys
import csv
import re
from datetime import datetime

import grass.script as gs

try:
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


def collapse_whitespace(text):
    """Minimize the whitespace in the text.

    Replaces multiple whitespaces including the unicode ones
    by a single space.

    Removes leading and trailing whitespace.
    """
    return re.sub(r"\s+", " ", text)


def minimize_whitespace(text):
    """Minimize the whitespace in the text.

    Replaces multiple whitespaces including the unicode ones
    by a single space.

    Removes leading and trailing whitespace.
    """
    return collapse_whitespace(text).strip()


def reformat_date(detect_dates, date_format, date):
    """Reformats date into a desired format

    If *date* is not recognized as a date by one of the
    *detect_dates* formats, original *date* is returned.
    """
    for detect_date in detect_dates:
        try:
            date = datetime.strptime(column, detect_date)
            column = date.strftime(date_format)
        except ValueError:
            # We assume the value is not a date, so we don't touch it.
            pass
    return date


def main():
    options, flags = gs.parser()
    in_filename = options["input"]
    out_filename = options["output"]
    input_separator = gs.separator(options["separator"])
    prefix = options["prefix"]
    # https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
    date_formats = None
    if options["recognized_date"]:
        date_formats = options["recognized_date"].split(",")
    out_date_format = options["clean_date"]
    missing_names = options["missing_names"].split(",")
    # TODO: lowercase the column names

    if prefix and re.match("[^A-Za-z]", prefix[0]):
        gs.fatal(
            _(
                "Prefix (now <{prefix}>) must start with an ASCII letter (a-z or A-Z in English alphabeth)"
            ),
            prefix=prefix,
        )

    with open(in_filename, "r", newline="") as infile, open(
        out_filename, "w", newline=""
    ) as outfile:
        # TODO: Input format to parameters (important)
        # TODO: Output format to parameters (somewhat less important)
        input_csv = csv.reader(infile, delimiter=input_separator, quotechar='"')
        output_csv = csv.writer(
            outfile, delimiter=",", quotechar='"', lineterminator="\n"
        )
        for i, row in enumerate(input_csv):
            # TODO: Optionally remove newlines from cells.
            # In header and body replace by space (and turns into underscore for header).
            if i == 0:
                new_row = []
                num_unnamed_columns = 0
                duplicated_number = 2  # starting at two fro duplicated names
                for column_number, column in enumerate(row):
                    if date_formats:
                        column = reformat_date(date_formats, out_date_format, column)
                    if not column:
                        if not num_unnamed_columns:
                            column = missing_names[0]
                        elif len(missing_names) == 1:
                            column = f"{missing_names[0]}_{column_number + 1}"
                        elif num_unnamed_columns < len(missing_names):
                            column = missing_names[num_unnamed_columns]
                        else:
                            column = f"{missing_names[-1]}_{name_duplicated}"
                            duplicated_number += 1
                        num_unnamed_columns += 1
                    column = minimize_whitespace(column)
                    # TODO: Also duplicate column names should be resolved here.
                    # Perhaps just move the else of no column names here or perhaps not
                    # because it would be difficult to navigate the code.
                    column = make_name_sql_compliant(column, fallback_prefix=prefix)
                    new_row.append(column)
            else:
                # TODO: Optionally reformat dates in the body too (but without prefix).
                # TODO: Recognize numbers with spaces and commas and fix them.
                # For example, 10,000 and 10 000,5 should/might be
                # 10000 (or 10.0) 10000.5.
                # TODO: General find and replace for cells (which could take care of some escape chars
                # or other mess. Question is how to make it general/more than one replace pair.
                # (Remove would be easier to have in the interface.)
                new_row = []
                row_has_content = False
                for column in row:
                    if column:
                        row_has_content = True
                    # TODO: Use bools for this, perhaps a dedicated class for this type of option.
                    # This is an experiment with extremely aggressive replacemt of flags by options.
                    if "collapse_whitespace" in options["cell_clean"]:
                        column = collapse_whitespace(column)
                    if "strip_whitespace" in options["cell_clean"]:
                        column = column.strip()
                    if date_formats and "date_format" in options["cell_clean"]:
                        column = reformat_date(date_formats, out_date_format, column)
                    new_row.append(column)
                # Skips completely empty rows and rows with only separators.
                if not row_has_content:
                    continue
                # TODO: Add except csv.Error as error:
            output_csv.writerow(new_row)


if __name__ == "__main__":
    sys.exit(main())
