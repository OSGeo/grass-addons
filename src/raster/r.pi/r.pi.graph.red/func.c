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

DCELL min_dist(Patch *frags, int n1, int n2)
{
    int p1, p2;
    DCELL min = 1000000.0;

    /* for all cells in the first patch */
    for (p1 = 0; p1 < frags[n1].count; p1++) {
        Coords *c1 = frags[n1].first_cell + p1;

        /* if cell at the border */
        if (c1->neighbors < 4) {
            /* for all cells in the second patch */
            for (p2 = 0; p2 < frags[n2].count; p2++) {
                /* if cell at the border */
                Coords *c2 = frags[n2].first_cell + p2;

                if (c2->neighbors < 4) {
                    DCELL d = dist(c1, c2);

                    if (d < min) {
                        min = d;
                    }
                }
            }
        }
    }

    return min;
}

DCELL nearest_points(Patch *frags, int n1, int n2, Coords *np1, Coords *np2)
{
    int p1, p2;
    DCELL min = 1000000.0;

    /* for all cells in the first patch */
    for (p1 = 0; p1 < frags[n1].count; p1++) {
        Coords *c1 = frags[n1].first_cell + p1;

        /* if cell at the border */
        if (c1->neighbors < 4) {
            /* for all cells in the second patch */
            for (p2 = 0; p2 < frags[n2].count; p2++) {
                Coords *c2 = frags[n2].first_cell + p2;

                /* if cell at the border */
                if (c2->neighbors < 4) {
                    DCELL d = dist(c1, c2);

                    if (d < min) {
                        min = d;
                        *np1 = *c1;
                        *np2 = *c2;
                    }
                }
            }
        }
    }

    return min;
}

DCELL min_dist_to_location(Patch *frags, int patch, double loc_x, double loc_y)
{
    int p;
    DCELL min = MAX_DOUBLE;

    /* for all cells in the first patch */
    for (p = 0; p < frags[patch].count; p++) {
        Coords *cell = frags[patch].first_cell + p;

        /* if cell at the border */
        if (cell->neighbors < 4) {
            DCELL dx = loc_x - cell->x;
            DCELL dy = loc_y - cell->y;
            DCELL d = sqrt(dx * dx + dy * dy);

            if (d < min) {
                min = d;
            }
        }
    }

    return min;
}

int get_dist_matrix(DCELL *distmatrix, Patch *fragments, int fragcount)
{
    int i, j;

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

int get_nearest_neighbor(DCELL *distmatrix, int fragcount, int patch)
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

int *find_cluster(int *adjacency_matrix, int patch, int fragcount, int *curpos,
                  int *flag_arr)
{
    int i;
    int *list;
    int *first;
    int *last;
    int offset;

    list = G_malloc(fragcount * sizeof(int));
    first = list;
    last = list + 1;

    list[0] = patch;
    flag_arr[patch] = 1;

    while (first < last) {
        /* save patch */
        *curpos = *first;
        curpos++;

        /* add unclassified neighbors to the list */
        offset = (*first) * fragcount;
        for (i = 0; i < fragcount; i++) {
            if (adjacency_matrix[offset + i] == 1 && flag_arr[i] == 0) {
                flag_arr[i] = 1;
                *last = i;
                last++;
            }
        }

        /* pass processed patch */
        first++;
    }

    G_free(list);

    return curpos;
}

int find_clusters(Cluster *cluster_list, int *adjacency_matrix, int fragcount)
{
    int i;
    int count = 0;
    int *flag_arr;
    int *curpos = cluster_list[0].first_patch;

    flag_arr = G_malloc(fragcount * sizeof(int));
    memset(flag_arr, 0, fragcount * sizeof(int));

    for (i = 0; i < fragcount; i++) {
        if (flag_arr[i] == 0) {
            cluster_list[count].first_patch = curpos;
            curpos =
                find_cluster(adjacency_matrix, i, fragcount, curpos, flag_arr);
            cluster_list[count].count =
                curpos - cluster_list[count].first_patch;
            count++;
        }
    }

    /* debug output */
    /*fprintf(stderr, "Clusters:\n");
       for(i = 0; i < count; i++) {
       int j;
       for(j = 0; j < cluster_list[i].count; j++) {
       int patch = cluster_list[i].first_patch[j];
       fprintf(stderr, "%d ", patch);
       }
       fprintf(stderr, "\n");
       } */

    G_free(flag_arr);

    return count;
}

void f_nearest_neighbor(int *adjacency_matrix, DCELL *distmatrix, int fragcount,
                        DCELL max_dist)
{
    int i;

    for (i = 0; i < fragcount; i++) {
        int nn = get_nearest_neighbor(distmatrix, fragcount, i);

        if (nn > -1 && distmatrix[i * fragcount + nn] < max_dist) {
            adjacency_matrix[i * fragcount + nn] = 1;
            adjacency_matrix[nn * fragcount + i] = 1;
        }
    }
}

void f_relative_neighbor(int *adjacency_matrix, DCELL *distmatrix,
                         int fragcount, DCELL max_dist)
{
    int i, j, k;

    for (i = 0; i < fragcount - 1; i++) {
        for (j = i + 1; j < fragcount; j++) {
            DCELL dist = distmatrix[i * fragcount + j];

            /* not connected, if distance is too big */
            if (dist >= max_dist)
                continue;

            /* assume i-th and j-th patches are connected */
            adjacency_matrix[i * fragcount + j] = 1;
            adjacency_matrix[j * fragcount + i] = 1;

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
                    adjacency_matrix[i * fragcount + j] = 0;
                    adjacency_matrix[j * fragcount + i] = 0;
                    break;
                }
            }
        }
    }
}

void f_gabriel(int *adjacency_matrix, DCELL *distmatrix, int fragcount,
               DCELL max_dist)
{
    int i, j, k;

    for (i = 0; i < fragcount - 1; i++) {
        for (j = i + 1; j < fragcount; j++) {
            DCELL dist = distmatrix[i * fragcount + j];

            /* not connected, if distance is too big */
            if (dist >= max_dist)
                continue;

            /* assume i-th and j-th patches are connected */
            adjacency_matrix[i * fragcount + j] = 1;
            adjacency_matrix[j * fragcount + i] = 1;

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
                    adjacency_matrix[i * fragcount + j] = 0;
                    adjacency_matrix[j * fragcount + i] = 0;
                    break;
                }
            }
        }
    }
}

void f_spanning_tree(int *adjacency_matrix, DCELL *distmatrix, int fragcount,
                     DCELL max_dist)
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

    /* repeat for each patch */
    for (i = 0; i < fragcount; i++) {
        /* pass on next minimum node */
        curmin = nextmin;
        nextmin = 0;

        /* connect current minimum node with its parent and set distance to 0 */
        /* connect only if parent is assigned and distance is less than max_dist
         */
        if ((parent = parents[curmin]) != -1 &&
            distmatrix[parent * fragcount + curmin] < max_dist) {
            adjacency_matrix[curmin * fragcount + parent] = 1;
            adjacency_matrix[parent * fragcount + curmin] = 1;
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
    }

    G_free(parents);
    G_free(distances);
}

/*********************************
 *            INDICES            *
 *********************************/

void f_connectance_index(DCELL *values, Cluster *cluster_list,
                         int cluster_count, int *adjacency_matrix,
                         Patch *fragments, int fragcount, DCELL *distmatrix)
{
    int i;
    int p, q;

    /* for each cluster */
    for (i = 0; i < cluster_count; i++) {
        int n = cluster_list[i].count;
        DCELL val = 0;

        /* single patch is 100% connected */
        if (n == 1) {
            values[i] = 100.0;
            continue;
        }

        /* for each patch pair in the cluster */
        for (p = 0; p < cluster_list[i].count - 1; p++) {
            for (q = p + 1; q < cluster_list[i].count; q++) {
                int patch1 = cluster_list[i].first_patch[p];
                int patch2 = cluster_list[i].first_patch[q];

                if (adjacency_matrix[patch1 * fragcount + patch2] == 1) {
                    val++;
                }
            }
        }

        values[i] = 100.0 * val / (n * (n - 1) * 0.5);
    }
}

void f_gyration_radius(DCELL *values, Cluster *cluster_list, int cluster_count,
                       int *adjacency_matrix, Patch *fragments, int fragcount,
                       DCELL *distmatrix)
{
    int i;
    int *p;

    /* for each cluster */
    for (i = 0; i < cluster_count; i++) {
        int n = cluster_list[i].count;
        double avg_x = 0.0;
        double avg_y = 0.0;
        int count = 0;
        DCELL val = 0.0;

        /* calculate cluster centroid */
        for (p = cluster_list[i].first_patch;
             p < cluster_list[i].first_patch + cluster_list[i].count; p++) {
            int cell_index;

            for (cell_index = 0; cell_index < fragments[*p].count;
                 cell_index++) {
                Coords *cell = fragments[*p].first_cell + cell_index;

                avg_x += cell->x;
                avg_y += cell->y;
                count++;
            }
        }
        avg_x /= (double)count;
        avg_y /= (double)count;

        /* for each patch in the cluster */
        for (p = cluster_list[i].first_patch;
             p < cluster_list[i].first_patch + cluster_list[i].count; p++) {
            val += min_dist_to_location(fragments, *p, avg_x, avg_y);
        }

        values[i] = val / (double)n;
    }
}

void f_cohesion_index(DCELL *values, Cluster *cluster_list, int cluster_count,
                      int *adjacency_matrix, Patch *fragments, int fragcount,
                      DCELL *distmatrix)
{
    int i;
    int *p;

    /* for each cluster */
    for (i = 0; i < cluster_count; i++) {
        int total_area = 0;
        DCELL num = 0.0;
        DCELL denom = 0.0;

        /* for each patch in the cluster */
        for (p = cluster_list[i].first_patch;
             p < cluster_list[i].first_patch + cluster_list[i].count; p++) {
            int perim = 0;
            int area = fragments[*p].count;

            /* find perimeter */
            int cell_index;

            for (cell_index = 0; cell_index < fragments[*p].count;
                 cell_index++) {
                Coords *cell = fragments[*p].first_cell + cell_index;

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

void f_percent_patches(DCELL *values, Cluster *cluster_list, int cluster_count,
                       int *adjacency_matrix, Patch *fragments, int fragcount,
                       DCELL *distmatrix)
{
    int i;

    /* for each cluster */
    for (i = 0; i < cluster_count; i++) {
        int patch_count = cluster_list[i].count;

        values[i] = (DCELL)patch_count / (DCELL)fragcount * 100.0;
    }
}

void f_percent_area(DCELL *values, Cluster *cluster_list, int cluster_count,
                    int *adjacency_matrix, Patch *fragments, int fragcount,
                    DCELL *distmatrix)
{
    int i;
    int *p;

    int area_all = 0;

    for (i = 0; i < fragcount; i++) {
        area_all += fragments[i].count;
    }

    /* for each cluster */
    for (i = 0; i < cluster_count; i++) {
        int area_cluster = 0;

        /* for each patch in the cluster */
        for (p = cluster_list[i].first_patch;
             p < cluster_list[i].first_patch + cluster_list[i].count; p++) {
            area_cluster += fragments[*p].count;
        }

        values[i] = (DCELL)area_cluster / (DCELL)area_all * 100.0;
    }
}

void f_number_patches(DCELL *values, Cluster *cluster_list, int cluster_count,
                      int *adjacency_matrix, Patch *fragments, int fragcount,
                      DCELL *distmatrix)
{
    int i;

    /* for each cluster */
    for (i = 0; i < cluster_count; i++) {
        values[i] = (DCELL)cluster_list[i].count;
    }
}

void f_number_links(DCELL *values, Cluster *cluster_list, int cluster_count,
                    int *adjacency_matrix, Patch *fragments, int fragcount,
                    DCELL *distmatrix)
{
    int i;
    int *p, *q;

    /* for each cluster */
    for (i = 0; i < cluster_count; i++) {
        int links = 0;

        /* for each patch in the cluster */
        for (p = cluster_list[i].first_patch;
             p < cluster_list[i].first_patch + cluster_list[i].count - 1; p++) {
            /* for each other patch in the cluster */
            for (q = p + 1;
                 q < cluster_list[i].first_patch + cluster_list[i].count; q++) {
                if (adjacency_matrix[*q * fragcount + *p] == 1) {
                    links++;
                }
            }
        }

        values[i] = (DCELL)links;
    }
}

void f_mean_patch_size(DCELL *values, Cluster *cluster_list, int cluster_count,
                       int *adjacency_matrix, Patch *fragments, int fragcount,
                       DCELL *distmatrix)
{
    int i;
    int *p;

    /* for each cluster */
    for (i = 0; i < cluster_count; i++) {
        int patch_count = cluster_list[i].count;
        int area_cluster = 0;

        /* for each patch in the cluster */
        for (p = cluster_list[i].first_patch;
             p < cluster_list[i].first_patch + cluster_list[i].count; p++) {
            area_cluster += fragments[*p].count;
        }

        if (patch_count > 0) {
            values[i] = (DCELL)area_cluster / (DCELL)patch_count;
        }
        else {
            values[i] = 0.0;
        }
    }
}

void f_largest_patch_size(DCELL *values, Cluster *cluster_list,
                          int cluster_count, int *adjacency_matrix,
                          Patch *fragments, int fragcount, DCELL *distmatrix)
{
    int i;
    int *p;

    /* for each cluster */
    for (i = 0; i < cluster_count; i++) {
        int max_area = 0;

        /* for each patch in the cluster */
        for (p = cluster_list[i].first_patch;
             p < cluster_list[i].first_patch + cluster_list[i].count; p++) {
            int area = fragments[*p].count;

            if (area > max_area) {
                max_area = area;
            }
        }

        values[i] = (DCELL)max_area;
    }
}

DCELL get_diameter(Patch *frags, int n)
{
    int p1, p2;
    DCELL max = 0.0;

    /* for all cells in the first patch */
    for (p1 = 0; p1 < frags[n].count; p1++) {
        Coords *c1 = frags[n].first_cell + p1;

        /* if cell at the border */
        if (c1->neighbors < 4) {
            /* for all cells in the second patch */
            for (p2 = p1 + 1; p2 < frags[n].count; p2++) {
                Coords *c2 = frags[n].first_cell + p2;

                /* if cell at the border */
                if (c2->neighbors < 4) {
                    DCELL d = dist(c1, c2);

                    if (d > max) {
                        max = d;
                    }
                }
            }
        }
    }
    return max;
}

void f_largest_patch_diameter(DCELL *values, Cluster *cluster_list,
                              int cluster_count, int *adjacency_matrix,
                              Patch *fragments, int fragcount,
                              DCELL *distmatrix)
{
    int i;
    int *p;

    /* for each cluster */
    for (i = 0; i < cluster_count; i++) {
        DCELL max_diameter = 0;

        /* for each patch in the cluster */
        for (p = cluster_list[i].first_patch;
             p < cluster_list[i].first_patch + cluster_list[i].count; p++) {
            DCELL diameter = get_diameter(fragments, *p);

            if (diameter > max_diameter) {
                max_diameter = diameter;
            }
        }

        values[i] = max_diameter;
    }
}

/* implements floyd-warshall algorithm for finding shortest pathes */
void f_graph_diameter_max(DCELL *values, Cluster *cluster_list,
                          int cluster_count, int *adjacency_matrix,
                          Patch *fragments, int fragcount, DCELL *distmatrix)
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

            if (adjacency_matrix[index]) {
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
    for (i = 0; i < cluster_count; i++) {
        /* search for the maximum distance between two patches in this cluster
         */
        DCELL max_dist = 0.0;
        int *patch;

        for (patch = cluster_list[i].first_patch;
             patch < cluster_list[i].first_patch + cluster_list[i].count - 1;
             patch++) {
            int *other_patch;

            for (other_patch = patch + 1;
                 other_patch <
                 cluster_list[i].first_patch + cluster_list[i].count;
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
