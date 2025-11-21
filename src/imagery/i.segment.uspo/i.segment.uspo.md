## DESCRIPTION

*i.segment.uspo* provides unsupervised segmentation parameter
optimization for
*[i.segment](https://grass.osgeo.org/grass-stable/manuals/i.segment.html)*
determined by the compromise between intra-segment variance and
inter-segment spatial autocorrelation.

The module runs segmentation across a user defined set of thresholds and
minimum segment sizes, as well, for the mean shift algorithm, a set of
spectral and spatial bandwiths. For the mean shift algorithm, you can
also activate adaptive bandwidth using the *-a* flag.

The user provides an imagery **group** and the name of an **output**
text file where parameter and optimization values for all tested
segmentations are stored. The user can either give a list of thresholds
and minimum sizes, or provides start, stop and step values for each. In
addition, the user can provide a list of named **regions** for which to
test the segmentation. This allows to not test the entire image, but
rather to test specific areas in the image that might be characterstic
for specific types of land cover.

The module then selects the parameters providing the highest values of a
given optimization function. The number of "best" parameter combinations
to provide to the user per **region** is defined by **number\_best**.

Two optimization functions are available via the
**optimization\_function** parameter: A simple sum of the normalized
criteria values as defined by Espindola et al (2006), or the F-function
as defined by Johnson et al (2015). When using the F-function, the user
can determine the **f\_function\_alpha** value which determines the
relative weight of the intra-segment variance as compared to the
inter-segment spatial autocorrelation. A value of 0.5 gives the former
half weight of the latter, A value of 2 gives the former double weight
than the latter.

The optimization functions use intra-segment variance and inter-segment
spatial autocorrelation. For the latter, the user can chose to use
either [Moran's I](https://en.wikipedia.org/wiki/Moran%27s_I) or
[Geary's C](https://en.wikipedia.org/wiki/Geary%27s_C).

The user can chose between non-hierarchical (default) and hierarchical
segmentation using the **h** flag. The latter uses each segmentation at
a given threshold level as seed for the segmentation at the next
threshold level within a given minimum segment size. Note that this
leads to less optimal parallelization as for a given minsize, all
segmentations have to be done sequentially (see below).

The **segment\_map** parameter allows to provide a basename for keeping
the **number\_best** best segmentations for each given **region**
according to the optimization function. The resulting map names will be
a combination of this basename, the region, the threshold, the minsize
and the rank of the map within the region according to its optimization
criteria value.

The module uses high-level parallelization (running different
segmentations in parallel and then running the collection of parameter
values in parallel). The parameter **processes** allows to define how
many processes should be run in parallel. Note that when using
hierarchical segmentation the number of parallel processes is limited to
the number of different mininum segment sizes to test.

The **k** flag allows to keep all segmentation maps created during the
process.

## NOTES

The module depends on the addon
[r.neighborhoodmatrix](https://grass.osgeo.org/grass-stable/manuals/addons/r.neighborhoodmatrix.html)
which needs to be installed.

Any unsupervised optimization can at best be a support to the user.
Visual and other types of validation of the results, possibly comparing
several of the "best" solutions, remain necessary.

Even though the module allows the user to test different *minsizes*, it
is probably better to run the module with minsizes=1 and then adapt the
minsize in the final run of
[i.segment](https://grass.osgeo.org/grass-stable/manuals/i.segment.html)
depending on the desired minimum mapping unit.

In hierarchical segmentation mode, each segmentation is used as seed for
the next hierarchical level. This means that these segmentations have to
be run sequentially. Currently, parallelization is thus only used if
more than one value was given for *minsize*. In a future version,
parallelization should optionally be run by region if the number of
regions is larger than the number of different *minsize* values.

## EXAMPLE

```sh
g.region -au n=220767 s=220392 w=638129 e=638501 res=1 save=region1
g.region -au n=222063 s=221667 w=637659 e=638058 res=1 save=region2
i.group ortho input=ortho_2001_t792_1m
i.segment.uspo group=ortho regions=region1,region2 \
    output=ortho_parameters.csv segment_map=ortho_uspo \
    threshold_start=0.02 threshold_stop=0.21 threshold_step=0.02 \
    minsizes=5,10,15 number_best=5 processes=4 memory=4000
```

## REFERENCES

G. M. Espindola , G. Camara , I. A. Reis , L. S. Bins , A. M. Monteiroi
(2006), Parameter selection for region-growing image segmentation
algorithms using spatial autocorrelation, International Journal of
Remote Sensing, Vol. 27, Iss. 14, pp. 3035-3040,
<https://doi.org/10.1080/01431160600617194>  
  
B. A. Johnson, M. Bragais, I. Endo, D. B. Magcale-Macandog, P. B. M.
Macandog (2015), Image Segmentation Parameter Optimization Considering
Within- and Between-Segment Heterogeneity at Multiple Scale Levels: Test
Case for Mapping Residential Areas Using Landsat Imagery, ISPRS
International Journal of Geo-Information, 4(4), pp. 2292-2305,
<https://doi.org/10.3390/ijgi4042292>

## SEE ALSO

*[i.segment](https://grass.osgeo.org/grass-stable/manuals/i.segment.html),
[i.group](https://grass.osgeo.org/grass-stable/manuals/i.group.html),
[i.segment.hierarchical](i.segment.hierarchical.md),
[r.neighborhoodmatrix](r.neighborhoodmatrix.md)*

## AUTHOR

Moritz Lennert
