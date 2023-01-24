/***************************************************************
 *
 * MODULE:       v.delaunay3d
 *
 * AUTHOR(S):    Martin Landa <landa.martin gmail.com>
 *
 * PURPOSE:      Creates a 3D Delaunay triangulation vector map
 *
 * COPYRIGHT:    (C) 2013 by Martin Landa, and the GRASS Development Team
 *
 *               This program is free software under the GNU General
 *               Public License (>=v2). Read the file COPYING that
 *               comes with GRASS for details.
 *
 ****************************************************************/

#include <cstdlib>
#include <vector>

/* must be included before GRASS headers (GRASS is using _n reserved word) */
#include <CGAL/Exact_predicates_inexact_constructions_kernel.h>
#include <CGAL/Triangulation_3.h>
#include <CGAL/Delaunay_triangulation_3.h>

extern "C" {
#include <grass/vector.h>
#include <grass/glocale.h>
}

#include "local_proto.h"

int main(int argc, char *argv[])
{
    int type; /* line or face */
    int field;
    unsigned int npoints, nvertices;

    struct GModule *module;

    struct {
        struct Option *input, *field, *output;
    } opt;
    struct {
        struct Flag *line, *plain;
    } flag;

    struct Map_info In, Out;

    std::vector<Point> points;
    Triangulation *T;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("vector"));
    G_add_keyword(_("geometry"));
    G_add_keyword(_("3D triangulation"));
    module->description = _("Creates a 3D triangulation from an input vector "
                            "map containing points or centroids.");

    opt.input = G_define_standard_option(G_OPT_V_INPUT);

    opt.field = G_define_standard_option(G_OPT_V_FIELD_ALL);

    opt.output = G_define_standard_option(G_OPT_V_OUTPUT);

    flag.plain = G_define_flag();
    flag.plain->key = 'p';
    flag.plain->description = _("Perform plain triangulation");

    flag.line = G_define_flag();
    flag.line->key = 'l';
    flag.line->description =
        _("Output triangulation as a graph (lines), not faces");

    if (G_parser(argc, argv)) {
        exit(EXIT_FAILURE);
    }

    if (flag.line->answer)
        type = GV_LINE;
    else
        type = GV_FACE;

    /* open input map */
    Vect_open_old2(&In, opt.input->answer, "", opt.field->answer);
    Vect_set_error_handler_io(&In, &Out);
    /* check if the map is 3D */
    if (!Vect_is_3d(&In))
        G_fatal_error(_("Vector map <%s> is not 3D"), Vect_get_full_name(&In));

    field = Vect_get_field_number(&In, opt.field->answer);

    /* create output */
    Vect_open_new(&Out, opt.output->answer, WITH_Z); /* output is always 3D */
    Vect_hist_copy(&In, &Out);
    Vect_hist_command(&Out);

    /* read points */
    npoints = read_points(&In, field, points);
    Vect_close(&In);

    /* do 3D triangulation */
    G_message(_("Creating TEN..."));
    if (!flag.plain->answer)
        T = reinterpret_cast<Triangulation *>(
            new DelaunayTriangulation(points.begin(), points.end()));
    else
        T = new Triangulation(points.begin(), points.end());

    nvertices = T->number_of_vertices();
    if (nvertices != npoints)
        G_fatal_error(_("Invalid number of vertices %d (%d)"), nvertices,
                      npoints);

    G_message(_("Number of vertices: %d"), nvertices);
    G_message(_("Number of edges: %lu"), T->number_of_finite_edges());
    G_message(_("Number of triangles: %lu"), T->number_of_finite_facets());
    G_message(_("Number of tetrahedrons: %lu"), T->number_of_finite_cells());

    G_message(_("Writing output features..."));

    write_lines(&Out, type, T);

    Vect_build(&Out);
    Vect_close(&Out);

    exit(EXIT_SUCCESS);
}
