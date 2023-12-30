#include <grass/vector.h>

#include "proto.h"

void write_ellipse(struct Map_info *Out, struct line_pnts *Ellipse,
                   struct line_cats *Cats)
{
    /* variables */
    double xc, yc;
    int i, n;

    /* write boundary */
    Vect_write_line(Out, GV_BOUNDARY, Ellipse, Cats);

    /* write centroid */
    xc = 0;
    yc = 0;
    n = Ellipse->n_points;

    for (i = 0; i < n; i++) {
        xc += Ellipse->x[i];
        yc += Ellipse->y[i];
    }

    xc /= n;
    yc /= n;
    Vect_reset_line(Ellipse);
    Vect_append_point(Ellipse, xc, yc, 0);
    Vect_cat_set(Cats, 1, 1);
    Vect_write_line(Out, GV_CENTROID, Ellipse, Cats);
    Vect_destroy_line_struct(Ellipse);

    /* build topology and close map */
    Vect_build(Out);
    Vect_close(Out);
}
