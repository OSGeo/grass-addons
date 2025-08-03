#include <stdio.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/raster.h>

#define PI           3.1415926
#define HARMONIC_MAX 5000

void fourier(DCELL *outrast, DCELL *inrast, int length, int harmonic_number)
{
    int u, t, col, original_length, count = 0;
    double t_obs[HARMONIC_MAX] = {0.0};
    double t_sim[HARMONIC_MAX] = {0.0};
    for (col = 0; col < length; col++) {
        if (Rast_is_d_null_value(&((DCELL *)inrast)[col])) {
            Rast_set_d_null_value(&outrast[col], 1);
        }
        else {
            t_obs[count] = (double)inrast[col];
            outrast[col] = 0.0;
            count++;
        }
    }
    // Adjust length to actual count without null values
    original_length = length;
    length = count;
    double fcos[HARMONIC_MAX] = {0.0};
    double fsin[HARMONIC_MAX] = {0.0};
    double fm[HARMONIC_MAX] = {0.0};
    double fp[HARMONIC_MAX] = {0.0};

    // Generate F[u], Fm[u] and Fp[u] for u=1 to q
    // u is spectral dimension
    // t is temporal dimension
    for (u = 0; u < harmonic_number; u++) {
        for (t = 0; t < length; t++) {
            fcos[u] += t_obs[t] * cos(2 * PI * u * t / length);
            fsin[u] += t_obs[t] * sin(2 * PI * u * t / length);
        }
        fcos[u] /= length;
        fsin[u] /= length;
        fm[u] = pow(pow(fcos[u], 2) + pow(fsin[u], 2), 0.5);
        fp[u] = atan2(fcos[u], fsin[u]);
    }
    for (t = 0; t < length; t++) {
        for (u = 0; u < harmonic_number; u++) {
            t_sim[t] =
                t_sim[t] + fm[u] * (cos((2 * PI * u * t / length) - fp[u]) +
                                    sin((2 * PI * u * t / length) + fp[u]));
        }
    }
    count = 0;
    for (col = 0; col < original_length; col++) {
        if (Rast_is_d_null_value(&((DCELL *)outrast)[col])) {
            /*Do nothing*/
        }
        else {
            outrast[col] = (DCELL)t_sim[count];
            count++;
        }
    }
}
