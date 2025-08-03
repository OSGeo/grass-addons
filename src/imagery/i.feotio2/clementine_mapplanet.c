#include <stdio.h>
#include <math.h>

double feolucey2000(double uvvis2, double uvvis4)
{
    //\cite{lucey2000lunar}
    return (17.427 * (-atan2f(((uvvis4 / uvvis2) - 1.19), (uvvis2 - 0.08))) -
            7.565);
}

double feolawrence2002(double uvvis2, double uvvis4)
{
    //\cite{lawrence2002iron}
    return (
        5.7 * ((-0.147 + 0.372 * (-(uvvis4 / uvvis2 - 1.22) / (uvvis2 - 0.04)) +
                (-0.036) *
                    pow((-(uvvis4 / uvvis2 - 1.22) / (uvvis2 - 0.04)), 2))) +
        2.15);
}

double feowilcox2005(double uvvis2, double uvvis4)
{
    //\cite{wilcox2005mapping}
    return (-137.97 * ((uvvis2 * 0.9834) + (uvvis4 / uvvis2 * 0.1813)) + 57.46);
}

double omatlucey2000(double uvvis2, double uvvis4)
{
    //\cite{lucey2000lunar}
    return (
        sqrtf(pow((uvvis2 - 0.08), 2) + pow(((uvvis4 / uvvis2) - 1.19), 2)));
}

double omatwilcox2005(double uvvis2, double uvvis4)
{
    //\cite{wilcox2005mapping}
    return ((uvvis2 * 0.1813) - ((uvvis4 / uvvis2) * 0.9834));
}

double tio2lucey2000(double uvvis1, double uvvis2)
{
    //\cite{lucey2000lunar}
    return (3.708 *
            pow((atan2f(((uvvis1 / uvvis2) - 0.42), (uvvis2 - 0.0))), 5.979));
}
