#include <stdio.h>
#include <math.h>
#include <stdlib.h>

/* Automated Water Extraction Index
 * Feyisa, G.L., Meilby, H., Fensholt, R., & Proud, S.R. (2014). Automated Water
Extraction Index: A new technique for surface water mapping using Landsat
imagery. Remote Sensing of Environment, 140, 23–35.
http://dx.doi.org/10.1016/j.rse.2013.08.029.
 * Landsat TM/ETM+ : 4 × (b2 - b5 ) - (0.25 × b4 + 2.75 × b5 )
 */
double awei_noshadow(double greenchan, double nirchan, double chan5chan)
{
    double result =
        4 * (greenchan - chan5chan) - (0.25 * nirchan + 2.75 * chan5chan);
    return result;
}

/* Automated Water Extraction Index
 * Feyisa, G.L., Meilby, H., Fensholt, R., & Proud, S.R. (2014). Automated Water
Extraction Index: A new technique for surface water mapping using Landsat
imagery. Remote Sensing of Environment, 140, 23–35.
http://dx.doi.org/10.1016/j.rse.2013.08.029.
 * Landsat TM/ETM+ : b1 + 2.5 × b2 - 1.5 × (b4 + b5 ) - 0.25 × b7
 */
double awei_shadow(double bluechan, double greenchan, double nirchan,
                   double chan5chan, double chan7chan)
{
    double result = bluechan + 2.5 * greenchan - 1.5 * (nirchan + chan5chan) -
                    0.25 * chan7chan;
    return result;
}
