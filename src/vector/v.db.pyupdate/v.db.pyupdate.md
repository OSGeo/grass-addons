## DESCRIPTION

*v.db.pyupdate* assigns a new value to a column in the attribute table
connected to a given map. The new value is a result of a Python
expression. In other words, this module allows updating attribute values
using Python. Existing column values and, if specified, any installed
Python packages can be used to compute the new value. The module works
similarly to UPDATE statement from SQL, but it allows to use Python
syntax and functions for the cost of longer processing time.

The Python expression is specified by the **expression** option.
Existing attribute values can be accessed in this expression using the
column names. For example, an expression `place_name.split(",")[0]`
would uses Python string function `split` on a value from column
`place_name` assuming that column place\_name is of SQL type TEXT.

### Attributes

Attributes are accessible as variables using the column names as
specified in the attribute table. By default, all attributes will be
also accessible using the column name in all lower case. If this is not
desired, **-k** flag can be used to keep only the original name and not
provide the additional lower-cased version.

The types of variables in Python are `int` and `float` according if the
attribute value can be represented by `int` and `float` respectively.
The `str` type is used for all other values. If other types (objects)
are desired, they need to be constructed in explicitly. The result of
the expression needs to be something which can be converted into string
by the Python format function such as `int`, `float`, or `str`.

### Packages

The Python `math` package is loaded by default for convenience, so
expressions such as `math.cos(column_name)` are possible without further
settings. Additional packages can be loaded using the option
**packages**. Multiple packages can be specified as a comma separated
list, for example, `os,cmath,json`.

If the **-s** flag is specified, the imports of the packages specified
by option **packages** are additionally imported using a star import,
i.e., `import *`. This is considered a bad practice for general Python
code, but doing this might be helpful for constructing concise
expressions. The star import makes all functions (and other objects)
from the package available without the need to specify a package name.
For example, **packages** set to `math` with **-s** allows us to write
`cos(column_name)` bringing the syntax closer to, e.g., raster algebra
with *r.mapcalc*.

An arbitrary form of import statements, such as `from math import cos`,
can be used with the Python file provided using the **function** option
(see below).

### Selecting rows to update

A subset of rows from the attribute table to update can be selected
(filtered) using the SQL-based **where** option and the Python-based
**condition** option. The **where** option uses SQL syntax and will
lower the number of rows processed by this module in Python thus making
the processing faster. On the other hand, the **condition** option uses
Python syntax and all the rows still need to be processed by this module
in Python. In other words, although both options selected a subset of
rows to update, the **where** option lowers also the number of rows to
process in Python. Using **condition** for expressions which could be
expressed using SQL will be always slower than using the **where**
option with SQL. The **where** option is a great fit for conditions such
as `name is null`. The **condition** option is advantageous for more
complex computations where SQL does not provide enough functionality or
in case consistency with the Python syntax in the **expression** option
is more desired than speed. The code in the **condition** option has
access to the same variables, functions, and packages as the expression
for computing the new value. Syntactically, the **where** option is the
SQL WHERE clause without the WHERE keyword, while the **condition**
option is Python `if` statement without the `if` keyword and the
trailing colon (`:`). Similarly to the SQL WHERE clause which selects
the rows to be processed, the **condition** option, when evaluated as
`True` for a given row, selects that row to be processed. If the
condition evaluates as `False`, the row is skipped (filtered out). Both
options can be used together. When none is specified, all rows (records)
are updated.

## NOTES

*v.db.pyupdate* is loading the attribute table into memory, computing
the new values in Python, and then executing SQL transaction to update
the attribute table. Thus, it is only suitable when memory consumption
or time are not an issue, for example for small datasets.

For simple expressions, SQL-based *v.db.update* is much more
advantageous.

The module uses only GRASS GIS interfaces to access the database, so it
works for all database backends used for attribute tables in GRASS GIS.
A future or alternative version may use, e.g., a more direct
`create_function` function from Connection from the sqlite3 Python
package.

If you are calling this module from Python, it is worth noting that you
cannot pass directly functions defined or imported in your current
Python file (Python module) nor access any of the variables. However,
you can use string substitution to pass the variable values and a
separate file with function definitions which you can also import into
your code.

## EXAMPLES

The examples are using the full North Carolina sample data set unless
noted otherwise.

### Using a mathematical function

First, we create a copy of the vector map in the current mapset, so we
can modify it. Then, we add a new column `log_july` for a logarithm of
values for July.

```sh
g.copy vector=precip_30ynormals,my_precip_30ynormals
v.db.addcolumn map=my_precip_30ynormals columns="log_july double precision"
```

Now, we compute the values for the new column using the Python `log`
function from the `math` Python package (which is imported by default):

```sh
v.db.pyupdate map=my_precip_30ynormals column="log_july" expression="math.log(jul)"
```

We can examine the result, e.g., with *v.db.select*:

```sh
v.db.select map=my_precip_30ynormals columns=jul,log_july
```

```sh
jul|logjuly
132.842|4.88916045210132
127|4.84418708645859
124.206|4.82194147751127
104.648|4.65060233738593
98.298|4.58800368106618
...
```

### Shortening expressions

In case we want to make the expression more succinct, the above example
can be modified using the **-s** flag in combination with **packages**
to enable star imports:

```sh
v.db.pyupdate map=my_precip_30ynormals column="log_july" expression="log(jul)" packages=math -s
```

The expression can be now shorter, but the `math` package needs to be
explicitly requested.

### Replacing of NULL values

In this example, we assume we have a vector map of buildings. These
buildings have attribute name, but some are missing value for the name
attribute, but have a building number. We use SQL WHERE clause to
identify those and Python expression with an f-string to generate a name
from the building number in format *Building num. N*:

```sh
v.db.pyupdate map=buildings column="name" expression="f'Building num. {building_number}'" where="name is null"
```

## SEE ALSO

- *[v.db.addcolumn](https://grass.osgeo.org/grass-stable/manuals/v.db.addcolumn.html)*
    to add a new column (to be filled with values later),
- *[v.db.update](https://grass.osgeo.org/grass-stable/manuals/v.db.update.html)*
    for attribute updates using SQL,
- *[db.execute](https://grass.osgeo.org/grass-stable/manuals/db.execute.html)*
    to execute general SQL statements,
- *[v.db.addtable](https://grass.osgeo.org/grass-stable/manuals/v.db.addtable.html)*
    to add a new table to an existing vector map,
- *[v.db.connect](https://grass.osgeo.org/grass-stable/manuals/v.db.connect.html)*
    to find details about attribute storage,
- *[v.db.join](https://grass.osgeo.org/grass-stable/manuals/v.db.join.html)*
    to add columns from one table to another,
- *[v.db.select](https://grass.osgeo.org/grass-stable/manuals/v.db.select.html)*
    to obtain values from an attribute and test WHERE clauses.

## AUTHOR

Vaclav Petras, [NCSU Center for Geospatial
Analytics](https://cnr.ncsu.edu/geospatial)
