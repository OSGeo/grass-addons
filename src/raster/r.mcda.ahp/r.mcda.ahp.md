## DESCRIPTION

The *r.mcda.ahp* Generate a raster map classified with analytic
hierarchy process (AHP) \[Saaty, 1977 and Saaty & Vargas, 1991\]

## NOTES

It is mandatory to build a pairwise comparation table with the same
order of input of criteria maps in the criteria field.

Example: r.mcda.ahp criteria=reclass\_slope,reclass\_sand,reclass\_elev
pairwise=pairwise output=outputMap

The file "pairwise" has to have a structure like this:

\#start file

1.0, 0.2, 3.0

5.0, 1.0, 5.0

0.3, 0.2, 1.0

\#comment: order: reclass\_slope,reclass\_sand,reclass\_

\#end file

The first row and first column are related to the first criteria
(reclass\_slope in our case); the second row and second column are
related to the second criteria (reclass\_sand in our case) and the third
row and third column are related to the third criteria ( reclass\_elev
in our cas), and so on.

In the work directory should be generated a log.txt file were you can
find additional information like: eigenvectors, eigenvalues, weights

## TODO

## SEE ALSO

*[r.roughset](r.roughset.md), [r.mcda.regime](r.mcda.regime.md),
[r.mcda.fuzzy](r.mcda.fuzzy.md) [r.mcda.electre](r.mcda.electre.md),
[r.mcda.roughset](r.mcda.roughset.md) [r.in.drsa](r.in.drsa.md)
[r.to.drsa](r.to.drsa.md)*

## AUTHORS

Antonio Boggia - Gianluca Massei  
Department of Economics and Appraisal - University of Perugia - Italy
