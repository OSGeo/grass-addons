---
name: m.eigensystem
description: Computes eigenvalues and eigenvectors for an NxN matrix
---

# Computes eigenvalues and eigenvectors for an NxN matrix

## DESCRIPTION

*m.eigensystem* determines the eigen values and eigen vectors for square
matricies. The *inputfile* must have the following format: the first
line contains an integer K which is the number of rows and columns in
the matrix; the remainder of the file is the matrix, i.e., K lines, each
containing K real numbers. For example:  
*(Examples in this help page use the Spearfish-imagery sample dataset
maps spot.ms.1, spot.ms.2, and spot.ms.3)*

```text
          3
          462.876649   480.411218   281.758307
          480.411218   513.015646   278.914813
          281.758307   278.914813   336.326645
```

The output will be K groups of lines; each group will have the format:

```text
          E   real part imaginary part   relative importance
          V   real part imaginary part
                   ... K lines ...
          N   real part imaginary part
                   ... K lines ...
          W   real part imaginary part
                   ... K lines ...
```

The *E* line is the eigen value. The *V* lines are the eigen vector
associated with E. The *N* lines are the V vector normalized to have a
magnitude of 1. The *W* lines are the N vector multiplied by the square
root of the magnitude of the eigen value (E).

For the example input matrix above, the output would be:

```sh
          E  1159.7452017844    0.0000000000   88.38
          V     0.6910021591    0.0000000000
          V     0.7205280412    0.0000000000
          V     0.4805108400    0.0000000000
          N     0.6236808478    0.0000000000
          N     0.6503301526    0.0000000000
          N     0.4336967751    0.0000000000
          W    21.2394712045    0.0000000000
          W    22.1470141296    0.0000000000
          W    14.7695575384    0.0000000000

          E     5.9705414972    0.0000000000    0.45
          V     0.7119385973    0.0000000000
          V    -0.6358200627    0.0000000000
          V    -0.0703936743    0.0000000000
          N     0.7438340890    0.0000000000
          N    -0.6643053754    0.0000000000
          N    -0.0735473745    0.0000000000
          W     1.8175356507    0.0000000000
          W    -1.6232096923    0.0000000000
          W    -0.1797107407    0.0000000000

          E   146.5031967184    0.0000000000   11.16
          V     0.2265837636    0.0000000000
          V     0.3474697082    0.0000000000
          V    -0.8468727535    0.0000000000
          N     0.2402770238    0.0000000000
          N     0.3684685345    0.0000000000
          N    -0.8980522763    0.0000000000
          W     2.9082771721    0.0000000000
          W     4.4598880523    0.0000000000
          W   -10.8698904856    0.0000000000

```

## NOTES

The relative importance of the eigen value (E) is the ratio (percentage)
of the eigen value to the sum of the eigen values. Note that the output
is not sorted by relative importance.

In general, the solution to the eigen system results in complex numbers
(with both real and imaginary parts). However, in the example above,
since the input matrix is symmetric (i.e., inverting the rows and
columns gives the same matrix) the eigen system has only real values
(i.e., the imaginary part is zero). This fact makes it possible to use
eigen vectors to perform principle component transformation of data
sets. The covariance or correlation matrix of any data set is symmetric
and thus has only real eigen values and vectors.

## PRINCIPLE COMPONENTS

To perform principle component transformation on GRASS data layers, one
would use *r.covar* to get the covariance (or correlation) matrix for a
set of data layers, *m.eigensystem* to extract the related eigen
vectors, and *r.mapcalc* to form the desired components. For example, to
get the eigen vectors for 3 layers:

```sh
(echo 3; r.covar map.1,map.2,map.3 | grep -v "N = ") | m.eigensystem
```

Note that since r.covar only outputs the matrix, we must manually
prepend the matrix size (3) using the echo command.

Then, using the W vector, new maps are created:

```sh
r.mapcalc "pc.1 = 21.2395*map.1 + 22.1470*map.2 + 14.7696*map.3"
r.mapcalc "pc.2 =  2.9083*map.1 +  4.4599*map.2 - 10.8699*map.3"
r.mapcalc "pc.3 =  1.8175*map.1 -  1.6232*map.2 -  0.1797*map.3"
```

## PROGRAM NOTES

The source code for this program requires a Fortran compiler.

The equivalent *i.pca* command is:

```sh
i.pca in=spot.ms.1,spot.ms.2,spot.ms.3 out=spot_pca
```

## SEE ALSO

*[i.pca](https://grass.osgeo.org/grass-stable/manuals/i.pca.html),
[r.covar](https://grass.osgeo.org/grass-stable/manuals/r.covar.html),
[r.mapcalc](https://grass.osgeo.org/grass-stable/manuals/r.mapcalc.html),
[r.rescale](https://grass.osgeo.org/grass-stable/manuals/r.rescale.html)*

## AUTHOR

This code uses routines from the EISPACK system.  
The interface was coded by Michael Shapiro, U.S.Army Construction
Engineering Research Laboratory
