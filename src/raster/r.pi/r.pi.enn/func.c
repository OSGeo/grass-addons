#include "local_proto.h"

DCELL value(DCELL *vals, int count)
{
    if (count <= 0)
        return 0;

    return vals[count - 1];
}

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
    DCELL min = 0;

    /* for all cells in the first patch */
    for (p1 = frags[n1]; p1 < frags[n1 + 1]; p1++) {
        /* if cell at the border */
        if (p1->neighbors < 4) {
            /* for all cells in the second patch */
            for (p2 = frags[n2]; p2 < frags[n2 + 1]; p2++) {
                /* if cell at the border */
                if (p2->neighbors < 4) {
                    DCELL d = dist(p1, p2);

                    if (min == 0 || d < min) {
                        min = d;
                    }
                }
            }
        }
    }
    return min;
}

int get_dist_matrix(int count)
{
    int i, j;

    distmatrix = (DCELL *)G_malloc(count * count * sizeof(DCELL));

    /* fill distance matrix */
    for (i = 0; i < count; i++) {
        for (j = i + 1; j < count; j++) {
            DCELL d = min_dist(fragments, i, j);

            distmatrix[i * count + j] = d;
            distmatrix[j * count + i] = d;
        }
    }

    return 0;
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

    /*fprintf(stderr, "\ndistrow =");
       for(i = 0; i < n; i++)
       fprintf(stderr, " %0.2f", distrow[i]);
       fprintf(stderr, "\n"); */

    G_free(distrow);
    G_free(indexrow);
}

int get_max_index(int *array, int size)
{
    int i;
    int max = 0;

    if (size <= 0)
        return -1;

    for (i = 0; i < size; i++) {
        if (array[i] > array[max])
            max = i;
    }

    return max;
}

int get_nearest_indices(int count, int *num_array, int num_count)
{
    int i;
    int max = 0;

    /* get maximum number */
    max = get_max_index(num_array, num_count);

    patch_n = num_array[max] < count - 1 ? num_array[max] : count - 1;

    /* fprintf(stderr, "\n%d nearest patches taken into account.\n\n", patch_n);
     */

    nearest_indices = (int *)G_malloc(count * patch_n * sizeof(int));

    /* for all patches */
    for (i = 0; i < count; i++) {
        /* display progress */
        G_percent(i, count, 2);

        get_smallest_n_indices(nearest_indices + i * patch_n, distmatrix,
                               patch_n, count, i);

        /*              fprintf(stderr, "\npatch %d:", i);
           for(j = 0; j < patch_n; j++)
           fprintf(stderr, " %d", nearest_indices[i * patch_n + j]);
           fprintf(stderr, "\n"); */
    }

    return 0;
}

int f_dist(DCELL *vals, int count, int *num_array, int num_count,
           f_statmethod statmethod)
{
    int n;
    int i, j, index;

    DCELL *distances = (DCELL *)G_malloc(patch_n * sizeof(DCELL));

    /* for all patches */
    for (i = 0; i < count; i++) {
        for (j = 0; j < patch_n; j++) {
            index = nearest_indices[i * patch_n + j];
            distances[j] = distmatrix[i * count + index];
        }

        for (j = 0; j < num_count; j++) {
            n = num_array[j] < count - 1 ? num_array[j] : count - 1;
            vals[i + j * count] = statmethod(distances, n);
        }
    }

    G_free(distances);

    return 0;
}

int f_area(DCELL *vals, int count, int *num_array, int num_count,
           f_statmethod statmethod)
{
    int n;
    int i, j, index;

    DCELL *areas = (DCELL *)G_malloc(patch_n * sizeof(DCELL));

    /* for all patches */
    for (i = 0; i < count; i++) {
        for (j = 0; j < patch_n; j++) {
            index = nearest_indices[i * patch_n + j];
            areas[j] = (DCELL)(fragments[index + 1] - fragments[index]);
        }

        for (j = 0; j < num_count; j++) {
            n = num_array[j] < count - 1 ? num_array[j] : count - 1;
            vals[i + j * count] = statmethod(areas, n);
        }
    }

    G_free(areas);

    return 0;
}

int f_perim(DCELL *vals, int count, int *num_array, int num_count,
            f_statmethod statmethod)
{
    int n;
    int i, j, index, border;
    Coords *p;

    DCELL *perims = (DCELL *)G_malloc(patch_n * sizeof(DCELL));

    /* for all patches */
    for (i = 0; i < count; i++) {
        for (j = 0; j < patch_n; j++) {
            border = 0;

            index = nearest_indices[i * patch_n + j];

            /* for all cells in a patch */
            for (p = fragments[index]; p < fragments[index + 1]; p++) {
                border += 4 - p->neighbors;
            }
            perims[j] = (DCELL)(border);
        }

        for (j = 0; j < num_count; j++) {
            n = num_array[j] < count - 1 ? num_array[j] : count - 1;
            vals[i + j * count] = statmethod(perims, n);
        }
    }

    G_free(perims);

    return 0;
}

int f_shapeindex(DCELL *vals, int count, int *num_array, int num_count,
                 f_statmethod statmethod)
{
    int n;
    int i, j, index, border, area;
    Coords *p;

    DCELL *shapes = (DCELL *)G_malloc(patch_n * sizeof(DCELL));

    /* for all patches */
    for (i = 0; i < count; i++) {
        for (j = 0; j < patch_n; j++) {
            border = 0;

            index = nearest_indices[i * patch_n + j];

            /* for all cells in a patch */
            for (p = fragments[index]; p < fragments[index + 1]; p++) {
                border += 4 - p->neighbors;
            }
            area = (int)(fragments[index + 1] - fragments[index]);

            shapes[j] = (DCELL)border / (4 * sqrt((DCELL)area));
        }

        for (j = 0; j < num_count; j++) {
            n = num_array[j] < count - 1 ? num_array[j] : count - 1;
            vals[i + j * count] = statmethod(shapes, n);
        }
    }

    G_free(shapes);

    return 0;
}

int f_path_dist(DCELL *vals, int count, int *num_array, int num_count,
                f_statmethod statmethod)
{
    int n;
    int i, j, k, index;

    DCELL *distances = (DCELL *)G_malloc(patch_n * sizeof(DCELL));
    int *flags = (int *)G_malloc(count * sizeof(int));

    /* for all patches */
    for (i = 0; i < count; i++) {
        int act_patch = i;

        /* clear flags array */
        memset(flags, 0, count * sizeof(int));

        for (j = 0; j < patch_n; j++) {
            /* get nearest patch for the act_patch */
            /* ignore those already marked in flags */
            k = 0;
            do {
                index = nearest_indices[act_patch * patch_n + k++];
            } while (flags[index] == 1);
            /* mark current patch */
            flags[act_patch] = 1;

            distances[j] = distmatrix[act_patch * count + index];
            act_patch = index;
        }

        /*              fprintf(stderr, "\ndistances for patch %d", i);
           for(j = 0; j < patch_n; j++)
           fprintf(stderr, " %0.2f", distances[j]); */

        for (j = 0; j < num_count; j++) {
            n = num_array[j] < count - 1 ? num_array[j] : count - 1;
            vals[i + j * count] = statmethod(distances, n);
        }
    }

    G_free(distances);

    return 0;
}
