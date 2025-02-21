## DESCRIPTION

***r.change.info*** calculates landscape change assessment for a series
of categorical maps, e.g. land cover/land use, with different measures
based on information theory and machine learning. More than two
**input** maps can be specified.

***r.change.info*** moves a processing window over the **input** maps.
This processing window is the current landscape under consideration. The
size of the window is defined with **size**. Change assessment is done
for each processing window (landscape) separately. The centers of the
processing windows are **step** cells apart and the **output** maps will
have a resolution of **step** input cells. **step** should not be larger
than **size**, otherwise some cells will be skipped. If **step** is half
of **size** , the moving windows will overlap by 50%. The overlap
increases when **step** becomes smaller. A smaller **step** and/or a
larger **size** will require longer processing time.

The measures *information gain*, *information gain ratio*, *CHI-square*
and *Gini-impurity* are commonly used in decision tree modelling
(Quinlan 1986) to compare distributions. These measures as well as the
statistical distance are based on landscape structure and are calculated
for the distributions of patch categories and/or patch sizes. A patch is
a contiguous block of cells with the same category (class), for example
a forest fragment. The proportion of changes is based on cell changes in
the current landscape.

### Cell-based change assessment

The method **pc** calculates the *proportion of changes* as the actual
number of cell changes in the current landscape divided by the
theoretical maximum number of changes (number of cells in the processing
window x (number of input maps - 1)).

### Landscape structure change assessment

#### Landscape structure

For each processing window, the number of cells per category are counted
and patches are identified. The size and category of each patch are
recorded. From these cell and patch statistics, three kinds of patterns
(distributions) are calculated:

- **1. Distributions over categories (e.g land cover class)**  
    This provides information about changes in categories (e.g land
    cover class), e.g. if one category becomes more prominent. This
    detects changes in category composition.
- **2. Distributions over size classes**  
    This provides information about fragmentation, e.g. if a few large
    fragments are broken up into many small fragments. This detects
    changes in fragmentation.
- **3. Distributions over categories and size classes.**  
    This provides information about whether particular combinations of
    category and size class changed between input maps. This detects
    changes in the general landscape structure.

The latter is obtained from the category and size of each patch, i.e.
each unique category - size class combination becomes a separate class.

The numbers indicate which distribution will be used for the selected
method (see below).

A low change in category distributions and a high change in size
distributions means that the frequency of categories did not change much
whereas the size of patches did change.

#### Information gain

The methods **gain1, gain2 and gain3** calculate the *information gain*
after Quinlan (1986). The information gain is the difference between the
entropy of the combined distribution and the average entropy of the
observed distributions (conditional entropy). A larger value means
larger differences between input maps.

Information gain indicates the absolute amount of information gained (to
be precise, reduced uncertainty) when considering the individual input
maps instead of their combination. When cells and patches are
distributed over a large number of categories and a large number of size
classes, information gain tends to over-estimate changes.

The information gain can be zero even if all cells changed, but the
distributions (frequencies of occurrence) remained identical. The square
root of the information gain is sometimes used as a distance measure and
it is closely related to Fisher's information metric.

#### Information gain ratio

The methods **ratio1, ratio2 and ratio3** calculate the *information
gain ratio* that changes occurred, estimated with the ratio of the
average entropy of the observed distributions to the entropy of the
combined distribution. In other words, the ratio is equivalent to the
ratio of actual change to maximum possible change (in uncertainty). The
gain ratio is better suited than absolute information gain when the
cells are distributed over a large number of categories and a large
number of size classes. The gain ratio here follows the same rationale
as the gain ratio of Quinlan (1986), but is calculated differently.

The gain ratio is always in the range (0, 1). A larger value means
larger differences between input maps.

#### CHI-square

The methods **chisq1, chisq2 and chisq3** calculate *CHI square* after
Quinlan (1986) to estimate the relevance of the different input maps. If
the input maps are identical, the relevance measured as CHI-square is
zero, i.e. no change occurred. If the input maps differ from each other
substantially, major changes occurred and the relevance measured as
CHI-square is large.

#### Gini impurity

The methods **gini1, gini2 and gini3** calculate the *Gini impurity*,
which is 1 - Simpson's index, or 1 - 1 / diversity, or 1 - 1 / 2^entropy
for alpha = 1. The Gini impurity can thus be regarded as a modified
measure of the diversity of a distribution. Changes occurred when the
diversity of the combined distribution is larger than the average
diversity of the observed distributions, thus a larger value means
larger differences between input maps.

The Gini impurity is always in the range (0, 1) and calculated with  
  
G = 1 - ∑ p<sub>i</sub><sup>2</sup>

The methods *information gain* and *CHI square* are the most sensitive
measures, but also the most susceptible to noise. The *information gain
ratio* is less sensitive, but more robust against noise. The *Gini
impurity* is the least sensitive and detects only drastic changes.

#### Distance

The methods **dist1, dist2 and dist3** calculate the statistical
*distance* from the absolute differences between the average
distribution and the observed distributions. The distance is always in
the range (0, 1). A larger value means larger differences between input
maps.

Methods using the category or size class distributions (*gain1*,
*gain2*, *ratio1*, *ratio2* *gini1*, *gini2*, *dist1*, *dist2*) are less
sensitive than methods using the combined category and size class
distributions (*gain3*, *ratio3*, *gini3*, *dist3*).

For a thorough change assessment it is recommended to calculate
different change assessment measures (at least information gain and
information gain ratio) and investigate the differences between these
change assessments.

## NOTES

### Shannon's entropy

Entropies for information gain and its ratio are by default Shannon
entropies *H*, calculated with  
  
H = ∑ p<sub>i</sub> \* log<sub>2</sub>(p<sub>i</sub>)

The entropies are here calculated with base 2 logarithms. The upper
bound of information gain is thus log<sub>2</sub>(number of classes).
Classes can be categories, size classes, or unique combinations of
categories and size classes.

### Rényi's entropy

The **alpha** option can be used to calculate general entropies
*H<sub>α</sub>* after Rényi (1961) with the formula  
  
H<sub>α</sub> = 1 / (1 - α) \* log<sub>2</sub> (∑
p<sub>i</sub><sup>α</sup>)

An **alpha** \< 1 gives higher weight to small frequencies, whereas an
**alpha** \> 1 gives higher weight to large frequencies. This is useful
for noisy input data such as the MODIS land cover/land use products
MCD12\*. These data often differ only in single-cell patches. These
differences can be due to the applied classification procedure.
Moreover, the probabilities that a cell has been assigned to class A or
class B are often very similar, i.e. different classes are confused by
the applied classification procedure. In such cases an **alpha** \> 1,
e.g. 2, will give less weight to small changes and more weight to large
changes, to a degree alleviating the problem of class confusion.

## EXAMPLES

Assuming there is a time series of the MODIS land cover/land use product
MCD12Q1, land cover type 1, available, and the raster maps have the
names

```sh
MCD12Q1.A2001.Land_Cover_Type_1
MCD12Q1.A2002.Land_Cover_Type_1
MCD12Q1.A2003.Land_Cover_Type_1
...
```

then a change assessment can be done with

```sh
r.change.info in=`g.list type=rast pat=MCD12Q1.A*.Land_Cover_Type_1 sep=,` \
              method=pc,gain1,gain2,ratio1,ratio2,dist1,dist2
              out=MCD12Q1.pc,MCD12Q1.gain1,MCD12Q1.gain2,MCD12Q1.ratio1,MCD12Q1.ratio2,MCD12Q1.dist1,MCD12Q1.dist2 \
              radius=20 step=40 alpha=2
```

## SEE ALSO

*[r.neighbors](https://grass.osgeo.org/grass-stable/manuals/r.neighbors.html)*  
*[g.region](https://grass.osgeo.org/grass-stable/manuals/g.region.html)*  
*[r.li.shannon](https://grass.osgeo.org/grass-stable/manuals/r.li.shannon.html)*  
*[r.li.simpson](https://grass.osgeo.org/grass-stable/manuals/r.li.simpson.html)*  
*[r.li.renyi](https://grass.osgeo.org/grass-stable/manuals/r.li.renyi.html)*  
*[r.clump](https://grass.osgeo.org/grass-stable/manuals/r.clump.html)*

## REFERENCES

- Quinlan, J.R. 1986. Induction of decision trees. Machine Learning 1:
    81-106. [DOI:10.1007/BF00116251](https://doi.org/10.1007/BF00116251)
- Rényi, A. 1961. [On measures of information and
    entropy.](https://digitalassets.lib.berkeley.edu/math/ucb/text/math_s4_v1_article-27.pdf)
    Proceedings of the fourth Berkeley Symposium on Mathematics,
    Statistics and Probability 1960: 547-561.
- Shannon, C.E. 1948. A Mathematical Theory of Communication. Bell
    System Technical Journal 27(3): 379-423.
    [DOI:10.1002/j.1538-7305.1948.tb01338.x](https://doi.org/10.1002/j.1538-7305.1948.tb01338.x)

## AUTHOR

Markus Metz
