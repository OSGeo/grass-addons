/****************************************************************************
 *
 * MODULE:       i.gcp
 *
 * AUTHOR(S):    Huidae Cho <grass4u gmail.com>
 *
 * PURPOSE:      Manages ground control points non-interactively.
 *
 * COPYRIGHT:    (C) 2016 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

#include <stdlib.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/imagery.h>
#include <grass/glocale.h>

/* points.c */
void backup_point_file(const char *);
void restore_backup_point_file(const char *);
void list_backup_point_file(const char *);
void remove_backup_point_file(const char *);
int find_point_file(const char *);
void remove_point_file(const char *);
void create_point_file(const char *);
void list_points(struct Control_Points *);

int main(int argc, char **argv)
{
    struct GModule *module;
    struct {
        struct Option *group;
        struct Option *image_coords;
        struct Option *target_coords;
        struct Option *status;
        struct Option *point;
    } opt;
    struct {
        struct Flag *list;
        struct Flag *clear;
        struct Flag *delete;
        struct Flag *use;
        struct Flag *ignore;
        struct Flag *backup;
        struct Flag *restore;
        struct Flag *list_backup;
        struct Flag *remove_backup;
    } flag;
    char *group, **image_coords, **target_coords;
    int status;
    int i;
    struct Control_Points cp;
    int num_deleted;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("imagery"));
    G_add_keyword(_("georectification"));
    G_add_keyword(_("GCP"));
    module->description =
        _("Manages Ground Control Points (GCPs) non-interactively.");

    opt.group = G_define_standard_option(G_OPT_I_GROUP);

    opt.image_coords = G_define_standard_option(G_OPT_M_COORDS);
    opt.image_coords->key = "image_coordinates";
    opt.image_coords->description = _("Image coordinates to add");

    opt.target_coords = G_define_standard_option(G_OPT_M_COORDS);
    opt.target_coords->key = "target_coordinates";
    opt.target_coords->description = _("Target coordinates to add");

    opt.status = G_define_option();
    opt.status->key = "status";
    opt.status->description = _("Status for new ground control points");
    opt.status->type = TYPE_STRING;
    opt.status->options = "use,ignore";
    opt.status->answer = "use";

    opt.point = G_define_option();
    opt.point->key = "point";
    opt.point->description = _("Point number(s) to manage");
    opt.point->type = TYPE_INTEGER;
    opt.point->multiple = YES;
    opt.point->options = "1-";

    flag.list = G_define_flag();
    flag.list->key = 'l';
    flag.list->description = _("List all ground control points");

    flag.clear = G_define_flag();
    flag.clear->key = 'c';
    flag.clear->description = _("Clear all ground control points");

    flag.delete = G_define_flag();
    flag.delete->key = 'd';
    flag.delete->description = _("Delete selected ground control points");

    flag.use = G_define_flag();
    flag.use->key = 'u';
    flag.use->description = _("Use selected ground control points");

    flag.ignore = G_define_flag();
    flag.ignore->key = 'i';
    flag.ignore->description = _("Ignore selected ground control points");

    flag.backup = G_define_flag();
    flag.backup->key = 'b';
    flag.backup->description = _("Back up the point file");

    flag.restore = G_define_flag();
    flag.restore->key = 'r';
    flag.restore->description = _("Restore the backup point file");

    flag.list_backup = G_define_flag();
    flag.list_backup->key = 'L';
    flag.list_backup->description =
        _("List all ground control points in the backup point file");

    flag.remove_backup = G_define_flag();
    flag.remove_backup->key = 'B';
    flag.remove_backup->description = _("Remove the backup point file");

    /* both image and target coordinates are required collectively */
    G_option_collective(opt.image_coords, opt.target_coords, NULL);
    /* one of these flags or options is required, but point= alone is not */
    G_option_required(flag.list, flag.clear, flag.delete, flag.use, flag.ignore,
                      flag.backup, flag.restore, flag.list_backup,
                      flag.remove_backup, opt.image_coords, NULL);
    /* however, they are mutually exclusive except flag.list */
    G_option_exclusive(flag.clear, flag.delete, flag.use, flag.ignore,
                       flag.backup, flag.restore, flag.list_backup,
                       flag.remove_backup, opt.image_coords, NULL);
    /* don't need to list after clear, backup, or restore */
    G_option_exclusive(flag.list, flag.clear, flag.backup, flag.restore,
                       flag.list_backup, flag.remove_backup, NULL);
    /* point= is used to select points to delete, use, or ignore */
    G_option_requires(flag.delete, opt.point, NULL);
    G_option_requires(flag.use, opt.point, NULL);
    G_option_requires(flag.ignore, opt.point, NULL);

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    group = opt.group->answer;
    image_coords = opt.image_coords->answers;
    target_coords = opt.target_coords->answers;
    status = strcmp(opt.status->answer, "use") == 0;

    /* does group exist? */
    if (!I_find_group(group))
        G_fatal_error(_("Specified group does not exist in current mapset"));

    if (flag.backup->answer) {
        /* back up point file */
        backup_point_file(group);
        exit(EXIT_SUCCESS);
    }

    if (flag.restore->answer) {
        /* restore backup point file */
        restore_backup_point_file(group);
        exit(EXIT_SUCCESS);
    }

    if (flag.list_backup->answer) {
        /* list backup point file */
        list_backup_point_file(group);
        exit(EXIT_SUCCESS);
    }

    if (flag.remove_backup->answer) {
        /* remove backup point file */
        remove_backup_point_file(group);
        exit(EXIT_SUCCESS);
    }

    if (flag.clear->answer) {
        /* remove control point file */
        remove_point_file(group);
        exit(EXIT_SUCCESS);
    }

    /* read in control points if any */
    if (find_point_file(group)) {
        if (!I_get_control_points(group, &cp))
            G_fatal_error(_("Failed to read control point file"));
    }
    else {
        cp.count = 0;
        cp.e1 = NULL;
        cp.n1 = NULL;
        cp.e2 = NULL;
        cp.n2 = NULL;
        cp.status = NULL;
    }
    num_deleted = 0;

    if (flag.delete->answer || flag.use->answer || flag.ignore->answer) {
        /* delete, use, or ignore existing control points */
        char *ans;
        int j, tmp;
        int *points;
        int num_points;
        int new_status;

        if (cp.count == 0)
            G_fatal_error(_("There are no control points to manage"));

        /* read control point numbers */
        for (num_points = 0; opt.point->answers[num_points]; num_points++)
            ;
        points = (int *)G_malloc(num_points * sizeof(int));

        for (i = j = 0; (ans = opt.point->answers[i]); i++) {
            char *p;

            /* if ans is a range */
            if ((p = strchr(ans, '-'))) {
                int lo, hi;

                /* more than one range is not allowed in one answer */
                if (p != strrchr(ans, '-'))
                    G_fatal_error(_("%s: Invalid range for point numbers"),
                                  ans);
                /* only lo-hi is allowed, not lo- or -hi */
                if (sscanf(ans, "%d-%d", &lo, &hi) == 2) {
                    if (hi < lo) {
                        tmp = hi;
                        hi = lo;
                        lo = tmp;
                    }
                }
                else
                    G_fatal_error(_("%s: Invalid range for point numbers"),
                                  ans);

                if (hi > cp.count)
                    hi = cp.count;

                num_points += hi - lo;
                points = (int *)G_realloc(points, num_points * sizeof(int));

                for (; lo <= hi; lo++)
                    points[j++] = lo;
            }
            else {
                tmp = atoi(ans);
                if (tmp > cp.count)
                    tmp = cp.count;

                points[j++] = tmp;
            }
        }

        /* no points selected */
        if (num_points == 0)
            G_fatal_error(_("No control points selected to manage"));

        if (flag.delete->answer)
            /* the imagery library only stores status >= 0 */
            new_status = -1;
        else if (flag.use->answer)
            /* status = 1 means use */
            new_status = 1;
        else
            /* status = 0 means ignore */
            new_status = 0;

        for (i = 0; i < cp.count; i++) {
            int j;

            /* find points */
            for (j = 0; j < num_points; j++) {
                if (points[j] == i + 1) {
                    /* update status */
                    cp.status[i] = new_status;
                    break;
                }
            }
        }

        if (new_status == -1) {
            for (i = 0; i < cp.count; i++) {
                if (cp.status[i] == -1)
                    num_deleted++;
            }
        }
    }
    else if (image_coords) {
        /* add new control points */
        int n;

        /* # of image coords must be the same as # of target coords */
        for (i = 0; image_coords[i]; i++)
            ;
        n = i;

        for (i = 0; target_coords[i]; i++)
            ;
        if (i != n)
            G_fatal_error(_("Image and target coordinates have different "
                            "numbers of points"));

        /* loop through all image and target coordinates */
        for (i = 0; i < n; i += 2) {
            double e1, n1, e2, n2;

            e1 = atof(image_coords[i]);
            n1 = atof(image_coords[i + 1]);
            e2 = atof(target_coords[i]);
            n2 = atof(target_coords[i + 1]);

            /* create a new control point */
            I_new_control_point(&cp, e1, n1, e2, n2, status);
        }
    }

    /* save control points */
    if (!I_put_control_points(group, &cp))
        G_fatal_error(_("Failed to write control point file"));

    if (flag.list->answer) {
        /* list existing control points */
        if (cp.count - num_deleted > 0)
            list_points(&cp);
        else
            fprintf(stdout, _("No control points found\n"));
    }

    exit(EXIT_SUCCESS);
}
