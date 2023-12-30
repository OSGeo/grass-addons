#include <math.h>
/*
 * Wilcox, B.B., Lucey, P.G., Gillis, J.J., 2005. Mapping iron in the lunar
 * mare: An improved approach. J. Geophys. Res. 110(E11):2156-2202. with theta
 * = 1.3885 rad, the ‘average slope of the trends in the mare’ from Wilcox et al
 * (2005).
 */
double feo(double r750, double r950, double theta)
{
    return (-137.97 * (r750 * sin(theta) + (r950 / r750) * cos(theta)) + 57.46);
}

/*@inproceedings{zhang2013mapping,
  title={Mapping lunar TiO2 and FeO with Chandrayaan-1 M3 Data},
  author={Zhang, W and Bowles, NE},
  booktitle={Lunar and Planetary Institute Science Conference Abstracts},
  volume={44},
  pages={1212},
  year={2013}
}*/
double feozhang2013(double r750, double r950)
{
    return (17.83 * (-atan2f(((r950 / r750) - 1.26), (r750 - 0.01))) - 6.82);
}
