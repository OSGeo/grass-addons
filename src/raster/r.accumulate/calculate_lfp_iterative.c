#include <math.h>
#include <grass/gis.h>
#include <grass/vector.h>
#include <grass/dbmi.h>
#include <grass/glocale.h>
#include "global.h"

struct neighbor {
    int row;
    int col;
    double accum;
    double down_length;
    double min_length;
    double max_length;
};

struct neighbor_stack {
    struct neighbor *accum;
    int n;
    int nalloc;
};

struct headwater_list {
    struct neighbor *head;
    int n;
    int nalloc;
};

static struct Cell_head window;
static int nrows, ncols;
static double diag_length;
static double cell_area;

static void add_table(struct Map_info *, char *, dbDriver **,
                      struct field_info **);
static void trace_up(struct cell_map *, struct raster_map *, int, int,
                     struct line_list *);
static void find_up(struct cell_map *, struct raster_map *, int, int, double,
                    double, struct neighbor *, int *, struct headwater_list *);
static void init_up_stack(struct neighbor_stack *);
static void free_up_stack(struct neighbor_stack *);
static void push_up(struct neighbor_stack *, struct neighbor *);
static struct neighbor pop_up(struct neighbor_stack *);
static void init_headwater_list(struct headwater_list *);
static void free_headwater_list(struct headwater_list *);
static void add_headwater(struct headwater_list *, struct neighbor *);
static int compare_neighbor_max_length(const void *, const void *);

void calculate_lfp_iterative(struct Map_info *Map, struct cell_map *dir_buf,
                             struct raster_map *accum_buf, int *id, char *idcol,
                             struct point_list *outlet_pl)
{
    struct line_list ll;
    struct line_cats *Cats;
    int i, cat;
    dbDriver *driver = NULL;
    struct field_info *Fi = NULL;
    dbString sql;

    if (idcol) {
        add_table(Map, idcol, &driver, &Fi);
        db_init_string(&sql);
    }

    G_get_set_window(&window);

    nrows = dir_buf->nrows;
    ncols = dir_buf->ncols;
    diag_length = sqrt(pow(window.ew_res, 2.0) + pow(window.ns_res, 2.0));
    cell_area = window.ew_res * window.ns_res;

    init_line_list(&ll);

    Cats = Vect_new_cats_struct();

    /* loop through all outlets and find the longest flow path for each */
    cat = 1;
    G_message(_("Calculating longest flow paths iteratively..."));
#pragma omp parallel for schedule(dynamic) private(j)
    for (i = 0; i < outlet_pl->n; i++) {
        int row = (int)Rast_northing_to_row(outlet_pl->y[i], &window);
        int col = (int)Rast_easting_to_col(outlet_pl->x[i], &window);
        int j;

        G_percent(i, outlet_pl->n, 1);

        /* if the outlet is outside the computational region, skip */
        if (row < 0 || row >= nrows || col < 0 || col >= ncols) {
            G_warning(_("Skip outlet (%f, %f) outside the current region"),
                      outlet_pl->x[i], outlet_pl->y[i]);
            continue;
        }

        reset_line_list(&ll);

        /* trace up flow accumulation */
        trace_up(dir_buf, accum_buf, row, col, &ll);

        if (!ll.n) {
            if (idcol)
                G_fatal_error(_("Failed to calculate the longest flow path for "
                                "outlet %s=%d"),
                              idcol, id[i]);
            else
                G_fatal_error(_("Failed to calculate the longest flow path for "
                                "outlet at (%f, %f)"),
                              outlet_pl->x[i], outlet_pl->y[i]);
        }

        /* write out longest flow paths */
        for (j = 0; j < ll.n; j++) {
            Vect_reset_cats(Cats);

            Vect_cat_set(Cats, 1, cat);
            Vect_write_line(Map, GV_LINE, ll.lines[j]->Points, Cats);

            if (idcol) {
                char *buf;

                G_asprintf(&buf, "insert into %s (%s, %s) values (%d, %d)",
                           Fi->table, Fi->key, idcol, cat, id[i]);
                db_set_string(&sql, buf);

                if (db_execute_immediate(driver, &sql) != DB_OK)
                    G_fatal_error(_("Unable to create table: %s"),
                                  db_get_string(&sql));
                db_free_string(&sql);
            }

            cat++;
        }
    }
    G_percent(1, 1, 1);

    free_line_list(&ll);

    Vect_destroy_cats_struct(Cats);

    if (driver) {
        db_commit_transaction(driver);
        db_close_database_shutdown_driver(driver);
    }
}

static void add_table(struct Map_info *Map, char *idcol, dbDriver **pdriver,
                      struct field_info **pFi)
{
    dbDriver *driver;
    struct field_info *Fi;
    char *buf;
    dbString sql;

    Fi = Vect_default_field_info(Map, 1, NULL, GV_1TABLE);

    driver = db_start_driver_open_database(Fi->driver,
                                           Vect_subst_var(Fi->database, Map));
    db_set_error_handler_driver(driver);
    db_begin_transaction(driver);

    if (!driver)
        G_fatal_error(_("Unable to open database <%s> by driver <%s>"),
                      Fi->database, Fi->driver);

    G_asprintf(&buf, "create table %s (%s integer, %s integer)", Fi->table,
               Fi->key, idcol);
    db_init_string(&sql);
    db_set_string(&sql, buf);

    if (db_execute_immediate(driver, &sql) != DB_OK)
        G_fatal_error(_("Unable to create table: %s"), db_get_string(&sql));
    db_free_string(&sql);

    if (db_grant_on_table(driver, Fi->table, DB_PRIV_SELECT,
                          DB_GROUP | DB_PUBLIC) != DB_OK)
        G_fatal_error(_("Unable to grant privileges on table <%s>"), Fi->table);

    if (Vect_map_add_dblink(Map, 1, NULL, Fi->table, GV_KEY_COLUMN,
                            Fi->database, Fi->driver))
        G_fatal_error(_("Unable to add database link for vector map <%s>"),
                      Vect_get_full_name(Map));

    *pdriver = driver;
    *pFi = Fi;
}

static void trace_up(struct cell_map *dir_buf, struct raster_map *accum_buf,
                     int row, int col, struct line_list *ll)
{
    double cur_acc;
    int i, nup;
    struct neighbor up[8];
    struct neighbor_stack up_stack;
    struct headwater_list hl;
    struct point_list pl;

    /* if the current cell is outside the computational region, stop tracing */
    if (row < 0 || row >= nrows || col < 0 || col >= ncols)
        return;

    /* if the current accumulation is 1 (headwater), stop tracing */
    cur_acc = get(accum_buf, row, col);
    if (cur_acc == 1)
        return;

    init_headwater_list(&hl);

    find_up(dir_buf, accum_buf, row, col, cur_acc, 0, up, &nup, &hl);

    /* if a headwater cell is found, stop tracing */
    if (!nup)
        return;

    init_up_stack(&up_stack);

    /* push upstream cells */
    for (i = nup - 1; i >= 0; i--)
        push_up(&up_stack, &up[i]);

    do {
        /* pop one upstream cell */
        struct neighbor cur_up = pop_up(&up_stack);

        /* find its upstream cells */
        find_up(dir_buf, accum_buf, cur_up.row, cur_up.col, cur_up.accum,
                cur_up.down_length, up, &nup, &hl);
        if (nup) {
            /* push its upstream cells */
            for (i = nup - 1; i >= 0; i--)
                push_up(&up_stack, &up[i]);
        }
        else {
            /* headwater cell */
            if (!hl.n || cur_up.down_length == hl.head[0].down_length)
                /* if first or tie, add it */
                add_headwater(&hl, &cur_up);
            else if (cur_up.down_length > hl.head[0].down_length) {
                /* if longer than existing, replace */
                hl.n = 1;
                hl.head[0] = cur_up;
            }
        }
    } while (up_stack.n);

    free_up_stack(&up_stack);

    init_point_list(&pl);
#pragma omp parallel for schedule(dynamic) private(i)
    for (i = 0; i < hl.n; i++) {
        int r = hl.head[i].row;
        int c = hl.head[i].col;
        struct line *line;
        double x, y;

        reset_point_list(&pl);

        do {
            int dir = dir_buf->c[r][c];

            x = Rast_col_to_easting(c + 0.5, &window);
            y = Rast_row_to_northing(r + 0.5, &window);
            add_point(&pl, x, y);

            if (dir == NW || dir == N || dir == NE)
                r--;
            else if (dir == SW || dir == S || dir == SE)
                r++;
            if (dir == NW || dir == W || dir == SW)
                c--;
            else if (dir == NE || dir == E || dir == SE)
                c++;
        } while (row != r || col != c);

        x = Rast_col_to_easting(c + 0.5, &window);
        y = Rast_row_to_northing(r + 0.5, &window);
        add_point(&pl, x, y);

        line = (struct line *)G_malloc(sizeof(struct line));
        line->Points = Vect_new_line_struct();
        Vect_copy_xyz_to_pnts(line->Points, pl.x, pl.y, NULL, pl.n);
        line->length = Vect_line_length(line->Points);
        add_line(ll, line);
    }

    free_point_list(&pl);
    free_headwater_list(&hl);
}

static void find_up(struct cell_map *dir_buf, struct raster_map *accum_buf,
                    int row, int col, double cur_acc, double down_length,
                    struct neighbor *up, int *nup, struct headwater_list *hl)
{
    int i, j;

    *nup = 0;
    for (i = -1; i <= 1; i++) {
        /* skip edge cells */
        if (row + i < 0 || row + i >= nrows)
            continue;

        for (j = -1; j <= 1; j++) {
            /* skip the current and edge cells */
            if ((i == 0 && j == 0) || col + j < 0 || col + j >= ncols)
                continue;

            /* if a neighbor cell flows into the current cell with no flow
             * loop, store its accumulation in the accum array */
            if (dir_buf->c[row + i][col + j] == dir_checks[i + 1][j + 1][0] &&
                dir_buf->c[row][col] != dir_checks[i + 1][j + 1][1]) {
                double up_acc = get(accum_buf, row + i, col + j);

                /* upstream accumulation must always be less than the current
                 * accumulation; upstream accumulation can be greater than the
                 * current accumulation in a subaccumulation raster */
                if (up_acc < cur_acc) {
                    /* diagonal if i * j == -1 or 1
                     * horizontal if i == 0
                     * vertical if j == 0 */
                    double length =
                        down_length +
                        (i && j ? diag_length
                                : (i ? window.ns_res : window.ew_res));

                    up[*nup].row = row + i;
                    up[*nup].col = col + j;
                    up[*nup].accum = up_acc;
                    /* current length */
                    up[*nup].down_length = length;
                    /* theoretically, the shortest longest flow path is when
                     * all accumulated upstream cells form a square */
                    up[*nup].min_length = length + sqrt(cell_area * up_acc);
                    /* the current upstream cell's downstream length +
                     * theoretical longest upstream length; theoretically, the
                     * longest longest flow path is when all accumulated
                     * upstream cells are diagonally flowing */
                    up[*nup].max_length = length + diag_length * up_acc;
                    (*nup)++;
                }
            }
        }
    }

    if (*nup > 1) {
        /* sort upstream cells by max_length in descending order */
        qsort(up, *nup, sizeof(struct neighbor), compare_neighbor_max_length);

        /* theoretically, the longest longest flow path is when all accumulated
         * upstream cells are diagonally flowing; only keep cells whose
         * theoretical longest upstream length is greater than or equal to the
         * first cell's theoretical shortest upstream length */
        for (i = 1; i < *nup && up[i].max_length >= up[0].min_length; i++)
            ;
        *nup = i;
    }

    if (hl->n) {
        for (i = 0; i < *nup; i++) {
            /* if the current cell's theoretical longest lfp < all existing,
             * skip tracing because it's impossible to obtain a longer lfp */
            for (j = 0; j < hl->n && up[i].max_length < hl->head[j].down_length;
                 j++)
                ;

            if (j == hl->n)
                break;
        }
        *nup = i;
    }
}

static void init_up_stack(struct neighbor_stack *up_stack)
{
    up_stack->nalloc = up_stack->n = 0;
    up_stack->accum = NULL;
}

static void free_up_stack(struct neighbor_stack *up_stack)
{
    if (up_stack->accum)
        G_free(up_stack->accum);
    init_up_stack(up_stack);
}

static void push_up(struct neighbor_stack *up_stack, struct neighbor *up)
{
    if (up_stack->n == up_stack->nalloc) {
        up_stack->nalloc += REALLOC_INCREMENT;
        up_stack->accum = (struct neighbor *)G_realloc(
            up_stack->accum, up_stack->nalloc * sizeof(struct neighbor));
    }
    up_stack->accum[up_stack->n++] = *up;
}

static struct neighbor pop_up(struct neighbor_stack *up_stack)
{
    struct neighbor up;

    if (up_stack->n > 0) {
        up = up_stack->accum[--up_stack->n];
        if (up_stack->n == up_stack->nalloc - REALLOC_INCREMENT) {
            up_stack->nalloc -= REALLOC_INCREMENT;
            up_stack->accum = (struct neighbor *)G_realloc(
                up_stack->accum, up_stack->nalloc * sizeof(struct neighbor));
        }
    }

    return up;
}

static void init_headwater_list(struct headwater_list *hl)
{
    hl->nalloc = hl->n = 0;
    hl->head = NULL;
}

static void free_headwater_list(struct headwater_list *hl)
{
    if (hl->head)
        G_free(hl->head);
    init_headwater_list(hl);
}

static void add_headwater(struct headwater_list *hl, struct neighbor *h)
{
    if (hl->n == hl->nalloc) {
        hl->nalloc += REALLOC_INCREMENT;
        hl->head = (struct neighbor *)G_realloc(
            hl->head, hl->nalloc * sizeof(struct neighbor));
        if (!hl->head)
            G_fatal_error(_("Unable to increase headwater list"));
    }
    hl->head[hl->n++] = *h;
}

static int compare_neighbor_max_length(const void *a, const void *b)
{
    const struct neighbor *ap = (const struct neighbor *)a;
    const struct neighbor *bp = (const struct neighbor *)b;
    const double diff = bp->max_length - ap->max_length;

    /* descending by max_length */
    return diff < 0 ? -1 : diff > 0;
}
