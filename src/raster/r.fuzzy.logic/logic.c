#include <grass/gis.h>
#include <grass/glocale.h>
#include "local_proto.h"

float f_and(float x, float y, int family)
{

    switch (family) {

    case ZADEH:
        return MIN(x, y);
        break;

    case PRODUCT:
        return x * y;
        break;

    case DRASTIC:
        return MAX(x, y) == 1 ? MIN(x, y) : 0;
        break;

    case LUKASIEWICZ:
        return MAX((x + y - 1), 0);
        break;

    case FODOR:
        return (x + y) > 1 ? MIN(x, y) : 0;
        break;

    case HAMACHER:
        return (x == y == 0) ? 0 : (x * y) / ((x + y) - x * y);
        break;
    }
    return -1; /* error */
}

float f_or(float x, float y, int family)
{
    float b;

    switch (family) {

    case ZADEH:
        return MAX(x, y);
        break;

    case PRODUCT:
        return x + y - x * y;
        break;

    case DRASTIC:
        return (MIN(x, y) == 0) ? MAX(x, y) : 1;
        break;

    case LUKASIEWICZ:
        return MIN((x + y), 1);
        break;

    case FODOR:
        return (x + y < 1) ? MAX(x, y) : 1;
        break;

    case HAMACHER:
        return (x + y) / (1 + x * y);
        break;
    }
    return -1; /* error */
}

float f_imp(float x, float y, int family)
{

    switch (family) {

    case ZADEH:
        return (x <= y) ? 1 : y;
        break;

    case PRODUCT:
        return MIN(y / x, 1);
        break;

    case DRASTIC:
        return -1; /* not avaialble */
        break;

    case LUKASIEWICZ:
        return MIN((1 - x + y), 1);
        break;

    case FODOR:
        return (x <= y) ? 1 : MAX(1 - x, y);
        break;
    }
    return -1; /* error */
}

float f_not(float x, int family)
{

    if (family == HAMACHER)
        return (1 - x) / (1 + x);
    else
        return ((1 - x) < 0 || (1 - x) > 1) ? -1 : 1 - x;
}
