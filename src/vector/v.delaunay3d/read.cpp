/* must be included before GRASS headers (GRASS is using _n reserved word) */
#include <CGAL/Exact_predicates_inexact_constructions_kernel.h>
#include <CGAL/Triangulation_3.h>
#include <CGAL/Delaunay_triangulation_3.h>

extern "C" {
#include <grass/vector.h>
#include <grass/glocale.h>
}

#include "local_proto.h"

int read_points(struct Map_info *Map, int field, std::vector<Point> &OutPoints)
{
    int npoints;
    double x, y, z;

    struct line_pnts *Points;

    Points = Vect_new_line_struct();

    /* set constraints */
    Vect_set_constraint_type(Map, GV_POINTS);
    if (field > 0)
        Vect_set_constraint_field(Map, field);

    /* read points */
    npoints = 0;
    G_message(_("Reading points..."));
    while (TRUE) {
        if (Vect_read_next_line(Map, Points, NULL) < 0)
            break;

        G_progress(npoints, 1e3);

        if (Points->n_points != 1) {
            G_warning(_("Invalid point skipped"));
            continue;
        }

        x = Points->x[0];
        y = Points->y[0];
        z = Points->z[0];

        G_debug(3, "new point added: %f, %f, %f", x, y, z);
        OutPoints.push_back(Point(x, y, z));
        npoints++;
    }
    G_progress(1, 1);

    Vect_destroy_line_struct(Points);

    G_debug(1, "read_points(): %d", npoints);

    return npoints;
}
