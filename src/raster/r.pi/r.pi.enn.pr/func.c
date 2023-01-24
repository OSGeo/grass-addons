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

void get_smallest_n_indices(int *row, DCELL *matrix, int n, int count,
                            int focal)
{
    int i, j;
    int min;
    int tmpI;
    DCELL tmp;

    /* get row from distance matrix */
    DCELL *distrow = (DCELL *)G_malloc(count * sizeof(DCELL));
    int *indexrow = (int *)G_malloc(count * sizeof(int));

    for (i = 0; i < count; i++) {
        distrow[i] = matrix[focal * count + i];
        indexrow[i] = i;
    }
    distrow[focal] = MAX_DOUBLE;

    /* perform n-times selection sort step */
    for (i = 0; i < n; i++) {
        min = i;
        for (j = i; j < count; j++)
            if (distrow[j] < distrow[min])
                min = j;
        /* exchange minimum element and i-th element */
        tmp = distrow[min];
        distrow[min] = distrow[i];
        distrow[i] = tmp;
        tmpI = indexrow[min];
        indexrow[min] = indexrow[i];
        indexrow[i] = tmpI;
    }

    /* copy n smallest values to row */
    for (i = 0; i < n; i++) {
        row[i] = indexrow[i];
    }

    G_free(distrow);
    G_free(indexrow);
}

int get_area(Coords **frags, int patch)
{
    return frags[patch + 1] - frags[patch];
}

void f_distance(DCELL *vals, Coords **frags, int count, f_statmethod statmethod)
{
    int i, j, index1, index2;
    DCELL d1, d2;
    int diffcount, area, allarea;
    DCELL *distmatrix = get_dist_matrix(count);
    int *neighb_indices = (int *)G_malloc(count * 2 * sizeof(int));
    DCELL *differences = (DCELL *)G_malloc(count * sizeof(DCELL));
    int *actpos;

    /* collect 2 nearest neighbor indices and measure overall area */
    allarea = 0;
    for (i = 0, actpos = neighb_indices; i < count; i++, actpos += 2) {
        get_smallest_n_indices(actpos, distmatrix, 2, count, i);
        allarea += get_area(fragments, i);
    }

    /* calculate differences */
    for (i = 0; i < count; i++) {
        area = 0;
        diffcount = 0;
        for (j = 0; j < count; j++) {
            if (neighb_indices[2 * j] == i) {
                index1 = neighb_indices[2 * j];
                index2 = neighb_indices[2 * j + 1];
                d1 = distmatrix[j * count + index1];
                d2 = distmatrix[j * count + index2];

                differences[diffcount] = d2 - d1;
                diffcount++;
                area += get_area(fragments, j);
            }
        }

        vals[3 * i] = statmethod(differences, diffcount);
        vals[3 * i + 1] = (DCELL)diffcount / (DCELL)count;
        vals[3 * i + 2] = (DCELL)area / (DCELL)allarea;
    }

    G_free(distmatrix);
    G_free(neighb_indices);
    G_free(differences);

    return;
}

void f_area(DCELL *vals, Coords **frags, int count, f_statmethod statmethod)
{
    int i, j, index1, index2;
    DCELL d1, d2;
    int diffcount, area, allarea;
    DCELL *distmatrix = get_dist_matrix(count);
    int *neighb_indices = (int *)G_malloc(count * 2 * sizeof(int));
    DCELL *differences = (DCELL *)G_malloc(count * sizeof(DCELL));
    int *actpos;

    /* collect 2 nearest neighbor indices and measure overall area */
    allarea = 0;
    for (i = 0, actpos = neighb_indices; i < count; i++, actpos += 2) {
        get_smallest_n_indices(actpos, distmatrix, 2, count, i);
        allarea += get_area(fragments, i);
    }

    /* calculate differences */
    for (i = 0; i < count; i++) {
        area = 0;
        diffcount = 0;
        for (j = 0; j < count; j++) {
            if (neighb_indices[2 * j] == i) {
                index1 = neighb_indices[2 * j];
                index2 = neighb_indices[2 * j + 1];
                /* get areas */
                d1 = get_area(fragments, index1);
                d2 = get_area(fragments, index2);

                differences[diffcount] = d2 - d1;
                diffcount++;
                area += get_area(fragments, j);
            }
        }

        vals[3 * i] = statmethod(differences, diffcount);
        vals[3 * i + 1] = (DCELL)diffcount / (DCELL)count;
        vals[3 * i + 2] = (DCELL)area / (DCELL)allarea;
    }

    G_free(distmatrix);
    G_free(neighb_indices);
    G_free(differences);

    return;
}
