#include <math.h>
#include <grass/gis.h>
#include <grass/vector.h>
#include <grass/dbmi.h>
#include <grass/glocale.h>
#include "global.h"

struct neighbor_accum
{
    int row;
    int col;
    int accum;
};

static void add_table(struct Map_info *, char *, dbDriver **,
                      struct field_info **);
static int trace_up(struct cell_map *, struct raster_map *,
                    struct Cell_head *, int, int, struct point_list *,
                    struct line_list *);
static int compare_neighbor_accum(const void *, const void *);
static int compare_line(const void *, const void *);

void calculate_lfp(struct Map_info *Map, struct cell_map *dir_buf,
                   struct raster_map *accum_buf, int *id, char *idcol,
                   struct point_list *outlet_pl)
{
    struct Cell_head window;
    int rows = accum_buf->rows, cols = accum_buf->cols;
    struct point_list pl;
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

    init_point_list(&pl);
    init_line_list(&ll);

    Cats = Vect_new_cats_struct();

    /* loop through all outlets and find the longest flow path for each */
    cat = 1;
    G_message(_("Calculating longest flow path..."));
    for (i = 0; i < outlet_pl->n; i++) {
        int row = (int)Rast_northing_to_row(outlet_pl->y[i], &window);
        int col = (int)Rast_easting_to_col(outlet_pl->x[i], &window);
        int j;

        G_percent(i, outlet_pl->n, 1);

        /* if the outlet is outside the computational region, skip */
        if (row < 0 || row >= rows || col < 0 || col >= cols) {
            G_warning(_("Skip outlet (%f, %f) outside the current region"),
                      outlet_pl->x[i], outlet_pl->y[i]);
            continue;
        }

        /* trace up flow accumulation */
        reset_point_list(&pl);
        reset_line_list(&ll);

        trace_up(dir_buf, accum_buf, &window, row, col, &pl, &ll);

        if (!ll.n)
            G_fatal_error(_("Failed to calculate the longest flow path for outlet (%f, %f)"),
                          outlet_pl->x[i], outlet_pl->y[i]);

        /* sort lines by length in descending order */
        qsort(ll.lines, ll.n, sizeof(struct line *), compare_line);

        /* write out the longest flow path */
        for (j = 0; j < ll.n && ll.lines[j]->length == ll.lines[0]->length;
             j++) {
            Vect_reset_cats(Cats);

            Vect_cat_set(Cats, 1, cat);
            Vect_line_reverse(ll.lines[j]->Points);
            Vect_write_line(Map, GV_LINE, ll.lines[j]->Points, Cats);

            if (driver) {
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

    free_point_list(&pl);
    free_line_list(&ll);

    Vect_destroy_cats_struct(Cats);

    if (driver) {
        db_commit_transaction(driver);
        db_close_database_shutdown_driver(driver);
    }
}

static void add_table(struct Map_info *Map, char *idcol, dbDriver ** pdriver,
                      struct field_info **pFi)
{
    dbDriver *driver;
    struct field_info *Fi;
    char *buf;
    dbString sql;

    Fi = Vect_default_field_info(Map, 1, NULL, GV_1TABLE);

    driver =
        db_start_driver_open_database(Fi->driver,
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

    if (db_grant_on_table
        (driver, Fi->table, DB_PRIV_SELECT, DB_GROUP | DB_PUBLIC) != DB_OK)
        G_fatal_error(_("Unable to grant privileges on table <%s>"),
                      Fi->table);

    if (Vect_map_add_dblink
        (Map, 1, NULL, Fi->table, GV_KEY_COLUMN, Fi->database, Fi->driver))
        G_fatal_error(_("Unable to add database link for vector map <%s>"),
                      Vect_get_full_name(Map));

    *pdriver = driver;
    *pFi = Fi;
}

static int trace_up(struct cell_map *dir_buf, struct raster_map *accum_buf,
                    struct Cell_head *window, int row, int col,
                    struct point_list *pl, struct line_list *ll)
{
    static struct line_pnts *Points = NULL;
    static double diag_length;
    int rows = dir_buf->rows, cols = dir_buf->cols;
    double x, y;
    int i, j, nup;
    struct neighbor_accum up_accum[8];

    /* if the current cell is outside the computational region, stop tracing */
    if (row < 0 || row >= rows || col < 0 || col >= cols)
        return 1;

    /* add the current cell */
    x = Rast_col_to_easting(col + 0.5, window);
    y = Rast_row_to_northing(row + 0.5, window);
    add_point(pl, x, y);

    /* if the current accumulation is 1 (headwater), stop tracing */
    if (get(accum_buf, row, col) == 1)
        return 1;

    nup = 0;
    for (i = -1; i <= 1; i++) {
        /* skip edge cells */
        if (row + i < 0 || row + i >= rows)
            continue;

        for (j = -1; j <= 1; j++) {
            /* skip the current and edge cells */
            if ((i == 0 && j == 0) || col + j < 0 || col + j >= cols)
                continue;

            /* if a neighbor cell flows into the current cell, store its
             * accumulation in the accum array */
            if (dir_buf->c[row + i][col + j] == dir_checks[i + 1][j + 1][0]) {
                up_accum[nup].row = row + i;
                up_accum[nup].col = col + j;
                up_accum[nup++].accum = get(accum_buf, row + i, col + j);
            }
        }
    }

    if (!nup)
        G_fatal_error(_("No upstream cells found for a non-headwater cell at (%f, %f)"),
                      x, y);

    /* sort upstream cells by accumulation in descending order */
    qsort(up_accum, nup, sizeof(struct neighbor_accum),
          compare_neighbor_accum);

    if (!Points) {
        Points = Vect_new_line_struct();
        diag_length =
            sqrt(pow(window->ew_res, 2.0) + pow(window->ns_res, 2.0));
    }

    /* trace up upstream cells */
    for (i = 0; i < nup; i++) {
        /* store pl->n to come back later */
        int split_pl_n = pl->n;

        /* theoretically, the longest longest flow path is when all accumulated
         * upstream cells are diagonally flowing */
        double max_length = up_accum[i].accum * diag_length;

        /* skip the current cell if its theoretical longest upstream length is
         * shorter than the first cell's theoretical shortest upstream length
         */
        if (i > 0 && max_length < up_accum[0].accum)
            continue;

        /* if the current cell's theoretical longest lfp < all existing, skip
         * tracing because it's impossible to obtain a longer lfp */
        if (ll->n) {
            Vect_reset_line(Points);
            Vect_copy_xyz_to_pnts(Points, pl->x, pl->y, NULL, pl->n);

            /* the current cell's downstream length + theoretical longest
             * upstream length */
            max_length += Vect_line_length(Points);

            for (j = 0; j < ll->n && max_length < ll->lines[j]->length; j++) ;

            if (j == ll->n)
                continue;
        }

        /* if tracing is successful, store the line and its length */
        if (trace_up
            (dir_buf, accum_buf, window, up_accum[i].row, up_accum[i].col, pl,
             ll) && pl->n > 0) {
            static struct line *line;
            double length;

            Vect_reset_line(Points);
            Vect_copy_xyz_to_pnts(Points, pl->x, pl->y, NULL, pl->n);
            length = Vect_line_length(Points);

            for (j = 0; j < ll->n && length < ll->lines[j]->length; j++) ;

            /* if first or length >= any existing */
            if (!ll->n || j < ll->n) {
                if (!ll->n || length == ll->lines[j]->length) {
                    /* first or length == existing (tie); add new */
                    line = (struct line *)G_malloc(sizeof(struct line));
                    line->Points = Vect_new_line_struct();
                    add_line(ll, line);
                }
                else {
                    /* length > existing; replace existing */
                    line = ll->lines[j];
                    Vect_reset_line(line->Points);
                }
                Vect_copy_xyz_to_pnts(line->Points, pl->x, pl->y, NULL,
                                      pl->n);
                line->length = length;
            }
        }

        /* keep tracing if the next upstream cell has the same largest
         * accumulation */
        pl->n = split_pl_n;
    }

    return 0;
}

static int compare_neighbor_accum(const void *a, const void *b)
{
    const struct neighbor_accum *ap = (const struct neighbor_accum *)a;
    const struct neighbor_accum *bp = (const struct neighbor_accum *)b;

    /* descending by accum */
    return bp->accum - ap->accum;
}

static int compare_line(const void *a, const void *b)
{
    const struct line **ap = (const struct line **)a;
    const struct line **bp = (const struct line **)b;

    /* descending by length */
    if ((*ap)->length < (*bp)->length)
        return 1;
    if ((*ap)->length > (*bp)->length)
        return -1;
    return 0;
}
