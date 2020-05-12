#include <grass/gis.h>
#include <grass/glocale.h>
#include "global.h"

void init_point_list(struct point_list *pl)
{
    pl->nalloc = pl->n = 0;
    pl->x = pl->y = NULL;
}

void reset_point_list(struct point_list *pl)
{
    pl->n = 0;
}

void free_point_list(struct point_list *pl)
{
    if (pl->x)
        G_free(pl->x);
    if (pl->y)
        G_free(pl->y);
    init_point_list(pl);
}

/* adapted from r.path */
void add_point(struct point_list *pl, double x, double y)
{
    if (pl->n == pl->nalloc) {
        pl->nalloc += REALLOC_INCREMENT;
        pl->x = (double *)G_realloc(pl->x, pl->nalloc * sizeof(double));
        pl->y = (double *)G_realloc(pl->y, pl->nalloc * sizeof(double));
        if (!pl->x || !pl->y)
            G_fatal_error(_("Unable to increase point list"));
    }
    pl->x[pl->n] = x;
    pl->y[pl->n] = y;
    pl->n++;
}
