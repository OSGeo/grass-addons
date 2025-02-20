## DESCRIPTION

*r.crater* This program estimates the size of a gravity dominated impact
crater or the projectile that made it.

*Forward mode* This mode needs to know the projectile details  
L: projectile diameter (m)  
r\_proj: projectile density (kg/m^3)  
Vi: Projectile velocity (km/s)  
theta: projectile impact angle (degrees) for Gault scaling law (flag2)  
Solid\_rock or not (1 or 0) for Gault scaling law (flag2)  

*Backward mode*This mode needs to know the crater details  

## NOTES

Gault scaling law saturates at craters 1000 Diameter Apparent Transient,
and was essentially designed for regolith (Moon surface).

Below is explanation from the Meloch Fortran code (not included because
of copyright)

Three different estimates are presented, but the pi-scaling method is
currently considered the best\!

Impact conditions: argv\[1\]: enter the impact velocity in km/sec
argv\[2\]: enter the impact angle in degrees

Target descriptors: argv\[3\]: enter the target density in kg/m^3
argv\[4\]: enter the acceleration of gravity in m/sec^2

argv\[5\]: enter the target type, (1-3): type 1 = liquid water type 2 =
loose sand type 3 = competent rock or saturated soil argv\[6\]: enter
the projectile density in kg/m^3

argv\[7\]: enter the type of computation desired (1 or 2): Mode 1,
crater size Mode 2, projectile size

Mode 1: Estimate crater diameter from projectile size Mode 1 case:
Projectile descriptors: argv\[8\]: enter the projectile diameter in m

Mode 2: Estimate crater size from crater diameter\*/ Mode 2 case: Crater
descriptor: argv\[8\]: enter the transient crater diameter in m (if the
final, not the transient crater diameter is known, enter zero (0.0)
here) argv\[9\]: \[optional\] enter the final crater diameter in m

## NOTES

## SEE ALSO

*[r.drain](https://grass.osgeo.org/grass-stable/manuals/r.drain.html),
[r.out.ascii](https://grass.osgeo.org/grass-stable/manuals/r.out.ascii.html)*

## AUTHOR

Yann Chemin
