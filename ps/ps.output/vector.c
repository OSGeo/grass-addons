
#include <string.h>
#include <grass/Vect.h>
#include "vector.h"
#include "ps_info.h"
#include "local_proto.h"


/* allocate memory space for a new vector */
int vector_new(void)
{
    int i = PS.vct_files;

    ++PS.vct_files;
    PS.vct = (VECTOR *) G_realloc(PS.vct, PS.vct_files * sizeof(VECTOR));

    PS.vct[i].type = NONE;
    return i;
}

/* ****************** */

/* GEOGRAPHIC */
/* geographic coordinates to paper coordinates */
/* Siempre lo pone para permitir correcto cerrado de paths */
int where_moveto(double east, double north)
{
    int x, y;
    double dx, dy;

    G_plot_where_xy(east, north, &x, &y);

    dx = ((double)x) / 10.;
    dy = ((double)y) / 10.;

    fprintf(PS.fp, "%.1f %.1f M ", dx, dy);
    return 0;
}

int where_lineto(double east, double north)
{
    int x, y;
    double dx, dy;

    G_plot_where_xy(east, north, &x, &y);

    dx = (double)x / 10.;
    dy = (double)y / 10.;

    fprintf(PS.fp, "%.1f %.1f L ", dx, dy);

    return 0;
}
