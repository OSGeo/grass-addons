#include <grass/gis.h>
#include <grass/glocale.h>
#include "global.h"

void init_point_list(struct point_list *pl)
{
    pl->nalloc = pl->n = 0;
    pl->row = pl->col = NULL;
    pl->x = pl->y = NULL;
}

void reset_point_list(struct point_list *pl)
{
    pl->n = 0;
}

void free_point_list(struct point_list *pl)
{
    if (pl->row)
        G_free(pl->row);
    if (pl->col)
        G_free(pl->col);
    if (pl->x)
        G_free(pl->x);
    if (pl->y)
        G_free(pl->y);
    init_point_list(pl);
}

void add_point(struct point_list *pl, int row, int col)
{
    if (pl->n == pl->nalloc) {
        pl->nalloc += REALLOC_INCREMENT;
        pl->row = G_realloc(pl->row, sizeof *pl->row * pl->nalloc);
        pl->col = G_realloc(pl->col, sizeof *pl->col * pl->nalloc);
        if (!pl->row || !pl->col)
            G_fatal_error(_("Unable to increase point list"));
    }
    pl->row[pl->n] = row;
    pl->col[pl->n] = col;
    pl->n++;
}

void add_point_xy(struct point_list *pl, double x, double y)
{
    if (pl->n == pl->nalloc) {
        pl->nalloc += REALLOC_INCREMENT;
        pl->x = G_realloc(pl->x, sizeof *pl->x * pl->nalloc);
        pl->y = G_realloc(pl->y, sizeof *pl->y * pl->nalloc);
        if (!pl->x || !pl->y)
            G_fatal_error(_("Unable to increase point list"));
    }
    pl->x[pl->n] = x;
    pl->y[pl->n] = y;
    pl->n++;
}
