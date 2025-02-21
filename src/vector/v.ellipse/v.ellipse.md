## DESCRIPTION

*v.ellipse* computes the best-fitting ellipse for **input** vector map
and creates new **output** vector map with ellipse. Input vector data
might be 2D points, lines, or areas.

![image-alt](v_ellipse.png)  
*Fig: Fitting ellipse created with v.ellipse*

The parameters of ellipse are printed on output if **--verbose** flag is
given.

## EXAMPLE

Example of *v.ellipse* created around set of points (using data
*points\_of\_interest*, North Carolina sample data set). Ellipse is is
approximated by linestring with point distance 1 degree (**step**).

```sh
v.ellipse input=points_of_interest output=ellipse step=1
```

## REFERENCES

- [Charles F. Van Loan: Using the Ellipse to Fit and Enclose Data
    Points.](https://www.cs.cornell.edu/cv/OtherPdf/Ellipse.pdf)

## SEE ALSO

*[v.hull](https://grass.osgeo.org/grass-stable/manuals/v.hull.html)*

## AUTHOR

Tereza Fiedlerova, OSGeoREL, Czech Technical University in Prague, Czech
Republic
