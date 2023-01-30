#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/stats.h>
#include <math.h>
#include "local_proto.h"

DCELL dist(Coords *p1, Coords *p2)
{
    int x1 = p1->x;
    int y1 = p1->y;
    int x2 = p2->x;
    int y2 = p2->y;
    int dx = x2 - x1;
    int dy = y2 - y1;

    return sqrt(dx * dx + dy * dy);
}

DCELL min_dist(Coords **frags, int n1, int n2)
{
    Coords *p1, *p2;
    DCELL min = 1000000.0;

    /* for all cells in the first patch */
    for (p1 = frags[n1]; p1 < frags[n1 + 1]; p1++) {
        /* if cell at the border */
        if (p1->neighbors < 4) {
            /* for all cells in the second patch */
            for (p2 = frags[n2]; p2 < frags[n2 + 1]; p2++) {
                /* if cell at the border */
                if (p2->neighbors < 4) {
                    DCELL d = dist(p1, p2);

                    if (d < min) {
                        min = d;
                    }
                }
            }
        }
    }

    return min;
}

DCELL *get_dist_matrix(int count)
{
    int i, j;
    DCELL *distmatrix;

    distmatrix = (DCELL *)G_malloc(count * count * sizeof(DCELL));

    /* fill distance matrix */
    for (i = 0; i < count; i++) {
        for (j = i + 1; j < count; j++) {
            DCELL d = min_dist(fragments, i, j);

            distmatrix[i * count + j] = d;
            distmatrix[j * count + i] = d;
        }
    }

    return distmatrix;
}

void compute_values(DCELL *vals, int fragcount, int min, int max,
                    f_func stat_method)
{
    int i, j;
    int counter;
    DCELL *distmatrix = get_dist_matrix(fragcount);
    DCELL *patch_vals = (DCELL *)G_malloc(fragcount * sizeof(DCELL));

    fprintf(stderr, "fragcount = %d\n\n", fragcount);

    for (i = 0; i < fragcount; i++) {
        counter = 0;
        for (j = 0; j < fragcount; j++) {
            if (i != j) {
                DCELL d = distmatrix[i * fragcount + j];

                if (d >= min && d <= max) {
                    patch_vals[counter] = valsbuf[j];
                    counter++;
                }
            }
        }

        /*              fprintf(stderr, "patch_values%d:", i);
           for(j = 0; j < counter; j++) {
           fprintf(stderr, " %0.2f", patch_vals[j]);
           }
           fprintf(stderr, "\n"); */

        vals[i] = stat_method(patch_vals, counter);
        /* fprintf(stderr, "vals[%d] = %0.2f\n", i, vals[i]); */
    }

    G_free(distmatrix);
    G_free(patch_vals);

    return;
}
