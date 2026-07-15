#include <float.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#include "random2.h"

#define TRUE  -1
#define FALSE 0

#ifdef M_PI
#else
#define M_PI (3.141592653589793115997963468544185161590576171875)
#endif

static long random_irpi();
static void srandom_irpi(unsigned int);

static long (*randomProc)() = random_irpi;
static void (*seedProc)(unsigned int) = srandom_irpi;

double Uniform(UniSave *uniData, double mean, double std_devn)
{
    /*
     * Return a uniform random variate of zero mean and unit variance
     *   - rember that variance of a uniform pdf is  (b-a)^2/12
     */
    std_devn *= sqrt(12.0);
    return (mean - std_devn / 2) +
           std_devn * (double)randomProc() / ((double)uniData->randMax + 1);
}

double SimpleUniform(UniSave *uniData, double min, double max)
{
    return min +
           (max - min) * (double)randomProc() / ((double)uniData->randMax + 1);
}

double Cauchy(UniSave *uniData, double mean, double half_width)
{
    return (mean +
            half_width * tan(SimpleUniform(uniData, -M_PI / 2, M_PI / 2)));
}

double Gaussian(UniSave *uniData, double mean, double std_devn)
{
    static int iset = 0;
    static double gset;
    double fac, r, v1, v2;
    if (iset == 0) {
        do {
            v1 = 2.0 * ((double)(randomProc() & uniData->randMax) /
                        (double)uniData->randMax) -
                 1.0;
            v2 = 2.0 * ((double)(randomProc() & uniData->randMax) /
                        (double)uniData->randMax) -
                 1.0;
            r = v1 * v1 + v2 * v2;
        } while (r >= 1.0);
        fac = sqrt(-2.0 * log(r) / r);
        gset = v1 * fac;
        iset = 1;
        return v2 * fac * std_devn + mean;
    }
    else {
        iset = 0;
        return gset * std_devn + mean;
    }
}

void Init_RNG(UniSave *uniData, unsigned int seed)
{
    uniData->randMax = RAND_MAX;
    seedProc(seed);
    return;
}

// keeping these random functions here, even if they reference teh standard lib
// functions, because this allows for the possibility to extend with more random
// functions in the future, once the licensing issues are solved.

static long random_irpi()
{
    return (long)rand();
}

static void srandom_irpi(unsigned int seed)
{
    srand(seed);
}
