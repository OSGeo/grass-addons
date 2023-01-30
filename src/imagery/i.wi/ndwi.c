#include <stdio.h>
#include <math.h>
#include <stdlib.h>

/* Normalized Difference Water Index (NDWI McFeeters)
 * McFeeters, S.K. (1996). The use of the Normalized Difference Water Index
(NDWI) in the delineation of open water features. International Journal of
Remote Sensing, 17, 1425–1432. http://dx.doi.org/10.1080/01431169608948714.
 * Landsat TM/ETM+ : (b2-b4)/(b2+b4) (green-NIR)/(green+NIR)
 */
double ndwi_mcfeeters(double greenchan, double nirchan)
{
    double result;

    if ((greenchan + nirchan) == 0.0) {
        result = -1.0;
    }
    else {
        result = (greenchan - nirchan) / (greenchan + nirchan);
    }
    return result;
}

/* Normalized Difference Water Index (NDWI Xu)
 * Xu, H. (2006). Modification of normalised difference water index (NDWI) to
enhance open water features in remotely sensed imagery. International Journal of
Remote Sensing, 27, 3025–3033. http://dx.doi.org/10.1080/01431160600589179.
 * Landsat TM/ETM+ : (b2-b5)/(b2+b5) (green-MIR)/(green+MIR)
 */
double ndwi_xu(double greenchan, double chan5chan)
{
    double result;

    if ((greenchan + chan5chan) == 0.0) {
        result = -1.0;
    }
    else {
        result = (greenchan - chan5chan) / (greenchan + chan5chan);
    }
    return result;
}
