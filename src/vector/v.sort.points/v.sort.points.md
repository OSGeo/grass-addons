## DESCRIPTION

*v.sort.points* takes an **input** point vector map, sorts the points by
the values in the sort **column** and then writes the result to the
**output** map.

This is useful to display symbols in sizes proportionate to that same
column without having big symbols hide small symbols.

By setting the **r** flag, the user can also chose to reverse the
sorting order putting points with the highest value in front.

## EXAMPLE

```sh
d.vect -r map=schools_wake@PERMANENT type=point,line,boundary,area,face width=1 icon=basic/circle size=1 size_column=CAPACITYTO
v.sort.points input=schools_wake output=sorted_schools column=CAPACITYTO
d.vect -r map=sorted_schools@user1 type=point,line,boundary,area,face width=1 icon=basic/circle size=1 size_column=CAPACITYTO
```

## AUTHOR

Moritz Lennert
