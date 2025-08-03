#include <unistd.h>
#include <string.h>
#include "globals.h"
#include <grass/gis.h>
#include <grass/glocale.h>

/* read the target for the group and cast it into the alternate GRASS env */

static int which_env;

int get_target(void)
{
    char location[GNAME_MAX];
    char mapset[GNAME_MAX];
    char buf[GPATH_MAX];
    int stat;

    G_debug(1, "get_target()");

    if (!I_get_target(group.name, location, mapset)) {
        G_fatal_error(_("No target specified for group <%s>"), group.name);
    }

    sprintf(buf, "%s/%s", G_gisdbase(), location);
    if (access(buf, 0) != 0) {
        G_warning(_("Target location <%s> not found"), location);
        G_warning(_("Please run i.target for group <%s>"), group.name);
        G_fatal_error(_("Can not continue"));
    }

    G_create_alt_env();
    G_setenv("LOCATION_NAME", location);
    stat = G_mapset_permissions(mapset);
    if (stat > 0) {
        G_setenv("MAPSET", mapset);
        G_create_alt_search_path();
        G_switch_env();
        G_switch_search_path();
        which_env = SRC_ENV;
        return 1;
    }
    G_fatal_error(_("Mapset <%s> in target location <%s> - %s"), mapset,
                  location,
                  stat == 0 ? _("permission denied") : _("not found"));

    return 0;
}

int select_env(int env)
{
    if (which_env != env) {
        G_switch_env();
        G_switch_search_path();
        which_env = env;
    }

    return 0;
}

int select_current_env(void)
{
    if (which_env != SRC_ENV) {
        G_switch_env();
        G_switch_search_path();
        which_env = SRC_ENV;
    }

    return 0;
}

int select_target_env(void)
{
    if (which_env != TGT_ENV) {
        G_switch_env();
        G_switch_search_path();
        which_env = TGT_ENV;
    }

    return 0;
}
