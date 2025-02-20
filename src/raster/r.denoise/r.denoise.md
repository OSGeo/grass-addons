## DESCRIPTION

Sun et al.'s (2007) [denoising
algorithm](https://www.cs.cf.ac.uk/meshfiltering/index_files/Page342.htm)
is a feature-preserving mesh denoising algorithm that smooths the
surfaces of computer models of three dimensional objects such as those
used in computer-aided design and graphics. It removes random noise
while preserving sharp features and smoothing with minimal changes to
the original data. *r.denoise* is a Python script that allows the
algorithm to be run on DEMs from within *GRASS*. Denoising DEMs can
improve clarity and quality of derived products such as slope and
hydraulic maps.

The amount of smoothing is controlled by the **threshold** and
**iterations** parameters. Increasing the **threshold** decreases how
sharp a feature needs to be in order to be preserved e.g. decreases the
smoothing. To preserve ridge crests in mountain areas, T \> 0.9 is
recommended. Setting T too high results in the preservation of noise.
For SRTM data, which is already partly smoothed by NASA, T = 0.99 can be
used. Increasing the number of *iterations* increases the smoothing and
the range of spatial correlation of the output dataset. A small number,
e.g. 5 or fewer, typically gives the best results. See the REFERENCES
for more detailed information.

## NOTES

*r.denoise* works with a Cartesian coordinate system. Thus data in
geographic (lat-long) coordinates require projection during processing.
The script is able to do this if the [EPSG
code](http://www.epsg-registry.org/) of a suitable coordinate system is
provided.

## REQUIREMENTS

*r.denoise* requires that *mdenoise*, the executable version of Sun et
al.'s (2007) denoising algorithm, is available on the $PATH. *mdenoise*
can be compiled and installed as follows:

```sh
wget http://www.cs.cf.ac.uk/meshfiltering/index_files/Doc/mdsource.zip
unzip mdsource.zip
cd mdenoise
g++ -o mdenoise mdenoise.cpp triangle.c
ln -s `pwd`/mdenoise /some/directory/on/the/$PATH
```

The python version of *r.denoise* uses
[pyproj](https://github.com/jswhit/pyproj):

```sh
pip install pyproj
```

## REFERENCES

  - For further information on denoising DEMs, see: [Using Sun's
    denoising algorithm on topographic
    data](https://personalpages.manchester.ac.uk/staff/neil.mitchell/mdenoise/).
  - Sun X, Rosin PL, Martin RR, Langbein FC (2007) Fast and Effective
    Feature-Preserving Mesh Denoising. IEEE Transactions on
    Visualisation and Computer Graphics, 13(5):925-938
    [doi:10.1109/TVCG.2007.1065](https://doi.org/10.1109/TVCG.2007.1065)
  - Stevenson JA, Sun X, Mitchell NC. (2009) Despeckling SRTM and other
    topographic data with a denoising algorithm. Geomorphology,
    144:238-252.
    [doi:10.1016/j.geomorph.2009.07.006](https://doi.org/10.1016/j.geomorph.2009.07.006)

## SEE ALSO

*[r.stats](https://grass.osgeo.org/grass-stable/manuals/r.stats.html),
[r.in.xyz](https://grass.osgeo.org/grass-stable/manuals/r.in.xyz.html),
[r.neighbors](https://grass.osgeo.org/grass-stable/manuals/r.neighbors.html),
[r.topidx](https://grass.osgeo.org/grass-stable/manuals/r.topidx.html)*

## AUTHORS

John A Stevenson  
johnalexanderstevenson *at* yahoo *dot* co *dot* uk  
  
The module was written as part of a project funded by
[EPSRC](https://www.ukri.org/councils/epsrc) Grant no. EP/C007972/1
(P.I. Paul Rosin, Cardiff University).  
  
Module ported to Python by [Carlos H.
Grohmann](http://carlosgrohmann.com/)  
Institute of Energy and Environment, University of Sao Paulo, Brazil
