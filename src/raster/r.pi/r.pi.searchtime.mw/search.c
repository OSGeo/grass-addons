#include "local_proto.h"

/* globals */

int global_progress = 0;
int pickpos_count;
int perception_count;
int pos_count;
WeightedCoords *pos_arr;
Displacement *displacements;
Displacement *perception;
Displacement *positions;

int nx, ny, sizex, sizey;

/*
   initializes all individuals for a window
 */
void init_individuals(int x, int y, DCELL *costmap, int n, int sx)
{
    int i, j, index;
    Displacement *cell;

    /* fill positions array with possible starting positions */
    pos_count = 0;
    for (j = y; j < sizey + y; j++) {
        for (i = x; i < sizex + x; i++) {
            /* test if position should be considered */
            if (costmap[i + j * sx] > 0) {
                positions[pos_count].x = i;
                positions[pos_count].y = j;
                pos_count++;
            }
        }
    }

    for (i = 0; i < n; i++) {
        /* pick random cell */
        index = Random(pos_count);
        cell = positions + index;

        indi_array[i].x = cell->x + 0.5;
        indi_array[i].y = cell->y + 0.5;
        indi_array[i].dir = 2 * M_PI * Randomf();
        indi_array[i].path = 0;
        indi_array[i].finished = 0;
    }

    /* test output */
    /*G_message("Individuals:");
       for(i = 0; i < n; i++) {
       fprintf(stderr, "(%d, %d)dir=%0.2f;", indi_array[i].x, indi_array[i].y,
       indi_array[i].dir);
       } */
}

/*
   sets back an individual, when position is illegal
 */
void set_back(int indi)
{
    int index;
    Displacement *cell;

    /* pick border cell */
    index = Random(pos_count);
    cell = positions + index;

    indi_array[indi].x = cell->x;
    indi_array[indi].y = cell->y;
    indi_array[indi].dir = 2 * M_PI * Randomf();
    indi_array[indi].finished = 0;
}

/*
   sets displacement pixels taking advantage of symmetry
 */
void set_pixels(Displacement *values, int x, int y, int r)
{
    if (y == 0) {
        values[0].x = x;
        values[0].y = 0;
        values[2 * r].x = 0;
        values[2 * r].y = x;
        values[4 * r].x = -x;
        values[4 * r].y = 0;
        values[6 * r].x = 0;
        values[6 * r].y = -x;
    }
    else if (y == x) {
        values[r].x = y;
        values[r].y = y;
        values[3 * r].x = -y;
        values[3 * r].y = y;
        values[5 * r].x = -y;
        values[5 * r].y = -y;
        values[7 * r].x = y;
        values[7 * r].y = -y;
    }
    else if (y < x) {
        values[r - x + y].x = x;
        values[r - x + y].y = y;
        values[r + x - y].x = y;
        values[r + x - y].y = x;
        values[3 * r - x + y].x = -y;
        values[3 * r - x + y].y = x;
        values[3 * r + x - y].x = -x;
        values[3 * r + x - y].y = y;
        values[5 * r - x + y].x = -x;
        values[5 * r - x + y].y = -y;
        values[5 * r + x - y].x = -y;
        values[5 * r + x - y].y = -x;
        values[7 * r - x + y].x = y;
        values[7 * r - x + y].y = -x;
        values[7 * r + x - y].x = x;
        values[7 * r + x - y].y = -y;
    }
}

/*
   calculates displacements for a circle of given radius
 */
void calculate_displacement(Displacement *values, int radius)
{
    int dx = radius;
    int dy = 0;
    float dx_ = (float)dx - 0.5f;
    float dy_ = (float)dy + 0.5f;
    float f = 0.5f - (float)radius;

    set_pixels(values, dx, dy, radius);

    while (dx > dy) {
        if (f < 0) {
            f += 2 * dy_ + 1;
            dy_++;
            dy++;
        }
        else {
            f += 1 - 2 * dx_;
            dx_--;
            dx--;
        }

        set_pixels(values, dx, dy, radius);
    }
}

/*
   fills a weighted array with possible next positions
 */
void pick_nextpos(WeightedCoords *result, int indi, int *map, DCELL *costmap,
                  int sx, int sy)
{
    int i;
    double ex_step, ex_pos;
    Individual *individual = indi_array + indi;
    int actx = individual->x;
    int acty = individual->y;
    int dir_index = Round(individual->dir * 8.0 * (double)step_length);
    int pos = dir_index - 2 * step_length;

    if (pos < 0) {
        pos += 8 * step_length;
    }

    for (i = 0; i < pickpos_count; i++, pos++) {
        result[i].x = actx + displacements[pos].x;
        result[i].y = acty + displacements[pos].y;
        result[i].dir = (double)pos / (8.0 * (double)step_length);
        if (result[i].dir >= 1) {
            result[i].dir--;
        }

        /* if out of limits, use weight=1 until better handling */
        if (actx < 0 || actx >= sx || acty < 0 || acty >= sy) {
            result[i].weight = 1;
        }
        else {
            /* get weight from costmap */
            result[i].weight = costmap[(int)acty * sx + (int)actx];
        }
    }

    /* apply perception multiplicator */
    dir_index = Round(individual->dir * 8.0 * (double)perception_range);
    pos = dir_index - 2 * perception_range;
    ex_step = (double)perception_range / (double)step_length;
    ex_pos = (double)pos;
    for (i = 0; i < pickpos_count; i++) {
        int patch_flag = 0;

        ex_pos += ex_step;
        while (pos < ex_pos) {
            int x = actx + perception[pos].x;
            int y = acty + perception[pos].y;

            if (x >= 0 && x < sx && y >= 0 && y < sy) {
                int val = map[x + y * sx];

                patch_flag |= (val > TYPE_NOTHING);
            }
            pos++;
        }

        if (patch_flag) {
            result[i].weight *= multiplicator;
        }
    }

    return;
}

/*
   performs a single step for an individual
 */
void indi_step(int indi, int *map, DCELL *costmap, int sx, int sy)
{
    int i;
    double sum;
    Individual *individual = indi_array + indi;
    double rnd;
    double newx, newy, newdir;
    int act_cell;

    /* if position is a patch, then set finished = true */
    int x = individual->x;
    int y = individual->y;

    act_cell = map[y * sx + x];
    if (act_cell > TYPE_NOTHING) {
        /* count patch immigrants for this patch */
        patch_imi[act_cell]++;
        individual->finished = 1;
        return;
    }

    /* test output */
    /* fprintf(stderr, "actpos: x = %0.2f, y = %0.2f\n", individual->x,
     * individual->y); */

    /* write an array with possible next positions */
    pick_nextpos(pos_arr, indi, map, costmap, sx, sy);

    /* test output */
    /*      G_message("Nextpos array:\n");
       for(i = 0; i < pickpos_count; i++) {
       fprintf(stderr, "(x=%d,y=%d,dir=%0.2f,weight=%0.2f)\n",
       pos_arr[i].x, pos_arr[i].y, pos_arr[i].dir, pos_arr[i].weight);
       } */

    /* if no next position is possible, then set back */
    sum = 0;
    for (i = 0; i < pickpos_count; i++) {
        sum += pos_arr[i].weight;
    }
    if (sum == 0) {
        set_back(indi);

        return;
    }

    /* pick a next position randomly, considering the weights */
    pos_arr[0].weight = pos_arr[0].weight / sum;
    for (i = 1; i < pickpos_count; i++) {
        pos_arr[i].weight = pos_arr[i - 1].weight + pos_arr[i].weight / sum;
    }
    rnd = Randomf();
    for (i = 0; i < pickpos_count; i++) {
        if (pos_arr[i].weight > rnd)
            break;
    }
    newx = pos_arr[i].x;
    newy = pos_arr[i].y;
    newdir = pos_arr[i].dir;

    /* test output */
    /* fprintf(stderr, "pick: x = %0.2f, y = %0.2f\n\n", newx, newy); */

    /* if new position is out of limits, then set back */
    if (newx < 0 || newx >= sx || newy < 0 || newy >= sy) {
        set_back(indi);

        return;
    }

    /* set new position */
    individual->x = newx;
    individual->y = newy;

    /* count path of the individuum */
    if (include_cost) {
        individual->path += 100 / costmap[(int)newy * sx + (int)newx];
    }
    else {
        individual->path++;
    }
    individual->dir = newdir;

    /* if new position is a patch, then set finished = true */
    /*act_cell = map[(int)newy * sx + (int)newx];
       if (act_cell > TYPE_NOTHING) { */
    /* count patch immigrants for this patch */
    /*patch_imi[act_cell]++;
       individual->finished = 1;
       } */

    return;
}

/*
   performs a search run for a single fragment
 */
DCELL window_run(int x, int y, int *map, DCELL *costmap, int n, int sx, int sy)
{
    int i;
    int step_cnt = 0;
    int finished_cnt = 0;
    int limit = ceil(n * percent / 100);

    init_individuals(x, y, costmap, n, sx);

    /* perform a step for each individual */
    finished_cnt = 0;
    while (finished_cnt < limit && step_cnt <= maxsteps) {
        for (i = 0; i < n; i++) {
            if (!indi_array[i].finished) {
                indi_step(i, map, costmap, sx, sy);

                /* test if new individuum finished */
                if (indi_array[i].finished) {
                    finished_cnt++;

                    global_progress++;
                    G_percent(global_progress, nx * ny * n, 1);

                    if (finished_cnt >= limit)
                        break;
                }
            }
        }

        step_cnt++;
    }

    return (DCELL)step_cnt;
}

/*
   performs a search run for each fragment
 */
void perform_search(DCELL *values, int *map, DCELL *costmap, int size,
                    f_statmethod **stats, int stat_count, int n, int fragcount,
                    int sx, int sy)
{
    int i;
    f_statmethod *func;
    int x, y;

    /* allocate paths array */
    DCELL *indi_paths = (DCELL *)G_malloc(n * sizeof(DCELL));

    /* allocate individuals array */
    indi_array = (Individual *)G_malloc(n * sizeof(Individual));

    /* allocate pickpos result array */
    pickpos_count = 4 * step_length + 1;
    pos_arr =
        (WeightedCoords *)G_malloc(pickpos_count * sizeof(WeightedCoords));

    /* allocate displacement arrays */
    displacements =
        (Displacement *)G_malloc(16 * step_length * sizeof(Displacement));
    perception =
        (Displacement *)G_malloc(16 * perception_range * sizeof(Displacement));

    /* calculate displacements */
    calculate_displacement(displacements, step_length);
    memcpy(displacements + 8 * step_length, displacements,
           8 * step_length * sizeof(Displacement));

    calculate_displacement(perception, perception_range);
    memcpy(perception + 8 * perception_range, perception,
           8 * perception_range * sizeof(Displacement));

    /*      fprintf(stderr, "Displacements:");
       for(i = 0; i < pickpos_count; i++) {
       fprintf(stderr, " (%d, %d)", displacements[i].x, displacements[i].y);
       } */

    memset(patch_imi, 0, fragcount * sizeof(int));

    nx = size > 0 ? sx - size + 1 : 1;
    ny = size > 0 ? sy - size + 1 : 1;
    sizex = size > 0 ? size : sx;
    sizey = size > 0 ? size : sy;

    /* allocate positions array */
    positions = (Displacement *)G_malloc(sizex * sizey * sizeof(Displacement));

    /* perform a search run for each window */
    for (x = 0; x < nx; x++) {
        for (y = 0; y < ny; y++) {
            window_run(x, y, map, costmap, n, sx, sy);

            for (i = 0; i < n; i++) {
                indi_paths[i] = indi_array[i].path;
            }

            for (i = 0; i < stat_count; i++) {
                func = stats[i];
                values[(i * ny + y) * nx + x] = func(indi_paths, n);
            }
        }
    }

    G_percent(1, 1, 1);

    G_free(positions);
    G_free(indi_paths);
    G_free(indi_array);
    G_free(pos_arr);
    G_free(displacements);
}
