/****************************************************************************
 *
 * MODULE:       v.to.db
 * AUTHOR(S):    Pietro Zambelli <peter.zamb gmail com> (from v.to.db)
 * PURPOSE:      load values from vector to database
 * COPYRIGHT:    (C) 2000-2010 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

#include <stdlib.h>
#include <grass/glocale.h>
#include "global.h"

struct value *Values;
struct options options;

int main(int argc, char *argv[])
{
    int nareas;
    struct Map_info Map;
    struct GModule *module;
    struct field_info *Fi;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("vector"));
    G_add_keyword(_("attribute table"));
    G_add_keyword(_("database"));
    module->description = _("Populates attribute values from vector features.");
    module->overwrite = 1;

    parse_command_line(argc, argv);

    G_begin_distance_calculations();
    G_begin_polygon_area_calculations();

    /* open map */
    Vect_set_open_level(2);
    Vect_open_old(&Map, options.name, "");

    Fi = Vect_get_field(&Map, options.field);

    if (Fi == NULL) {
        G_fatal_error(_("Database connection not defined for layer %d. "
                        "Use v.db.connect first."),
                      options.field);
    }

    /* allocate array for values */
    nareas = Vect_get_num_areas(&Map);
    Values = (struct value *)G_calloc(nareas + 1, sizeof(struct value));

    read_areas(&Map, nareas);
    export2csv(nareas);

    Vect_close(&Map);

    /* free list */
    G_free(Values);

    exit(EXIT_SUCCESS);
}
