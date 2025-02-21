## NAME

*r.fidimo* performs analysis of fish dispersal based on leptokurtic
dispersal kernels. It calculates fish dispersal along river corridors
based on a user's stream network input, fish source populations and
species-specific dispersal parameters.

## OPTIONS

### Stream parameters

- **river**  
    Name of input stream network map (thinned raster map) on which the
    calculations of dispersal is performed. In cases of very meandering
    rivers (with bends narrower than the spatial resolution of the
    analysis (cell size) it is recommended to run v.generalize and
    r.thin and/or to use *r.fidimo.river* in advance. The stream network
    should only consist of tree-like structures, as braiding rivers and
    networks with two-side connected side arms will not work. Check the
    raster beforehand carefully\!
- **outflow\_point**  
    Name of the outflow point txt-file (single point) for the
    calculation of the flow direction within the provided river network.
    The text-file must only contain a single |-separated coordinate pair
    (X|Y; same coordinate system as the **river** network raster). The
    file should not contain any headings, etc. e.g. the content of the
    file can look like:

```sh
545287.44|1942020.18
```

- **barriers**  
    Name of input barrier text-file indicating the geographical position
    and passability of barriers e.g. weirs. The file should contain the
    X and Y coordinate and a value for passability (0-1 where 0 is
    impassable and 1 is 100% passable). The values must be |-separated:

```sh
3543350.8001|6064831.9001|1
3535061.5179|6064457.5321|0.3
```

### Source populations

The source populations can be provided either as random points (flag
-r), or as fixed source population raster (flag -f).

- **n\_source**  
    For the random locations; number or percentage of cells containing
    source populations. The model selects randomly cell (number
    specified by the user) and assigns a starting density of 1 to each
    occupied cell.
- **source\_populations**  
    Input raster map indicating the starting density per cell. All cells
    with densities \> 0 will act as source populations for the model.
    The raster map must have the resolution as the river raster and all
    source population cells must also be part of the river raster.

### Dispersal parameters

- **species**  
    Selected species with predefined L and AR (see R-package
    'fishmove').
- **L**  
    Length of fish which should be modelled. Increasing L is positively
    correlated with larger dispersal distances. Setting L will overwrite
    any species-settings (see R-package 'fishmove').
- **AR**  
    Aspect ratio of the caudal fin of a fish which should be modelled.
    Increasing AR is positively correlated with larger dispersal
    distances. etting AR will overwrite any species-settings (see
    R-package 'fishmove').
- **T**  
    Time interval for one modelling step. The dispersal kernel is time
    dependent and increasing T is positively correlated with larger
    dispersal distances (see R-package 'fishmove').
- **p**  
    Share of the stationary component of the population. The value is
    set to 0.67 by default (my Paper).

### Output

- **output**  
    The base name of the output file(s). The output raster files will be
    %output%\_fit respectively %output%\_lwr and %output%\_upr if a
    statistical interval is set.
- **statistical\_interval**  
    Statistical interval (confidence or prediction) derived from the
    regression analysis (see R-package 'fishmove'). If a statistical
    interval is set, three output maps will be created (fit, lwr and
    upr).

### Dependencies

- RPy2
- NumPy
- SciPy
- Sqlite3
- r.stream.order

## SEE ALSO

*[r.stream.order](https://grass.osgeo.org/grass-stable/manuals/r.stream.order.html),
[r.watershed](https://grass.osgeo.org/grass-stable/manuals/r.watershed.html)*

## REFERENCES

Radinger, J., Kail, J., & Wolter, C. (2014). FIDIMO — A free and open source GIS-based dispersal model for riverine fish. *Ecological Informatics, 24*, 238–247. [https://doi.org/10.1016/j.ecoinf.2013.06.002](https://doi.org/10.1016/j.ecoinf.2013.06.002).

## AUTHOR

Johannes Radinger, Leibniz-Institute of Freshwater Ecology and Inland
Fisheries, Berlin (Germany)
