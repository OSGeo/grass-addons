## DESCRIPTION

*v.flexure* computes how the rigid outer shell of a planet deforms
elastically in response to surface-normal loads by solving equations for
plate bending. This phenomenon is known as "flexural isostasy" and can
be useful in cases of glacier/ice-cap/ice-sheet loading, sedimentary
basin filling, mountain belt growth, volcano emplacement, sea-level
change, and other geologic processes. *v.flexure* and
[r.flexure](r.flexure.md) are the GRASS GIS interfaces to the the model
[**gFlex**](https://csdms.colorado.edu/wiki/Model:GFlex). As both
*v.flexure* and [r.flexure](r.flexure.md) are interfaces to gFlex, this
must be downloaded and installed. The most recent versions of **gFlex**
are available from <https://github.com/awickert/gFlex>, and installation
instructions are avaliable on that page via the *README.md* file.

## NOTES

**input** is a vector points file containing the loads in units of
force. Typically, this will be a representation of a distributed field
of loads as a set of points, so the user will implicitly include the
area over which a stress (vertical load) acts into the quantities in the
database table of **input**.

**te**, written in standard text as T<sub>e</sub>, is the lithospheric
elastic thickness.

**output** is provided as a grid of vector points corresponding to the
GRASS region when this command is invoked. Be sure to use *g.region* to
properly set the input region\! **raster\_output** is the same output,
except converted to a raster grid at the same resolution as the current
computational region. If you have a grid spacing that is much smaller
than a flexural wavelength, it is possible to interpolate the vector
output to a much finer resolution than this raster output provides.

The [Community Surface Dynamics Modeling
System](https://csdms.colorado.edu), into which **gFlex** is integrated,
is a community-driven effort to build an open-source modeling
infrastructure for Earth-surface processes.

## SEE ALSO

*[v.flexure](v.flexure.md),
[v.surf.bspline](https://grass.osgeo.org/grass-stable/manuals/v.surf.bspline.html)*

## REFERENCES

Wickert, A. D. (2015), Open-source modular solutions for flexural
isostasy: gFlex v1.0, *Geoscientific Model Development Discussions*,
*8*(6), 4245–4292, doi:10.5194/gmdd-8-4245-2015.

Wickert, A. D., G. E. Tucker, E. W. H. Hutton, B. Yan, and S. D. Peckham
(2011), [Feedbacks between surface processes and flexural isostasy: a
motivation for coupling
models](https://csdms.colorado.edu/csdms_wiki/images/Andrew_Wickert_CSDMS_2011_annual_meeting.pdf),
in *CSDMS 2011 Meeting: Impact of time and process scales*, Student
Keynote, Boulder, CO.

van Wees, J. D., and S. Cloetingh (1994), A Finite-Difference Technique
to Incorporate Spatial Variations In Rigidity and Planar Faults Into 3-D
Models For Lithospheric Flexure, *Geophysical Journal International*,
*117*(1), 179–195,
[doi:10.1111/j.1365-246X.1994.tb03311.x](https://doi.org/10.1111/j.1365-246X.1994.tb03311.x).

## AUTHOR

Andrew D. Wickert
