## DESCRIPTION

***r.damflood*** - The definition of flooding areas is of considerable
importance for both the risk analysis and the emergency management. This
command, in particular, is an embedded GRASS GIS hydrodynamic 2D model
that allows to obtain flooding area due to a failure of a dam, given the
geometry of the reservoir and of the downstream area, the initial
conditions and the dam breach geometry.  
The numerical model solves the conservative form of the shallow water
equations (SWE) using a finite volume method (FVM); the intercell flux
is computed by the "upwind method and the water-level gradient is
evaluated by weighted average of both upwind and downwind gradient.
Additional details of the specific numerical scheme adopted in the model
are presented in references \[1\].  
The command allows to generate raster time series, of water depth and
flow velocity, with time resolution defined by user. Each time series is
identified by a number of raster maps named with a common prefix as
specified by the user and the time instant which it refers expressed in
seconds from the dam failure, joined by the underscore character (e.g.;
myvel\_125, myvel\_250, myvel\_375, etc.).  
Because this new module has been implemented with the aim to provide an
instrument for risk assessment fully within a GIS environment, it should
be able to provide intensity maps directly applicable in those
analyses.In floods, intensity generally corresponds to the maximum flow
depth, but in the particular case of flash floods, where velocities are
normally high, it is recommended to use as intensity indicator the
maximum between the water depth and the product of water velocity and
water depth. For this reason, with this module, in addition to the water
depth and velocity maps, the user can choose a variety of output raster
maps: maximum water depth, maximum water velocity, and maximum intensity
raster maps.  
In case on high numerical stability problem, the user is warned, and the
simulation is stopped.  
  
***Use***  

***Requested input:***  
The required input are:  
\- a DTM including the lake bathimetry and the dam elevation over the
ground \[elev\],  
\- a map with the initial condition easily obtained with
[r.lake](https://grass.osgeo.org/grass-stable/manuals/r.lake.html)
command \[lake\],  
\- a dam breach width raster map \[dambreak\] which can be obtained
using [r.dam](r.dam.md) grass add-on script,  
\- a Manning's roughness coefficient raster map, easily obtained from a
reclassification of a land use map
([r.reclass](https://grass.osgeo.org/grass-stable/manuals/r.reclass.html))
\[manning\],  
\- the simulation time length expressed in *seconds* \[tstop\].  
  
***Output map and additional output options:***  
First the user can set a specific time lag \[deltat\] expressed in
*seconds*, that is used for the output map (depth and velocity)
generation. and also an additional series of instants
\[opt\_t\],expressed in *seconds* from the beginning of the simulation),
used to generate further water flow depth and velocity maps at desired
precise times.  
The user can choose between one of the following time series raster maps
as output: - flow depth \[h\],  
\- flow velocity \[vel\],  
\- a raster map with maximum water depth \[hmax\], relative flooding
intensity \[i\_hmax\], that is the product of water depth and velocity,
and the relative time of occurence\[t\_hmax\],  
\- a raster map with maximum water velocity \[vmax\], relative flooding
intensity \[i\_vmax\], and the relative time of occurence\[t\_vmax\],  
\- a raster map with maximum flooding intensity \[imax\] and the
relative time of occurence\[t\_imax\].  
\- a raster map with the time of arriving of the Wave-Front
\[wavefront\]  
  
where and the raster maps are coded as "prefix" + "\_" + "elapsed
seconds": e.g. *mydepth\_125*.  
  
*Obviously at least one output map prefix must be specified.*  
The unit of measurements of output raster maps are expresssed using the
*International System* (*S.I.*).  
  
***Options:***  
Using a specific flag, the user can obtain another raster map with flow
directions that can be visualized using a specific display command
([d.rast.arrow](https://grass.osgeo.org/grass-stable/manuals/d.rast.arrow.html))
of the GRASS GIS software.  
  
Actually two different dam failure type are considered by the command:
*(i)* full breach, *(ii)* partial breach.  
![image-alt](./dam_failure.png)  
In case of total istantaeous dam break (configuration *i*), the initial
velocity is computed directly applying the SWE at the first time step;
while in case of partial dam breach (configuration *ii*) the user can
choose between don't use any hypothesis, like in the previous
configuration, or evaluate the initial velocity using the overflow
spillway equation:  
*V* = *0.4* <span class="radic"><sup>`
 `</sup>√<span class="radicand" style="text-decoration:overline">`(2 g
h)`</span>  
where *V* is the water flow velocity expressed in m/s, *g* is the
gravitational acceleration expressed in m/s<sup>2</sup> and *h* is the
water depth in correspondence of the dam breach expresssed in meters
(m).  
Optionally the user may modify the initial timestep used for the
numerical solution of the SWE (*default value = 0.01 s*), nevertheless
the timestep \[\], and choose a specific failure tipe corresponding to
different computational method for the initial velocity estimation.  
  
***Notes***  
  
*(GRASS ANSI C command)* </span>

## AUTHORS

Roberto Marzocchi ([e-mail](mailto:roberto.marzocchi@gter.it)) and
Massimiliano Cannata ([e-mail](mailto:massimiliano.cannata@supsi.ch)).
The GRASS tool was developed by Institute of earth science (IST),
University of applied science of Italian Switzerland (SUPSI), Lugano -
Division of geomatics [web-page](http://istgeo.ist.supsi.ch/site/)  
Actually the debug is assured by:  
\- [Gter srl](https://www.gter.it/) (Genoa, Italy)  
\- [IST -SUPSI](https://sites.supsi.ch/ist_en.html) (Lugano,
Switzerland)  
The numerical model, originally developed by the National Center for
Computational Hydroscience and Engineering of the University of
Mississippi, has been reformulated and modified by the authors
introducing important new features to consider the numerical stability
and the type of dam failure, and currently is written in ANSI C
programming language within GRASS.  
  
## SEE ALSO

*[r.lake](https://grass.osgeo.org/grass-stable/manuals/r.lake.html)*,
*[r.reclass](https://grass.osgeo.org/grass-stable/manuals/r.reclass.html)*,
*[d.rast.arrow](https://grass.osgeo.org/grass-stable/manuals/d.rast.arrow.html)*,
*[r.inund.fluv](r.inund.fluv.md)*.  
Details of the numerical model are presented in references.  
Details of use and developing of <span></span> are available
[here](http://istgeo.ist.supsi.ch/site/projects/dambreak).  

## REFERENCES

\[1\] Cannata M. & Marzocchi R. (2012). Two-dimensional dam break
flooding simulation: a GIS embedded approach. - Natural Hazards
61(3):1143-1159  
\[2\]
[Pdf](http://gfoss2009.crs4.it/en/system/files/marzocchi_cannata_licensed.pdf)
presentation of the work at the "X Meeting degli Utenti Italiani di
GRASS - GFOSS" (It) [web-page](http://gfoss2009.crs4.it/en/node/61)  
\[3\] Pdf presentation of the work at the FOSS4G 2009 (En) -
[web-page](http://2009.foss4g.org/researchpapers/#researchpaper_10)  
\[4\] Pdf presentation of the work at the Geoitalia 2011 conference
(En)-
[document](https://dl.dropbox.com/u/3019930/marzocchi_cannata_geoitalia2011.pdf)  

*Last changed: $27 februar 2013 09:40:00 CET $*
