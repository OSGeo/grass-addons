## DESCRIPTION

*v.flexure* computes how the rigid outer shell of a planet deforms elastically in response to surface-normal point loads by solving equations for plate bending. This phenomenon is known as "flexural isostasy" and is relevant to glacier/ice-cap/ice-sheet loading, sedimentary basin filling, mountain belt growth, volcano emplacement, sea-level change, and other geologic processes. *v.flexure* and *[r.flexure](r.flexure.html)* are the GRASS GIS interfaces to the model [**gFlex**](https://gflex.readthedocs.io/). *v.flexure* requires **gFlex ≥ 2.0.0**:

<div class="code">

    pip install "gflex>=2.0.0"

</div>

Full documentation and installation instructions are at <https://gflex.readthedocs.io/>.

## NOTES

*v.flexure* uses the Superposition of Analytical Solutions for Non-Gridded points (SAS_NG) method in gFlex. Each input point load is treated as a concentrated force, and the far-field deflection is computed analytically as the superposition of Kelvin–Bessel (kei) functions. **input** is a vector points map. Each point represents a load in units of force \[N\]. For a distributed load field discretized as points, the user should incorporate the tributary area and load stress into the values stored in the attribute column specified by **column**.

**te**, written in standard notation as T<sub>e</sub>, is the lithospheric elastic thickness (scalar only for *v.flexure*; use *[r.flexure](r.flexure.html)* for spatially variable T<sub>e</sub>).

**output** is a raster map of deflections at the spacing and extent of the current GRASS computational region. Be sure to use *[g.region](https://grass.osgeo.org/grass-stable/manuals/g.region.html)* to set the region before running the module.

**w_points** is an optional existing vector points map at which deflection will also be evaluated. This allows deflection to be computed at arbitrary locations such as GPS stations, boreholes, or tide gauges that do not align with the raster grid. The deflection value at each point is written into the column specified by **w_column** (default: `w`), which is added to the map's attribute table if it does not already exist. The raster grid and the w_points locations are evaluated in a single gFlex solve, so there is no additional computational cost.

In latitude/longitude coordinates, *v.flexure* automatically computes great-circle distances between load and output points.

## EXAMPLES

### Three seamounts along a volcanic chain

Three point loads represent seamounts spaced 500 km apart. Each force (~5 × 10<sup>16</sup> N) corresponds roughly to a seamount with a 25 km base radius, 3 km height, and basalt density. Because the flexural parameter α ≈ 41 km for T<sub>e</sub> = 25 km is much smaller than the 500 km spacing, the three depressions are essentially independent; their deflections add linearly everywhere.

<div class="code">

    # Domain: 2000 × 1000 km at 20 km resolution (projected CRS required)
    g.region n=1000000 s=0 e=2000000 w=0 res=20000

    # Three seamounts along the chain (x y, one per line)
    echo "500000 500000
    1000000 500000
    1500000 500000" | v.in.ascii format=point input=- output=seamount_chain

    # Add load column and set the same force [N] for all three points
    v.db.addtable map=seamount_chain
    v.db.addcolumn map=seamount_chain columns="force double precision"
    v.db.update map=seamount_chain column=force value=5e16

    # SAS_NG deflection; raster output required
    v.flexure input=seamount_chain column=force \
        te=25 te_units=km \
        output=w_chain_rast

    # Optionally also evaluate at a set of tide-gauge or GPS stations
    v.flexure input=seamount_chain column=force \
        te=25 te_units=km \
        output=w_chain_rast \
        w_points=tide_gauges w_column=w_flexure

    d.rast w_chain_rast
    d.legend w_chain_rast

</div>

## SEE ALSO

*[r.flexure](r.flexure.html), [v.surf.bspline](https://grass.osgeo.org/grass-stable/manuals/v.surf.bspline.html)*

## REFERENCES

Wickert, A. D. (2016), Open-source modular solutions for flexural isostasy: gFlex v1.0, *Geoscientific Model Development*, *9*(3), 997–1017, doi:[10.5194/gmd-9-997-2016](https://doi.org/10.5194/gmd-9-997-2016).

## AUTHOR

Andrew D. Wickert
