## DESCRIPTION

*v.nnstat* indicates clusters, separations or random distribution of
point dataset in 2D or 3D space using Nearest Neighbour Analysis (NNA).
The method is based on comparison of observed average distance between
the nearest neighbours and the distance which would be expected if
points in the dataset are distributed randomly. More detailed
information about theoretical background is provided in ([Clark and
Evans, 1954](https://web.archive.org/web/20171205194648/https://courses.washington.edu/bio480/Week1-PAPER-Clark_and_Evans1954.pdf)),
([Chandrasekhar, 1943,
p. 86-87](https://doi.org/10.1103/RevModPhys.15.1)). Details about the
module and testing are summarized in
([Stopkova, 2013](https://doi.org/10.14311/gi.11.2)).

## EXAMPLES

### Comparison of 2D and 3D NNA

On the example of dataset that contains 2000 randomly distributed
points, basic settings of analysis dimension (2D or 3D) will be
examined:

  - **2D NNA** may be performed using **2D vector layer**. If 2D NNA is
    required to be performed using **3D vector layer**,
    <span class="underline">flag *-2*</span> should be marked. The
    results of both cases can be seen below.
    
    ```sh
    v.nnstat input=rand_2000_2d
    ```
    

    Output in the command line:
    
    <table>
    <colgroup>
    <col style="width: 100%" />
    </colgroup>
    <tbody>
    <tr class="odd">
    <td></td>
    </tr>
    </tbody>
    </table>
    
    ```sh
    v.nnstat input=rand_2000_3d -2
    ```
    

    Output in the command line:
    
    <table>
    <colgroup>
    <col style="width: 100%" />
    </colgroup>
    <tbody>
    <tr class="odd">
    <td></td>
    </tr>
    </tbody>
    </table>
    
    **NOTE:** Comparing the results of 2D NNA with results summarized in
    ([Stopkova, 2013](https://doi.org/10.14311/gi.11.2)), there can be
    seen small difference between the values of area. It is assumed to
    be caused by differences in transformed coordinates of the convex
    hull that have been computed using two versions of the module.

  - **3D NNA** can be performed just using **3D vector layer**. If 3D
    NNA is required to be performed using **2D vector layer**,
    <span class="underline">name of the column in attribute table that
    contains elevation values</span> must be set. The results of both
    cases can be seen below.
    
    ```sh
    v.nnstat input=rand_2000_3d
    ```
    

    Output in the command line:
    
    <table>
    <colgroup>
    <col style="width: 100%" />
    </colgroup>
    <tbody>
    <tr class="odd">
    <td></td>
    </tr>
    </tbody>
    </table>
    
    ```sh
    v.nnstat input=rand_2000_2d zcolumn=z
    ```
    

    Output in the command line:
    
    <table>
    <colgroup>
    <col style="width: 100%" />
    </colgroup>
    <tbody>
    <tr class="odd">
    <td></td>
    </tr>
    </tbody>
    </table>

  - **Warning**: If flag *-2* is set up together with *zcolumn*, the
    flag will have higher priority and 2D NNA will be performed.

### Comparison of various datasets

In ([Stopkova, 2013](https://doi.org/10.14311/gi.11.2)), there might be
seen other examples (also clustered and dispersed datasets).

## TODO

  - add **graphical output**

## SEE ALSO

*[v.hull](https://grass.osgeo.org/grass-stable/manuals/v.hull.html)*

## REFERENCES:

Stopkova, 2013: Extension of mathematical background for Nearest
Neighbour Analysis in three-dimensional space,
<https://doi.org/10.14311/gi.11.2>,
<https://ojs.cvut.cz/ojs/index.php/gi/article/view/gi.11.2/2396>

## REQUIREMENTS

  - **LAPACK / BLAS** (libraries for numerical computing) for GMATH
    library (GRASS Numerical Library)  
    <https://www.netlib.org/lapack> (usually available on Linux distros)

## AUTHOR

Eva Stopkova  
functions for computation of Minimum Bounding Box volume (Minimum
Bounding Rectangle area) are based on functions for computing convex
hull from the module *v.hull* (Aime, A., Neteler, M., Ducke, B., Landa,
M.)
