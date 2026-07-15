## DESCRIPTION

*i.pysptools.unmix* extracts endmembers from imagery group and performs
spectral unmixing using [pysptools](https://pysptools.sourceforge.io/).
The module creates an endmember text file and endmember raster maps.

The module is a wrapper around the **pysptools** Python library, that
integrates its functionality for [Endmember
Extraction](https://pysptools.sourceforge.io/eea.html) and [Spectral
Unmixing](https://pysptools.sourceforge.io/abundance_maps.html) into
GRASS GIS.

It requires that the Python libraries **pysptools** and **scikit-learn**
are installed (see below).

Supported algorithms for [Endmember
Extraction](https://pysptools.sourceforge.io/eea.html) are:

- *NFINDR*: N-FINDR endmembers induction algorithm after Winter
    (1999), that also makes use of an Automatic Target Generation
    Process (ATGP) (Plaza & Chang 2006). (*Default*)
- *FIPPI*: Fast Iterative Pixel Purity Index after Chang (2006)
- *PPI*: Pixel Purity Index

Supported algorithms for [Spectral
Unmixing](https://pysptools.sourceforge.io/abundance_maps.html) are:

- *FCLS*: Fully Constrained Least Squares (FCLS): Estimates endmember
    abundance per pixel with the constraint that values are non-negative
    and sum up to one per pixel (*Default*)
- *UCLS*: Unconstrained Least Squares (UCLS): Estimates endmember
    abundance per pixel in an unconstrained way
- *NNLS*: Non-negative Constrained Least Squares (NNLS): Estimates
    endmember abundance per pixel with the constraint that values are
    non-negative

## NOTES

Number of endmembers to extract (*endmember\_n*) is supposed to be lower
than the number of bands in the imagery group. Only the *PPI* method can
extract more endmembers than there are bands in the imagery group.

## EXAMPLE

Example for the North Carolina sample dataset:

```sh
# Create list of bands excluding thermal bands
bands=`g.list type=raster pattern="lsat7_2002*" exclude="lsat7_2002_6?" separator=','`
echo "$bands"

# Create imagery group
i.group group=lsat_2002 input="$bands"

# set computation region
g.region raster=lsat7_2002_10 -p

# Extract Endmembers and perform spectral unmixing using pysptools
# resulting in an endmember text file and raster maps (here: 5 endmember)
i.pysptools.unmix input=lsat_2002 endmembers=endmembers endmember_n=5 \
  output=spectrum.txt prefix=lsat_spectra --v

# Compare to result from i.spec.unmix addon
i.spec.unmix group=lsat7_2002 matrix=sample/spectrum.dat result=lsat7_2002_unmix \
  error=lsat7_2002_unmix_err iter=lsat7_2002_unmix_iterations
```

## REQUIREMENTS

- python-cvxopt (install through system software management)
- python-matplotlib (install through system software management)
- python-scikit-learn (install through system software management)
- python-scipy (install through system software management)
- [pysptools library](https://pypi.org/project/pysptools)
- [scikit-learn library](https://pypi.org/project/scikit-learn)

## REFERENCES

- Chang, C.-I. 2006: A fast iterative algorithm for implementation of
    pixel purity index. Geoscience and Remote Sensing Letters, IEEE,
    3(1): 63-67.
- Plaza, A. & Chang, C.-I. 2006: Impact of Initialization on Design of
    Endmember Extraction Algorithms. Geoscience and Remote Sensing, IEEE
    Transactions. 44(11): 3397-3407.
- Winter, M. E. 1999: N-FINDR: an algorithm for fast autonomous
    spectral end-member determination in hyperspectral data. Presented
    at the Imaging Spectrometry V, Denver, CO, USA, (3753): 266-275.

## SEE ALSO

*[i.spec.unmix](i.spec.unmix.md)*

## AUTHORS

Stefan Blumentrath, [Norwegian Institute for Nature Research (NINA),
Oslo, Norway](https://www.nina.no)  
Zofie Cimburova, [Norwegian Institute for Nature Research (NINA), Oslo,
Norway](https://www.nina.no)
