/*****************************************************************************
 *
 * MODULE:     v.out.ply
 * AUTHOR(S):  Markus Metz
 *             based on v.out.ascii
 *
 * PURPOSE:    Writes GRASS vector data as PLY files
 *
 * COPYRIGHT:  (C) 2011 by the GRASS Development Team
 *
 *             This program is free software under the GNU General
 *             Public License (>=v2). Read the file COPYING that comes
 *             with GRASS for details.
 *
 *****************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/vector.h>
#include <grass/glocale.h>

#include "local_proto.h"

int main(int argc, char *argv[])
{
    struct GModule *module;
    struct Map_info Map;

    FILE *fp = NULL;
    char *input, *output, **columns, *field_name;
    int format, dp, field, region, type;
    int pnts, cat;
    struct Cell_head window;
    struct bound_box box;
    struct line_pnts *Points;
    struct line_cats *Cats;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("vector"));
    G_add_keyword(_("export"));
    G_add_keyword(_("ply"));
    module->description = _("Exports a vector map to a PLY file.");

    parse_args(argc, argv, &input, &output, &format, &dp, &field_name, &columns,
               &region);

    /* topology not needed */
    Vect_set_open_level(1);
    if (Vect_open_old2(&Map, input, "", field_name) < 0)
        G_fatal_error(_("Unable to open vector map <%s>"), input);

    field = Vect_get_field_number(&Map, field_name);

    if (strcmp(output, "-") != 0) {
        if ((fp = fopen(output, "w")) == NULL) {
            G_fatal_error(_("Unable to open file <%s>"), output);
        }
    }
    else {
        fp = stdout;
    }

    /* get the region */
    G_get_window(&window);
    Vect_region_box(&window, &box);
    if (!Vect_is_3d(&Map)) {
        box.T = PORT_DOUBLE_MAX;
        box.B = -PORT_DOUBLE_MAX;
    }

    /* count points */
    Points = Vect_new_line_struct();
    Cats = Vect_new_cats_struct();
    pnts = 0;
    while ((type = Vect_read_next_line(&Map, Points, Cats)) > 0) {
        if (type == GV_POINT) {
            if (field > 0 && !(Vect_cat_get(Cats, field, &cat)))
                continue;
            if (region && !Vect_point_in_box(Points->x[0], Points->y[0],
                                             Points->z[0], &box))
                continue;

            pnts++;
        }
    }
    if (pnts < 1)
        G_fatal_error(_("No points found, nothing to be exported"));

    /* write ply header */
    write_ply_header(fp, &Map, input, field_name, (const char **)columns, pnts,
                     dp);

    if (columns)
        G_message(_("Fetching data..."));

    write_ply_body_ascii(fp, &Map, dp, region, field, (const char **)columns,
                         &box);

    if (fp != NULL)
        fclose(fp);

    Vect_close(&Map);

    exit(EXIT_SUCCESS);
}
