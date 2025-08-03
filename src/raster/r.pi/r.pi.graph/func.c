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

DCELL nearest_points(Coords **frags, int n1, int n2, Coords *np1, Coords *np2)
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
                        *np1 = *p1;
                        *np2 = *p2;
                    }
                }
            }
        }
    }

    return min;
}

DCELL min_dist_to_location(Coords **frags, int patch, double loc_x,
                           double loc_y)
{
    Coords *p;
    DCELL min = MAX_DOUBLE;

    /* for all cells in the first patch */
    for (p = frags[patch]; p < frags[patch + 1]; p++) {
        /* if cell at the border */
        if (p->neighbors < 4) {
            DCELL dx = loc_x - p->x;
            DCELL dy = loc_y - p->y;
            DCELL d = sqrt(dx * dx + dy * dy);

            if (d < min) {
                min = d;
            }
        }
    }

    return min;
}

int get_dist_matrix(int fragcount)
{
    int i, j;

    distmatrix = (DCELL *)G_malloc(fragcount * fragcount * sizeof(DCELL));

    /* fill distance matrix */
    for (i = 0; i < fragcount; i++) {
        for (j = i + 1; j < fragcount; j++) {
            DCELL d = min_dist(fragments, i, j);

            distmatrix[i * fragcount + j] = d;
            distmatrix[j * fragcount + i] = d;
        }
    }

    return 0;
}

int get_nearest_neighbor(int patch, int fragcount)
{
    int i;
    int min = -1;
    DCELL min_dist = MAX_DOUBLE;
    int offset = patch * fragcount;

    for (i = 0; i < fragcount; i++) {
        if ((i != patch) && (distmatrix[offset + i] < min_dist)) {
            min_dist = distmatrix[offset + i];
            min = i;
        }
    }

    return min;
}

int *FindCluster(int patch, int *curpos, int *flag_arr, int fragcount)
{
    int i;
    int *list;
    int *first;
    int *last;
    int offset;

    list = G_malloc(fragcount * sizeof(int));

    list[0] = patch;
    flag_arr[patch] = 1;
    first = list;
    last = list + 1;

    while (first < last) {
        /* save patch */
        *curpos = *first;
        curpos++;

        /* add unclassified neighbors to the list */
        offset = *first * fragcount;
        for (i = 0; i < fragcount; i++) {
            if (adjmatrix[offset + i] == 1 && flag_arr[i] == 0) {
                flag_arr[i] = 1;
                *last = i;
                last++;
            }
        }

        /* pass processed patch */
        first++;

        /* fprintf(stderr, "list:");
           for(p = first; p < last; p++) {
           fprintf(stderr, " %d", *p);
           }
           fprintf(stderr, "\n");   */
    }

    return curpos;
}

void FindClusters(int fragcount)
{
    int i;
    int *flag_arr;

    clusters[0] = patches;
    clustercount = 0;

    flag_arr = G_malloc(fragcount * sizeof(int));

    memset(flag_arr, 0, fragcount * sizeof(int));

    for (i = 0; i < fragcount; i++) {
        if (flag_arr[i] == 0) {
            clustercount++;
            clusters[clustercount] =
                FindCluster(i, clusters[clustercount - 1], flag_arr, fragcount);
        }
    }

    G_free(flag_arr);
}

void f_nearest_neighbor(DCELL max_dist, int fragcount)
{
    int i;

    for (i = 0; i < fragcount; i++) {
        int nn = get_nearest_neighbor(i, fragcount);

        if (nn > -1 && distmatrix[i * fragcount + nn] < max_dist) {
            adjmatrix[i * fragcount + nn] = 1;
            adjmatrix[nn * fragcount + i] = 1;
        }
    }
}

void f_relative_neighbor(DCELL max_dist, int fragcount)
{
    int i, j, k;

    for (i = 0; i < fragcount - 1; i++) {
        for (j = i + 1; j < fragcount; j++) {
            DCELL dist = distmatrix[i * fragcount + j];

            /* not connected, if distance is too big */
            if (dist >= max_dist)
                continue;

            /* assume i-th and j-th patches are connected */
            adjmatrix[i * fragcount + j] = 1;
            adjmatrix[j * fragcount + i] = 1;

            /* test if other patch is in the central lens between i-th and j-th
             * patches */
            for (k = 0; k < fragcount; k++) {
                DCELL dist1, dist2;
                int offset;

                /* skip i-th and j-th patches */
                if (k == i || k == j)
                    continue;

                offset = k * fragcount;
                dist1 = distmatrix[offset + i];
                dist2 = distmatrix[offset + j];

                if (dist1 < dist && dist2 < dist) {
                    /* i-th and j-th patches are not connected */
                    adjmatrix[i * fragcount + j] = 0;
                    adjmatrix[j * fragcount + i] = 0;
                    break;
                }
            }
        }
    }
}

void f_gabriel(DCELL max_dist, int fragcount)
{
    int i, j, k;

    for (i = 0; i < fragcount - 1; i++) {
        for (j = i + 1; j < fragcount; j++) {
            DCELL dist = distmatrix[i * fragcount + j];

            /* not connected, if distance is too big */
            if (dist >= max_dist)
                continue;

            /* assume i-th and j-th patches are connected */
            adjmatrix[i * fragcount + j] = 1;
            adjmatrix[j * fragcount + i] = 1;

            /* test if other patch is in the circle around i-th and j-th patches
             */
            for (k = 0; k < fragcount; k++) {
                DCELL dist1, dist2;
                int offset;

                /* skip i-th and j-th patches */
                if (k == i || k == j)
                    continue;

                offset = k * fragcount;
                dist1 = distmatrix[offset + i];
                dist2 = distmatrix[offset + j];

                if ((dist1 * dist1 + dist2 * dist2) < (dist * dist)) {
                    /* i-th and j-th patches are not connected */
                    adjmatrix[i * fragcount + j] = 0;
                    adjmatrix[j * fragcount + i] = 0;
                    break;
                }
            }
        }
    }
}

void f_spanning_tree(DCELL max_dist, int fragcount)
{
    int i, j;
    int *parents;
    DCELL *distances;
    int curmin;
    int nextmin = 0;
    int parent;

    parents = G_malloc(fragcount * sizeof(int));
    distances = G_malloc(fragcount * sizeof(DCELL));

    /* init parents and distances list */
    for (i = 0; i < fragcount; i++) {
        parents[i] = -1;
        distances[i] = MAX_DOUBLE;
    }

    /* repeat fragcount times */
    for (i = 0; i < fragcount; i++) {
        /* pass on next minimum node */
        curmin = nextmin;
        nextmin = 0;

        /* connect current minimum node with its parent and set distance to 0 */
        /* connect only if parent is assigned and distance is less than max_dist
         */
        if ((parent = parents[curmin]) != -1 &&
            distmatrix[parent * fragcount + curmin] < max_dist) {
            adjmatrix[curmin * fragcount + parent] = 1;
            adjmatrix[parent * fragcount + curmin] = 1;
        }
        distances[curmin] = 0.0;

        /* debug output */
        /*G_message("New patch: %d, connecting to patch %d", curmin,
         * parents[curmin]); */

        /* find the next node for minimum spanning tree */
        for (j = 0; j < fragcount; j++) {
            /* get distance to the current minimum node */
            DCELL dist = distmatrix[curmin * fragcount + j];

            /* skip the current minimum node */
            if (j == curmin)
                continue;

            /* if this distance is smaller than the stored one */
            /* then set a new distance and update parent list  */
            if (dist < distances[j]) {
                distances[j] = dist;
                parents[j] = curmin;
            }

            /* update the next minimum node */
            if (distances[nextmin] == 0 ||
                (distances[j] > 0 && distances[j] < distances[nextmin])) {
                nextmin = j;
            }
        }

        /* debug output */
        /*G_message("parent list:");
           for(j = 0; j < fragcount; j++) {
           fprintf(stderr, "%d ", parents[j]);
           }
           fprintf(stderr, "\n");
           G_message("distance list:");
           for(j = 0; j < fragcount; j++) {
           fprintf(stderr, "%0.2f ", distances[j]);
           }
           fprintf(stderr, "\n"); */
    }

    G_free(parents);
    G_free(distances);
}

void f_connectance_index(DCELL *values, int fragcount)
{
    int i;
    int *p, *q;

    /* for each cluster */
    for (i = 0; i < clustercount; i++) {
        int n = clusters[i + 1] - clusters[i];
        DCELL val = 0;

        /* single patch is 100% connected */
        if (n == 1) {
            values[i] = 100.0;
            continue;
        }

        /* for each patch in the cluster */
        for (p = clusters[i]; p < clusters[i + 1] - 1; p++) {
            for (q = p + 1; q < clusters[i + 1]; q++) {
                if (adjmatrix[*p * fragcount + *q] == 1) {
                    val++;
                }
            }
        }

        values[i] = 100.0 * val / (n * (n - 1) * 0.5);
    }
}

void f_gyration_radius(DCELL *values, int fragcount)
{
    int i;
    int *p;

    Coords *cell;

    /* for each cluster */
    for (i = 0; i < clustercount; i++) {
        int n = clusters[i + 1] - clusters[i];
        double avg_x = 0.0;
        double avg_y = 0.0;
        int count = 0;
        DCELL val = 0.0;

        /* calculate cluster centroid */
        for (p = clusters[i]; p < clusters[i + 1]; p++) {
            for (cell = fragments[*p]; cell < fragments[*p + 1]; cell++) {
                avg_x += cell->x;
                avg_y += cell->y;
                count++;
            }
        }
        avg_x /= (double)count;
        avg_y /= (double)count;

        /* for each patch in the cluster */
        for (p = clusters[i]; p < clusters[i + 1]; p++) {
            val += min_dist_to_location(fragments, *p, avg_x, avg_y);
        }

        values[i] = val / (double)n;
    }
}

void f_cohesion_index(DCELL *values, int fragcount)
{
    int i;
    int *p;
    Coords *cell;

    /* for each cluster */
    for (i = 0; i < clustercount; i++) {
        int total_area = 0;
        DCELL num = 0.0;
        DCELL denom = 0.0;

        /* for each patch in the cluster */
        for (p = clusters[i]; p < clusters[i + 1]; p++) {
            int perim = 0;
            int area = fragments[*p + 1] - fragments[*p];

            /* find perimeter */
            for (cell = fragments[*p]; cell < fragments[*p + 1]; cell++) {
                /* if cell is on the edge */
                if (cell->neighbors < 4) {
                    perim++;
                }
            }

            /* update total number of cells in the cluster */
            total_area += area;

            num += (double)perim;
            denom += (double)perim * sqrt((double)area);
        }

        values[i] = (1.0 - num / denom) /
                    (1.0 - 1.0 / sqrt((double)total_area)) * 100.0;
    }
}

void f_percent_patches(DCELL *values, int fragcount)
{
    int i;

    /* for each cluster */
    for (i = 0; i < clustercount; i++) {
        int patch_count = clusters[i + 1] - clusters[i];

        values[i] = (DCELL)patch_count / (DCELL)fragcount * 100.0;
    }
}

void f_percent_area(DCELL *values, int fragcount)
{
    int i;
    int *p;

    int area_all = fragments[fragcount] - fragments[0];

    /* for each cluster */
    for (i = 0; i < clustercount; i++) {
        int area_cluster = 0;

        /* for each patch in the cluster */
        for (p = clusters[i]; p < clusters[i + 1]; p++) {
            area_cluster += fragments[*p + 1] - fragments[*p];
        }

        values[i] = (DCELL)area_cluster / (DCELL)area_all * 100.0;
    }
}

void f_number_patches(DCELL *values, int fragcount)
{
    int i;

    /* for each cluster */
    for (i = 0; i < clustercount; i++) {
        values[i] = (DCELL)(clusters[i + 1] - clusters[i]);
    }
}

void f_number_links(DCELL *values, int fragcount)
{
    int i;
    int *p, *q;

    /* for each cluster */
    for (i = 0; i < clustercount; i++) {
        int links = 0;

        /* for each patch in the cluster */
        for (p = clusters[i]; p < clusters[i + 1]; p++) {
            /* for each other patch in the cluster */
            for (q = p + 1; q < clusters[i + 1]; q++) {
                if (adjmatrix[*q * fragcount + *p] == 1) {
                    links++;
                }
            }
        }

        values[i] = (DCELL)links;
    }
}

void f_mean_patch_size(DCELL *values, int fragcount)
{
    int i;
    int *p;

    /* for each cluster */
    for (i = 0; i < clustercount; i++) {
        int patch_count = clusters[i + 1] - clusters[i];
        int area_cluster = 0;

        /* for each patch in the cluster */
        for (p = clusters[i]; p < clusters[i + 1]; p++) {
            area_cluster += fragments[*p + 1] - fragments[*p];
        }

        values[i] = (DCELL)area_cluster / (DCELL)patch_count;
    }
}

void f_largest_patch_size(DCELL *values, int fragcount)
{
    int i;
    int *p;

    /* for each cluster */
    for (i = 0; i < clustercount; i++) {
        int max_area = 0;

        /* for each patch in the cluster */
        for (p = clusters[i]; p < clusters[i + 1]; p++) {
            int area = fragments[*p + 1] - fragments[*p];

            if (area > max_area) {
                max_area = area;
            }
        }

        values[i] = (DCELL)max_area;
    }
}

DCELL get_diameter(Coords **frags, int n)
{
    Coords *p1, *p2;
    DCELL max = 0.0;

    /* for all cells in the first patch */
    for (p1 = frags[n]; p1 < frags[n + 1]; p1++) {
        /* if cell at the border */
        if (p1->neighbors < 4) {
            /* for all cells in the second patch */
            for (p2 = p1 + 1; p2 < frags[n + 1]; p2++) {
                /* if cell at the border */
                if (p2->neighbors < 4) {
                    DCELL d = dist(p1, p2);

                    if (d > max) {
                        max = d;
                    }
                }
            }
        }
    }
    return max;
}

void f_largest_patch_diameter(DCELL *values, int fragcount)
{
    int i;
    int *p;

    /* for each cluster */
    for (i = 0; i < clustercount; i++) {
        DCELL max_diameter = 0;

        /* for each patch in the cluster */
        for (p = clusters[i]; p < clusters[i + 1]; p++) {
            DCELL diameter = get_diameter(fragments, *p);

            if (diameter > max_diameter) {
                max_diameter = diameter;
            }
        }

        values[i] = max_diameter;
    }
}

/* implements floyd-warshall algorithm for finding shortest pathes */
void f_graph_diameter_max(DCELL *values, int fragcount)
{
    int i, j, k;
    DCELL *pathmatrix;

    /* initialize path matrix */
    pathmatrix = G_malloc(fragcount * fragcount * sizeof(DCELL));

    for (i = 0; i < fragcount; i++) {
        pathmatrix[i * fragcount + i] = 0.0;

        for (j = i + 1; j < fragcount; j++) {
            int index = i * fragcount + j;
            int index_mirror = j * fragcount + i;

            if (adjmatrix[index]) {
                pathmatrix[index] = pathmatrix[index_mirror] =
                    distmatrix[index];
            }
            else {
                pathmatrix[index] = pathmatrix[index_mirror] = MAX_DOUBLE;
            }
        }
    }

    /* for each patch */
    for (k = 0; k < fragcount; k++) {
        /* for every other patch */
        for (i = 0; i < fragcount; i++) {
            /* for every third patch */
            for (j = 0; j < fragcount; j++) {
                /* get direct path and detour over p3 */
                DCELL direct = pathmatrix[i * fragcount + j];
                DCELL indirect = pathmatrix[i * fragcount + k] +
                                 pathmatrix[k * fragcount + j];

                /* if detour is shorter */
                if (indirect < direct) {
                    pathmatrix[i * fragcount + j] = indirect;
                }
            }
        }
    }

    /* for each cluster */
    for (i = 0; i < clustercount; i++) {
        /* search for the maximum distance between two patches in this cluster
         */
        DCELL max_dist = 0.0;
        int *patch;

        for (patch = clusters[i]; patch < clusters[i + 1]; patch++) {
            int *other_patch;

            for (other_patch = patch + 1; other_patch < clusters[i + 1];
                 other_patch++) {
                DCELL dist = pathmatrix[*patch * fragcount + *other_patch];

                if (dist > max_dist) {
                    max_dist = dist;
                }
            }
        }

        values[i] = max_dist;
    }

    G_free(pathmatrix);
}
