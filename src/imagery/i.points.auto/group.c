#include <unistd.h>
#include <string.h>
#include "globals.h"
#include <grass/glocale.h>

/* get group */

int get_group(void)
{
    int i, check_ok;
    char xname[GNAME_MAX], xmapset[GMAPSET_MAX];
    char *sname, *smapset;

    G_debug(1, "get_group()");

    /* check if group exists */
    if (!I_find_group(group.name))
        G_fatal_error(_("Imagery group <%s> does not exist"), group.name);

    /* check if any files are in the group */
    if (!I_get_group_ref(group.name, &group.ref))
        G_fatal_error(_("No imagery defined for group <%s>"), group.name);

    if (group.ref.nfiles <= 0)
        G_fatal_error(_("Group <%s> contains no imagery"), group.name);

    /* check if selected source image exists */
    if (!G_find_file2("cell", group.img, ""))
        G_fatal_error(_("Source image <%s> does not exist"), group.img);

    /* check if selected source image is in group */
    /* split file in name and mapset */
    if (G_name_is_fully_qualified(group.img, xname, xmapset)) {
        sname = xname;
        smapset = xmapset;
    }
    else {
        sname = group.img;
        smapset = NULL;
    }
    check_ok = 0;

    for (i = 0; i < group.ref.nfiles; i++) {
        if (!strcmp(sname, group.ref.file[i].name)) {
            if (!smapset)
                check_ok = 1;
            else if (!strcmp(smapset, group.ref.file[i].mapset)) {
                check_ok = 1;
            }
        }
        if (check_ok)
            break;
    }
    if (!check_ok)
        G_fatal_error(_("Source map <%s> is not in group <%s>"), group.img,
                      group.name);

    return 1;
}
