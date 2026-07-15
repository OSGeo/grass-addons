## DESCRIPTION

*i.superpixels.slic* performs superpixel segmentation using a k means
method, based on the work of Achanta et al. 2010. (SLIC = Simple Linear
Iterative Clustering). The number of superpixels is determined either
with the **num\_pixels** option (number of superpixels) or with the
**step** option (distance between initial super pixel centers).

The **compactness** option controls the compactness of the resulting
superpixels. A larger **compactness** value will cause spatially more
compact, but spectrally more heterogeneous superpixels. This is the most
important parameter of the module. A reasonable value should be
determined for small test regions before applying the module to a large
region.

The resultant number of superpixels will most often be larger than the
initial number of superpixels because the initial number of superpixels
is used to create seeds and SLIC assigns pixels to seeds. Pixels
assigned to the same seed are usually not connected. The final number of
superpixels is the number of clumps, also known as connected components,
objects, regions, or blobs. The final number of superpixels can be
reduced with the **minsize** option.

## NOTES

### Input bands

Contrary to the original Achanta et al. SLIC algorithm which allows only
RGB input images (which are internally transformed into LAB color space,
*i.superpixels.slic* allows the use of any number of input bands. These
bands can be either spectral bands of imagery, or any other pseudo-bands
relevant to the analysis at hand (NDVI, texture, precipitation, etc).
All band values are normalized to a common 0-1 scale to ensure
comparability in the spectral distance calculations. Therefore results
will not be identical with the original implementation.

### Iterations

In each iteration, the assignment of pixels to superpixels and the
superpixels themselves (spatial and spectral means) are updated until
either the maximum number of iterations is reached or until the
superpixels no longer change. More iterations will provide better
results but will increase processing time. The module will stop earlier
if convergence is reached, but it can take 1000 or more iterations until
convergence is reached.

### Step

Step size has to be larger than 1 to be meaningful, as otherwise each
individual pixel would be considered as a superpixel. If no step size or
a step size of less than 2 given, the module estimates a step size
internally on the basis of the number of superpixels (**num\_pixels** -
200 by default).

### Minimum segment size

If a minimum segment size of 2 or larger is given with the **minsize**
parameter, segments with a smaller pixel count will be merged with their
most similar neighbor.

In the original implementation of Achanta et al., a minimum segment size
is internally determined, and segments smaller than this minimum segment
size are merged with an arbitrarily chosen neigbour. Therefore results
will not be identical with the original implementation, even if a
minimum segment size identical to the minimum segment size internally
determined in the original implementation of Achanta et al. is used.

### Creating seeds for *i.segment*

If the purpose is to create seeds for *i.segment*, a small number of
iterations (at least 10) should be sufficient. Further on, a large
number of superpixels or a small step should be used, and small clumps
should not be merged.

### Image segmentation

If the purpose is to perform image segmentation with
*i.superpixels.slic*, a larger number of iterations (e.g. 100) should be
used in order to obtain more stable superpixels. In this case, larger
superpixels can be used and small clumps can be removed with the
**minsize** option.

### Normalization of spectral distances (SLIC0)

If the **-n** flag is used, the spectral distance of a pixel to a given
superpixel is divided by the maximum previously observed spectral
distance to that superpixel. This is an adaptation of the so-called
*SLIC0* (SLIC zero) method.

After each iteration, the largest spectral distance to a superpixel is
determined from all pixels assigned to that superpixel. In the next
iteration, pixel assignment to superpixels is updated and spectral
distances of pixels to superpixels are divided by the largest spectral
distance of the current superpixel when evaluating a potential
assignment of a pixel to a superpixel.

Contrary to the Achanta et al. version of SLIC0, *i.superpixels.slic*
takes into account the *compactness* value chosen by the user even when
the **-n** flag is used.

SLIC0 implies that more heterogeneous superpixels have a larger maximum
spectral distance. For a given pixel, the normalized spectral distance
will be smaller for a more heterogeneous superpixel than for a more
homogeneous superpixel. This favours more heterogeneous superpixels
which can steal pixels from more homogeneous superpixels even if the not
normalized spectral distance of a pixel to a homogeneous superpixel is
smaller than to a heterogeneous pixel. As a consequence, heterogeneous
superpixels can become larger and and even more heterogeneous. This
effect becomes stronger with larger differences in the spectral
homogeneity of neighboring superpixels, and with a lower *compactness*
value, as spectral difference then gets a bigger weight.

### Perturbing initial superpixel centers

Initial superpixel centers can be optimized with the **perturb** option.
The objective of this optimization of initial superpixel centers is to
create more distinct and more homogeneous superpixels. Superpixel
centers are shifted to more uniform areas, the pixel with the smallest
gradient. The module guarantees that no two superpixel centers are
shifted to the same position. The **perturb** option is interpreted as
percent of the maximum allowable shift distance such that no two
superpixel centers can obtain the same position.

### Memory vs disk cache

*i.superpixels.slic* can handle very large amounts of data. Depending on
the amount of data and the available RAM memory, as defined by the
*memory* parameter, the module will either work with memory cache,
storing everything in memory, or with a disk cache, storing elements on
disk and only retrieving the data when necessary. Disk cache is slower,
but the data can be much larger than the RAM memory can hold. By
default, the *memory* parameter is set fairly low for modern computer
systems (500MB). Users should thus make sure to adjust the value to
their system.

## EXAMPLES

### Segmentation of Landsat images and NDVI

List Landsat imagery in the full NC sample dataset:

```sh
g.list type=raster pattern='lsat*' sep=comma mapset=PERMANENT
```

Set the computation region to one of the rasters (all have the same
extent and resolution):

```sh
g.region raster=lsat7_2002_10 -p
```

Use the list to create an imagery group:

```sh
i.group group=lsat subgroup=lsat input=`g.list type=raster pattern='lsat*' sep=comma mapset=PERMANENT`
```

Perform the segmentation:

```sh
i.superpixels.slic input=lsat output=segments num_pixels=2000
```

Convert the segments to vectors for further analysis and visualization:

```sh
r.to.vect input=segments output=segments type=area
```

Show the boundaries between the segments with false color image in the
background:

```sh
d.rgb red=lsat7_2002_70 green=lsat7_2002_50 blue=lsat7_2002_30
d.vect map=segments fill_color=none
```

Let's compute the NDVI using
*[r.mapcalc](https://grass.osgeo.org/grass-stable/manuals/r.mapcalc.html)*
and assign average NDVI to each of the vector areas:

```sh
i.vi red=lsat7_2002_30 nir=lsat7_2002_40 viname=ndvi output=ndvi
v.rast.stats map=segments raster=ndvi column_prefix=ndvi method=average
```

And now visualize the segments using the NDVI value for coloring the
areas with the `ndvi` color table but keeping the area boundaries black:

```sh
g.copy vector=segments,segments_color
v.colors map=segments_color use=attr column=ndvi_average color=ndvi
d.vect map=segments_color width=2 icon=basic/point
d.vect map=segments fill_color=none
```

![Average NDVI in each superpixel area (segment)](i_superpixels_slic.png)  
*Average NDVI in each superpixel area (segment)*

## REFERENCES

SLIC Superpixels. 2010. Radhakrishna Achanta, Appu Shaji, Kevin Smith,
Aurelien Lucchi, Pascal Fua, and Sabine Susstrunk. EPFL Technical Report
no. 149300.  
SLIC Superpixels Compared to State-of-the-art Superpixel Methods. 2012.
Radhakrishna Achanta, Appu Shaji, Kevin Smith, Aurelien Lucchi, Pascal
Fua, and Sabine Süsstrunk. IEEE Transactions on Pattern Analysis and
Machine Intelligence, 34(11), 2274 - 2282.  
[SLIC(0)
website](https://www.epfl.ch/labs/ivrl/research/slic-superpixels)

## SEE ALSO

*[g.gui.iclass](https://grass.osgeo.org/grass-stable/manuals/g.gui.iclass.html),
[i.group](https://grass.osgeo.org/grass-stable/manuals/i.group.html),
[i.segment](https://grass.osgeo.org/grass-stable/manuals/i.segment.html),
[i.clump](https://grass.osgeo.org/grass-stable/manuals/i.clump.html),
[i.maxlik](https://grass.osgeo.org/grass-stable/manuals/i.maxlik.html),
[i.smap](https://grass.osgeo.org/grass-stable/manuals/i.smap.html),
[r.kappa](https://grass.osgeo.org/grass-stable/manuals/r.kappa.html)*

## AUTHORS

Rashad Kanavath, India  
Markus Metz
