#include <stdio.h>
#include <math.h>
#include <stdlib.h>

/* WI
 * Adrian Fisher, Neil Flood, Tim Danaher, Comparing Landsat water index methods
 * for automated water classification in eastern Australia, Remote Sensing of
 * Environment, Volume 175, 15 March 2016, Pages 167-182, ISSN 0034-4257,
 * http://dx.doi.org/10.1016/j.rse.2015.12.055. Landsat TM/ETM+ : 1.7204 + 171
 * b2 + 3 b3 - 70 b4 - 45 b5 - 71 b7
 */
double wi(double greenchan, double redchan, double nirchan, double chan5chan,
          double chan7chan)
{
    double result = 1.7204 + 171 * greenchan + 3 * redchan - 70 * nirchan -
                    45 * chan5chan - 71 * chan7chan;
    return result;
}
