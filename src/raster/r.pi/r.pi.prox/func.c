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

int f_proximity(DCELL *vals, Coords **frags, int count, int min, int max)
{
    int i, j;
    DCELL *distmatrix = get_dist_matrix(count);

    for (i = 0; i < count; i++) {
        DCELL prox = 0.0;

        for (j = 0; j < count; j++) {
            if (i != j) {
                DCELL area = (DCELL)(frags[j + 1] - frags[j]);
                DCELL d = distmatrix[i * count + j];

                if (d >= min && d <= max)
                    prox += area / d;
            }
        }
        vals[i] = prox;
    }

    G_free(distmatrix);

    return 0;
}

int f_modified_prox(DCELL *vals, Coords **frags, int count, int min, int max)
{
    int i, j;
    DCELL *distmatrix = get_dist_matrix(count);

    for (i = 0; i < count; i++) {
        DCELL prox = 0.0;
        DCELL area;

        for (j = 0; j < count; j++) {
            if (i != j) {
                DCELL area = (DCELL)(frags[j + 1] - frags[j]);
                DCELL d = distmatrix[i * count + j];

                if (d >= min && d <= max)
                    prox += area / d;
            }
        }
        area = (DCELL)(frags[i + 1] - frags[i]);

        vals[i] = prox * area;
    }

    G_free(distmatrix);

    return 0;
}

int f_neighborhood(DCELL *vals, Coords **frags, int count, int min, int max)
{
    int i, j;
    DCELL *distmatrix = get_dist_matrix(count);

    for (i = 0; i < count; i++) {
        int patchcount = 0;

        for (j = 0; j < count; j++) {
            if (i != j) {
                DCELL d = distmatrix[i * count + j];

                if (d >= min && d <= max)
                    patchcount++;
            }
        }
        vals[i] = patchcount;
    }

    G_free(distmatrix);

    return 0;
}
