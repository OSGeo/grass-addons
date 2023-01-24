# r.landscape.evol

## DESCRIPTION

_r.landscape.evol_ takes as input a raster digital elevation model (DEM) of
surface topography and an input raster DEM of bedrock elevations, as well
as several environmental variables, and computes the net change in elevation
due to erosion and deposition Stream Power equation, the Shear Stress
equation, or the USPED equation.

## NOTES

### Transport capacity equations

Users may select to use the Stream Power equation, the Shear Stress equation,
or the USPED equations with variable **transp_eq**. All three equations
estimate transport capacity as `[kg/m.s]`, and thus eventually
erosion/deposition rate as `[kg/m2.s]`, which is transformed to `[vertical
meters/cell]` using the variable **sdensity** (see below for details of these
conversions).

It is important to note that in this new version of _r.landscape.evol_, only
_one_ transport equation will be used to model sediment flux across the entire
landscape. Chane in process will be simulated through scalar `m` and `n`
exponents (see below for details).

#### 1) Stream power equation

    Tc=Kt*gw*1/N*h^m*B^n

      where: h = depth of flow = (i*A)/(0.595*t)
      and: B = slope (rise over run)

a) GIS Implementation:

    Tc=K*C*P*gw*(1/N)*((i*A)/(0.595*t))^m*(tan(S)^n)

b) Variables:

* Tc = Transport Capacity [kg/meters.second]
* K\*C\*P ~ Kt = mitigating effects of soil type, vegetation cover, and
  land-use practices. [unitless]
* gw = Hydrostatic pressure of water 9810 [kg/m2.second]
* N = Manning's coefficient (0.3-0.6 for different types of stream channels) [unitless]
* i = rainfall intensity [m/rainfall event]
* A = upslope accumulated area per contour (cell) width [m2/m] = [m]
* 0.595 = constant for time-lagged peak flow (assumes symmetrical unit-hydrograph)
* t = length of rainfall event [seconds]
* S = topographic slope [degrees]
* m = transport coefficient for upslope area [unitless]
* n = transport coefficient for slope [unitless]

c) Converted to Map Algebra:

        ${K}*${C}*${P} * exp(${manningn}, -1) * 9810. * exp((((${rain}/1000.)*\
        ${flowacc})/(0.595*${stormtimet})), graph(${flowacc}, ${exp_m1a},\
        ${exp_m1b}, ${exp_m2a},${exp_m2b}) ) * exp(tan(${slope}), graph(${slope},\
        ${exp_n1a},${exp_n1b}, ${exp_n2a},${exp_n2b}))

d) NOTES:

* This is likely the best of the three equations for simulating erosion at the
  scale of small watersheds, including overland flow on hillslopes and
  channelized flow in gullies and streams.
* It is likely not appropriate for simulating erosion and deposition processes
  in larger rivers, especially meandering  flood plains.
* `K*C*P` should equal an appropriate value of `Kt`: 0.001 for a soft
  substrate, 0.0001 for a normal substrate, 0.00001 for a hard substrate,
  0.000001 for a very hard substrate. See note below about methods for scaling
  these values.
* `N` should likely scale with channel vegetation so that 0.03 = clean/straight
  stream channel, 0.035 = major free-flowing river, 0.04 = sluggish stream with
  pools, 0.06 = very clogged streams. See below for methods to scale these
  values.

#### 2) Shear stress equation

    Tc=Kt*tau^m

      where: tau = shear stress = gw*h*B
      and: B = slope (rise over run)
      and: h = depth of flow = (i*A)/(0.595*t)

a) GIS Implmentation:

    Tc=K*C*P*(gw*((i*A)/(0.595*t)*(tan(S))))^n

b) Variables:

* Tc = Transport Capacity [kg/meters.second]
* K\*C\*P ~ Kt = mitigating effects of soil type, vegetation cover, and land-use
  practices. [unitless]
* gw = Hydrostatic pressure of water 9810 [kg/m2.second]
* N = Manning's coefficient ~0.3-0.6 for different types of stream channels [unitless]
* i = rainfall intensity [m/rainfall event]
* A = upslope accumulated area per contour (cell) width [m2/m] = [m]
* 0.595 = constant for time-lagged peak flow (assumes symmetrical unit-hydrograph)
* t = length of rainfall event [seconds]
* B = topographic slope [degrees]
* n = transport coefficient (here assumed to be scaled to slope) [unitless]

c) Converted to Map Algebra:

    ${K}*${C}*${P} * exp(9810.*(((${rain}/1000)*${flowacc})/(0.595*\
    ${stormtimet}))*tan(${slope}), graph(${flowacc}, ${exp_n1a},${exp_n1b},\
     ${exp_n2a},${exp_n2b}))

d) NOTES:

* This implementation of the Shear Stress equation assumes the critical shear
  stress is 0.
* This means the equation is likely to over predict erosion in situations where
  shear stress is less than the actual critical shear stress, such as on
  vegetated hillslopes.
* `K*C*P` should equal an appropriate value of `Kt`: 0.001 for a soft
  substrate, 0.0001 for a normal substrate, 0.00001 for a hard substrate,
  0.000001 for a very hard substrate. See note below about methods for scaling
  these values.
* `N` should likely scale with channel vegetation so that 0.03 = clean/straight
  stream channel, 0.035 = major free-flowing river, 0.04 = sluggish stream with
  pools, 0.06 = very clogged streams. See below for methods to scale these
  values.

#### 3) USPED equation

    Tc=R*K*C*P*A^m*B^n`

      where: B = slope (rise over run)

a) GIS Implementation:

    Tc=R*K*C*P*A^m*tan(S)^n

b) Variables:

* Tc = Transport Capacity [kg/meters.second]
* R = Rainfall intensity factor [MJ.mm/ha.h.yr]
* K\*C\*P ~ Kt = mitigating effects of soil type, vegetation cover, and
  land-use practices. [unitless]
* A = upslope accumulated area per contour (cell) width [m2/m] = [m]
* S = topographic slope [degrees]
* m = transport coefficient for upslope area [unitless]
* n = transport coefficient for slope [unitless]

c) Converted to Map Algebra:

    (${R}*${K}*${C}*${P}*exp((${flowacc}*${res}),graph(${flowacc}, ${exp_m1a},\
    ${exp_m1b}, ${exp_m2a},${exp_m2b}))*exp(sin(${slope}), graph(${slope}, \
    ${exp_n1a},${exp_n1b}, ${exp_n2a},${exp_n2b})))

d) NOTES:

* The USPED equation is best suited for modeling erosion and deposition on
  hillslopes and small gullies.
* It will vastly over predict erosion/deposition in channels and streams.

### Scalar m and n exponents to simulate changing process across landscapes

Exponents `m` and `n` are used to influence the behavior of the transport
equations by differentially weighting the influence of upslope accumulated area
(and thus depth of flow) (`m`) or the influence of local slope (`n`). Depending
on how these are each weighted, transport estimates can be made for overland
flow processes, rilling and gullying, or channelized flow (see references below,
but in particular Peckham 2003, Mathier et al 1989, and Kwang and Parker 2017).
Following a suggestion in Peckham 2003, this new version of _r.landscape.evol_
simulates change in process across the landscape by scaling `m` and `n` to
changes in topography and flow accumulation. As this is largely an experimental
process, the specifics of this scaling are exposed to the user via the **m** and
**n** variables. The user can define the scalar relationship of `m` to surface
flow accumulation, and `n` to local slope. Sensible default values are included
to help the user know where to start.

Exponent `m` relates to the influence of upslope area (and thus flow depth,
discharge) on transport capacity in the Stream Power and USPED, but is not used
in the Shear Stress equation. Values of `m` are generally thought to be between
2 and 1, and experimentation suggests that they should scale _inversely_ with
increasing depth of flow. Exponent `m` will scale linearly with the value of
flow accumulation between the two cutoff thresholds specified:
`"thresh1,m1,thresh2,m2"`. So, for example, if you would like the value of
exponent `m` to scale from 1.2 to 1 between a flow accumulation value of 5 and
50, enter the following into the variable **m**: `"5,1.2,50,1"`. The exponent
`m` will remain 1.2 for all cells where flow accumulation is below 5, and will
remain 1 for all cells with flow accumulation above 50. It will scale linearly
between 1.2 and 1 for all cells with values of flow accumulation between 5 and
50.

A literature search indicates that maximum values of `m` should be less than or
equal to 2, and that scaling between 1.2 and 1 is probably a good range to
start with.

Exponent `n` relates to the influence of local topographic slope on transport
capacity, and is used in the Stream Power, Shear Stress, and USPED equations.
Values of `n` are  generally thought to be between 2 and 1, and experimentation
suggests that they should scale _inversely_ with increasing local slope.
Exponent `n` will scale linearly with slope between the two slope cutoff
thresholds specified: `"thresh1,n1,thresh2,n2"`. So, for example, if you would
like the value of exponent `n` to scale from 1.3 to 1 between a slope value of
10 and 30, enter the following into the variable **n**: `"10,1.3,30,1"`.
The exponent `n` will remain 1.3 for all cells where slope is below 5, and will
remain 1 for all cells with slope above 30. It will scale linearly between 1.3
and 1 for all cells with values of slope between 5 and 30.

A literature search indicates that maximum values values of `n` should be less
than or equal to 2, and that scaling between 1.3 and 1 is probably a good range
to start with.

### Scaling other input values

To ensure proper behavior for landscape evolution simulation over long periods,
it is important that most of the important variables be allowed to vary
spatially as they would on a real landscape. The three most important sets of
variables are a) Soil, vegetation cover, and land use factors **k**, **c**,
**p**, which together approximate erodibility factor `Kt`, b) Manning's N
**manningn** which is used to estimate stream power/shear stress of flowing
water in different types of channels and surface conditions, and c)
**flowcontrib**, the rainfall excess rate (percentage of direct precipitation
that will flow off of a cell), which is used to estimate the flow depth (see
below).

Because upslope accumulated area `A` is a major influencing factor in each of
the three equations, transport capacity (and thus erosion/deposition rate) will
be inordinately governed by `A` as values of flow accumulation approach very
large numbers (e.g., >> 10,000). This will be partially mitigated with scalar
`m` and `n` (see above), but will need additional dampening by scaling `Kt`,
`N`, and rainfall excess.

`Kt` is composed of the `K`, `C`, and `P` factors. If empirical patterns of
`K`, `C`, and `P` are known (e.g., digitized or classified from remotely senses
data products), these should be entered as maps in input variables **k**,
**c**, and **p**.

If empirically determined maps of these variables are not available, it is
possible to use constants in their place, but it will be much better to create
maps using some theoretical concepts. The simplest way is to scale `C` to a
wetness index using the principle that the more water accumulation, the denser
the vegetation. From a DEM, it is possible to calculate the TCI topographic
wetness index using _r.watershed_ with output parameter **tci**. Here is an
example set of _r.recode_ rules to create a `C` map from TCI to enter in input
variable **c**:

    0:3:0.1:0.01
    3:7:0.01:0.005
    7:10:0.005:0.004
    10:*:0.004

Here, low values of TCI will be coded as shrubs or open woodlands. Moderate
values of TCI will become wooded, and high values of TCI will coded as dense
riparian vegetation. It's important to note that this should be done with a TCI
map created with _r.watershed_ on the same DEM that will be used as the initial
DEM for the simulation.

From here, it is possible to map rainfall excess to values of `C`. The
following recode rules will achieve a reasonable mapping:

    0.1:0.05:85:80
    0.05:0.01:80:60
    0.01:0.005:60:45
    0.005:0.001:45:35

Here, as vegetation becomes more protective of detachment, it is also scaled to
become more conducive to water infiltration, and thus more prohibitive to
excess water escaping from the cell. The resulting map should be entered into
input variable **flowcontrib**.

Finally, Manning's `N` can be scaled to flow accumulation (i.e., computed with
_r.watershed_) using the following recode rules to create an input map for
variable **manningn**:

    0:10:0.03:0.04
    10:100:0.04:0.05
    100:10000:0.05:0.06
    10000:*:0.06

Here, the assumption is that as flow accumulation increases, the channel will
become more complex. These particular rules assume that the scale of analysis
is at the level of small watershed feeding into a small trunk stream, not a
large free-flowing river. If some empirical data about channel conditions are
known, then the values used in the recode statement should be adjusted to
reflect this. Again, it's important to note that this should be done with a
flow accumulation map created with _r.watershed_ on the same DEM that will be
used as the initial DEM for the simulation. Further, the -a flag in
_r.watershed_ should be checked so that the output flow accumulation will
contain only positive numbers.

### Creating a hydrologically-appropriate base DEM

It is vitally important the the input starting DEM be hydrologically valid and
at an appropriate raster resolution. Resolution should be scaled to the size of
the region being modeled, with the caveat that the assumptions of the way the
transport equations are implemented will start to break down at larger cell
resolutions. As a general rule of thumb, cell resolution should be <= 10m. This
can be achieved through resampling/interpolation from coarser data sets (e.g.,
a 30m SRTM DEM). If interpolation is used, it is best to use an interpolation
procedure that will result in relatively smooth interpolated DEM with minimal
depressions. Generally, _v.surf.bspline_ achieves good results when the spline
step is double to triple the cell resolution of the coarser input map, and the
smoothing parameter is set to provide some additional smoothing (e.g., ~0.1).
This results in an interpolated DEM with a smooth surface and minimal localized
depressions caused by over-fitting to localized surface trends. Although
_v.surf.rst_ can also be used, it often produces rectilinear artifacts from
it's segmentation procedure that can adversely affect simulation of water flow
on the interpolated DEM.

The DEM should be clipped to a contiguous watershed boundary (e.g., extracted
with _r.watershed_ or _r.water.outlet_). Rectilinear input maps will produce
erroneous results outside of internally contiguous watersheds leading to faulty
statistics, so it is more useful to clip to the watershed of interest (e.g.,
using _r.mapcalc_).

Finally, in order to assure that water will flow naturally across the DEM, it
is important to ensure that the DEM is depressionless. This _could_ be achieved
with _r.fill.dir_ to fill any interior basins to an elevation level with their
spill point, but doing so creates many flat areas where otherwise channelized
flow will diverge (and thus deposit). This can be partially addressed by
adjusting **convergence** to a low value, which forces the flow accumulation
routine in _r.watershed_ to send a higher proportion of the flow to the most
downstream cell.

However, a much better, if more complicated approach is to create a
depressionless DEM by _carving_ the main streams through any blockages. The
module _r.carve_ can do this relatively simply, but you are only able to use a
uniform stream width and depth. Ideally, the width and depth of the carved
channels should decrease in width and depth from the basin outlet to the stream
sources. To do this requires several steps. First extract an
appropriately-scaled stream network using _r.watershed_ and/or
_r.stream.extract__ and an appropriate interior basin threshold parameter to
isolate main trunk streams with some smaller tributary branches. Use this
output raster streams map as the input to the addon module _r.stream.order_
with the output option for the Shreve stream order. This will create a raster
streams map where trunk streams are coded with a large number, and tributaries
with smaller numbers. Use _r.univar_ to determine the maximum Shreve value, and
then use _r.mapcalc__ to standardize the values between 0 and 1 by dividing the
Shreve-scaled streams map by the maximum Shreve order value (ensure that you
use a decimal point behind the maximum value number so that a floating point
map will be made). The standardized Shreve order streams raster map is then
converted to a line vector map with _r.to.vect_ with option **column** set in
order to write the scaled Shreve order into the table. This vector map is then
input into _v.buffer_ with option **column** set to the column where the scaled
Shreve order values were saved and flag **t** is selected so that the attribute
table will transfer to the new file. Also set option **scale** to the maximum
channel width (in meters) of the largest trunk stream in the streams map, which
will create a vector areas map with streams scaled to the appropriate widths.
This vector areas map should then be converted back to a raster map with
_v.to.rast_, making sure that the option **use** is set to "attr" and the
option **attribute_column** is set so that the scaled Shreve order values will
be saved as the raster values. Finally, use _r.mapcalc_ to scale the Sherve
order values into the depth of the carved streams by multiplying the converted
buffer raster map by the maximum desired depth of the largest trunk stream.
This final output raster map will now be scaled to both width and depth
throughout the stream network. Use _r.mapcalc_ to "carve" into the DEM by
subtracting this scaled width/depth map from the DEM. As a final measure to
ensure that there is no stream blockage, you can use the module _r.carve_ with
the streams vector map and the "precarved" DEM, which will ensure that no high
areas exist in the channel bottoms. Finally, you may wish to re-interpolate the
carved DEM so that harsh angles on the edges of the carved banks are removed.
Using a bicubic interpolation in _v.surf.bspline_ with relatively long spline
step and high smoothing should accomplish this.

### Estimating soil depth

Soil depth is important in the routine, as it provides a depth-based limitation
on the amount of erosion that can occur at any particular cell (see below). The
depth of soil available to erode is the difference between the current surface
elevations (DEM) and the bedrock elevation map **initbdrk**. The simplest way
to estimate the bedrock elevation map is to subtract a constant from the
starting DEM map used for **elev** using _r.mapcalc_. A more complex bedrock
topography can be estimated using the addon module _r.soildepth_. In either
case, it is important to use the same DEM to derive the bedrock elevations as
you will use for the initial starting topography in the simulation.

### Climate data file

Users can use constants for climate data, or can use an input climate file with
columns of comma separated values arranged in order of:
`"R,rain,storms,stormlength,stormsi"` A new line should be used for each year
of the simulation. The file can have a one-line header or no header. Do not
included a column containing dates, but ensure that the number of rows matches
the value you input for **number**.

Note that only the USPED equation needs a value for R factor, and USPED does
not need the remaining climate variables. In the case of using USPED, only the
first column  needs to contain data (for R factor), but you still need to
include all columns (the remaining columns can be with zeros or NaN's).

In the case of using the Stream Power or Shear Stress equations, you still must
create a CSV file with 5 columns, but the first column (for R Factor) can be
filled with zeros or NaN's.

When using a climate file, you enter the path to the text file as variable
**climfile**. This will override values or maps entered into variables **r**,
**rain**, **storms**, **stormlength**, or **stormsi**. A fatal error message
will be raised if the number of rows in the input climate file does not match
the value entered for the variable **number**.

### Rainfall excess and flow accumulation

This module will take rainfall totals into account when calculating the value
of flow accumulation. It does so using _r.watershed_ and the value of
**flowcontrib** to calculate flow accumulation scaled by the percentage of rain
that will flow off the cell (i.e., rainfall - infiltration). See above for a
method to scale **flowcontrib** to C factor.

### Temporal Interval

The USPED equation relies on the value of R from the RUSLE equation to define
the temporal interval for landscape evolution. Typically, R is estimated at a
yearly temporal interval, so it is important to understand the time step of
your R input data before simulation with the USPED equation.

The Stream Power and Shear Stress equations, on the other hand, accept
storm-level data. This can be aggregated at any time step (per-storm, daily,
weekly, monthly, yearly, decadal, etc.). The time step does not need to be an
even interval; this means you can model on a per-storm basis where the interval
between storms is not the same. To do so, you would use the option to enter a
climate file where each line would detail the timing and intensity of each
storm. You would then run the simulation with variable **number** equal to the
total number of storms in your study interval.

### Approximation of depth of flow for Stream Power and Shear Stress equations

Flow depth is an important component for estimating stream power or shear
stress. Here, it is estimated using upslope accumulated area (as modified by
rainfall excess), rain fall in a typical erosion causing event (e.g., greater
than ~30mm), and the length of the typical erosion causing event. Depth at peak
flow is then estimated by assuming a symmetrical unit-hydrograph where total
flow is the area below the hydrograph curve, and the total length equal to
duration of the storm. The constant 0.595 is used to estimate the depth at peak
flow under a symmetrical hydrograph where the area under the graph equals A
(upslope accumulated area), and the horizontal width of the base of the
hydrograph is equal to the length of the storm in seconds (**stormlength**).

One of the benefits of this approach is that it is not tied to any specific
time scale; any amount of time equal to or greater than 1 second can be
modeled. For example, hourly rainfall totals can be entered as **rain** in
sequence, with **stormtime** set to 3600 seconds, **storms** set to 1, and
**stormi** set to 1. Hourly data could be aggregated to the level of the
individual storm with the total for each storm entered as **rain**,
**stormtime** equal to the total number of seconds each storm lasted,
**storms** set to 1, and **stormi** set to some proportion of the storm where
flow was at or near peak depths (e.g. 0.05). Daily rainfall totals can be
entered as **rain** in sequence, with **stormtime** set to 84600 seconds,
**storms** set to 1, and **stormi** set to some proportion where flow is at
peak (e.g., 0.05). Monthly totals can be broken up into proportions per rain
day, entered as **rain** with **stormtime** set to 84600 seconds, **storms**
set to the number of storms that occurred that month, and **stormi** set to
some proportion where flow is at or near peak depth (e.g., 0.05). Weekly,
yearly, decadal, etc., totals can be entered in the same manner.

This approach is more flexible than using R factor to encapsulate rainfall
intensivity, as with USPED, as often R factor can only be estimated from
rainfall totals at the timescale of the year or decade.

<!-- markdownlint-disable line-length -->
### Conversion of output of divergence to calculated erosion and deposition in vertical meters of elevation change
<!-- markdownlint-enable line-length -->

In order to convert the changes in transport capacity into the amount of
elevation gained or lost by deposition or erosion, first the divergence in
transport capacity is calculated in the EW and NS directions. These are then
added back together to calculate the divergence in transport capacity (flux) in
the direction of flow across the cell. Once this is done, the units are in
kg/m2.s of sediment gained or lost. This is converted to meters of elevation
gained or lostby dividing by soil density [kg/m3]. For USPED, which is tied to
the temporal interval of R factor, this typically provides [m/year] as the
output units. For the shear stress and stream power equations, however, this
first comes out in units of [m/s]. It is then necessary to multiply by the
number of seconds at peak flow depth (**stormi** \* **stormtime**) and then by
the number of erosive storms (**storms**) per year to get [m/year] elevation
change.

### Computing elevation changes from one year to next

To compute the new surface elevation after erosion and deposition have
occurred, it is necessary to add this year's ED map to last year's DEM,
checking first if the amount of erodible soil in a given cell is less than the
amount of erosion calculated. The cell will be prevented from eroding past this
amount. If there is some soil depth remaining in the cell, then if the amount
of erosion is more than the amount of soil, the routine will remove all the
remaining soil and stop. Otherwise it will remove the amount of calculated
erosion. If there is deposition, then it will be added on top of current depth
of sediment (even if no sediment is currently in the cell).

Finally, this routine is sensitive to edge effects carried forward from
calculation of slope or other neighborhood routines used earlier in the module.
To prevent null cells at the edges of maps, (the edge cells have no upstream
cell, so get turned null), the initial DEM is patched underneath. Thus, the
perimeter cells will never change in elevation throughout the simulation. Users
are therefore strongly suggested to use a watershed boundary for their input
maps (e.g., extracted from _r.watershed_, and then clipped with the map
calculator), as cells at the watershed boundary should not change in elevation
much in real world scenarios over the time spans of landscape evolution
intended to be modeled with this module (100's to 1000's of years).

## KNOWN ISSUES

This module is sensitive to the geometry of the input DEM. False flat areas and
very steep slope transitions that are in the path of the flowlines will result
in erroneous values, and perhaps even lead to instability in the landscape
evolution algorithms that will exhibit as large "spikes" and "pits" in the
output DEM's after several iterations, and may lead to numerical instability
and NULL values in the various output maps. Preconditioning the input DEM to
reduce these issues, which can be introduced during initial interpolation, or
by the process of filling basins with _r.fill.basins_ or carving streams with
_r.carve_.

The module is also sensitive to input climate parameters and the exponents of
flow and how they are scaled. It is important to test these out extensively
before use.

At this time, this module should be considered to be at a robust alpha stage.
It appears stable enough, but needs to be tested more extensively before it can
be considered stable and ready for production use.

## SEE ALSO

The [MEDLAND](http://medland.asu.edu) project at Arizona State University

[r.watershed](https://grass.osgeo.org/grass-stable/manuals/r.watershed.html),
[r.terraflow](https://grass.osgeo.org/grass-stable/manuals/r.terraflow.html),
[r.mapcalc](https://grass.osgeo.org/grass-stable/manuals/r.mapcalc.html)

Mitasova, H., C. M. Barton, I. I. Ullah, J. Hofierka, and R. S. Harmon 2013
GIS-based soil erosion modeling. In Remote Sensing and GIScience in
Geomorphology, edited by J. Shroder and M. P. Bishop. 3:228-258.
San Diego: Academic Press.

## REFERENCES

Aiello, A., Adamo, M., Canora, F., 2015. Remote sensing and GIS to assess soil
erosion with RUSLE3D and USPED at river basin scale in southern Italy.
CATENA 131, 174–185. <https://doi.org/10.1016/j.catena.2015.04.003>

Aksoy, H., Kavvas, M.L., 2005. A review of hillslope and watershed scale
erosion and sediment transport models. CATENA 64, 247–271.
<https://doi.org/10.1016/j.catena.2005.08.008>

Ayala, G., French, C., 2005. Erosion modeling of past land-use practices in the
Fiume di Sotto di Troina river valley, north-central Sicily. Geoarchaeology 20,
149–167.

Benavidez, R., Jackson, B., Maxwell, D., Norton, K., 2018. A review of the
(Revised) Universal Soil Loss Equation (R/USLE): with a view to increasing its
global applicability and improving soil loss estimates. Hydrology and Earth
System Sciences Discussions 1–34. <https://doi.org/10.5194/hess-2018-68>

Bosco, C., de Rigo, D., Dewitte, O., Poesen, J., Panagos, P., 2015. Modelling
soil erosion at European scale: towards harmonization and reproducibility.
Natural Hazards and Earth System Science 15, 225–245.
<https://doi.org/10.5194/nhess-15-225-2015>

Davy, P., Crave, A., 2000. Upscaling local-scale transport processes in
large-scale relief dynamics. Physics and Chemistry of the Earth, Part A: Solid
Earth and Geodesy 25, 533–541. <https://doi.org/10.1016/S1464-1895(00)00082-X>

Dietrich, W.E., Bellugi, D.G., Sklar, L.S., Stock, J.D., Heimsath, A.M.,
Roering, J.J., 2003. Geomorphic Transport Laws for Predicting Landscape form
and Dynamics, in: Wilcock, P.R., Iverson, R.M. (Eds.), Prediction in
Geomorphology, Geophysical Monograph. American Geophysical Union, pp. 103–132.

Diodato, N., 2006. Predicting RUSLE (Revised Universal Soil Loss Equation)
Monthly Erosivity Index from Readily Available Rainfall Data in Mediterranean
Area. The Environmentalist 26, 63–70.
<https://doi.org/10.1007/s10669-006-5359-x>

Hammad, A.A., Lundekvam, H., Børresen, T., 2004. Adaptation of RUSLE in the
Eastern Part of the Mediterranean Region. Environmental Management 34, 829–841.

Hancock, G.R., 2004. Modelling soil erosion on the catchment and landscape
scale using landscape evolution models – a probabilistic approach using digital
elevation model error, in: Super Soil 2004:3rd Australian New Zealand Soils
Conference. University of Sydney, Australia.

Kelley, A.D., Malin, M.C., Nielson, G.M., 1988. Terrain simulation using a
model of stream erosion. ACM SIGGRAPH Computer Graphics 22, 263–268.

Koko, Š., 2011. Simulation of gully erosion using the SIMWE model and GIS.
Landform Analysis 17, 81–86.

Kwang, J.S., Parker, G., 2017. Landscape evolution models using the stream
power incision model show unrealistic behavior when _m/n_ equals 0.5. Earth
Surface Dynamics 5, 807–820. <https://doi.org/10.5194/esurf-5-807-2017>

Martínez-Casasnovas, J.A., Sánchez-Bosch, I., 2000. Impact assessment of changes
in land use/conservation practices on soil erosion in the Penedès-Anoia vineyard
region (NE Spain). Soil and Tillage Research 57, 101–106.

Mathier, L., Roy, A.G., Paré, J.P., 1989. The effect of slope gradient and
length on the parameters of a sediment transport equation for sheetwash.
CATENA 16, 545–558. <https://doi.org/10.1016/0341-8162(89)90041-6>

Mitasova, H., Barton, C.M., Ullah, I.I., Hofierka, J., Harmon, R.S., 2013.
GIS-based soil erosion modeling, in: Shroder, J., Bishop, M.P. (Eds.), Remote
Sensing and GIScience in Geomorphology, Treatise in Geomorphology. Academic Press,
San Diego, pp. 228–258.

Mitasova, H., Brown, W.M., Johnston, D., 2002. Terrain Modeling and Soil Erosion
Simulation Final Report. Geographic Modeling Systems Lab, University of Illinois
at Urbana-Champaign.

Mitasova, H., Hofierka, J., Zlocha, M., Iverson, L.R., 1996a. Modelling
topographic potential for erosion and deposition using GIS. International journal
of geographical information systems 10, 629–641.
<https://doi.org/10.1080/02693799608902101>

Mitasova, H., Mitas, L., Brown, W.M., 2001. Multiscale Simulation of Land Use
Impact on Soil Erosion and Deposition Patterns, in: Stott, D.E., Mohtar, R.H.,
Steinhardt, G.C. (Eds.), Sustaining the Global Farm: 10th International Soil
Conservation Organization Meeting Held May 24-29, 1999. Purdue University and
the USDA-ARS National Soil Erosion Research Laboratory, pp. 1163–1169.

Mitasova, H., Mitas, L., Brown, W.M., Johnston, D., 1996b. Multidimensional Soil
Erosion/Deposition Modeling Part III: Process based erosion simulation.
Geographic Modeling and Systems Laboratory, University of Illinois at
Urban-Champaign.

Mitasova, H., Mitas, L., Brown, W.M., Johnston, D.M., 1999. Terrain modeling and
Soil Erosion Simulations for Fort Hood and Fort Polk test areas. Geographic
Modeling and Systems Laboratory, University of Illinois at Urbana-Champaign.

Onori, F., De Bonis, P., Grauso, S., 2006. Soil erosion prediction at the basin
scale using the revised universal soil loss equation (RUSLE) in a catchment of
Sicily (southern Italy). Environmental Geology 50, 1129–1140.

Panagos, P., Ballabio, C., Borrelli, P., Meusburger, K., Klik, A., Rousseva, S.,
Tadić, M.P., Michaelides, S., Hrabalíková, M., Olsen, P., Aalto, J., Lakatos, M.,
Rymszewicz, A., Dumitrescu, A., Beguería, S., Alewell, C., 2015a. Rainfall
erosivity in Europe. Science of The Total Environment 511, 801–814.
<https://doi.org/10.1016/j.scitotenv.2015.01.008>

Panagos, P., Borrelli, P., Meusburger, K., Alewell, C., Lugato, E.,
Montanarella, L., 2015b. Estimating the soil erosion cover-management factor at
the European scale. Land Use Policy 48, 38–50.
<https://doi.org/10.1016/j.landusepol.2015.05.021>

Panagos, P., Borrelli, P., Meusburger, K., van der Zanden, E.H., Poesen, J.,
Alewell, C., 2015c. Modelling the effect of support practices (P-factor) on the
reduction of soil erosion by water at European scale. Environmental
Science & Policy 51, 23–34. <https://doi.org/10.1016/j.envsci.2015.03.012>

Panagos, P., Meusburger, K., Ballabio, C., Borrelli, P., Alewell, C., 2014.
Soil erodibility in Europe: A high-resolution dataset based on LUCAS. Science of
The Total Environment 479–480, 189–200.
<https://doi.org/10.1016/j.scitotenv.2014.02.010>

Peckham, S.D., 2003. Fluvial landscape models and catchment-scale sediment
transport. Global and Planetary Change 39, 31–51.
<https://doi.org/10.1016/S0921-8181(03)00014-6>

Peeters, I., Rommens, T., Verstraeten, G., Govers, G., Van Rompaey, A.,
Poesen, J., Van Oost, K., 2006. Reconstructing ancient topography through erosion
modelling. Geomorphology 78, 250–264.

Pistocchi, A., Cassani, G., Zani, O., n.d. Use of the USPED model for mapping
soil erosion and managing best land conservation practices 7.

Renard, K.G., Foster, G.R., Weesies, G.A., McCool, D.K., Yoder, D.C., 1997.
Predicting soil erosion by water: a guide to conservation planning with the
Revised Universal Soil Loss Equation (RUSLE), in: Agriculture Handbook.
US Department of Agriculture, Washington, DC, pp. 1–251.

Renard, K.G., Foster, G.R., Weesies, G.A., Porter, J.P., 1991. RUSLE: Revised
Universal Soil Loss Equation. Journal of Soil and Water Conservation 46, 30–33.

Renard, K.G., Freimund, J.R., 1994. Using monthly precipitation data to estimate
the R-factor in the revised USLE. Journal of Hydrology 157, 287–306.

Sklar, L.S., Riebe, C.S., Marshall, J.A., Genetti, J., Leclere, S., Lukens, C.L.,
Merces, V., 2017. The problem of predicting the size distribution of sediment
supplied by hillslopes to rivers. Geomorphology 277, 31–49.
<https://doi.org/10.1016/j.geomorph.2016.05.005>

Terranova, O., Antronico, L., Coscarelli, R., Iaquinta, P., 2009. Soil erosion
risk scenarios in the Mediterranean environment using RUSLE and GIS: An
application model for Calabria (southern Italy). Geomorphology 112, 228–245.
<https://doi.org/10.1016/j.geomorph.2009.06.009>

Tucker, G.E., Whipple, K.X., 2002. Topographic outcomes predicted by stream
erosion models: Sensitivity analysis and intermodel comparison.
J. Geophys. Res 107, 1–1.

Warren, S.D., Mitasova, H., Hohmann, M.G., Landsberger, S., Skander, F.Y.,
Ruzycki, T.S., Senseman, G.M., 2005. Validation of a 3-D enhancement of the
Universal Soil Loss Equation for preediction of soil erosion and sediment
deposition. Catena 64, 281–296.

Whipple, K.X., Tucker, G.E., 2002. Implications of sediment-flux-dependent river
incision models for landscape evolution. Journal of Geophysical Research 107.

Whipple, K.X., Tucker, G.E., 1999. Dynamics of the stream-power river incision
model; implications for height limits of mountain ranges, landscape response
timescales, and research needs. Journal of Geophysical Research 104, 17,661-17,674.

Willgoose, G., 2005. Mathematical Modeling of Whole Landscape Evolution. Annual
Review of Earth and Planetary Sciences 33, 443–459.

## AUTHORS

Isaac I. Ullah, C. Michael Barton, and Helena Mitasova
