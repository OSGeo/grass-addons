## DESCRIPTION

*m.gcp.filter* filters GCPs using the distance between the computed
coordinates and the actual coordinates of each GCP. The result of the
filtering (number of points to use after filtering, number of points
filtered out, final RMS error) is printed out.

The transformation equations are computed anew for each iteration. The
GCP with the largest distance between the computed coordinates and the
actual coordinates is deactivated and the next iteration is started.
Filtering stops when the overall RMS error is below the given
**threshold** or when the number of active GCPs is equal to the required
minimum number of points or when the optional maximum number of
iterations (option **iterations**) has been reached. With the **-d**
flag, the largest GCP error is used instead of the overall RMS error.

*m.gcp.filter* uses by default the results of forward transformations
(source to target) for filtering. With the **-b** flag, the results of
backward transformations (target to source) are used.

The status of GCPs (active / inactive) is only updated with the **-u**
flag. GCPs that have been filtered out will be deactivated, not deleted.

## NOTES

The transformations are:

order=1:

```text
    e = [E0 E1][1].[1]
        [E2  0][e] [n]

    n = [N0 N1][1].[1]
        [N2  0][e] [n]
```

order=2:

```text
    e = [E0 E1 E3][1 ] [1 ]
        [E2 E4  0][e ].[n ]
        [E5  0  0][e²] [n²]

    n = [N0 N1 N3][1 ] [1 ]
        [N2 N4  0][e ].[n ]
        [N5  0  0][e²] [n²]
```

order=3:

```text
    e = [E0 E1 E3 E6][1 ] [1 ]
        [E2 E4 E7  0][e ].[n ]
        [E5 E8  0  0][e²] [n²]
        [E9  0  0  0][e³] [n³]

    n = [N0 N1 N3 N6][1 ] [1 ]
        [N2 N4 N7  0][e ].[n ]
        [N5 N8  0  0][e²] [n²]
        [N9  0  0  0][e³] [n³]
```

\["." = dot-product, (AE).N = N'EA.\]

In other words, order=1 and order=2 are equivalent to order=3 with the
higher coefficients equal to zero.

## SEE ALSO

*[m.transform](https://grass.osgeo.org/grass-stable/manuals/m.transform.html),
[i.rectify](https://grass.osgeo.org/grass-stable/manuals/i.rectify.html)*

## AUTHOR

Markus Metz
