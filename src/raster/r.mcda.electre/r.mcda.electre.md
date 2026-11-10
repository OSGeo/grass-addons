## DESCRIPTION

*r.mcda.electre* is the implementation of the ELECTRE multicriteria
algorithm in GRASS GIS environment. It is one of the available tools in
the r.mcda suite. It requires as an input the list of raster
representing the criteria to be assessed in the multicriteria evaluation
and the vector of weights to be assigned. Every single cell of the GRASS
region is considered as one of the possible alternatives to evaluate and
it is described with the value assumed for the same cell by the raster
used as criteria. There are two output files. One represents the spatial
distribution of the concordance index, the other one of the discordance
index. The optimal solution is the one presenting the maximum
concordance value and the minimum discordance value at the same time.

## NOTES

The module does not standardize the raster-criteria. Therefore, they
must be prepared before by using, for example, r.mapcalc. The weights
vector is always normalized so that the sum of the weights is 1.

## CITE AS

Massei, G., Rocchi, L., Paolotti, L., Greco, S., & Boggia, Decision
Support Systems for environmental management: A case study on wastewater
from agriculture, Journal of Environmental Management, Volume 146, 15
December 2014, Pages 491-504, ISSN 0301-4797

## REFERENCE

Roy, B. (1971) Problem and methods with multiple objective functions
Mathematical programming 1, 239-266.

Roy, B. (1990): The outranking approach and the foundations of Electre
methods , Document du LAMSADE, Paris.

Janssen R. (1994) - Multiobjective decision support for environmental
management, Kluwer Academic Publishers.

GRASS Development Team (2015)

## SEE ALSO

*[r.mcda.input](r.mcda.input.md), [r.mcda.topsis](r.mcda.topsis.md), [r.mcda.roughset](r.mcda.roughset.md), [r.mcda.output](r.mcda.output.md)*

## AUTHORS

Antonio Boggia - Gianluca Massei  
Department of Economics and Appraisal - University of Perugia - Italy
