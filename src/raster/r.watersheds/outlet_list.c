#include <grass/vector.h>
#include <grass/glocale.h>
#include "global.h"

static struct Cell_head window;

void init_outlet_list(struct outlet_list *ol)
{
    G_get_set_window(&window);

    ol->nalloc = ol->n = 0;
    ol->row = ol->col = NULL;
    ol->id = NULL;
}

void reset_outlet_list(struct outlet_list *ol)
{
    ol->n = 0;
}

void free_outlet_list(struct outlet_list *ol)
{
    if (ol->row)
        free(ol->row);
    if (ol->col)
        free(ol->col);
    if (ol->id)
        free(ol->id);
    init_outlet_list(ol);
}

/* adapted from r.path */
void add_outlet(struct outlet_list *ol, double x, double y, int id)
{
    if (ol->n == ol->nalloc) {
        ol->nalloc += REALLOC_INCREMENT;
        ol->row = realloc(ol->row, sizeof *ol->row * ol->nalloc);
        ol->col = realloc(ol->col, sizeof *ol->col * ol->nalloc);
        ol->id = realloc(ol->id, sizeof *ol->id * ol->nalloc);
        if (!ol->row || !ol->col || !ol->id)
            G_fatal_error(_("Unable to increase outlet list"));
    }
    ol->row[ol->n] = (int)Rast_northing_to_row(y, &window);
    ol->col[ol->n] = (int)Rast_easting_to_col(x, &window);
    ol->id[ol->n] = id;
    ol->n++;
}

struct outlet_list *read_outlets(char *outlets_name, char *layer, char *idcol)
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

    Fi = Vect_get_field(&Map, field);
    driver = db_start_driver_open_database(Fi->driver,
                                           Vect_subst_var(Fi->database, &Map));
    if (db_column_Ctype(driver, Fi->table, idcol) != DB_C_TYPE_INT)
        G_fatal_error(
            _("Column <%s> in vector map <%s> must be of integer type"), idcol,
            outlets_name);

    Points = Vect_new_line_struct();
    Cats = Vect_new_cats_struct();
    nlines = Vect_get_num_lines(&Map);
    init_outlet_list(outlets_l);

    for (line = 1; line <= nlines; line++) {
        int ltype, cat, id;

        G_percent(line, nlines, 1);

        ltype = Vect_read_line(&Map, Points, Cats, line);
        Vect_cat_get(Cats, field, &cat);

        if (ltype != GV_POINT || cat < 0)
            continue;

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

        add_outlet(outlets_l, Points->x[0], Points->y[0], id);
    }

    if (driver)
        db_close_database_shutdown_driver(driver);

    Vect_close(&Map);

    return outlets_l;
}
