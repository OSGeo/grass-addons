#include "local_proto.h"

int gather_positions(Position *res, int *map, int value, int x, int y,
                     int sizex, int sizey)
{
    int i, j;
    int count = 0;

    for (j = y; j < y + sizey; j++) {
        for (i = x; i < x + sizex; i++) {
            /* test if position should be considered */
            if (map[j * sx + i] == value) {
                res[count].x = i;
                res[count].y = j;
                count++;
            }
        }
    }

    return count;
}

/* returns an array with n random positions from the free positions array */
void get_random_positions(Position *res, int pos_count, Position *free_arr,
                          int free_count)
{
    /* this will save the size of the temporal array */
    int cur_size = free_count;
    int cur_pos = 0;
    int i;

    /* create a temporal copy of the free positions array */
    Position *temp = (Position *)G_malloc(free_count * sizeof(Position));

    memcpy(temp, free_arr, free_count * sizeof(Position));

    /* choose n random positions */
    /* delete used positions, to prevent DCELL choice */
    for (i = 0; i < pos_count; i++) {
        int pos = Random(cur_size);

        res[cur_pos].x = temp[pos].x;
        res[cur_pos].y = temp[pos].y;

        cur_size--;
        cur_pos++;

        /* replace current position with the last one */
        temp[pos] = temp[cur_size];
    }

    G_free(temp);

    return;
}

void get_dist_matrix(DCELL *res, Position *positions, int count)
{
    int i, j;

    for (i = 0; i < count; i++) {
        res[i * count + i] = 0.0;
        for (j = i + 1; j < count; j++) {
            Position *pos1 = positions + i;
            Position *pos2 = positions + j;
            DCELL dx = pos2->x - pos1->x;
            DCELL dy = pos2->y - pos1->y;
            DCELL val = sqrt(dx * dx + dy * dy);

            res[i * count + j] = val;
            res[j * count + i] = val;
        }
    }

    return;
}

void get_n_smallest(DCELL *res, DCELL *dist_matrix, int count, int index, int n)
{
    int i, j;
    int cur_size = count - 1;
    DCELL *temp = (DCELL *)G_malloc(count * sizeof(DCELL));
    int border = n < count ? n : count;

    /* copy the index distance row to a temp array */
    memcpy(temp, dist_matrix + index * count, count * sizeof(DCELL));
    temp[index] = temp[cur_size];

    /* get n smallest values */
    for (i = 0; i < border; i++) {
        res[i] = MAX_DOUBLE;
        for (j = 0; j < cur_size; j++) {
            if (temp[j] < res[i]) {
                res[i] = temp[j];
            }
        }

        /* delete i-th minimum */
        cur_size--;
        temp[i] = temp[cur_size];
    }

    G_free(temp);
}

/* performs actual analysis for one window */
DCELL perform_test(Position *positions, int count)
{
    int i;
    DCELL *dist_matrix = (DCELL *)G_malloc(count * count * sizeof(DCELL));

    /* TODO: support m-nearest neighbors analysis */
    DCELL nn_dist;
    DCELL sum = 0;

    get_dist_matrix(dist_matrix, positions, count);

    for (i = 0; i < count; i++) {
        get_n_smallest(&nn_dist, dist_matrix, count, i, 1 /* later m */);
        sum += nn_dist;
    }

    G_free(dist_matrix);

    return sum / count;
}

void clark_evans(DCELL *values, int *map, int *mask, int n, int size)
{
    int x, y, nx, ny, sizex, sizey, i;
    Position *free_arr, *pos_arr;
    int free_count, pos_count;
    DCELL value;
    int progress = 0;

    DCELL *reference;
    DCELL ref_value;
    Position *rand_arr;

    /* calculate window size */
    nx = size > 0 ? sx - size + 1 : 1;
    ny = size > 0 ? sy - size + 1 : 1;
    sizex = size > 0 ? size : sx;
    sizey = size > 0 ? size : sy;

    /* allocate memory */
    free_arr = (Position *)G_malloc(sizex * sizey * sizeof(Position));
    pos_arr = (Position *)G_malloc(sizex * sizey * sizeof(Position));
    reference = (DCELL *)G_malloc(n * sizeof(DCELL));
    rand_arr = (Position *)G_malloc(sizex * sizey * sizeof(Position));

    /* for each window */
    for (y = 0; y < ny; y++) {
        for (x = 0; x < nx; x++) {
            /* get relevant positions */
            free_count =
                gather_positions(free_arr, mask, 1, x, y, sizex, sizey);
            pos_count = gather_positions(pos_arr, map, 1, x, y, sizex, sizey);

            if (free_count >= pos_count && pos_count > 1) {
                /* calculate reference value n times */
                for (i = 0; i < n; i++) {
                    get_random_positions(rand_arr, pos_count, free_arr,
                                         free_count);
                    reference[i] = perform_test(rand_arr, pos_count);
                    progress++;
                    G_percent(progress, n * nx * ny, 1);
                }

                /* calculate real value */
                value = perform_test(pos_arr, pos_count);
                ref_value = average(reference, n);

                value = value / ref_value;
            }
            else {
                value = -1;
                progress += n;
                G_percent(progress, n * nx * ny, 1);
            }

            values[y * nx + x] = value;
        }
    }

    G_free(pos_arr);
    G_free(free_arr);
    G_free(reference);
    G_free(rand_arr);

    return;
}

void donnelly(DCELL *values, int *map, int *mask, int n, int size)
{
    int x, y, nx, ny, sizex, sizey, i;
    Position *free_arr, *pos_arr;
    int free_count, pos_count;
    DCELL value;
    int progress = 0;

    DCELL *reference;
    DCELL ref_value;
    Position *rand_arr;
    DCELL correction;

    /* calculate window size */
    nx = size > 0 ? sx - size + 1 : 1;
    ny = size > 0 ? sy - size + 1 : 1;
    sizex = size > 0 ? size : sx;
    sizey = size > 0 ? size : sy;

    /* allocate memory */
    free_arr = (Position *)G_malloc(sizex * sizey * sizeof(Position));
    pos_arr = (Position *)G_malloc(sizex * sizey * sizeof(Position));
    reference = (DCELL *)G_malloc(n * sizeof(DCELL));
    rand_arr = (Position *)G_malloc(sizex * sizey * sizeof(Position));

    /* for each window */
    for (y = 0; y < ny; y++) {
        for (x = 0; x < nx; x++) {
            /* get relevant positions */
            free_count =
                gather_positions(free_arr, mask, 1, x, y, sizex, sizey);
            pos_count = gather_positions(pos_arr, map, 1, x, y, sizex, sizey);

            correction =
                (0.051 + 0.041 / sqrt(pos_count)) * 2 * (nx + ny) / pos_count;

            if (free_count >= pos_count && pos_count > 1) {
                /* calculate reference value n times */
                for (i = 0; i < n; i++) {
                    DCELL tmp;

                    get_random_positions(rand_arr, pos_count, free_arr,
                                         free_count);
                    tmp = perform_test(rand_arr, pos_count);

                    /* donnelly correction */
                    reference[i] = 0.5 * tmp + correction;

                    progress++;
                    G_percent(progress, n * nx * ny, 1);
                }

                /* calculate real value */
                value = perform_test(pos_arr, pos_count);

                /* donnelly correction */
                value = 0.5 * value + correction;

                ref_value = average(reference, n);

                value = value / ref_value;
            }
            else {
                Rast_set_d_null_value(&value, 1);
                progress += n;
                G_percent(progress, n * nx * ny, 1);
            }

            values[y * nx + x] = value;
        }
    }

    G_free(pos_arr);
    G_free(free_arr);
    G_free(reference);
    G_free(rand_arr);

    return;
}
