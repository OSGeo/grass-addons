#include <stdio.h>
#include <grass/gis.h>
#include <grass/imagery.h>
#include <grass/glocale.h>

#define POINT_FILE     "POINTS"
#define POINT_BAK_FILE "POINTS_BAK"

void list_points(struct Control_Points *);

/* copied from lib/imagery/points.c */
static int I_read_control_points(FILE *fd, struct Control_Points *cp)
{
    char buf[100];
    double e1, e2, n1, n2;
    int status;

    cp->count = 0;

    /* read the control point lines. format is:
       image_east image_north  target_east target_north  status
     */
    cp->e1 = NULL;
    cp->e2 = NULL;
    cp->n1 = NULL;
    cp->n2 = NULL;
    cp->status = NULL;

    while (G_getl2(buf, sizeof buf, fd)) {
        G_strip(buf);
        if (*buf == '#' || *buf == 0)
            continue;
        if (sscanf(buf, "%lf%lf%lf%lf%d", &e1, &n1, &e2, &n2, &status) == 5)
            I_new_control_point(cp, e1, n1, e2, n2, status);
        else
            return -4;
    }

    return 1;
}
/**********/

void backup_point_file(const char *group)
{
    char path[GPATH_MAX], bak[GPATH_MAX];

    if (!I_find_group_file(group, POINT_FILE))
        G_fatal_error(_("No control point file exists"));

    if (I_find_group_file(group, POINT_BAK_FILE))
        G_fatal_error(_("Backup control point file alreay exists"));

    G_file_name_misc(path, "group", POINT_FILE, group, G_mapset());
    G_file_name_misc(bak, "group", POINT_BAK_FILE, group, G_mapset());

    if (!G_copy_file(path, bak))
        G_fatal_error(
            _("Unable to create a backup copy of control point file"));
}

void restore_backup_point_file(const char *group)
{
    char path[GPATH_MAX], bak[GPATH_MAX];

    if (!I_find_group_file(group, POINT_BAK_FILE))
        G_fatal_error(_("No backup control point file exists"));

    G_file_name_misc(path, "group", POINT_FILE, group, G_mapset());
    G_file_name_misc(bak, "group", POINT_BAK_FILE, group, G_mapset());

    if (!G_copy_file(bak, path))
        G_fatal_error(_("Unable to restore backup control point file"));
}

void list_backup_point_file(const char *group)
{
    FILE *fd;
    int stat;
    struct Control_Points cp;

    if (!I_find_group_file(group, POINT_BAK_FILE))
        G_fatal_error(_("No backup control point file exists"));

    fd = I_fopen_group_file_old(group, POINT_BAK_FILE);
    if (fd == NULL)
        G_fatal_error(
            _("Unable to open backup control point file for group [%s in %s]"),
            group, G_mapset());

    stat = I_read_control_points(fd, &cp);
    fclose(fd);
    if (stat < 0)
        G_fatal_error(
            _("Bad format in control point file for group [%s in %s]"), group,
            G_mapset());

    list_points(&cp);
}

void remove_backup_point_file(const char *group)
{
    if (!I_find_group_file(group, POINT_BAK_FILE))
        G_fatal_error(_("No backup control point file exists"));

    if (G_remove_misc("group", POINT_BAK_FILE, group) < 0)
        G_fatal_error(_("Unable to remove backup control point file"));
}

int find_point_file(const char *group)
{
    return I_find_group_file(group, POINT_FILE);
}

void remove_point_file(const char *group)
{
    if (!I_find_group_file(group, POINT_FILE))
        return;

    if (G_remove_misc("group", POINT_FILE, group) < 0)
        G_fatal_error(_("Unable to remove control point file"));
}

void create_point_file(const char *group)
{
    FILE *fd;

    if (I_find_group_file(group, POINT_FILE))
        G_fatal_error(_("Control point file already exists"));

    fd = I_fopen_group_file_new(group, POINT_FILE);
    if (fd == NULL)
        G_fatal_error(
            _("Unable to create control point file for group [%s in %s]"),
            group, G_mapset());

    fclose(fd);
}

void list_points(struct Control_Points *cp)
{
    int i, j;

    fprintf(stdout, "%5s %7s %15s %15s %15s %7s %6s\n", "point", "", "image",
            "", "target", "", "status");
    fprintf(stdout, "%5s %15s %15s %15s %15s\n", "", "east", "north", "east",
            "north");
    for (i = 0, j = 1; i < cp->count; i++) {
        if (cp->status[i] >= 0)
            fprintf(stdout, "%5d %15f %15f %15f %15f %6s\n", j++, cp->e1[i],
                    cp->n1[i], cp->e2[i], cp->n2[i],
                    cp->status[i] == 1 ? "use" : "ignore");
    }
}
