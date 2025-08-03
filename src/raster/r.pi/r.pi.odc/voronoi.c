#include "local_proto.h"

/*
   globals
 */
DCELL *areas;
Point *empty_space;
PatchPoint *new_edge;

/*
   allocates memory, initializes the buffers
 */
void init_voronoi(int *map, int sx, int sy, int fragcount)
{
    int x, y;

    areas = (DCELL *)G_malloc(fragcount * sizeof(DCELL));
    empty_space = (Point *)G_malloc(sx * sy * sizeof(Point));
    new_edge = (PatchPoint *)G_malloc(sx * sy * sizeof(Point));

    memset(areas, 0, fragcount * sizeof(DCELL));
    memset(adj_matrix, 0, fragcount * fragcount * sizeof(int));

    /* gather list of empty space */
    empty_count = 0;
    for (x = 0; x < sx; x++) {
        for (y = 0; y < sy; y++) {
            if (map[x + y * sx] == TYPE_NOTHING) {
                empty_space[empty_count].x = x;
                empty_space[empty_count].y = y;
                empty_count++;
            }
        }
    }
}

/*
   deletes point stride from list
 */
int delete_stride(int index, int count, Point *list, int size)
{
    if (index < 0 || index + count > size)
        return size;

    memcpy(list + index, list + index + count,
           (size - index - count) * sizeof(Point));

    return size - count;
}

/*
   deletes point from list
 */
int delete_point(int index, Point *list, int size)
{
    if (index < 0 || index > size - 1)
        return size;

    memcpy(list + index, list + index + 1, (size - index - 1) * sizeof(Point));

    return size - 1;
}

/*
   adds point to list
 */
int add_point(int x, int y, Point *list, int size)
{
    list[size].x = x;
    list[size].y = y;

    return size + 1;
}

/*
   gathers neighbors of a pixel
 */
int gather_neighbors(int *res, int *map, int x, int y, int sx, int sy,
                     int diag_grow, int fragcount)
{
    int r, l, t, b;
    int nx, ny;
    int count;
    int val;

    /* checklist marks patch neighbors with 1 and not neighbors with 0 */
    int *checklist = (int *)G_malloc(fragcount * sizeof(int));

    memset(checklist, 0, fragcount * sizeof(int));

    /* iterate through neighbors and gather the not empty ones */

    count = 0;
    if (diag_grow) {
        l = x > 0 ? x - 1 : 0;
        t = y > 0 ? y - 1 : 0;
        r = x < sx - 1 ? x + 1 : sx - 1;
        b = y < sy - 1 ? y + 1 : sy - 1;

        for (nx = l; nx <= r; nx++) {
            for (ny = t; ny <= b; ny++) {
                val = map[nx + ny * sx];
                if (val > TYPE_NOTHING && checklist[val] == 0) {
                    checklist[val] = 1;
                    res[count] = val;
                    count++;
                }
            }
        }
    }
    else {
        if (x > 0) { /* left */
            val = map[x - 1 + y * sx];
            if (val > TYPE_NOTHING && checklist[val] == 0) {
                checklist[val] = 1;
                res[count] = val;
                count++;
            }
        }
        if (x < sx - 1) { /* right */
            val = map[x + 1 + y * sx];
            if (val > TYPE_NOTHING && checklist[val] == 0) {
                checklist[val] = 1;
                res[count] = val;
                count++;
            }
        }
        if (y > 0) { /* up */
            val = map[x + (y - 1) * sx];
            if (val > TYPE_NOTHING && checklist[val] == 0) {
                checklist[val] = 1;
                res[count] = val;
                count++;
            }
        }
        if (y < sy - 1) { /* down */
            val = map[x + (y + 1) * sx];
            if (val > TYPE_NOTHING && checklist[val] == 0) {
                checklist[val] = 1;
                res[count] = val;
                count++;
            }
        }
    }

    G_free(checklist);
    return count;
}

/*
   grows patches by 1 pixel
 */
void grow_step(int *map, int sx, int sy, int diag_grow, int fragcount)
{
    int i, j;
    int *neighbors;
    int x, y;
    int patch;
    int neighb_cnt;
    DCELL area;
    int new_count = 0;

    /* alocate memory */
    neighbors = (int *)G_malloc(fragcount * sizeof(int));

    /* iterate through empty space */

    for (i = empty_count - 1; i >= 0; i--) {
        x = empty_space[i].x;
        y = empty_space[i].y;

        /* if at least one patch edge adjacent */
        neighb_cnt = gather_neighbors(neighbors, map, x, y, sx, sy, diag_grow,
                                      fragcount);

        if (neighb_cnt > 0) {
            empty_count = delete_point(i, empty_space, empty_count);

            /* add new edge point */
            new_edge[new_count].x = x;
            new_edge[new_count].y = y;
            new_edge[new_count].patch =
                neighb_cnt == 1 ? neighbors[0] : TYPE_NOGO;
            new_count++;

            /* add voronoi area to patches respectively */
            area = 1 / (double)neighb_cnt;
            for (j = 0; j < neighb_cnt; j++) {
                areas[neighbors[j]] += area;
            }
        }
    }

    /* mark edge points on the map */
    for (i = 0; i < new_count; i++) {
        x = new_edge[i].x;
        y = new_edge[i].y;
        patch = new_edge[i].patch;
        map[x + y * sx] = patch;

        if (patch > TYPE_NOTHING) {
            /* test adjacency and mark adjacent patches in the matrix */
            neighb_cnt = gather_neighbors(neighbors, map, x, y, sx, sy,
                                          diag_grow, fragcount);
            for (j = 0; j < neighb_cnt; j++) {
                int index1 = patch;
                int index2 = neighbors[j];

                /* G_message(_("patches %d and %d are adjacent"), index1,
                 * index2); */

                if (index1 != index2) {
                    adj_matrix[index1 + index2 * fragcount] = 1;
                    adj_matrix[index2 + index1 * fragcount] = 1;
                }
            }
        }
    }
}

/*
   Expands one patch
 */
void expand_patch(int patch, int fragcount)
{
    int i;
    int *list = (int *)G_malloc(fragcount * sizeof(int));
    int *begin = list;
    int *end = list;
    int *p;
    int level = 2;
    int new_count;
    int unleveled = fragcount - 1;

    /* initialize list with direct neighbors of the patch */
    for (i = 0; i < fragcount; i++) {
        if (adj_matrix[patch * fragcount + i] == 1) {
            *end = i;
            end++;
            unleveled--;
        }
    }

    /* while(unleveled > 0) { */
    while (begin < end) {
        new_count = 0;
        /* for each patch on the list */
        for (p = begin; p < end; p++) {
            /* push all direct neighbors of higher level on the list */
            for (i = 0; i < fragcount; i++) {
                /* if i-th patch is an unleveled neighbor */
                if (i != patch && adj_matrix[(*p) * fragcount + i] == 1 &&
                    adj_matrix[patch * fragcount + i] == 0) {
                    *(end + new_count) = i;
                    new_count++;
                    unleveled--;

                    /* save neighbor in adjacency matrix */
                    adj_matrix[patch * fragcount + i] = level;
                }
            }
        }

        begin = end;
        end += new_count;
        level++;

        /* test output */
        /*              for(p = begin; p < end; p++) {
           fprintf(stderr, "%d ", *p);
           }
           fprintf(stderr, "\n\n");
           for(i = 0; i < fragcount; i++) {
           for(j = 0; j < fragcount; j++) {
           fprintf(stderr, "%d", adj_matrix[i * fragcount + j]);
           }
           fprintf(stderr, "\n");
           }
           G_message("Unleveled: %d", unleveled); */
    }

    /*
    for (i = 0; i < fragcount - 1; i++) {
        int j;

        for (j = i + 1; j < fragcount; j++) {
            if (adj_matrix[i * fragcount + j] == 0) {
                G_message("Patch %d und %d sind nicht verbunden!",  i, j);
            }
        }
    }
    */

    G_free(list);
}

/*
   Expands adjacency matrix by including neighbors of higher grade
 */
void expand_matrix(int fragcount)
{
    int row;

    for (row = 0; row < fragcount; row++) {
        expand_patch(row, fragcount);
    }
}

/*
   constucts a voronoi diagram
 */
void voronoi(DCELL *values, int *map, int sx, int sy, int diag_grow,
             int fragcount)
{
    int i;
    int max_empty;
    int last_empty = 0;

    /* init buffers */
    init_voronoi(map, sx, sy, fragcount);

    /* while empty_space not empty ready grow patch buffers by 1 */

    max_empty = empty_count;
    while (empty_count != last_empty) {
        last_empty = empty_count;
        grow_step(map, sx, sy, diag_grow, fragcount);

        G_percent(max_empty - empty_count, max_empty, 1);
    }

    /* write result */
    for (i = 0; i < fragcount; i++) {
        values[i] = areas[i];
    }

    expand_matrix(fragcount);

    G_free(areas);
    G_free(empty_space);
    G_free(new_edge);

    return;
}

/*
   uses values of neighboring patches and the adjacency matrix
   to perform a statistical analysis of all neighbors of the focal patch

   res = ( areas( stat1(patch1, patch2, ...), stat2(patch1, patch2, ...), ... ),
   odds(), ... )
 */
void calc_neighbors(DCELL *res, DCELL *focals, f_statmethod **methods,
                    int stat_count, f_compensate compensate, int neighbor_level,
                    int fragcount)
{
    int i, j, method;
    int count;
    DCELL val;
    DCELL *areasn = (DCELL *)G_malloc(fragcount * sizeof(DCELL));
    DCELL *odds = (DCELL *)G_malloc(fragcount * sizeof(DCELL));
    DCELL *ratios = (DCELL *)G_malloc(fragcount * sizeof(DCELL));

    /* for each patch gather areas and odds of neighbors */
    for (i = 0; i < fragcount; i++) {
        count = 0;
        /* iterate over the corresponding row in the adjacency matrix */
        for (j = 0; j < fragcount; j++) {
            /* if patch i(focal) and patch j(neighbor) are adjacent */
            if (adj_matrix[j + i * fragcount] == neighbor_level) {
                areasn[count] = fragments[j + 1] - fragments[j];
                odds[count] = focals[j];
                ratios[count] = compensate(odds[count], count);
                count++;
            }
        }

        /* now we have areas and odds of all neighbors */
        /* use the statistical methods to combine these */
        for (method = 0; method < stat_count; method++) {
            /* write areas for neighbors of patch i */
            val = methods[method](areasn, count);
            res[method * fragcount + i] = val;

            /* write odds for neighbors of patch i */
            val = methods[method](odds, count);
            res[stat_count * fragcount + method * fragcount + i] = val;

            /* write ratios for neighbors of patch i */
            val = methods[method](ratios, count);
            res[2 * stat_count * fragcount + method * fragcount + i] = val;
        }
    }

    G_free(areas);
    G_free(odds);

    return;
}

void getNeighborCount(DCELL *res, int fragcount)
{
    int i, j;

    /* for each patch count neighbors */
    for (i = 0; i < fragcount; i++) {
        res[i] = 0;

        /* iterate over the corresponding row in the adjacency matrix */
        for (j = 0; j < fragcount; j++) {
            /* if patch i(focal) and patch j(neighbor) are adjacent */
            if (adj_matrix[j + i * fragcount] == 1) {
                res[i]++;
            }
        }
    }
}
