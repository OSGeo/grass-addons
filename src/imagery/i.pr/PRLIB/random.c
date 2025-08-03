/*
   The following routines are borrowed from "Numerical Recipes in C"

   for

   extraction of samples from normal and uniform distributions
 */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#define M1  259200
#define IA1 7141
#define IC1 54773
#define RM1 (1.0 / M1)
#define M2  134456
#define IA2 8121
#define IC2 28411
#define RM2 (1.0 / M2)
#define M3  243000
#define IA3 4561
#define IC3 51349

double ran1(int *idum)

/*
   return a double from a uniform distributio over [0,1].
   Idum inizialize the procedure
 */
{
    static long ix1, ix2, ix3;
    static double r[98];
    double temp;
    static int iff = 0;
    int j;

    if (*idum < 0 || iff == 0) {
        iff = 1;
        ix1 = (IC1 - (*idum)) % M1;
        ix1 = (IA1 * ix1 + IC1) % M1;
        ix2 = ix1 % M2;
        ix1 = (IA1 * ix1 + IC1) % M1;
        ix3 = ix1 % M3;
        for (j = 1; j <= 97; j++) {
            ix1 = (IA1 * ix1 + IC1) % M1;
            ix2 = (IA2 * ix2 + IC2) % M2;
            r[j] = (ix1 + ix2 * RM2) * RM1;
        }
        *idum = 1;
    }
    ix1 = (IA1 * ix1 + IC1) % M1;
    ix2 = (IA2 * ix2 + IC2) % M2;
    ix3 = (IA3 * ix3 + IC3) % M3;
    j = 1 + ((97 * ix3) / M3);
    if (j > 97 || j < 1) {
        fprintf(stderr, "RAN1: this cannot happen\n");
        exit(-1);
    }
    temp = r[j];
    r[j] = (ix1 + ix2 * RM2) * RM1;
    return temp;
}

double gasdev(int *idum)

/*
   return a double from a normal distribution (m=0, v=1).
   Idum inizialize the procedure
 */
{
    static int iset = 0;
    static double gset;
    double fac, r, v1, v2;

    if (iset == 0) {
        do {
            v1 = 2.0 * ran1(idum) - 1.0;
            v2 = 2.0 * ran1(idum) - 1.0;
            r = v1 * v1 + v2 * v2;
        } while (r >= 1.0 || r == 0.0);
        fac = sqrt(-2.0 * log(r) / r);
        gset = v1 * fac;
        iset = 1;
        return v2 * fac;
    }
    else {
        iset = 0;
        return gset;
    }
}

double expdev(int *idum)
{
    return -log(ran1(idum));
}

double gamdev(double A, double B, int *idum)
{
    int j, ia;
    double am, e, s, v1, v2, x, y, p;
    const double exp_m1 = 0.36787944117144232159;

    ia = (int)A;
    if (ia < 1) {
        e = 1.0 + exp_m1 * A;
        for (;;) {
            p = e * ran1(idum);
            if (p >= 1.0) {
                x = -log((e - p) / A);
                if (expdev(idum) >= (1.0 - A) * log(x))
                    break;
            }
            else {
                x = exp(log(p) / A);
                if (expdev(idum) >= x)
                    break;
            }
        }
        return x * B;
    }
    if (ia < 6) {
        x = 1.0;
        for (j = 1; j <= ia; j++)
            x *= ran1(idum);
        x = -log(x);
    }
    else {
        do {
            do {
                do {
                    v1 = 2.0 * ran1(idum) - 1.0;
                    v2 = 2.0 * ran1(idum) - 1.0;
                } while (v1 * v1 + v2 * v2 > 1.0);
                y = v2 / v1;
                am = ia - 1;
                s = sqrt(2.0 * am + 1.0);
                x = s * y + am;
            } while (x <= 0.0);
            e = (1.0 + y * y) * exp(am * log(x / am) - s * y);
        } while (ran1(idum) > e);
    }
    return x * B;
}
