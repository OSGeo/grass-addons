#include <stdio.h>

int water(double albedo, double ndvi)
{
    double result;

    if (albedo < 0.1 && ndvi < 0.1) {
        result = 1;
    }
    else {
        result = 0;
    }
    return result;
}
