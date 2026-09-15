#include <grass/gis.h>
#include <grass/site.h>
#include "global.h"
#include "globals.h"

int read_points_from_file(Training *training, char *site_file)
{
    char msg[256];
    char *mapset;
    FILE *out;
    Site *site;
    int dims = 0, cat = 0, strs = 0, dbls = 0;
    int code;

    mapset = G_find_sites(site_file, "");
    if (mapset == NULL) {
        sprintf(msg,
                "read_points_from_file-> Can't find vector points map <%s>",
                site_file);
        G_fatal_error(msg);
    }
    out = G_fopen_sites_old(site_file, mapset);
    if (out == NULL) {
        sprintf(msg,
                "read_points_from_file-> Can't open vector points map <%s>",
                site_file);
        G_fatal_error(msg);
    }
    if (G_site_describe(out, &dims, &cat, &strs, &dbls) != 0) {
        sprintf(msg, "read_points_from_file-> Error in G_site_describe");
        G_warning(msg);
        return 0;
    }
    site = (Site *)G_calloc(1, sizeof(Site));
    site = G_site_new_struct(0, dims, strs, dbls);
    while ((code = G_site_get(out, site)) > -1) {
        training->east[training->nexamples] = site->east;
        training->north[training->nexamples] = site->north;
        training->class[training->nexamples] = site->ccat;
        training->nexamples += 1;
    }
    G_sites_close(out);
    if (code != -1) {
        sprintf(msg, "read_points_from_file-> Error in G_site_get");
        G_warning(msg);
        return 0;
    }
    return 1;
}
