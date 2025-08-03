#include <stdio.h>

int water_modis(double surf_ref_7, double ndvi)
{
    double result;

    if (surf_ref_7 < 0.04 && ndvi < 0.1) {
        result = 1;
    }
    else {
        result = 0;
    }
    return result;
}
