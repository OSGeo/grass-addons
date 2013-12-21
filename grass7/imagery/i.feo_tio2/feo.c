#include<math.h>
/* 
 * Wilcox, B.B., Lucey, P.G., Gillis, J.J., 2005. Mapping iron in the lunar mare: An improved approach. J. Geophys. Res. 110(E11):2156-2202.
 * with theta = 1.3885 rad, the ‘average slope of the trends in the mare’ from Wilcox et al (2005).
 */
double feo(double r750, double r950, double theta)
{
    return (-137.97 *( r750 * sin(theta) + (r950/r750) * cos(theta) ) + 57.46);
}
