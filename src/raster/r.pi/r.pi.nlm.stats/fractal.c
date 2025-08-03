#include "local_proto.h"

void create_map(int *res, int size)
{
    double *fractbuf = (double *)G_malloc(size * size * sizeof(double));
    double min, max;
    double edge;
    int i, j;

    /* copy mask from to fractbuf */
    memmove(fractbuf, bigbuf, size * size * sizeof(double));

    /* create fractal */
    FractalIter(fractbuf, 1, pow(2, -sharpness), power, size);

    /* replace nan values with min value */
    MinMax(fractbuf, &min, &max, size * size);
    for (i = 0; i < size * size; i++)
        if (Rast_is_d_null_value(&fractbuf[i]))
            fractbuf[i] = min;

    /* find edge */
    edge = CutValues(fractbuf, landcover, size * size);

    MinMax(fractbuf, &min, &max, size * size);

    /* resample map to desired size */
    for (i = 0; i < sx; i++) {
        for (j = 0; j < sy; j++) {
            double val = DownSample(fractbuf, min, i, j, sx, sy, size);
            double old = buffer[i + j * sx];

            if (val >= edge && old == 0) {
                res[i + j * sx] = 1;
            }
            else {
                res[i + j * sx] = 0;
            }
        }
    }

    G_free(fractbuf);
}
