## DESCRIPTION

*r.flexure* computes how the rigid outer shell of a planet deforms
elastically in response to surface-normal loads by solving equations
for plate bending. This phenomenon is known as "flexural isostasy"
and is relevant to glacier/ice-cap/ice-sheet loading, sedimentary
basin filling, mountain belt growth, volcano emplacement, sea-level
change, and other geologic processes. *r.flexure* and
*[v.flexure](v.flexure.html)* are the GRASS GIS interfaces to the
model [**gFlex**](https://gflex.readthedocs.io/). As both *r.flexure*
and *[v.flexure](v.flexure.html)* are interfaces to gFlex, it must be
downloaded and installed. *r.flexure* requires **gFlex ≥ 2.0.0**:

    pip install "gflex>=2.0.0"

Full documentation and installation instructions are at
<https://gflex.readthedocs.io/>.

## NOTES

The parameter **method** selects the solution technique:

**FD** — Finite Difference\
Typically faster for large grids and supports spatially variable
elastic thickness via the van Wees and Cloetingh (1994) stencil.
Memory requirements scale with grid size; choose a grid spacing
appropriate for the flexural wavelength of the problem. Supports all
boundary conditions and in-plane stresses.

**FFT** — Fast Fourier Transform (spectral)\
Requires a scalar (uniform) elastic thickness. Supports in-plane
stresses. Fastest option for large uniform-T<sub>e</sub> grids. Each
opposite edge pair (west/east, north/south) is handled independently:
setting both sides of a pair to **periodic** makes that axis exactly
periodic; any other value (including the default **infinite**)
zero-pads that axis to approximate `no_outside_loads`. Mixed-axis
configurations are valid.

**SAS** — Superposition of Analytical Solutions\
Each grid cell is treated as a point load and its deflection computed
analytically. Best for smaller grids or when accuracy near individual
loads matters. Requires scalar elastic thickness. Boundary conditions
are not applicable; the solver inherently assumes an infinite plate
with no outside loads.

The flexural solution is generated for the current computational
region, so be sure to check
*[g.region](https://grass.osgeo.org/grass-stable/manuals/g.region.html)*
before running the module.

**input** is a 2-D raster of loads in units of stress \[Pa\], equal
to the load material density times gravitational acceleration times
column thickness. This is computed by the user prior to running the
module, and is not affected by the **g** parameter below (which
applies only to the restoring isostatic force).

**te**, written in standard notation as T<sub>e</sub>, is the
lithospheric elastic thickness. It may be either a scalar value or
(for FD only) a raster of spatially variable elastic thickness.

**Boundary conditions** apply to the FD and FFT solvers. SAS assumes
the plate extends to infinity with no outside loads and ignores
boundary condition settings.

The boundary conditions are:

**infinite** — gFlex canonical name: `no_outside_loads`\
The domain is automatically extended on that side by one flexural
wavelength with zero loads, the solve is performed on the enlarged
domain, and the deflection is trimmed back to the original region
before returning. For variable-T<sub>e</sub> FD runs, the elastic
thickness is also smoothly tapered across the padding ring to suppress
spurious deflections from abrupt rigidity gradients at the domain
edge (via the D-derivative terms in the van Wees & Cloetingh 1994
stencil). For FFT, the load array is zero-padded by `fft_pad_n_alpha`
× α per side (default 4α; α = (4D/Δρg)<sup>1/4</sup>) and trimmed
internally. This is the most physically realistic choice for isolated
loads far from any genuine plate edge, and is the default.

**clamped** — gFlex canonical name: `zero_displacement_zero_slope`\
Displacement *w* = 0 and slope *dw/dx* = 0 (or *dw/dy* = 0) at the
boundary. The plate is rigidly attached to a fixed wall: it can
neither deflect nor rotate at the edge. Use when the domain boundary
coincides with a stable craton or rigid block that prevents
deformation, or as a far-field approximation when the load is many
flexural wavelengths from the edge. Note: if any load is within one
flexural wavelength of a clamped boundary, the forebulge may be
artificially suppressed; gFlex will issue a warning in that case.

**pinned** — gFlex canonical name: `zero_displacement_zero_moment`\
Displacement *w* = 0 and bending moment *M* = *D d²w/dx²* = 0 at
the boundary. The plate cannot deflect at the edge but is free to
rotate; no bending moment is transmitted across the boundary.
Corresponds to a simply-supported (pinned) end in structural
mechanics. Use when the plate rests on a rigid foundation at its edge
without being clamped to it.

**free** — gFlex canonical name: `zero_moment_zero_shear`\
Bending moment *M* = 0 and shear force *V* = *D d³w/dx³* = 0 at the
boundary. The plate end is entirely free: no moment and no transverse
force are transmitted. Equivalent to the free end of a cantilever
(diving board). Use for rifted or passive continental margins where
the lithosphere has a broken, unsupported edge, for subduction
trenches with an applied edge load, and for broken-plate flexure
problems.

**mirror** — gFlex canonical name: `zero_slope_zero_shear`\
Slope *dw/dx* = 0 and shear force *V* = 0 at the boundary.
Mathematically equivalent to reflecting the load field (and, for
variable-T<sub>e</sub> runs, the elastic thickness field) across the
boundary, so the full domain is treated as the symmetric half of a
larger problem. Use when the loading geometry and lithospheric
structure are symmetric about the domain edge, for example along the
axis of a mid-ocean ridge or the crest of a symmetric mountain belt.

**periodic** (FD: matched pairs only; FFT: per opposite-edge pair)\
The opposite edges are treated as adjacent: the east edge connects to
the west edge and/or the north edge connects to the south edge. For
FD, periodic must be applied in matched pairs (both east–west or both
north–south); a one-sided periodic BC will produce a warning. For
FFT, each axis pair is handled independently: setting both sides of a
pair to **periodic** makes that axis exactly periodic, while leaving
the other pair at **infinite** (the default) zero-pads that axis.

Boundary conditions may be mixed freely across the four sides, except
that **periodic** must be applied in matched pairs. To minimize
boundary effects with explicit BCs, place domain edges at least one
flexural wavelength from the nearest load, or use **infinite** to let
gFlex extend the domain automatically.

**In-plane stresses** (**sigma_xx**, **sigma_yy**, **sigma_xy**) add
membrane (tectonic) stress terms to the governing equation, following
the full variable-D formulation. These are supported by the FD and
FFT solvers and default to 0 (no in-plane stress). Positive values
are tensional.

*r.flexure* may be run in latitude/longitude coordinates with the
**-l** flag. Because the module requires a single *dx* and *dy*, it
computes *dx* at the midpoint latitude of the domain. This
approximation degrades near the poles.

## EXAMPLES

### Asymmetric volcanic load on a laterally heterogeneous lithosphere

This example is based on the scenario in the
[gFlex documentation](https://gflex.readthedocs.io): a circular
volcanic edifice on a lithosphere whose elastic thickness rises from
15 km in the west to 35 km in the east across a sigmoid transition.
The thinner western lithosphere deflects more steeply and over a
shorter wavelength; the stiffer eastern side produces a broader
depression with a more prominent forebulge.

    # Domain: 750 × 750 km at 5 km resolution (projected CRS required)
    g.region n=750000 s=0 e=750000 w=0 res=5000

    # Sigmoid elastic thickness: 15 km (west) to 35 km (east)
    # tanh is unavailable in r.mapcalc; use the equivalent logistic form:
    #   0.5*(1 + tanh(u)) = 1/(1 + exp(-2u)), u = (x - cx)/(8*dx)
    r.mapcalc expression="te_sigmoid = 15000 + 20000 / (1 + exp(-(x()-375000) / 20000))"

    # Circular volcanic load (30 MPa) within 61.3 km of the domain centre
    # 30 MPa ≈ 1055 m of mantle-density rock; radius is 1.5 × the flexural parameter α
    r.mapcalc expression="load_volcano = if(sqrt((x()-375000)^2+(y()-375000)^2) <= 61300, 30000000.0, 0)"

    # FD flexural deflection; default infinite BCs approximate an unbounded plate
    r.flexure method=fd \
        input=load_volcano \
        te=te_sigmoid te_units=m \
        output=w_volcano

    d.rast w_volcano
    d.legend w_volcano

The result shows roughly 54 m of central subsidence and about 1 m of
forebulge uplift. The depression is deeper and narrower on the soft
(thin T<sub>e</sub>) western side and broader with a clearer forebulge
on the stiff eastern side.

For a broken-plate scenario (e.g. a passive margin or oceanic trench)
set the relevant edge to **free**:

    r.flexure method=fd \
        input=load_volcano \
        te=te_sigmoid te_units=m \
        output=w_volcano_free_south \
        southbc=free

## SEE ALSO

*[v.flexure](v.flexure.html)*

## REFERENCES

Wickert, A. D. (2016), Open-source modular solutions for flexural
isostasy: gFlex v1.0, *Geoscientific Model Development*, *9*(3),
997–1017,
doi:[10.5194/gmd-9-997-2016](https://doi.org/10.5194/gmd-9-997-2016).

van Wees, J. D., and S. Cloetingh (1994), A Finite-Difference
Technique to Incorporate Spatial Variations In Rigidity and Planar
Faults Into 3-D Models For Lithospheric Flexure, *Geophysical Journal
International*, *117*(1), 179–195,
doi:[10.1111/j.1365-246X.1994.tb03311.x](https://doi.org/10.1111/j.1365-246X.1994.tb03311.x).

## AUTHOR

Andrew D. Wickert
