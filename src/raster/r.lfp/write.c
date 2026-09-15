#include <stdio.h>
#include <grass/gis.h>
#include <grass/vector.h>
#include <grass/dbmi.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include "global.h"

#define INDEX(row, col) ((size_t)(row) * dir_map->ncols + (col))
#define DIR(row, col)   dir_map->cells.byte[INDEX(row, col)]

static void add_table(struct Map_info *, const char *, dbDriver **,
                      struct field_info **);

void write_lfp(const char *lfp_name, const char *idcol,
               struct outlet_list *outlet_l, struct raster_map *dir_map)
{
    struct Map_info Map;
    dbDriver *driver = NULL;
    struct field_info *Fi = NULL;
    dbString sql;
    struct Cell_head window;
    struct point_list pl;
    struct line_pnts *Points;
    struct line_cats *Cats;
    int cat;
    int i;

    if (Vect_open_new(&Map, lfp_name, 0) < 0)
        G_fatal_error(_("Unable to create vector map <%s>"), lfp_name);

    Vect_set_map_name(&Map, _("Longest flow paths"));
    Vect_hist_command(&Map);

    if (idcol) {
        add_table(&Map, idcol, &driver, &Fi);
        db_init_string(&sql);
    }

    G_get_set_window(&window);

    init_point_list(&pl);

    Points = Vect_new_line_struct();
    Cats = Vect_new_cats_struct();

    cat = 1;
    for (i = 0; i < outlet_l->n; i++) {
        int npnts = outlet_l->northo[i] + outlet_l->ndia[i] + 1;
        int j;

        G_percent(i, outlet_l->n, 1);

        for (j = 0; j < outlet_l->head_pl[i].n; j++) {
            int row = outlet_l->head_pl[i].row[j];
            int col = outlet_l->head_pl[i].col[j];
            int pnt = 0;

            reset_point_list(&pl);

            do {
                int dir;
                double x = Rast_col_to_easting(col + 0.5, &window);
                double y = Rast_row_to_northing(row + 0.5, &window);

                add_point_xy(&pl, x, y);

                switch ((dir = DIR(row, col))) {
                case NE:
                    row--;
                    col++;
                    break;
                case N:
                    row--;
                    break;
                case NW:
                    row--;
                    col--;
                    break;
                case W:
                    col--;
                    break;
                case SW:
                    row++;
                    col--;
                    break;
                case S:
                    row++;
                    break;
                case SE:
                    row++;
                    col++;
                    break;
                case E:
                    col++;
                    break;
                }
            } while (++pnt < npnts);

            Vect_reset_line(Points);
            Vect_copy_xyz_to_pnts(Points, pl.x, pl.y, NULL, pl.n);

            Vect_reset_cats(Cats);
            Vect_cat_set(Cats, 1, cat);
            Vect_write_line(&Map, GV_LINE, Points, Cats);

            if (idcol) {
                char *buf;

                G_asprintf(&buf, "insert into %s (%s, %s) values (%d, %d)",
                           Fi->table, Fi->key, idcol, cat, outlet_l->id[i]);
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

    Vect_destroy_line_struct(Points);
    Vect_destroy_cats_struct(Cats);

    if (!Vect_build(&Map))
        G_warning(_("Unable to build topology for vector map <%s>"), lfp_name);

    Vect_close(&Map);

    if (driver) {
        db_commit_transaction(driver);
        db_close_database_shutdown_driver(driver);
    }
}

void write_head_points(const char *heads_name, const char *idcol,
                       struct outlet_list *outlet_l)
{
    struct Map_info Map;
    dbDriver *driver = NULL;
    struct field_info *Fi = NULL;
    dbString sql;
    struct Cell_head window;
    struct line_pnts *Points;
    struct line_cats *Cats;
    int cat;
    int i;

    if (Vect_open_new(&Map, heads_name, 0) < 0)
        G_fatal_error(_("Unable to create vector map <%s>"), heads_name);

    Vect_set_map_name(&Map, _("Longest flow path heads"));
    Vect_hist_command(&Map);

    if (idcol) {
        add_table(&Map, idcol, &driver, &Fi);
        db_init_string(&sql);
    }

    G_get_set_window(&window);

    Points = Vect_new_line_struct();
    Cats = Vect_new_cats_struct();

    cat = 1;
    for (i = 0; i < outlet_l->n; i++) {
        int j;

        for (j = 0; j < outlet_l->head_pl[i].n; j++) {
            double x =
                Rast_col_to_easting(outlet_l->head_pl[i].col[j] + 0.5, &window);
            double y = Rast_row_to_northing(outlet_l->head_pl[i].row[j] + 0.5,
                                            &window);

            Vect_reset_line(Points);
            Vect_append_point(Points, x, y, 0);

            Vect_reset_cats(Cats);
            Vect_cat_set(Cats, 1, cat);
            Vect_write_line(&Map, GV_POINT, Points, Cats);

            if (idcol) {
                char *buf;

                G_asprintf(&buf, "insert into %s (%s, %s) values (%d, %d)",
                           Fi->table, Fi->key, idcol, cat, outlet_l->id[i]);
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

    Vect_destroy_line_struct(Points);
    Vect_destroy_cats_struct(Cats);

    if (!Vect_build(&Map))
        G_warning(_("Unable to build topology for vector map <%s>"),
                  heads_name);

    Vect_close(&Map);

    if (driver) {
        db_commit_transaction(driver);
        db_close_database_shutdown_driver(driver);
    }
}

void write_head_coors(const char *coors_path, const char *idcol,
                      struct outlet_list *outlet_l)
{
    FILE *fp;
    struct Cell_head window;
    int i;

    if (!(fp = fopen(coors_path, "w")))
        G_fatal_error(_("Unable to create file <%s>"), coors_path);

    fprintf(fp, "%s,lfp_id,x,y,row,column,length\n", idcol);

    G_get_set_window(&window);

    for (i = 0; i < outlet_l->n; i++) {
        int j;

        for (j = 0; j < outlet_l->head_pl[i].n; j++) {
            int row = outlet_l->head_pl[i].row[j];
            int col = outlet_l->head_pl[i].col[j];
            double x = Rast_col_to_easting(col + 0.5, &window);
            double y = Rast_row_to_northing(row + 0.5, &window);

            fprintf(fp, "%d,%d,%f,%f,%d,%d,%f\n", outlet_l->id[i], j + 1, x, y,
                    row, col, outlet_l->lflen[i]);
        }
    }

    fclose(fp);
}

static void add_table(struct Map_info *Map, const char *idcol,
                      dbDriver **pdriver, struct field_info **pFi)
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
