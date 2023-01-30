#include <stdio.h>
#include <math.h>
#include <stdlib.h>

/* T C W
 * Crist, E.P. (1985). A TM tasseled cap equivalent transformation for
reflectance factor data. Remote Sensing of Environment, 17, 301–306.
 * Landsat TM/ETM+ : 0.0315*b1 + 0.2021*b2 + 0.3102*b3 + 0.1594*b4 - 0.6806*b5 -
0.6109*b7
 */
double tcw(double bluechan, double greenchan, double redchan, double nirchan,
           double chan5chan, double chan7chan)
{
    double result = 0.0315 * bluechan + 0.2021 * greenchan + 0.3102 * redchan +
                    0.1594 * nirchan - 0.6806 * chan5chan - 0.6109 * chan7chan;
    return result;
}
