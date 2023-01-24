/* must be included before GRASS headers (GRASS is using _n reserved word) */
#include <CGAL/Exact_predicates_inexact_constructions_kernel.h>
#include <CGAL/Triangulation_3.h>
#include <CGAL/Delaunay_triangulation_3.h>

extern "C" {
#include <grass/vector.h>
#include <grass/glocale.h>
}

#include "local_proto.h"

void write_lines(struct Map_info *Out, int type, const Triangulation *T)
{
    int line;
    struct line_pnts *Points;
    struct line_cats *Cats;

    Points = Vect_new_line_struct();
    Cats = Vect_new_cats_struct();

    line = 1;
    if (type == GV_LINE) {
        Triangulation::Finite_edges_iterator eit;
        Point pt1, pt2;

        /* write edges as lines */
        for (eit = T->finite_edges_begin(); eit != T->finite_edges_end();
             ++eit) {
            pt1 = eit->first->vertex(eit->second)->point();
            pt2 = eit->first->vertex(eit->third)->point();
            G_debug(3, "edge: %f %f %f | %f %f %f", pt1.x(), pt1.y(), pt1.z(),
                    pt2.x(), pt2.y(), pt2.z());

            Vect_reset_line(Points);
            Vect_append_point(Points, pt1.x(), pt1.y(), pt1.z());
            Vect_append_point(Points, pt2.x(), pt2.y(), pt2.z());

            Vect_reset_cats(Cats);
            Vect_cat_set(Cats, 1, line++);

            Vect_write_line(Out, type, Points, Cats);
        }
    }
    else {
        int k;
        Triangulation::Finite_facets_iterator fit;
        Point pt1, pt2, pt3;

        /* write edges as lines */
        for (fit = T->finite_facets_begin(); fit != T->finite_facets_end();
             ++fit) {
            k = 1;
            pt1 = fit->first->vertex((fit->second + (k++)) % 4)->point();
            pt2 = fit->first->vertex((fit->second + (k++)) % 4)->point();
            pt3 = fit->first->vertex((fit->second + (k++)) % 4)->point();

            G_debug(3, "facet: %f %f %f | %f %f %f | %f %f %f", pt1.x(),
                    pt1.y(), pt1.z(), pt2.x(), pt2.y(), pt2.z(), pt3.x(),
                    pt3.y(), pt3.z());

            Vect_reset_line(Points);
            Vect_append_point(Points, pt1.x(), pt1.y(), pt1.z());
            Vect_append_point(Points, pt2.x(), pt2.y(), pt2.z());
            Vect_append_point(Points, pt3.x(), pt3.y(), pt3.z());

            Vect_reset_cats(Cats);
            Vect_cat_set(Cats, 1, line++);

            Vect_write_line(Out, type, Points, Cats);
        }
    }

    Vect_destroy_line_struct(Points);
    Vect_destroy_cats_struct(Cats);
}
