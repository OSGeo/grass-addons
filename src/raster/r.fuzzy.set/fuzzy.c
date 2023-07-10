#include <grass/glocale.h>
#include "local_proto.h"

float fuzzy(FCELL cell)
{

    float x, m;

    if (!side) { /* both left and right */

        if (cell <= p[0] || cell >= p[3])
            return 0.;
        if (cell >= p[1] && cell <= p[2])
            return 1.;

        x = (cell < p[1]) ? (cell - p[0]) / (p[1] - p[0])
                          : (p[3] - cell) / (p[3] - p[2]);
    }

    if (side) { /* left: 1 OR right: 2 */

        if (cell <= p[0])
            return (side == 1) ? 0. : 1.;
        if (cell >= p[1])
            return (side == 1) ? 1. : 0.;

        x = (side == 1) ? (cell - p[0]) / (p[1] - p[0])
                        : (p[1] - cell) / (p[1] - p[0]);
    }

    if (type == LINEAR)
        return x;

    if (type == JSHAPE) {
        m = (shape < 0) ? pow(2, 1 + shape) : pow(2, exp(2 * shape));
        return pow(tan(x * PI4), m);
    }

    if (type == GSHAPE) {
        m = (shape > 0) ? pow(2, 1 - shape) : pow(2, exp(-2 * shape));
        return pow(tan(x * PI4), 1 / m);
    }

    if (type == SSHAPE) {
        m = pow(2, exp(2 * abs(shape)));
        return (shape < 0) ? 1 - pow(cos(x * PI2), m) : pow(sin(x * PI2), m);
    }

    return -1; /* error */
}
