#include <stdio.h>
#include <math.h>
#include <stdlib.h>

/* Land Surface Water Index (LWSI)
 * a kind of Normalized Difference Water Index
 * Xiao X., Boles S., Frolking S., Salas W., Moore B., Li C., et al. (2002)
 * Landscape-scale characterization of cropland in China using vegetation and
 * Landsat TM images. International Journal of Remote Sensing, 23:3579-3594.
 */
double ls_wi(double nirchan, double swirchan)
{
    double result;

    if ((nirchan + swirchan) == 0.0) {
        result = -1.0;
    }
    else {
        result = (nirchan - swirchan) / (nirchan + swirchan);
    }
    return result;
}
