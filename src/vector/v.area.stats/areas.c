#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <grass/glocale.h>

#include "global.h"

int init_vals(struct value val)
{
    val.area_id = 0;
    val.cat = 0;
    val.nisles = 0;
    val.x_extent = 0;
    val.y_extent = 0;
    val.iperimeter = 0;
    val.iarea = 0;
    val.icompact = 0;
    val.ifd = 0;
    val.perimeter = 0;
    val.area = 0;
    val.boundarea = 0;
    val.aratio = 0;
    val.compact = 0;
    val.fd = 0;
    return 0;
}

/* This function now does one of 3 things:
 * 1) It reads the areas of the areas.
 * 2) It reads the perimeter lengths of the areas. If projection is LL, the
 * geodesic distance is used. 3) It calculates the compactness using this
 * formula: compactness = perimeter / (2 * sqrt(M_PI * area)) 4) It calculates
 * the fractal dimension of the bounding curve: D_L  = 2 * log(perimeter) /
 * log(area) (See B.B. Mandelbrot, The Fractal Geometry of Nature. 1982.)
 */
int read_areas(struct Map_info *Map, int nareas)
{
    int isle, aid, ax;
    struct line_pnts *Ppoints;
    struct bound_box Bbox;
    double iarea, iperimeter;

    Ppoints = Vect_new_line_struct();
    nareas = Vect_get_num_areas(Map);

    G_message(_("Reading areas..."));

    /* Cycle through all areas */
    for (aid = 1; aid <= nareas; aid++) {
        init_vals(Values[aid]);

        if (Vect_area_alive(Map, aid) > 0) {
            Vect_reset_line(Ppoints);

            Values[aid].area_id = aid;
            Values[aid].cat = Vect_get_area_cat(Map, aid, options.field);
            ;
            Vect_get_area_points(Map, aid, Ppoints);
            Values[aid].perimeter = Vect_line_geodesic_length(Ppoints);
            Values[aid].boundarea =
                G_area_of_polygon(Ppoints->x, Ppoints->y, Ppoints->n_points);
            Vect_line_box(Ppoints, &Bbox);
            Values[aid].x_extent = Bbox.E - Bbox.W;
            Values[aid].y_extent = Bbox.N - Bbox.S;
            Values[aid].nisles = Vect_get_area_num_isles(Map, aid);

            if (Values[aid].nisles) {
                for (isle = 0; isle < Values[aid].nisles; isle++) {
                    Vect_reset_line(Ppoints);
                    ax = Vect_get_area_isle(Map, aid, isle);
                    if (Vect_get_isle_points(Map, ax, Ppoints) == -1) {
                        G_fatal_error(_("Not able to read the isle <%d> of the "
                                        "area <%d>.\n"),
                                      isle, aid);
                    }

                    iarea = G_area_of_polygon(Ppoints->x, Ppoints->y,
                                              Ppoints->n_points);
                    iperimeter = Vect_line_geodesic_length(Ppoints);
                    Values[aid].icompact +=
                        iperimeter / (2.0 * sqrt(M_PI * iarea));
                    Values[aid].ifd += 2.0 * log(iperimeter) / log(iarea);
                    Values[aid].iarea += iarea;
                    Values[aid].iperimeter += iperimeter;
                    /* May be we can add also the mean and the std? */
                }
            }
            Values[aid].area = Values[aid].boundarea - Values[aid].iarea;
            Values[aid].aratio = Values[aid].iarea / Values[aid].boundarea;
            Values[aid].compact = Values[aid].perimeter /
                                  (2.0 * sqrt(M_PI * Values[aid].boundarea));
            Values[aid].fd =
                2.0 * log(Values[aid].perimeter) / log(Values[aid].boundarea);
        }
        G_percent(aid, nareas, 2);
    }
    return 0;
}
