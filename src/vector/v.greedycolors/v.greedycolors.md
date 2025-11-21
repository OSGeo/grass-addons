## DESCRIPTION

*v.greedycolors* assigns numbers to areas such that no two adjacent
areas have the same number. At the same time, it tries to use as few
numbers as possible. The numbers are stored in the attribute table, by
default in the column "greedyclr" which is created if not existing.
These numbers can then be used to assign RGB colors in a new column to
be used with e.g. *d.vect* .

*v.greedycolors* works best if areas have unique categories. If multiple
areas have the same category, the corresponding network of neighboring
areas can become fairly complex, resulting in a larger number of greedy
colors. If the purpose is to assign different colors to neighboring
areas, irrespective of their category values, unique category values
need to be assigned first, e.g. to a new layer with
*[v.category](v.category)*.

There is always at least one optimal solution for greedy colors, using
as few colors as possible. However, it is usually computationally
intensive and not practical to search for an optimal solution. Therefore
a good solution is aproximated by ordering the areas first, before
assigning greedy colors. Here, the areas with the least neighbors are
processed first.

## EXAMPLE

Assigning greedy colors to county boundaries in the North Carolina
sample dataset:

Make a copy of the data:

```sh
g.copy vect=boundary_county,my_boundary_county
```

Greedy colors

```sh
v.greedycolors map=my_boundary_county
```

Check number and frequency of greedy colors

```sh
db.select sql="select greedyclr,count(greedyclr) from my_boundary_county group by greedyclr"
```

gives

```text
greedyclr|count(greedyclr)
1|262
2|351
3|302
4|11
```

four different colors were needed such that no two adjacent areas have
the same color

Assign RGB colors:

```sh
v.db.addcolumn map=my_boundary_county column="GRASSRGB varchar(11)"

v.db.update map=my_boundary_county column=GRASSRGB value="127:201:127" where="greedyclr = 1"
v.db.update map=my_boundary_county column=GRASSRGB value="190:174:212" where="greedyclr = 2"
v.db.update map=my_boundary_county column=GRASSRGB value="253:192:134" where="greedyclr = 3"
v.db.update map=my_boundary_county column=GRASSRGB value="255:255:153" where="greedyclr = 4"
```

## SEE ALSO

*[v.colors](v.colors.md), [v.category](v.category.md)*

## AUTHOR

Markus Metz, mundialis, Germany
