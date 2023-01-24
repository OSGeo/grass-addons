#include "local_proto.h"

void valmap_output(int nrows, int ncols)
{
    int out_fd;
    int row;
    DCELL *result;

    result = (DCELL *)Rast_allocate_c_buf();

    /* write output */
    /* open the new cellfile  */
    out_fd = Rast_open_new("test_valmap", DCELL_TYPE);
    if (out_fd < 0) {
        G_fatal_error(_("can't create new cell file test_valmap\n"));
        exit(EXIT_FAILURE);
    }

    /* write the output file */

    for (row = 0; row < nrows; row++) {
        Rast_put_d_row(out_fd, &valmap[row * ncols]);
    }

    G_free(result);
}

/* find one contour strting at the given cell poition */
Position *find_contour(int *flagbuf, Position start, int dirx, int diry,
                       int nrows, int ncols, Position *list, int patch)
{
    /* start with the given cell */
    int x = start.x;
    int y = start.y;
    int dx = dirx;
    int dy = diry;
    int curpos = 0;

    list[curpos].x = x;
    list[curpos].y = y;

    while (1) { /* sorry for this while(true) loop */
        x += dx;
        y += dy;

        if (x >= 0 && x < ncols && y >= 0 && y < nrows) {
            if (flagbuf[y * ncols + x] == patch + 1) {
                /* a patch cell is encountered */
                int tmp;

                /* if it is not the current cell again */
                if (!(x == list[curpos].x && y == list[curpos].y)) {
                    /* test if this cell is the first one again */
                    if (x == start.x && y == start.y) {
                        /* if the entry vector is the opposite of the initial
                           exit vector then end search */
                        if (dx == -dirx && dy == -diry) {
                            break;
                        }
                    }
                    else {
                        /* new border cell found */
                        curpos++;
                        list[curpos].x = x;
                        list[curpos].y = y;
                    }
                }

                /* step back */
                x -= dx;
                y -= dy;

                /* turn left */
                tmp = dx;

                dx = dy;
                dy = -tmp;
            }
            else {
                /* a non-patch cell is encountered */
                /* turn right */
                int tmp = dx;

                dx = -dy;
                dy = tmp;

                /* mark this cell as visited */
                if (flagbuf[y * ncols + x] == 0) {
                    flagbuf[y * ncols + x] = -1;
                }
            }
        }
        else {
            /* a cell out of range is encountered */
            /* turn right */
            int tmp = dx;

            dx = -dy;
            dy = tmp;
        }
    } /* while(1) */

    /* adjust the patch border references */
    curpos++;

    return list + curpos;
}

/* find borders of a patch and sort cells accordingly */
void find_borders_patch(int *flagbuf, int patch, int nrows, int ncols)
{
    /* copy border cells into a separate border array */
    int cell_count = fragments[patch + 1] - fragments[patch];
    Position *border;
    PatchBorderList *list;
    int border_count = 0;
    Coords *p;
    int i;
    int curpos = 0;
    int first;
    int dx = 0;
    int dy = -1;

    border = G_malloc(cell_count * 2 * sizeof(Position));

    for (p = fragments[patch]; p < fragments[patch + 1]; p++) {
        if (p->neighbors < 4) {
            border[border_count].x = p->x;
            border[border_count].y = p->y;
            border_count++;
        }
    }

    /* test output */

    /*fprintf(stderr, "Border cells for patch %d:", patch);
       for(i = 0; i < border_count; i++) {
       fprintf(stderr, " (%d,%d)", border[i].x, border[i].y);
       }
       fprintf(stderr, "\n"); */

    /* G_message("Allocating for patch %d, border_count = %d", patch,
     * border_count); */

    /* initialize current patch border list */
    list = patch_borders + patch;

    list->positions = (Position *)G_malloc(2 * border_count * sizeof(Position));
    list->borders =
        (Position **)G_malloc((border_count + 1) * sizeof(Position *));
    list->borders[0] = list->positions;
    list->count = 0;

    /* if this is a 1-cell-patch then return here */
    if (cell_count == 1) {
        list->positions[0] = border[0];
        list->borders[1] = list->borders[0] + 1;
        list->count = 1;
        return;
    }

    /* find the top-left border cell */

    for (first = i = curpos; i < border_count; i++) {
        if (border[i].y < border[first].y ||
            (border[i].y == border[first].y && border[i].x < border[first].x)) {
            first = i;
        }
    }

    /* G_message("top-left border cell: (%d,%d)", border[first].x,
     * border[first].y); */

    /* set direction for the first run */

    /* repeat until all borders have been found */
    do {
        int pos;

        /* find next contour */
        list->borders[list->count + 1] =
            find_contour(flagbuf, border[first], dx, dy, nrows, ncols,
                         list->borders[list->count], patch);

        list->count++;

        /*G_message("Flagbuf:");
           int fx, fy;
           for(fy = 13; fy < 17; fy++) {
           for(fx = 30; fx < 40; fx++) {
           if(flagbuf[fy * ncols + fx] >= 0) {
           fprintf(stderr, "%x", flagbuf[fy * ncols + fx]);
           } else {
           fprintf(stderr, "*");
           }
           }
           fprintf(stderr, "\n");
           } */

        /*              G_message("Found contour:");
           Position *p;
           for(p = list->borders[list->count - 1]; p <
           list->borders[list->count]; p++) { fprintf(stderr, "(%d,%d) ", p->x,
           p->y);
           }
           fprintf(stderr, "\n"); */

        /* find a border cell which still has at least one unvisited empty
         * neighbor */
        first = -1;

        for (pos = 0; pos < border_count; pos++) {
            Position *pt = border + pos;

            int nx, ny; /* neighbor */
            int x = pt->x;
            int y = pt->y;

            /* test right neighbor */
            nx = x + 1;
            ny = y;
            if (nx >= 0 && nx < ncols && ny >= 0 && ny < nrows &&
                flagbuf[ny * ncols + nx] == 0) {
                first = pos;
                dx = nx - x;
                dy = ny - y;
                break;
            }
            /* test left neighbor */
            nx = x - 1;
            ny = y;
            if (nx >= 0 && nx < ncols && ny >= 0 && ny < nrows &&
                flagbuf[ny * ncols + nx] == 0) {
                first = pos;
                dx = nx - x;
                dy = ny - y;
                break;
            }
            /* test top neighbor */
            nx = x;
            ny = y + 1;
            if (nx >= 0 && nx < ncols && ny >= 0 && ny < nrows &&
                flagbuf[ny * ncols + nx] == 0) {
                first = pos;
                dx = nx - x;
                dy = ny - y;
                break;
            }
            /* test bottom neighbor */
            nx = x;
            ny = y - 1;
            if (nx >= 0 && nx < ncols && ny >= 0 && ny < nrows &&
                flagbuf[ny * ncols + nx] == 0) {
                first = pos;
                dx = nx - x;
                dy = ny - y;
                break;
            }
        }

        /*if(first >= 0) {
           G_message("Another contour starting at: (%d,%d), dir: (%d,%d)",
           border[first].x, border[first].y, dx, dy);
           } */
    } while (first >= 0 && list->count < 3);
}

/* find borders of all patches and sort cells accordingly */
void find_borders(int *flagbuf, int nrows, int ncols, int fragcount)
{
    int i;

    for (i = 0; i < fragcount; i++) {
        /*
        for(i = 10; i < 11; i++)
        G_message("Border %d", i);
        */
        find_borders_patch(flagbuf, i, nrows, ncols);

        G_percent(i + 1, fragcount, 1);
        /*G_message("%d of %d", i, fragcount); */
    }

    /* valmap_output(); */
}

/* gets normal to the patch border in the given cell's position */
Vector2 normal(int patch, int border_index, int cell)
{
    PatchBorderList list = patch_borders[patch];
    Position *border = list.borders[border_index];
    int cell_count =
        list.borders[border_index + 1] - list.borders[border_index];
    Position cell1, cell2, cell3;
    int dx1, dy1, dx2, dy2;
    double l;
    Vector2 res = {1.0, 0.0};

    /* G_message("Enter: patch = %d, cell_cnt = %d", patch, cell_count); */

    /* handle 1-pixel patches separately */
    if (cell_count <= 1) {
        return res;
    }

    /*    G_message("first cells: (%d, %d)", border[0].x, border[0].y); */

    /* get three consequtive cells */
    cell1 = border[((cell - 1) + cell_count) % cell_count];
    cell2 = border[cell];
    cell3 = border[(cell + 1) % cell_count];

    dx1 = cell2.x - cell1.x;
    dy1 = cell2.y - cell1.y;
    dx2 = cell3.x - cell2.x;
    dy2 = cell3.y - cell2.y;

    res.x = 0.5 * (dy1 + dy2);
    res.y = -0.5 * (dx1 + dx2);

    if (res.x == 0 && res.y == 0) {
        res.x = dx1;
        res.y = dy1;
    }

    /* normalize resulting vector */
    l = sqrt(res.x * res.x + res.y * res.y);

    res.x /= l;
    res.y /= l;

    return res;
}

/* returns a value from the cost map */
DCELL get_cost_value(int x, int y, int nrows, int ncols)
{
    if (x >= 0 && x < ncols && y >= 0 && y < nrows) {
        return map[y * ncols + x];
    }
    else {
        return -1.0;
    }
}

/* gets an array with values of the cost matrix cells in the range of the effect
 * cone of */
/* the given cell with the given normal */
int get_cost_values(DCELL *res, Position cell, Vector2 n, double distance,
                    double angle, double weight_param, int nrows, int ncols)
{
    int d = (int)distance;
    double ref = cos(0.5 * angle);

    /* fprintf(stderr, "Cell (%d, %d): ", cell.x, cell.y); */

    int x, y;
    int count = 0;

    for (x = cell.x - d; x <= cell.x + d; x++) {
        for (y = cell.y - d; y <= cell.y + d; y++) {
            /* test if position is in the effect cone */
            double dx = x - cell.x;
            double dy = y - cell.y;
            double l = sqrt(dx * dx + dy * dy);

            double angcos = (dx * n.x + dy * n.y) / l;

            DCELL val = get_cost_value(x, y, nrows, ncols);

            if (angcos >= ref && l <= distance && val >= 0) {
                /* incorporate distance */
                if (weight_param < MAX_DOUBLE) {
                    /* use l-1 as 1 is the smallest possible distance between
                     * two pixels */
                    val *= 1.0 - pow((l - 1.0) / distance, weight_param);
                }

                res[count] = val;
                count++;

                /* fprintf(stderr, "%0.2f ", val); */
            }
        }
    }

    /* fprintf(stderr, "\n"); */

    return count;
}

/* initializes border cell values for propagation */
void init_border_values(double distance, double angle, int buffer,
                        f_statmethod stat, double dist_weight, int nrows,
                        int ncols, int fragcount)
{
    int patch;
    int size = (int)distance * 2 + 1;
    DCELL *cost_values;
    double weight_param;

    size *= size;
    cost_values = (DCELL *)G_malloc(size * sizeof(DCELL));

    weight_param = tan(dist_weight * 0.5 * M_PI);

    for (patch = 0; patch < fragcount; patch++) {
        PatchBorderList list = patch_borders[patch];

        int contour;

        for (contour = 0; contour < list.count; contour++) {
            int cell;
            Position *p;

            for (p = list.borders[contour], cell = 0;
                 p < list.borders[contour + 1]; p++, cell++) {
                Vector2 n = normal(patch, contour, cell);

                int border_count =
                    list.borders[contour + 1] - list.borders[contour];

                int count, value;
                DCELL *buf;

                if (border_count == 1) {
                    count =
                        get_cost_values(cost_values, *p, n, distance, 2 * M_PI,
                                        weight_param, nrows, ncols);
                }
                else {
                    count = get_cost_values(cost_values, *p, n, distance, angle,
                                            weight_param, nrows, ncols);
                }

                value = Round(stat(cost_values, count) * (DCELL)buffer);

                buf = &valmap[p->y * ncols + p->x];

                if (*buf >= 0 && *buf < value) {
                    *buf = value;
                }

                /* G_message("Value for (%d, %d) = %d", p->x, p->y, value); */

                /* G_message("Normal to (%d, %d) is (%0.2f, %0.2f)", p->x, p->y,
                 * n.x, n.y); */
            }
        }
    }

    /*fprintf(stderr, "VALMAP:\n");
       int i, j;
       for(j = 0; j < nrows; j++) {
       for(i = 0; i < ncols; i++) {
       fprintf(stderr, "%03d ", (int)valmap[j * ncols + i]);
       }
       fprintf(stderr, "\n");
       } */

    G_free(cost_values);
}

int get_neighbors(Position *res, int x, int y, int nx, int ny, int nbr_cnt)
{
    int left, right, top, bottom;
    int i, j;
    int cnt = 0;

    switch (nbr_cnt) {
    case 4: /* von Neumann neighborhood */
        if (x > 0 && valmap[y * nx + x - 1] >= 0.0) {
            res[cnt].x = x - 1;
            res[cnt].y = y;
            cnt++;
        }
        if (y > 0 && valmap[(y - 1) * nx + x] >= 0.0) {
            res[cnt].x = x;
            res[cnt].y = y - 1;
            cnt++;
        }
        if (x < nx - 1 && valmap[y * nx + x + 1] >= 0.0) {
            res[cnt].x = x + 1;
            res[cnt].y = y;
            cnt++;
        }
        if (y < ny - 1 && valmap[(y + 1) * nx + x] >= 0.0) {
            res[cnt].x = x;
            res[cnt].y = y + 1;
            cnt++;
        }
        break;

    case 8: /* Moore neighborhood */
        left = x > 0 ? x - 1 : 0;
        top = y > 0 ? y - 1 : 0;
        right = x < nx - 1 ? x + 1 : nx - 1;
        bottom = y < ny - 1 ? y + 1 : ny - 1;
        for (i = left; i <= right; i++) {
            for (j = top; j <= bottom; j++) {
                if (!(i == x && j == y) && valmap[j * nx + i] >= 0.0) {
                    res[cnt].x = i;
                    res[cnt].y = j;
                    cnt++;
                }
            }
        }
        break;
    }

    return cnt;
}

/* propagates border values of a patch with a linear decrease */
void propagate_patch(int patch, int neighbor_count, f_propmethod prop_method,
                     int nrows, int ncols)
{
    Position *nbr_list =
        (Position *)G_malloc(neighbor_count * sizeof(Position));
    int cell_count = fragments[patch + 1] - fragments[patch];
    Position *stack = (Position *)G_malloc(2 * cell_count * sizeof(Position));
    Position *top = stack;

    /* put all border cells on the stack */
    Coords *p;

    for (p = fragments[patch]; p < fragments[patch + 1]; p++) {
        if (valmap[p->y * ncols + p->x] > 0.0) {
            top->x = p->x;
            top->y = p->y;
            top++;
        }
    }

    /* propagate values */
    while (top > stack) {
        int x, y;
        DCELL value;
        int nbr_cnt, i;

        /* pop from stack */
        top--;
        x = top->x;
        y = top->y;
        value = valmap[y * ncols + x];

        /* get neighbors */
        nbr_cnt = get_neighbors(nbr_list, x, y, ncols, nrows, neighbor_count);

        /* for each neighbor */
        for (i = 0; i < nbr_cnt; i++) {
            DCELL nbr_val, pass_val;

            x = nbr_list[i].x;
            y = nbr_list[i].y;
            nbr_val = valmap[y * ncols + x];

            pass_val = prop_method(value, propmap[y * ncols + x]);

            if (pass_val > nbr_val) {
                /* pass value and push neighbor on stack */
                valmap[y * ncols + x] = pass_val;
                *top = nbr_list[i];
                top++;
            }
        }
    }

    G_free(stack);
    G_free(nbr_list);
}

/* propagates border values with a linear decrease */
void propagate(int neighbor_count, f_propmethod prop_method, int nrows,
               int ncols, int fragcount)
{
    int patch;

    G_message("Propagating Values ...");

    for (patch = 0; patch < fragcount; patch++) {
        propagate_patch(patch, neighbor_count, prop_method, nrows, ncols);

        G_percent(patch + 1, fragcount, 1);
    }
}
