#!/usr/bin/env python

#
##############################################################################
#
# MODULE:    v.in.survey
#
# AUTHOR(S):     Eva Stopková
#        functions for DXF conversion are taken from (or based on)
#        the module v.out.dxf (Charles Ehlschlaeger and Radim Blazek)
#
# PURPOSE:       Create multiple vector layers based on one textfile
# COPYRIGHT:     (C) 2015 by the GRASS Development Team
#
#        This program is free software under the GNU General Public
#        License (version 2). Read the file COPYING that comes with
#        GRASS for details.
#
##############################################################################

# %module
# % description: Creates multiple vector layers from just one textfile
# % keyword: vector
# % keyword: import
# % keyword: ASCII
# % keyword: multiple
# %end

# % option G_OPT_F_INPUT
# % key: input
# % description: Name of input file to be imported
# % required: yes
# %end

# % option G_OPT_F_SEP
# % key: separator
# % guisection: Input format
# %end

# % option
# % key: pt_rules
# % guisection: Vector type codes
# % multiple: yes
# % description: Point(s): hosp.pt.01..., forest.tree.01 -> 'pt,tree'
# %end

# % option
# % key: ln_rules
# % guisection: Vector type codes
# % multiple: yes
# % description: Line(s): road.ln.01..., Danube.river.01 -> 'ln,river'
# %end

# % option
# % key: poly_rules
# % guisection: Vector type codes
# % multiple: yes
# % description: Polygon(s): hosp.area.01,..., forest.area.01 -> 'area'
# %end

# % option
# % key: skip
# % type: integer
# % required: NO
# % multiple: NO
# % answer: 0
# % description: Number of lines to skip at top of input file (points mode)
# % guisection: Points
# %end

# % option
# % key: columns
# % type: string
# % required: NO
# % multiple: NO
# % guisection: Points
# % label: Column definition in SQL style (points mode))
# % description: E.g.: 'x double precision, y double precision, cat int, name varchar(10)'
# %end

# % option
# % key: easting
# % type: integer
# % required: NO
# % multiple: NO
# % answer: 2
# % guisection: Points
# % label: Number of column used as easting coordinate (points mode)
# % description: First column is 1
# %end

# % option
# % key: northing
# % type: integer
# % required: NO
# % multiple: NO
# % answer: 3
# % guisection: Points
# % label: Number of column used as northing coordinate (points mode)
# % description: First column is 1
# %end

# % option
# % key: elevation
# % type: integer
# % required: NO
# % multiple: NO
# % answer: 0
# % guisection: Points
# % label: Number of column used as elevation (points mode)
# % description: First column is 1. If 0, z coordinate is not used
# %end

# % option G_OPT_M_DIR
# % key: outdir
# % guisection: Output settings
# % description: Name of directory to store separated files for each layer
# % required: no
# %end

# % option
# % key: merge_lyrs
# % guisection: Output settings
# % multiple: yes
# % description: Pattern(s) for layers to be merged
# %end

# % flag
# % key: z
# % description: Create 3D vector map
# %end

# % flag
# % key: e
# % description: Create a new empty vector map and exit. Nothing is read from input.
# %end

# % flag
# % key: n
# % description: Do not expect a header when reading in standard format
# % guisection: Input format
# %end

# % flag
# % key: t
# % description: Do not create table in points mode
# % guisection: Points
# %end

# % flag
# % key: r
# % description: Only import points falling within current region (points mode)
# % guisection: Points
# % end

# % flag
# % key: x
# % description: Convert to DXF
# % guisection: DXF conversion
# %end

# % option
# % key: dxf_file
# % description: Name of the DXF file
# % guisection: DXF conversion
# %end

# % option
# % key: draw_unit
# % description: Drawing units
# % answer: metric
# % options: metric, imperial
# % guisection: DXF conversion
# %end

# % option
# % key: textsize
# % description: Text height of the labels in DXF file
# % answer: 0.
# % guisection: DXF conversion
# %end

import fileinput
import os
import subprocess
from functools import reduce

import grass.script as grass
from grass.pygrass.messages import get_msgr


class MakeSameVarcharColTypeLengthMapTables:
    """Make same varchar column type length value in tables with same
    columns structure

    Same varchar column type length value is needed for 'v.patch'
    command.

    :param list tables: input tables list
    """

    def __init__(self, tables):
        self.process_tables(tables=tables)

    def get_clen_value(self, col):
        """Get column name with column length as tuple

        :param dict col: column definition
        {'str_1': {'ctype': 'CHARACTER', 'clen': '8'}

        :return list: column name with column length as tuple
        [('str_1', 8)]
        """

        return [(d[0], d[1]["clen"]) for d in col.items()]

    def get_symm_diff_cols(self, a, b):
        """Get symmetrict difference between two columns from two another
        tables

        :param dict a: column definition
        {'str_1': {'ctype': 'CHARACTER', 'clen': '8'}
        :param dict b: column definition
        {'str_1': {'ctype': 'CHARACTER', 'clen': '12'}

        :return set: symmetric difference between cols
        {('str_1', '12'), ('str_1', '8')}
        """

        if isinstance(a, dict):
            return set(self.get_clen_value(col=a)) ^ set(self.get_clen_value(col=b))
        else:
            return a ^ set(self.get_clen_value(col=b))

    def get_same_col_from_tables(self, tables_cols, col):
        """
        Get same column definition from different tables

        :param list tables_cols: tables columns definition from different
        tables
        [
        '{cat': {'ctype': 'INTEGER', 'clen': '20'},
        'dbl_1': {'ctype': 'DOUBLE PRECISION', 'clen': '20'},
        'dbl_2': {'ctype': 'DOUBLE PRECISION', 'clen': '20'},
        'str_1': {'ctype': 'CHARACTER', 'clen': '14'}},

        '{cat': {'ctype': 'INTEGER', 'clen': '20'},
        'dbl_1': {'ctype': 'DOUBLE PRECISION', 'clen': '20'},
        'dbl_2': {'ctype': 'DOUBLE PRECISION', 'clen': '20'},
        'str_1': {'ctype': 'CHARACTER', 'clen': '8'}},
        ...
        ]
        :param str col: col name e.g. 'str_1'

        :return list cols: list of same column with definition from
        different tables
        [
        {'str_1': {'ctype': 'CHARACTER', 'clen': '14'}},
        {'str_1': {'ctype': 'CHARACTER', 'clen': '8'}},
        ...
        ]
        """

        cols = []
        for table in tables_cols:
            cols.append({col: table[col]})
        return cols

    def process_tables(self, tables):
        """Get difference between varchar column type length value
        (max value) across different tables (same columns structure)
        and change varchar type column length value accodring max length
        value in the input other tables.

        Same varchar column type length value is needed for 'v.patch'
        command.

        :param list tables: list of input tables (with same columns
        structure)

        :return None
        """

        result = []
        for index, table in enumerate(tables):
            result.append({})
            stdout, stderr = grass.start_command(
                "db.describe",
                flags="c",
                table=table,
                stdout=subprocess.PIPE,
            ).communicate()
            if stdout:
                stdout = grass.decode(stdout)
                for row in stdout.split("\n"):
                    if row.count(":") == 3:
                        col, ctype, clen = row.split(":")[-3:]
                        result[index][col.strip()] = {
                            "ctype": ctype,
                            "clen": clen,
                        }

        if result and len(result) > 1:
            for col in result[0].keys():
                sym_diff = reduce(
                    self.get_symm_diff_cols,
                    self.get_same_col_from_tables(
                        tables_cols=result,
                        col=col,
                    ),
                )
                if sym_diff and len(sym_diff) > 1:
                    col, clen = max(sym_diff, key=lambda i: int(i[1]))
                    for index, t in enumerate(result):
                        if t[col]["clen"] == clen:
                            table = tables[index]
                            break
                    for table in list(filter(lambda i: i != table, tables)):
                        grass.run_command(
                            "v.db.addcolumn",
                            map=table,
                            columns="{}_ varchar({})".format(col, clen),
                        )
                        grass.run_command(
                            "v.db.update",
                            map=table,
                            column="{}_".format(col),
                            query_column=col,
                        )
                        grass.run_command(
                            "v.db.dropcolumn",
                            map=table,
                            columns=col,
                        )
                        grass.run_command(
                            "v.db.renamecolumn",
                            map=table,
                            column="{0}_,{0}".format(col),
                        )


class test:
    def __init__(self, test_file):
        self.test_file = test_file

    def files(self):  # test if file exists
        if not os.path.isfile(self.test_file):
            special = self.test_file.split("/")  # which file is being checked:
            # list of layers that have been done in previous session
            if special[len(special) - 1] == "_layers_done.txt":
                grass.fatal(
                    _(
                        "File <"
                        + self.test_file
                        + "> should contain list of existing layers."
                        + " The file does not exist, thus it is not"
                        + " possible to process script with -x flag."
                    )
                )
            else:  # any other file (input file)
                grass.fatal("File <" + self.test_file + "> does not exist.")
        return 0

    # test if file is blank
    def blank(self, want_blank):
        for line in self.test_file:
            # the file is blank and it should not be:
            if not line.strip() and want_blank is False:
                msgr.fatal(
                    _("File <" + self.lyr_name + "." + extension + "> is empty.")
                )
        return 0

    def overwrite_file(self):
        # the file is not blank and it should be
        if os.path.isfile(self.test_file):
            if overwrite_all is True:
                # remove potentially broken input file
                os.remove(self.test_file)
                msgr.message(
                    _("Existing file <" + self.test_file + "> has been removed...")
                )
            else:
                msgr.fatal(
                    _(
                        "File <"
                        + self.test_file
                        + "> exists. To overwrite it,"
                        + " please use --o flag..."
                    )
                )
        return 0


# ****** #


class glob:  # *** Global variables *** #
    separator = ""  # separator of the rows in the input data
    py_separator = ""
    outdir = ""
    infile = ""

    def __init__(self, infile, outdir, separator):
        test(infile).files()  # test file existence

        glob.infile = infile  # input file (name-east-north-[elev])
        glob.separator = separator
        glob.py_separator = self.g2py(separator)  # separator of the input data
        # directory to store separated files for each layer
        glob.outdir = self.test_dir(outdir)

    # separators from GRASS to Python
    # e.g. "pipe" -> "|"
    def g2py(self, separator):
        if separator == "pipe":
            py_separator = "|"
        elif separator == "comma":
            py_separator = ","
        elif separator == "space":
            py_separator = " "
        elif separator == "tab":
            py_separator = "\t"
        elif separator == "newline":
            py_separator = "\n"
        else:
            msgr.fatal(_("Please setup correct separator..."))

        return py_separator

    # test if output directory exists
    def test_dir(self, outdir):
        if outdir == "":
            outdir = "output"
            msgr.message(
                _("Output files will be stored " + "in the <output> directory.")
            )

        if not os.path.isdir(outdir):  # output directory does not exist
            os.makedirs(outdir)  # create new directory

        else:  # output directory exists
            msgr.warning(
                _(
                    "Output directory exists. It may contain layers"
                    + " that might be overwritten."
                )
            )

        return outdir


# ****** #


class Flag:
    signs = ""

    def __init__(self, sign):
        self.sign = sign
        Flag.signs = self.add_flag()

    def add_flag(self):  # test flags
        if flags[self.sign]:
            if Flag.signs == "":
                Flag.signs = self.sign
            else:
                Flag.signs += self.sign
        return Flag.signs


# ****** #


class inputs(glob, test):
    data = []  # input data
    n = 0
    dim = 0

    def __init__(self, skip_input):
        # no. of lines to be skipped in the input file
        self.skip_input = int(skip_input)
        inputs.data, inputs.n, inputs.dim = self.raw_data()  # extract xyz

    # find out data dimension
    def dimension(self, row, n_lines, skip_lines, find_dim):
        # remove blank elements
        filtered = [y for y in row if y != "\n" and y != "" and y != " " and y != "\t"]
        n = len(row)  # number of non-blank elements

        if find_dim is True:
            if n == 3:  # name easting northing
                inputs.dim = 2  # 2D
            elif n == 4:  # name easting northing elevation
                inputs.dim = 3  # 3D
            else:
                msgr.fatal(
                    _(
                        "Too many columns. Use input data in format"
                        + " 'name east north [elev]', please."
                    )
                )

            find_dim = False

        else:
            if n - 1 != inputs.dim:
                msgr.fatal(
                    _(
                        "Number of columns do not match. Please check"
                        + " rows "
                        + str(n_lines + skip_lines - 1)
                        + " and "
                        + str(n_lines + skip_lines)
                        + " in your data."
                    )
                )

        return inputs.dim, find_dim

    # test not allowed characters
    def characters(self, string, char):
        # list of forbidden characters
        avoid = [
            "-",
            "*",
            "/",
            "+",
            "\\",
            "|",
            "<",
            ">",
            "=",
            "~",
            "°",
            "!",
            "`",
            ";",
            ":",
            "@",
            "£",
            "$",
            "%",
            "&",
            "(",
            ")",
            "#",
            "^",
            "'",
            '"',
            "?",
            "§",
            "[",
            "]",
        ]
        # number of forbidden characters
        n_avoid = len(avoid)

        for i in range(0, n_avoid):
            if string.find(avoid[i]) > -1:
                if char == "-":  # test just '-' in names
                    msgr.fatal(
                        _(
                            "Please do not use SQL forbidden characters"
                            + " in your input data... remove all '"
                            + avoid[i]
                            + "' from point names."
                        )
                    )
                    break  # everything else has been tested
                else:  # general test:
                    if i == 0:  # do not test '-'
                        continue
                    msgr.fatal(
                        _(
                            "Please do not use SQL forbidden characters"
                            + " in your input data... remove all '"
                            + avoid[i]
                            + "' from the file."
                        )
                    )
        return 0

    # extract raw data
    def raw_data(self):
        open_input = open(glob.infile, "r")  # open input file for reading
        data = []
        find_dim = True  # unknown dimension of the data

        skip_lines = self.skip_input + skip.layers
        n_lines = 0  # number of non-blank lines

        for line in open_input:  # for each line in the file
            if n_lines < skip_lines:  # skip lines
                n_lines += 1
                continue

            if line.strip():  # use strip to check the content
                # test the data for SQL non-compliant content:
                # everything except '-' <=> allowed in numeric types
                self.characters(line, "general")
                n_lines += 1

            row = line.strip("\n").split(glob.py_separator)
            if len(row) == 1:
                msgr.fatal(_("Wrong separator type."))

            # test if the layer name does not start with a digit
            if line[0].isdigit():
                msgr.fatal(
                    _(
                        "Illegal vector map name <"
                        + row[0]
                        + ">. Must start with a letter."
                    )
                )

            # test point names:
            # - for '-' as SQL non-compliant content
            self.characters(row[0], "-")

            # - for length
            if len(row[0].split(".")) != 3:
                msgr.fatal(
                    _(
                        "Please rename point "
                        + row[0]
                        + " according to the script request in format"
                        + " 'lyr_name.vect_type_code.number'."
                    )
                )

            # make data array from the first unskipped non-blank line:
            # 2D or 3D
            inputs.dim, find_dim = self.dimension(row, n_lines, skip_lines, find_dim)

            # join everthing to data
            data.append(row)
        open_input.close()  # close input file

        if n_lines == skip_lines:
            msgr.warning(
                _(
                    "All the data is imported. Just patching"
                    + " and cleaning will be done if necessary."
                )
            )
            inputs.skip = True

            return None, None, inputs.skip
        if n_lines < 1:
            msgr.fatal(_("Empty input file."))

        # remove empty lines from the data
        data = [x for x in data if x != "\n"]
        inputs.n = len(data)  # number of elements

        # sort data by name
        inputs.data = sorted(data, key=lambda data: data[0])

        return inputs.data, inputs.n, inputs.dim


class vect_rules:
    pt = ""
    ln = ""
    poly = ""
    east = 2
    north = 3
    elev = 0

    def __init__(self, pt, ln, poly, east, north, elev):
        vect_rules.pt = pt.split(",")  # list of codes for point layer
        vect_rules.ln = ln.split(",")  # list of codes for line layer
        vect_rules.poly = poly.split(",")  # list of codes for boundary

        if (
            vect_rules.pt[0] == ""
            and vect_rules.ln[0] == ""
            and vect_rules.poly[0] == ""
        ):
            msgr.fatal(_("Any rule for vector geometry missing..."))

        vect_rules.east = east  # column with easting
        vect_rules.north = north  # column with northing
        vect_rules.elev = elev  # column with elevation


class files(glob):
    base = ""

    def __init__(self, base):
        files.base = base

    # create path to file
    def path2(self, extension):
        filename = glob.outdir + "/" + files.base + "." + extension
        return filename

    # open output file
    def open_output(self, skip_blank_test, dxf):
        out_file = glob.outdir + "/" + files.base
        if dxf is False:
            out_file += ".txt"

        test(out_file).overwrite_file()
        open_output = open(out_file, "a+")

        if skip_blank_test is False:
            test(out_file).blank(True)  # test if the file is blank

        return open_output


# ****** #


class skip(test, files):
    layers = 0
    existing = False
    lyr_names = ""  # names of the layers to be analyzed for merging
    vectors = ""  # geometry types of the layers for merging

    def __init__(self, existing):
        self.existing = existing

        if self.existing is True:
            # test if file exists
            test.files(glob.outdir + "/_layers_done.txt", "_layers_done.txt")
            # open list of existing layers
            done_lyrs = files.open_output(glob.outdir, "_layers_done", True, False)
            skip.layers, skip.lyr_names, skip.vectors = self.lines(done_lyrs)

    # count points in existing layers to skip lines
    def lines(self):
        i = 0  # index
        for line in glob.infile:  # for each line in the file
            if line.strip():  # use strip to check the content
                # test layer names for SQL non-compliant content:
                # everything except '-' <=> allowed in numeric types)
                test.characters(line, "general")

                # test layer names for '-' as SQL non-compliant content
                test.characters(line, "-")

                row = line.strip("\n").split(glob.py_separator)
                skip.layers += int(row[0])
                if i == 0:
                    skip.lyr_names = row[1]
                    skip.vectors = row[2]
                else:
                    skip.lyr_names += "," + row[1]
                    skip.vectors += "," + row[2]
                i += 1
        return skip.layers, skip.lyr_names, skip.vectors


# ****** #


class layer_init:
    def __init__(self, i):
        self.i = i
        self.name, self.code = self.define_name()  # setup name of the layer

    # setup name of the layer
    def define_name(self):
        # extract point name
        point_name = inputs.data[self.i][0].split(".")  # split the data by dot
        unit_name = point_name[0]  # core name of the layer
        self.code = point_name[1]  # vector type (point, line, boundary)
        self.name = unit_name + "_" + self.code  # whole layer name

        return self.name, self.code


# ****** #


class layer(glob, Flag, vect_rules, layer_init):
    unit = ""  # pure name of the layer
    code = ""  # code for geometry type according to the rules(P - L - B)
    name = ""  # name of the layer (unit_code)
    vector = ""  # geometry type of the layer (P - L - B)
    n_pts = 0  # number of lines / polygons
    close = 0  # index of closing point

    def __init__(self, i):
        self.i = i

        layer.name, layer.code = self.define_name()
        # open output file (test blank, no dxf)
        self.out = files(layer.name).open_output(False, False)

        # initial values for the new layer
        layer.n_pts = 0  # number of lines / polygons
        layer.close = i  # index of the closing point
        layer.vector = self.code2vector()  # geometry type
        layer.unit = self.setup_unit(1)

        self.vformat = self.grass_format()
        if self.vformat == "standard":
            # open backup file (test blank, no dxf)
            self.out_bckp = files(layer.name + "_bckp").open_output(False, False)

        self.test_existence(layer.name, False)  # test layer existence
        self.filename = files(layer.name).path2("txt")

    # compare code with rules to sort the layers
    def compare(self, rules, sign):
        n_rules = len(rules)  # number of rules for each vector type
        for i in range(0, n_rules):
            if layer.code == rules[i]:  # if code is the same as any rule:
                layer.vector = sign  # define vector type
        return layer.vector

    # sort layers according to codes (by user)
    # to points, lines and boundaries
    def code2vector(self):
        layer.vector = ""
        layer.vector = self.compare(vect_rules.pt, "P")  # test points
        if layer.vector != "":
            return layer.vector

        if layer.vector == "":  # if type undefined:
            layer.vector = self.compare(vect_rules.ln, "L")  # test lines
            if layer.vector != "":
                return layer.vector

        if layer.vector == "":  # if type still undefined:
            # test boundaries
            layer.vector = self.compare(vect_rules.poly, "B")
            if layer.vector != "":
                return layer.vector

        if layer.vector == "":  # if type remains undefined:
            msgr.fatal(
                _(
                    "Vector layer <"
                    + layer.name
                    + "> is not point,"
                    + " neither line, nor boundary. Please check"  # etc
                    + "your input data and rules that you have"  # etc
                    + "typed in."
                )
            )
            return 0

    # format, number of vertices and index of closing point (for polygons)
    def grass_format(self):
        if layer.vector == "P":
            self.vformat = "point"
        else:
            self.vformat = "standard"

        return self.vformat

    def not_point(self):
        if self.vformat != "P":
            layer.n_pts += 1  # number of points in the layer

        return layer.n_pts

    # test existence of the layer
    def test_existence(self, layer_name, final):
        # final: True - merging / cleaning (skip existing);
        #        False - any other (fatal error)

        # initial value: do not skip existing layer and make fatal error
        skip = False
        mapset = grass.gisenv()["MAPSET"]

        # make fatal error if there are any existing layers during data import
        if (
            overwrite_all is False
            and final is False
            and grass.find_file(layer_name, element="vector", mapset=mapset)[  # etc
                "file"
            ]
        ):
            msgr.fatal(
                _(
                    "Vector layer <"
                    + layer_name
                    + "> exists. Please"
                    + " remove the layer or rename the input points."
                )
            )

        # skip existing layers during final steps (merge and clean)
        if (
            final is True
            and grass.find_file(layer_name, element="vector", mapset=mapset)["file"]
        ):
            # change value: skip existing layer and do not make fatal error
            skip = True

        return skip

    # make new layer from subdataset written to separate file
    def make_new(self):
        # set up suffix for temporary line layers
        # to be transformed into polygon or to be added an attribute table
        suffix = ""
        separator = glob.separator
        if layer.vector != "P":
            suffix = "_" + layer.code + "_tmp"
            separator = "space"
        layer_name = layer.unit + suffix
        self.test_existence(layer_name, False)  # test layer existence

        in_ascii = grass.run_command(
            "v.in.ascii",
            input=self.filename,
            output=layer_name,
            format=self.vformat,
            separator=separator,
            x=vect_rules.east,
            y=vect_rules.north,
            z=vect_rules.elev,
            flags=Flag.signs,
            overwrite=overwrite_all,
        )

        # make polygon from boundaries
        if layer.vector == "B":
            self.test_existence(layer.name, False)  # test layer existence
            # add centroids and create polygon layer
            grass.run_command(
                "v.centroids",
                input=layer_name,
                output=layer.name,
                overwrite=overwrite_all,
            )
            # remove temporary line layer
            grass.run_command("g.remove", type="vector", name=layer_name, flags="f")
        elif self.vector == "L":
            # add categories to line layer
            grass.run_command(
                "v.category",
                input=layer_name,
                option="add",
                type="line",
                output=layer.name,
                overwrite=overwrite_all,
            )
            # remove the layer without cats
            grass.run_command("g.remove", type="vector", name=layer_name, flags="f")

        if self.vformat == "standard":
            self.set_attribute_table()

        # make a note that layer has been done"""
        # done_lyrs.write(str(self.n_elems) + glob.py_separator + layer.name +
        # glob.py_separator + self.vector + '\n')

        return 0

    # unit name according to temporary layer name (base + vector type code)
    def setup_unit(self, remove_suffix):
        if layer.vector != "P":
            base = layer.name.split("_")  # split point name by '_'
            layer.unit = base[0]  # unit name: base

            # all parts of the base without vector code
            for i in range(1, len(base) - remove_suffix):
                layer.unit += "_" + base[i]
        else:
            layer.unit = layer.name

        return layer.unit

    def check_number_pts(self):
        if layer.vector == "L" and layer.n_pts < 2:
            # can_be_broken = done_lyrs.readlines()[-1]
            msgr.fatal(_("Not enough points to make line layer <" + layer.name + ">."))
        if layer.vector == "B" and layer.n_pts < 3:
            msgr.fatal(
                _("Not enough points to make polygon layer <" + layer.name + ">.")
            )
        return 0

    # add two specific lines at the beginning of the file in standard format
    def standard_poly(self):
        if layer.vector == "B":  # for boundaries
            layer.n_pts += 1  # no. of vertices (including the closing point)
        return layer.n_pts

    def standard_header(self):
        # *** function based on answer 3: http://stackoverflow.com/  ...
        # questions/5287762/how-to-insert-a-new-line-before-the-first-line- ...
        # in-a-file-using-python
        for num, line in enumerate(
            fileinput.FileInput(self.filename, inplace=2)  # etc
        ):
            if num == 0:
                print(layer.vector + " " + str(layer.n_pts))
                print(line.strip("\n"))
            else:
                print(line.strip("\n"))
        # ***
        return 0

    # modify file to respect standard format for lines and boundaries:
    def complete_input(self):
        # add two specific lines at the beginning of the file
        layer.n_pts = self.standard_poly()
        self.standard_header()

        # add closing point (the 1st one of the subsample)
        if layer.vector == "B":  # just for boundaries
            with open(self.filename, "a") as self.out:
                self.write2("standard", self.out, layer.close)
        return 0

    def complete(self):
        # modify file to respect standard format for lines and boundaries:
        self.out.close()  # close layer input file
        if self.vformat == "standard":
            self.out_bckp.close()  # close backup file
            self.check_number_pts()
            self.complete_input()

        return 0

    def write(self, i):
        # write the point to the layer file
        if self.vformat == "point":
            self.write2("point", self.out, i)

        if self.vformat == "standard":
            self.write2("standard", self.out, i)  # nameless points
            self.write2("point", self.out_bckp, i)  # backup of point names

        layer.n_pts = self.not_point()  # setup for non-point layers
        return layer.n_pts

    # add atrribute table with the name of the layer
    def set_attribute_table(self):
        # add table with the name column
        grass.run_command(
            "v.db.addtable", map=layer.name, columns="lyr_name varchar(15)"
        )
        # update the name column with the 1st 15 characters of the layer's name
        grass.run_command(
            "v.db.update", map=layer.name, column="lyr_name", value=layer.name[:15]
        )
        return 0

    # write coordinates to file
    def write2(self, vformat, outfile, index):
        if vformat == "point":
            separator = glob.py_separator
        else:
            separator = " "

        if inputs.dim == 2:
            endline = "\n"
        if inputs.dim == 3:
            endline = separator

        # create input file for subsample of the 1st layer
        if vformat == "point":
            # point name (standard format is nameless)
            outfile.write(inputs.data[index][0] + separator)

        outfile.write(inputs.data[index][1] + separator)  # easting
        outfile.write(inputs.data[index][2] + endline)  # northing

        if inputs.dim == 3:
            outfile.write(inputs.data[index][3] + "\n")  # elevation

        return 0


# ****** #


class Merge_init(layer):  # Functionality for merging layers
    item = ""
    n_items = 0
    len_item = []  # array of length of layers' names

    def __init__(self, pattern):
        self.pattern = pattern  # list of merged layers
        merge_list = self.count_layers()
        Merge_init.item, Merge_init.n_items, Merge_init.len_item = merge_list

    # options -> properties of merged layers (count and names)
    def count_layers(self):
        # split pattern to the names of merged layers
        item = self.pattern.strip(" ").split(",")
        n_items = len(item)  # count merged layers

        len_item = [0 for i in range(0, n_items)]  # initialize
        for i in range(0, n_items):
            len_item[i] = len(item[i])  # array of length of layers' names

        return item, n_items, len_item


# ****** #


class Merge(Merge_init, layer):
    name = []  # export to DXF after merging
    vector = []  # export to DXF after merging
    n_pts = []
    filename = []
    init_add = True
    init_done = True
    wait4 = False

    def __init__(self, export2dxf):
        self.export2dxf = export2dxf
        if sum(Merge_init.len_item) > 0:
            if Merge.init_add is True:
                # export to DXF after merging
                Merge.name = ["" for i in range(0, Merge_init.n_items)]
                # export to DXF after merging
                Merge.vector = ["" for i in range(0, Merge_init.n_items)]
            (Merge.name, Merge.vector, Merge.init_add, Merge.wait4) = self.add_layers()

            # export to DXF if the layer is not to be merged
            # layer containing several objects
            if dxf.export2 is True and Merge.wait4 is True:
                # create merged file of the layer to be merged...
                # and convert it at last
                if Merge.init_done is True:
                    # number of points in merged layers
                    Merge.n_pts = [[] for i in range(0, Merge_init.n_items)]
                    for i in range(0, Merge_init.n_items):
                        # set up path to final merged file
                        Merge.filename.append(
                            files(Merge_init.item[i] + "_bckp").path2("txt")  # etc
                        )

                        test(Merge.filename[i]).overwrite_file()
                Merge.n_pts, Merge.init_done = self.outfiles()

    # add layer to the merge list according to pattern
    def add_layers(self):
        for i in range(0, Merge_init.n_items):
            # compare name of each layer with the items of the pattern:
            if layer.name[: Merge_init.len_item[i]] == Merge_init.item[i]:
                # test: layer to be merged and merged layer not to be identical
                if Merge_init.len_item[i] == len(layer.name):
                    msgr.fatal(
                        _(
                            "Please change merging rule or layer <"
                            + Merge_init.item[i]
                            + ">. Their names"
                            + " should not be identical."
                        )
                    )

                if Merge.name[i] == "":  # initial value:
                    # name of the first layer according to the pattern
                    Merge.name[i] = layer.name
                    # vector type of the first layer according to the pattern
                    Merge.vector[i] = layer.vector
                    Merge.init_add = False
                else:  # next values:
                    # add all suitable layers delimited by comma
                    Merge.name[i] += "," + layer.name
                    # add vector types of the layers
                    Merge.vector[i] += "," + layer.vector

                    # test if all layers have the same vector type
                    control_items = Merge.vector[i].split(",")  # create list
                    n_ctrl = len(control_items)  # length of the list

                    # compare two last values
                    if control_items[n_ctrl - 1] != control_items[n_ctrl - 2]:
                        msgr.fatal(
                            _(
                                "Please redefine merging option <"
                                + Merge.item[i]
                                + ">. Different vector"
                                + " types match this rule."
                            )
                        )
                if dxf.export2 is True:  # the layers should be exported 2 CAD:
                    Merge.wait4 = True  # do not export layers before merging
                    return (Merge.name, Merge.vector, Merge.init_add, Merge.wait4)

        return Merge.name, Merge.vector, Merge.init_add, Merge.wait4

    # merge files to convert several objects as one layer
    def outfiles(self):
        # compare current layer with the list of merged ones & derive settings.
        for i in range(0, Merge_init.n_items):  # for each merged layer:
            n_item = len(Merge_init.item[i])
            # if current layer is to be merged:
            if Merge.wait4 is True and layer.name[:n_item] == Merge_init.item[i]:
                merge_file = Merge.filename[i]
                # set up name of current file to be merged
                if layer.vector == "P":
                    add_file_name = files(layer.name).path2("txt")
                else:
                    add_file_name = files(layer.name + "_bckp").path2("txt")
                if layer.vector == "B":
                    subtract = -1
                else:
                    subtract = 0
                # add merged items to list of point number in the layer
                Merge.n_pts[i].append(layer.n_pts + subtract)
                Merge.init_done = False
                # test if file to be added is not blank
                with open(add_file_name, "r") as add_file:
                    test(add_file).blank(False)

                # test if final file that shall contain coordinates...
                # ... of all parts of the layer is blank
                with open(merge_file, "a+") as merged_file:
                    test(merged_file).blank(False)

                # add content of the current file to the final file
                with open(merge_file, "a") as merged_file:
                    with open(add_file_name, "r") as add_file:
                        for line in add_file:
                            merged_file.write(line)

        return Merge.n_pts, Merge.init_done

    # merge layers according to pattern items
    def layers(self):
        if sum(Merge_init.len_item) > 0:
            if not Merge.name:
                msgr.warning(
                    _(
                        "There are no layers to merge into <"  # etc
                        + Merge_init.item[0]
                        + ">."
                    )
                )
            MakeSameVarcharColTypeLengthMapTables(tables=Merge.name)
            # merge layers to temporary layer
            grass.run_command(
                "v.patch",
                input=Merge.name,
                output=Merge_init.item[0] + "_tmp",
                flags="e",
                overwrite=True,
            )
            for map in Merge.name:
                grass.run_command(
                    "g.remove",
                    flags="f",
                    type="vector",
                    name=map,
                )
        return 0

    # clean topology
    def clean_topology(self):
        if sum(Merge_init.len_item) > 0:
            for i in range(0, 1):
                if Merge.name[i] != "":  # just for merged layers

                    # find out code to recognize a type of the vector layer:
                    # split the name of the 1st layer to be merged...
                    element = Merge.name[i].split(",")[0]
                    part = element.split("_")  # ... by '_'
                    n_part = len(part)  # count parts
                    # code: the last part of the layer's name
                    code = part[n_part - 1]

                    # test vector type
                    if code == "line":
                        methods = "snap,break,rmdupl"  # topology clean
                        lyr_name = Merge.item[i] + "_line"  # final layer name
                    elif code != "pt":  # polygons
                        methods = "break,rmdupl,rmsa"  # topology clean
                        lyr_name = Merge.item[i]  # final layer name
                        # test if these layers have been merged already
                        current_layer.test_existence(lyr_name, False)

                    # each non-point layer that has not been cleaned yet:
                    if code != "pt":
                        temp = Merge.item[i] + "_tmp"  # temporary layer
                        # topology clean according to vector type
                        grass.run_command(
                            "v.clean", input=temp, output=lyr_name, tool=methods
                        )
                        # remove temporary layer
                        grass.run_command(
                            "g.remove", type="vector", name=temp, flags="f"
                        )
        return 0


# ****** #


class dxf(files):
    # based on v.out.dxf by Chuck Ehlschlaeger, Radim Blazek and Martin Landa
    export2 = False
    File = ""  # dxf file
    out = ""
    units = "metric"
    textsize = ""

    def __init__(self, export2, File, unit, textsize):
        dxf.export2 = export2
        dxf.File = File
        dxf.unit = unit
        dxf.textsize = float(textsize)

        # open dxf file
        if dxf.export2 is True:
            if dxf.File == "":
                msgr.fatal(
                    _("Please set up a name of the DXF file" + " or remove -x flag.")
                )

            # open dxf file and test if it is empty (should be)
            dxf.out = files(dxf.File).open_output(False, True)

            # setup height of the text if invalid value
            if dxf.textsize < 0.0:
                msgr.fatal(_("Text height must be positive."))

            if dxf.textsize == 0.0:
                # find extends and save textsize
                dxf.textsize = self.do_limits(True)
            else:
                # find extends and do not save textsize (given by the user)
                self.do_limits(False)

            self.make_tables()  # start section of the tables

    # estimate text size according to the map extents
    # original: make_layername (v.out.dxf: main)
    def do_limits(self, calculate_textsize):
        region = grass.region()
        self.north = region["n"]
        self.south = region["s"]
        self.east = region["e"]
        self.west = region["w"]

        self.header()
        self.draw_units()
        self.limits()
        self.endsec()

        if calculate_textsize is True:
            if (self.east - self.west) >= (self.north - self.south):
                dxf.textsize = (self.east - self.west) * text_ratio
            else:
                dxf.textsize = (self.north - self.south) * text_ratio

                return dxf.textsize
        else:
            return 0

    # set up drawing units
    def draw_units(self):
        if dxf.units == "imperial":
            code = 0
        elif dxf.units == "metric":
            code = 1
        else:
            msgr.fatal(
                _("Please set up the drawing units" + " to 'metric' or to 'imperial'.")
            )

        dxf.out.write("  9\n$MEASUREMENT\n 70\n%6d\n" % code)

        return 0

    # define tables
    # functions from v.out.dxf
    def make_tables(self):
        self.tables()
        self.linetype_table(1)
        self.solidline()
        self.endtable()
        self.layer_table(7)
        self.layer0()

        return 0

    # write the header
    # original: dxf_header (v.out.dxf: write_dxf)
    def header(self):
        dxf.out.write("  0\nSECTION\n  2\nHEADER\n")

        return 0

    # write tables
    # original: dxf_tables (v.out.dxf: write_dxf)
    def tables(self):
        dxf.out.write("  0\nSECTION\n  2\nTABLES\n")

        return 0

    # write entities
    # original: dxf_entities (v.out.dxf: write_dxf)
    def entities(self):
        dxf.out.write("  0\nSECTION\n  2\nENTITIES\n")

        return 0

    # end section
    # original: dxf_endsec (v.out.dxf: write_dxf)
    def endsec(self):
        dxf.out.write("  0\nENDSEC\n")

        return 0

    # finalize dxf file
    # original: dxf_eof (v.out.dxf: write_dxf)
    def eof(self):
        dxf.out.write("  0\nEOF\n")
        dxf.out.close()

        return 0

    # header stuff
    # original: dxf_limits (v.out.dxf: write_dxf)
    def limits(self):
        dxf.out.write(
            "  9\n$LIMMIN\n 10\n"
            + str(self.west)
            + "\n 20\n"  # etc
            + str(self.south)
            + "\n"
        )
        dxf.out.write(
            "  9\n$LIMMAX\n 10\n"
            + str(self.east)
            + "\n 20\n"  # etc
            + str(self.north)
            + "\n"
        )

        return 0

    # tables stuff
    # original: dxf_linetype_table (v.out.dxf: write_dxf)
    def linetype_table(self, numlines):
        dxf.out.write("  0\nTABLE\n  2\nLTYPE\n 70\n%6d\n" % numlines)

        return 0

    # original: dxf_layer_table (v.out.dxf: write_dxf)
    def layer_table(self, numlayers):
        dxf.out.write("  0\nTABLE\n  2\nLAYER\n 70\n%6d\n" % numlayers)

        return 0

    # end table
    # original: dxf_endtable (v.out.dxf: write_dxf)
    def endtable(self):
        dxf.out.write("  0\nENDTAB\n")

        return 0

    # write line
    # original: dxf_solidline (v.out.dxf: write_dxf)
    def solidline(self):
        dxf.out.write("  0\nLTYPE\n  2\nCONTINUOUS\n 70\n")
        dxf.out.write("    64\n  3\nSolid line\n 72\n    65\n")
        dxf.out.write(" 73\n     0\n 40\n0.0\n")

        return 0

    # todo: naco?
    # original: dxf_layer0 (v.out.dxf: write_dxf)
    def layer0(self):
        dxf.out.write("  0\nLAYER\n  2\n0\n 70\n     0\n")
        dxf.out.write(" 62\n     7\n  6\nCONTINUOUS\n")

        return 0

    # create list of the layers and of their properties...
    # ... and write them to dxf file
    # functions from v.out.dxf

    # end section of tables
    def end_tables(self):
        dxfs.endtable()
        dxfs.endsec()

        return 0

    # finalize dxf file
    def end_dxf(self):
        dxfs.endsec()  # end section
        dxfs.eof()  # puts final stuff in dxf_fp, closes file

        return 0

    # setup elevation according to 2D/3D geometry
    def setup_elev(self, point):
        if inputs.dim == 3:  # 3D objects:
            if point[3] == "":  # empty elevation:
                elev = str(0.0)  # setup 0.
            else:
                elev = point[3]  # setup value
        else:  # 2D objects:
            elev = str(0.0)  # setup 0.

        return elev


# ****** #


class dxf_layer_merged(Merge):
    name = ""
    vector = ""
    n_pts = ""

    def __init__(self, i):
        self.i = i
        dxf_layer_merged.name = Merge_init.item[i]
        dxf_layer_merged.vector = Merge.vector[i] if Merge.vector else ""
        dxf_layer_merged.n_pts = Merge.n_pts[i] if Merge.n_pts else ""
        Merge.wait4 = False


class dxf_layer(Merge, dxf):  # *** make separate dxf layers *** #
    color = 1  # layer color (1-255). 0 not recognized by AutoCAD Civil 2015.
    n = 0  # number of the layers
    name = []  # list of layers for drawing entities
    vector = []  # list of geometry types
    n_pts = []  # list of point numbers

    def __init__(self, set_layer):
        self.set_layer = set_layer

        # export to DXF if the layer is not to be merged
        # layer containing single object:
        if dxf.export2 is True and Merge.wait4 is False:
            self.dxf_properties()

        Merge.wait4 = False

    # DXF properties
    def dxf_properties(self):
        # add layer name to the list for drawing entities
        dxf_layer.name.append(self.set_layer.name)
        # add geometry type to the list for drawing entities
        dxf_layer.vector.append(self.set_layer.vector)
        # add no. of pts to the list
        dxf_layer.n_pts.append(self.set_layer.n_pts)

        dxf_layer.n += 1  # increase number of the layers to be drawn
        Merge.wait4 = False  # merging indicator to the default (no merge)

        self.layername()  # add layer name to the layer section
        dxf_layer.color = self.setup_color()

        return (
            dxf_layer.color,
            dxf_layer.n,
            dxf_layer.name,
        )  # etc
        dxf_layer.vector, dxf_layer.n_pts, Merge.wait4

    # define layers and their properties
    # original: make_layername (v.out.dxf: main)
    def layername(self):
        self.layercontent("", "CONTINUOUS", 0)  # geometry object
        self.layercontent("_elev_pts", "CONTINUOUS", 0)  # elevation (vertex)
        self.layercontent("_label_pts", "CONTINUOUS", 0)  # label (vertex)
        if layer.vector != "P":
            self.layercontent("_label", "CONTINUOUS", 0)  # label layer

        return 0

    # write layer
    # original: dxf_layer (v.out.dxf: write_dxf)
    def layercontent(self, suffix, linetype, is_frozen):
        if is_frozen:
            frozen = 1
        else:
            frozen = 64
        dxf.out.write(
            "  0\nLAYER\n  2\n"
            + dxf_layer.name[dxf_layer.n - 1]  # etc
            + suffix
            + "\n 70\n"
        )
        dxf.out.write("%6d\n 62\n%6d\n  6\n%s\n" % (frozen, self.color, linetype))

        return 0

    # extra color for each group of layers to export2dxf (geometry + labels)
    def setup_color(self):
        self.color += 1  # calculate new color indicator
        if self.color == 256:  # if maximum value of 255 has been exceeded:
            self.color = 1  # set up minimum again

        return self.color


# ****** #


class finalize_dxf(
    inputs,
    dxf,
    dxf_layer_merged,
):
    def __init__(self):
        dxfs.end_tables()  # close the section of the tables

        msgr.message(_("Converting layers to DXF..."))
        self.entities2()
        dxfs.end_dxf()  # finalize and close dxf file

    # add point to the entity in the dxf file
    # based on add_plines (v.out.dxf: main)
    def point2dxf(self, vector, point, seq_type):
        # create layer name according to entity type (geometry or text)
        if seq_type == "geometry":
            appendix = ""
        else:  # elevation or point label, or layer label
            appendix = "_" + seq_type

        self.layer2write = self.dxf_layer_name + appendix  # layer name

        # write geometry
        if seq_type == "geometry":
            if vector == "P":
                self.point2write(point)  # write point
            else:
                self.vertex(point)  # write vertex

        # write label to point or to the layer
        elif seq_type == "label":
            self.text2write(True, self.dxf_layer_name)  # write label

        # write elevation to the point
        else:
            if seq_type == "elev_pts":
                default_justification = False  # change justification mode
                text = self.setup_elev(point)  # text elevation (2D point: 0.0)
            if seq_type == "label_pts":
                default_justification = True  # keep default justification mode
                text = str(point[0])  # use point name as text

            # write point labels (name and elev)
            self.text2write(default_justification, text)

        return 0

    # label centroid
    def label_centroid(self, n):
        self.centroid.append(self.dxf_layer_name)  # add layer name
        self.centroid.append(self.sum_east / n)  # easting
        self.centroid.append(self.sum_north / n)  # northing
        self.centroid.append(self.sum_elev / n)  # elevation

        self.point2dxf("P", self.centroid, "label")  # label layer

        return 0

    # initial values for the label of the layer
    def init_label(self):
        # compute centroid for line/polygon elements
        self.sum_east = 0.0
        self.sum_north = 0.0
        self.sum_elev = 0.0
        self.centroid = []
        return self.sum_east, self.sum_north, self.sum_elev, self.centroid

    # write sequence to dxf
    def write_sequence(self, parts, seq_type):
        self.seq_type = seq_type

        with open(self.filename, "r+") as coord_file:  # open backup file:
            test(self.filename).files()  # test if the file exists
            test(self.filename).blank(False)  # test if the file is not blank

            # initial values for the label of the layer
            if self.seq_type == "label" and self.vector != "P":
                (
                    self.sum_east,
                    self.sum_north,
                    self.sum_elev,
                    self.centroid,
                ) = self.init_label()

            closing_pt = True  # current point should close the polygon shape

            # converting a layer with more than one object:
            if parts is not None:
                close_merged = 0  # point index for splitting line detection
                index_merged = 0  # index of the object in the layer
                # no. of points in labeled objects => closing point detection
                done = parts[0]
                sum_layer = sum(parts)

            for line in iter(coord_file.readline, ""):
                # extract point name and coordinates
                self.point = line.strip("\n").split(glob.py_separator)

                if self.seq_type != "label":
                    # write point to particular entity
                    self.point2dxf(self.vector, self.point, self.seq_type)

                # write label of the layer
                if self.seq_type == "label" and self.vector != "P":
                    # sum of coordinates
                    self.sum_east += float(self.point[1])
                    self.sum_north += float(self.point[2])
                    if inputs.dim == 3:
                        self.sum_elev += float(self.point[3])

                    # write label extra for each object in the layer
                    if parts is not None:
                        if close_merged == done - 1:  # closing point reached:
                            # no. of points in the object
                            n = parts[index_merged]
                            # compute and label centroid of the object
                            self.label_centroid(n)

                            # start writing centroid of the next object
                            # initial values for the label of the layer
                            if self.seq_type == "label" and self.vector != "P":
                                (
                                    self.sum_east,
                                    self.sum_north,
                                    self.sum_elev,
                                    self.centroid,
                                ) = self.init_label()

                            index_merged += 1  # index of the next object

                            # add number of currently labeled object to the sum
                            # to not exceed array size:
                            if index_merged < len(parts):
                                done += parts[index_merged]

                        # check the next point (closing or not)
                        close_merged += 1
                    # end: if merged_elements is not None
                # end: if seq_type == 'label_pts' and code != 'P'

                # write geometry of the layer
                if self.seq_type == "geometry":
                    if self.vector == "B":  # for polygon layer:
                        # if closing point (CP) missing in current session:
                        if closing_pt:
                            # save coordinates of (CP)
                            point0 = self.point
                            # => not necessary to save CP in the session now
                            closing_pt = False

                    # separated objects (lines or polygons)
                    if parts is not None and self.vector != "P":
                        if close_merged == done - 1:  # closing point reached:
                            # close the object:
                            if self.vector == "B":  # copy closing point (B)
                                # closing point
                                self.point2dxf(self.vector, point0, self.seq_type)
                            self.poly_end()  # end line/polygon object

                            # start new line/polygon object
                            # not after the last object:
                            if close_merged < sum_layer - 1:
                                self.polyline()
                            if self.vector == "B":
                                closing_pt = True

                            index_merged += 1  # index of the next object
                            # add number of currently labeled object to the sum
                            if index_merged < len(parts):
                                # to not exceed array size
                                done += parts[index_merged]

                        # check the next point (closing or not)
                        close_merged += 1
                    # end: if merged_elements is not None ...
                    # and (code == 'B' or code == 'L')
                # end: if seq_type == 'label_pts' and code != 'P'
            # end: line in iter(coord_file.readline, '')

            # single object in the layer:
            if parts is None:
                # close geometry
                if self.seq_type == "geometry":
                    if self.vector == "B":
                        # write closing point
                        self.point2dxf(self.vector, point0, self.seq_type)
                    if self.vector != "P":
                        self.poly_end()  # end polygon

                # label the layer
                if self.seq_type == "label" and self.vector != "P":
                    self.label_centroid(self.dxf_layer_n_pts)

        return 0

    # write geometry entities to dxf file
    def entities2(self):
        dxfs.entities()  # start section of entities

        j = 0  # index of merging pattern item (= merged layer name)
        for i in range(0, dxf_layer.n):
            self.dxf_layer_name = dxf_layer.name[i]
            self.vector = dxf_layer.vector[i]
            self.dxf_layer_n_pts = dxf_layer.n_pts[i]

            # set up input file appendix (depends on geometry type)
            if self.vector == "P":
                base = self.dxf_layer_name
            else:
                base = self.dxf_layer_name + "_bckp"
            self.filename = files(base).path2("txt")  # path to input file

            # write geometry
            if self.vector != "P":
                self.polyline()  # start polyline entity

            # if current layer has been merged:
            if Merge_init.item[j] == self.dxf_layer_name:
                parts = Merge.n_pts[j]  # find number of points in each object
                j += 1  # index of the next merged layer
            else:
                parts = None  # not merged layers: there are no parts

            # write geometry and label of the layer
            self.write_sequence(parts, "geometry")
            self.write_sequence(parts, "label")

            # write labels of the vertices
            self.write_sequence(None, "label_pts")

            # write elevations of the vertices
            self.write_sequence(None, "elev_pts")

        return 0

    # entities: point
    # original: dxf_point (v.out.dxf: write_dxf)
    def point2write(self, point):
        self.east = point[1]
        self.north = point[2]
        self.elev = self.setup_elev(point)

        dxf.out.write("0\nPOINT\n")
        dxf.out.write("8\n" + self.dxf_layer_name + "\n")
        dxf.out.write(
            "10\n"
            + self.east
            + "\n20\n"
            + self.north
            + "\n30\n"  # etc
            + self.elev
            + "\n"
        )

        return 0

    # entities: polyline
    # original: dxf_polyline (v.out.dxf: write_dxf)
    def polyline(self):
        dxf.out.write("0\nPOLYLINE\n")
        dxf.out.write("8\n" + self.dxf_layer_name + "\n")
        dxf.out.write("66\n1\n")
        # fprintf(dxf_fp,"10\n0.0\n 20\n0.0\n 30\n0.0\n"); *//* ?

        if inputs.dim == 3:
            dxf.out.write("70\n8\n")

        return 0

    # entities: vertex
    # original: dxf_vertex (v.out.dxf: write_dxf)
    def vertex(self, point):
        self.east = point[1]
        self.north = point[2]
        self.elev = self.setup_elev(point)

        dxf.out.write("0\nVERTEX\n")
        dxf.out.write("8\n" + self.dxf_layer_name + "\n")
        dxf.out.write(
            "10\n"
            + self.east
            + "\n20\n"
            + self.north
            + "\n 30\n"  # etc
            + self.elev
            + "\n"
        )

        return 0

    # entities: text
    # original: dxf_text (v.out.dxf: write_dxf)
    def text2write(self, default, text):
        self.east = self.point[1]
        self.north = self.point[2]
        self.elev = self.setup_elev(self.point)

        # start text entity
        dxf.out.write("  0\nTEXT\n  8\n" + self.layer2write + "\n")
        # reference point
        dxf.out.write(" 10\n%s\n20\n%s\n30\n%s\n" % (self.east, self.north, self.elev))
        # text properties
        dxf.out.write(" 40\n" + str(dxf.textsize) + "\n  1\n" + text + "\n")

        # do not use default justification (hz: left, v: baseline):
        if default is False:
            # justify to hz: rigth, v: top
            dxf.out.write(
                (" 72\n     2\n 73\n     3\n 11\n%s\n 21\n" + "%s\n 31\n%s\n")  # etc
                % (self.east, self.north, self.elev)
            )

        return 0

    # entities: end polyline
    # original: dxf_poly_end (v.out.dxf: write_dxf)
    def poly_end(self):
        dxf.out.write("  0\nSEQEND\n  8\n" + self.dxf_layer_name + "\n")

        return 0


# ****** #


def main():
    global msgr
    msgr = get_msgr()  # setup messenger as global variable

    global overwrite_all
    overwrite_all = grass.overwrite()

    global current_layer
    global dxfs
    global text_ratio  # size of text compared to screen = 1
    global centered
    global done_lyrs
    text_ratio = 0.003
    centered = 4

    # define options
    opt = glob(options["input"], options["outdir"], options["separator"])
    # open list of existing layers
    done_lyrs = files("_layers_done").open_output(True, False)

    # define rules for vector type
    rules = vect_rules(
        options["pt_rules"],
        options["ln_rules"],
        options["poly_rules"],
        options["easting"],
        options["northing"],
        options["elevation"],
    )

    # flags for v.in.ascii
    Flag("n")
    Flag("t")
    Flag("r")
    Flag("z")
    Flag("e")

    # export to dxf
    dxfs = dxf(
        flags["x"], options["dxf_file"], options["draw_unit"], options["textsize"]
    )

    # *** read input coordinates
    inp = inputs(options["skip"])

    # continue importing layers to GIS
    current_name = layer_init(0)
    current_layer = layer(0)  # initial layer settings

    # test options for merging layers
    merge_init = Merge_init(options["merge_lyrs"])  # manage items to merge

    # continue importing layers to GIS
    for i in range(0, inp.n):  # step: number of columns (3 or 4)
        new_name = layer_init(i)

        # compare current lyr name with i-th name
        if current_name.name != new_name.name:  # not equal =>
            current_layer.complete()  # finalize current layer's output file
            current_layer.make_new()  # import current layer
            merge = Merge(dxf.export2)  # add current layer to the merging list
            dxf_lyr = dxf_layer(current_layer)

            # make a note that layer has been done
            done_lyrs.write(
                str(current_layer.n_pts)
                + glob.py_separator  # etc
                + current_layer.name
                + glob.py_separator  # etc
                + current_layer.vector
                + "\n"
            )

            current_name = layer_init(i)
            current_layer = layer(i)  # setup new layer as current
        # end initializing a new layer

        current_layer.write(i)  # write the point to the file of current layer
    # end for i in range(0, n, dim+1)

    # *** process the last layer import
    current_layer.complete()  # finalize current layer's output file
    current_layer.make_new()  # import current layer
    merge = Merge(dxf.export2)  # add current layer to the merging list
    dxf_lyr = dxf_layer(current_layer)

    # make a note that layer has been done
    done_lyrs.write(
        str(current_layer.n_pts)
        + glob.py_separator  # etc
        + current_layer.name
        + glob.py_separator  # etc
        + current_layer.vector
        + "\n"
    )
    done_lyrs.close()

    # finalize merging and clean topology
    if merge.n_items > 0:
        merge.layers()  # merge the layers
        merge.clean_topology()  # clean topology

    # finalize DXF export
    if dxf.export2 is True:
        if merge.n_items > 0:
            # add merged layers
            for i in range(0, merge.n_items):
                dxf_pars = dxf_layer_merged(i)
                # add merged layers to the table of layers
                dxf_lyr = dxf_layer(dxf_pars)
        fin_dxf = finalize_dxf()  # create entities in DXF file

    return 0


if __name__ == "__main__":
    options, flags = grass.parser()
    main()
