#include <math.h>

/*
 * Lucey, P.G., Blewett, D.T., Jolliff, B.L., 2000. Lunar iron and titanium
 * abundance algorithms based on final processing of Clementine
 * ultraviolet-visible images. J. Geophys. Res. 105(E8): 20297-20305.
 *
 */
double tio2(double r415, double r750, double y0Ti, double s0Ti)
{
    return (3.708 * atan((r415 / r750) - y0Ti) / (r750 - s0Ti));
}
