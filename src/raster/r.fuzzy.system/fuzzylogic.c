#include "local_proto.h"

float fuzzy(FCELL cell, SETS *set)
{

    float x;

    if (!set->side) { /* both left and right */

        if (cell <= set->points[0] || cell >= set->points[3])
            return 0.;
        if (cell >= set->points[1] && cell <= set->points[2])
            return 1.;

        x = (cell < set->points[1])
                ? (cell - set->points[0]) / (set->points[1] - set->points[0])
                : (set->points[3] - cell) / (set->points[3] - set->points[2]);
    }

    if (set->side) { /* left: 1 OR right: 2 */

        if (cell <= set->points[0])
            return (set->side == 1) ? 0. : 1.;
        if (cell >= set->points[1])
            return (set->side == 1) ? 1. : 0.;

        x = (set->side == s_LEFT)
                ? (cell - set->points[0]) / (set->points[1] - set->points[0])
                : (set->points[1] - cell) / (set->points[1] - set->points[0]);
    }

    switch (set->shape) {
    case s_LINEAR:
        break;
    case s_SSHAPE:
        x = pow(sin(x * PI2), 2);
        break;
    case s_JSHAPE:
        x = pow(tan(x * PI4), 2);
        break;
    case s_GSHAPE:
        x = pow(tan(x * PI4), 1 / 2.);
        break;
    }

    if (set->hedge)
        x = (set->hedge > 0) ? pow(x, pow(2, set->hedge))
                             : pow(x, pow(0.5, (-set->hedge)));

    if (set->height < 1)
        x = x * set->height;

    return (x >= 0 && x <= 1) ? x : -1;
}

float f_and(float x, float y, logics family)
{
    switch (family) {

    case l_ZADEH:
        return MIN(x, y);
        break;

    case l_PRODUCT:
        return x * y;
        break;

    case l_DRASTIC:
        return MAX(x, y) == 1 ? MIN(x, y) : 0;
        break;

    case l_LUKASIEWICZ:
        return MAX((x + y - 1), 0);
        break;

    case l_FODOR:
        return (x + y) > 1 ? MIN(x, y) : 0;
        break;

    case l_HAMACHER:
        return (x == 0 || y == 0) ? 0 : (x * y) / ((x + y) - x * y);
        break;
    }
    return -1; /* error */
}

float f_or(float x, float y, logics family)
{

    switch (family) {

    case l_ZADEH:
        return MAX(x, y);
        break;

    case l_PRODUCT:
        return x + y - x * y;
        break;

    case l_DRASTIC:
        return (MIN(x, y) == 0) ? MAX(x, y) : 1;
        break;

    case l_LUKASIEWICZ:
        return MIN((x + y), 1);
        break;

    case l_FODOR:
        return (x + y < 1) ? MAX(x, y) : 1;
        break;

    case l_HAMACHER:
        return (x + y) / (1 + x * y);
        break;
    }
    return -1; /* error */
}

float f_not(float x, logics family)
{

    if (family == l_HAMACHER)
        return (1 - x) / (1 + x);
    else
        return ((1 - x) < 0 || (1 - x) > 1) ? -1 : 1 - x;
}
