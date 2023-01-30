#include "local_proto.h"

int GetCell(double *map, int x, int y, int size, double val, double *res)
{
    if ((x >= 0) && (x < size) && (y >= 0) && (y < size)) {
        *res = map[x + y * size];
        if (Rast_is_d_null_value(res)) {
            *res = val;
        }
        return 1;
    }

    *res = 0;

    return 0;
}

void SetCell(double *map, int x, int y, int size, double value)
{
    /*      fprintf(stderr, "writing value = %f to x = %d y = %d\n", value, x,
     * y); */
    if (!Rast_is_d_null_value(&map[x + y * size]))
        map[x + y * size] = value;
    /*      fprintf(stderr, "map[%d,%d] = %f\n", x, y, map[x + y * size]); */
}

double DownSample(double *map, double min, int x, int y, int newcols,
                  int newrows, int oldsize)
{
    int topleftX = oldsize * x / newcols;
    int topleftY = oldsize * y / newrows;
    int bottomrightX = oldsize * (x + 1) / newcols;
    int bottomrightY = oldsize * (y + 1) / newrows;

    int i, j;
    double cell;
    int cnt = 0;
    double sum = 0;

    for (i = topleftX; i < bottomrightX; i++) {
        for (j = topleftY; j < bottomrightY; j++) {
            if (GetCell(map, i, j, oldsize, min, &cell)) {
                cnt++;
                sum += cell;
            }
        }
    }

    return sum / (double)cnt;
}

double UpSample(int *map, int x, int y, int oldcols, int oldrows, int newsize)
{
    /* bilinear interpolation */
    double xval = ((double)x + 0.5) / (double)newsize * (double)oldcols;
    double yval = ((double)y + 0.5) / (double)newsize * (double)oldrows;
    int oldx = floor(xval);
    int oldy = floor(yval);

    /*double dummy;
       double fracx = modf(xval, dummy);
       double fracy = modf(yval, dummy);

       int i, j;

       for(i = -1; i <= 0; i++) {
       for(j = -1; j <= 0; j++) {
       int actx = oldx + i;
       int acty = oldy + j;

       if(actx >= 0 && actx < oldcols && acty >= 0 && acty < oldrows) {

       }
       }
       } */

    double res = 0;

    if (map[oldx + oldy * oldcols] != 0) {
        Rast_set_d_null_value(&res, 1);
    }
    return res;
}

void MinMax(double *map, double *min, double *max, int size)
{
    int i;

    *min = MAX_DOUBLE;
    *max = MIN_DOUBLE;

    if (size == 0)
        return;

    for (i = 1; i < size; i++) {
        if (!Rast_is_d_null_value(&map[i])) {
            if (map[i] < *min)
                *min = map[i];
            if (map[i] > *max)
                *max = map[i];
        }
    }
}

double CutValues(double *map, double mapcover, int size)
{
    int values[RESOLUTION];
    double min, max, span;
    int pixels;
    int i, index;
    int bottom, top;
    int topdif, bottomdif;

    /* get parameters */
    MinMax(map, &min, &max, size);
    if (min == max)
        G_fatal_error("CutValues(): min %g == max %g", min, max);
    span = max - min;
    pixels = Round(size * mapcover);

    /* classify heights */
    memset(values, 0, RESOLUTION * sizeof(int));
    for (i = 0; i < size; i++) {
        index = floor(RESOLUTION * (map[i] - min) / span);
        if (index >= RESOLUTION)
            index = RESOLUTION - 1;
        /*              index:= RES * map[i] / span - c; */
        values[index]++;
    }

    /* accumulate top to bottom */
    for (i = RESOLUTION - 1; i > 0; i--) {
        values[i - 1] += values[i];
    }

    /* find matching height */
    bottom = 0;
    top = RESOLUTION - 1;
    while (bottom < top) {
        if (values[bottom] >= pixels)
            bottom++;
        if (values[top] < pixels)
            top--;
    }
    if (values[bottom] < pixels)
        bottom--;
    if (values[top] >= pixels)
        top++;

    /* find the closest to the landcover */
    topdif = abs(values[top] - pixels);
    bottomdif = abs(values[bottom] - pixels);

    if (topdif < bottomdif) {
        return span * top / RESOLUTION + min;
    }
    else {
        return span * bottom / RESOLUTION + min;
    }
}

void FractalStep(double *map, double min, Point v1, Point v2, Point v3,
                 Point v4, double d, int size)
{
    Point mid;
    double val1, val2, val3, val4;
    double mval;
    double r;

    /* get values */
    int cnt = 0;

    if (GetCell(map, v1.x, v1.y, size, min, &val1))
        cnt++;
    if (GetCell(map, v2.x, v2.y, size, min, &val2))
        cnt++;
    if (GetCell(map, v3.x, v3.y, size, min, &val3))
        cnt++;
    if (GetCell(map, v4.x, v4.y, size, min, &val4))
        cnt++;

    /* calculate midpoints */
    mid.x = (v1.x + v2.x + v3.x + v4.x) / 4;
    mid.y = (v1.y + v2.y + v3.y + v4.y) / 4;

    /* calc mid values */
    r = (Randomf() - 0.5) * 2;
    mval = (val1 + val2 + val3 + val4) / cnt + r * d;

    /* set new values */
    SetCell(map, mid.x, mid.y, size, mval);
}

void FractalIter(double *map, double d, double dmod, int n, int size)
{
    int step;
    Point v1, v2, v3, v4;
    int i, x, y, dx;
    double actd = d;
    int xdisp;
    double min, max;

    MinMax(map, &min, &max, size * size);

    /* initialize corners */
    SetCell(map, 0, 0, size, 2 * (Randomf() - 0.5));
    SetCell(map, size - 1, 0, size, 2 * (Randomf() - 0.5));
    SetCell(map, 0, size - 1, size, 2 * (Randomf() - 0.5));
    SetCell(map, size - 1, size - 1, size, 2 * (Randomf() - 0.5));

    /* calculate starting step width */
    step = size - 1;

    for (i = 0; i < n; i++) {
        /* do diamond step */
        for (x = 0; x < (1 << i); x++) {
            for (y = 0; y < (1 << i); y++) {
                v1.x = x * step;
                v1.y = y * step;
                v2.x = (x + 1) * step;
                v2.y = y * step;
                v3.x = x * step;
                v3.y = (y + 1) * step;
                v4.x = (x + 1) * step;
                v4.y = (y + 1) * step;

                FractalStep(map, min, v1, v2, v3, v4, actd, size);
            }
        }

        /* adjust step */
        step >>= 1;

        /* do square step */
        xdisp = 1;
        for (y = 1; y <= (1 << (i + 0)); y++) {
            for (x = 1; x <= (1 << i) - xdisp - 1; x++) {
                dx = 2 * x + xdisp;
                v1.x = dx * step;
                v1.y = (y - 1) * step;
                v2.x = (dx + 1) * step;
                v2.y = y * step;
                v3.x = dx * step;
                v3.y = (y + 1) * step;
                v4.x = (dx - 1) * step;
                v4.y = y * step;

                FractalStep(map, min, v1, v2, v3, v4, actd, size);
            }

            /* switch row offset */
            if (xdisp == 0) {
                xdisp = 1;
            }
            else {
                xdisp = 0;
            }
        }

        /* adjust displacement */
        actd = actd * dmod;
    }
}
