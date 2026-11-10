#include <grass/dbmi.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/raster.h>
#include <grass/vector.h>

#include "global.h"

static struct Cell_head window;

struct outlet_list *read_outlets(char *outlets_name, char *layer, char *idcol,
                                 struct raster_map *dir_map, int find_full)
{
    struct outlet_list *outlets_l = G_malloc(sizeof *outlets_l);
    struct Map_info Map;
    dbDriver *driver = NULL;
    struct field_info *Fi;
    struct line_pnts *Points;
    struct line_cats *Cats;
    int field;
    int nlines, line;

    if (Vect_open_old2(&Map, outlets_name, "", layer) < 0)
        G_fatal_error(_("Unable to open vector map <%s>"), outlets_name);

    field = Vect_get_field_number(&Map, layer);

    /* avoid database queries for the default cat column; it's expensive */
    if (strcmp(idcol, GV_KEY_COLUMN) != 0) {
        Fi = Vect_get_field(&Map, field);
        if (!(driver = db_start_driver_open_database(
                  Fi->driver, Vect_subst_var(Fi->database, &Map))))
            G_fatal_error("Unable to start db driver");
        if (db_column_Ctype(driver, Fi->table, idcol) != DB_C_TYPE_INT)
            G_fatal_error(
                _("Column <%s> in vector map <%s> must be of integer type"),
                idcol, outlets_name);
    }

    G_get_set_window(&window);

    Points = Vect_new_line_struct();
    Cats = Vect_new_cats_struct();
    nlines = Vect_get_num_lines(&Map);

    init_outlet_list(outlets_l);

    for (line = 1; line <= nlines; line++) {
        int ltype, cat, id, row, col;

        G_percent(line, nlines, 1);

        ltype = Vect_read_line(&Map, Points, Cats, line);
        Vect_cat_get(Cats, field, &cat);

        if (ltype != GV_POINT || cat < 0)
            continue;

        row = (int)Rast_northing_to_row(Points->y[0], &window);
        col = (int)Rast_easting_to_col(Points->x[0], &window);

        /* if the outlet is outside the computational region, skip */
        if (row < 0 || row >= dir_map->nrows || col < 0 ||
            col >= dir_map->ncols) {
            G_message(_("Skip outlet (cat %d) at (%f, %f) outside the current "
                        "region"),
                      cat, Points->x[0], Points->y[0]);
            continue;
        }

        if (driver) {
            dbValue val;

            if (db_select_value(driver, Fi->table, Fi->key, cat, idcol, &val) <
                0)
                G_fatal_error(
                    _("Unable to read column <%s> in vector map <%s>"), idcol,
                    outlets_name);

            id = db_get_value_int(&val);
        }
        else
            id = cat;

        add_outlet(outlets_l, row, col, id, find_full);
    }

    if (driver)
        db_close_database_shutdown_driver(driver);

    Vect_close(&Map);

    return outlets_l;
}
