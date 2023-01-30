#include "local_proto.h"

int parse_map_file(STRING file)
{
    FILE *fd;
    int line = 0;
    char buf[500];
    STRING mapset;
    char map[30];
    int nmaps2 = 0, nsets = 0;
    fpos_t init;
    fpos_t position;
    int set_num;

    int i;

    fd = fopen(file, "r");
    if (!fd)
        G_fatal_error(_("Cannot open map file '%s'"), file);

    fgetpos(fd, &init);

    nmaps = 0;
    /* number of maps */
    while (fgets(buf, sizeof buf, fd)) {
        G_strip(buf);
        if (*buf != '%')
            continue;
        nmaps++;
    }
    s_maps = (MAPS *)G_malloc(nmaps * sizeof(MAPS));
    fsetpos(fd, &init); /* reset position */

    while (fgets(buf, sizeof buf, fd)) {
        line++;

        G_strip(buf);
        if (*buf == '#' || *buf == 0 || *buf == '\n')
            continue;

        if (*buf != '%' && *buf != '$')
            G_fatal_error(_("Wrong syntax at line %d: line must start with "
                            "<#>, <%%> or <$> or be empty line"),
                          line);

        if (*buf == '%') {

            fgetpos(fd, &position);

            sscanf(buf, "%[^\n]", map);
            char_strip(map, '%');
            G_strip(map);
            mapset = (STRING)G_find_raster2(map, "");

            if (mapset == NULL && strcmp(map, "_OUTPUT_"))
                G_fatal_error(_("Raster map <%s> not found"), map);

            if (!strcmp(map, "_OUTPUT_")) {
                strcpy(s_maps[nmaps2].name, output);
                s_maps[nmaps2].output = 1;
            }
            else {
                strcpy(s_maps[nmaps2].name, map);
                s_maps[nmaps2].output = 0;
            }
            s_maps[nmaps2].position = position;
            s_maps[nmaps2].nsets = get_nsets(fd, position);

            if (!s_maps[nmaps2].nsets)
                G_warning(_("map <%s> has no rules"), s_maps[nmaps2].name);

            if (s_maps[nmaps2].nsets)
                s_maps[nmaps2].sets =
                    (SETS *)G_malloc(s_maps[nmaps2].nsets * sizeof(SETS));

            set_num = 0;
            while (fgets(buf, sizeof buf, fd)) {
                G_strip(buf);

                if (*buf == '#' || *buf == 0 || *buf == '\n')
                    continue;
                if (*buf == '%')
                    break;

                parse_sets(&s_maps[nmaps2].sets[set_num++], buf,
                           s_maps[nmaps2].name);
            }
            fsetpos(fd, &position);

            if (nmaps2++ > nmaps)
                G_fatal_error(_("number of maps do not match"));
        }

    } /* end while */

    fclose(fd);
    return 0;
}

int parse_sets(SETS *set, char buf[], const char mapname[])
{

    char tmp[20];
    int i;

    char_strip(buf, '$');

    { /* check length of fuzzy value (cannot be longer than 20) */
        sscanf(buf, "%[^{] %[^\n]", tmp, buf);
        G_strip(tmp);

        if (strlen(tmp) < 21)
            strcpy(set->setname, tmp);
        else
            G_fatal_error(_("Map: <%s>, Membership: <%s>: Value name cannot be "
                            "longer than 20 chars, but has %d chars"),
                          mapname, tmp, (int)strlen(tmp));
    } /* check length of fuzzy value */

    { /* check if side is valid (both,left,right) */
        int done = 1;
        STRING sides[] = {"both", "left", "right"};

        char_strip(buf, '{');
        sscanf(buf, "%[^;] %[^\n]", tmp, buf);

        done = 0;
        for (i = 0; i < 3; ++i)
            if (strcmp(tmp, sides[i]) == 0) {
                done = 1;
                break;
            }

        if (done)
            set->side = i;
        else
            G_fatal_error(_(" Map: <%s>, Membership: <%s>:  <side> parameter "
                            "must be:  <left,right,both> but is: <%s>"),
                          mapname, set->setname, tmp);
    } /* end check if side is valid */

    { /* check number of points and order.  Point number limited to 10 chars
         including coma */
        char p[11];
        int npoints;

        char_strip(buf, ';');
        sscanf(buf, "%[^;] %[^\n]", tmp, buf);
        char_strip(tmp, ';');

        npoints = set->side ? 2 : 4;

        for (i = 0; i < npoints; ++i) {
            sscanf(tmp, "%[^,] %[^\n]", p, tmp);

            if (tmp[0] != ',' && i < (npoints - 1))
                G_fatal_error(_("Map: <%s>, Variable: <%s>: Require %d points "
                                "but has %d"),
                              mapname, set->setname, npoints, i + 1);

            if (sscanf(p, "%f", &set->points[i]) != 1)
                G_fatal_error(
                    _("Map: <%s>, Variable: <%s>: Points must be numeric  but "
                      "is: %s or space between '-' and digit"),
                    mapname, set->setname, p);

            char_strip(tmp, ',');

            if (i > 0 && (set->points[i] < set->points[i - 1]))
                G_fatal_error(_("Map: <%s>, Membership: <%s>: Points sequence "
                                "must be non-declining"),
                              mapname, set->setname);
        }

    } /* check number of points and order */

    { /* check if shape is valid (linear,sshaped,jshaped,gshaped) */
        int done = 1;
        STRING shapes[] = {"linear", "sshaped", "jshaped", "gshaped"};

        char_strip(buf, ';');
        sscanf(buf, "%[^;] %[^\n]", tmp, buf);

        done = 0;
        for (i = 0; i < 4; ++i)
            if (strcmp(tmp, shapes[i]) == 0) {
                done = 1;
                break;
            }

        if (done)
            set->shape = i;
        else
            G_fatal_error(
                _(" Map: <%s>, Variable: <%s>:  <shape> parameter must be: "
                  "<linear,sshaped,jshaped,gshaped> but is: <%s>"),
                mapname, set->setname, tmp);
    } /* end check if shape is valid */

    { /* check if hedge is valid  (integer) */
        char_strip(buf, ';');
        sscanf(buf, "%[^;] %[^\n]", tmp, buf);

        if (sscanf(tmp, "%d", &set->hedge) != 1)
            G_fatal_error(_("Map: <%s>, variable: <%s>: Hedge must be numeric  "
                            "but is: %s or space between '-' and digit"),
                          mapname, set->setname, tmp);

    } /* end check if hedge is valid */

    { /* check if height is valid  (float 0-1) */
        char_strip(buf, ';');
        sscanf(buf, "%[^}] %[^\n]", tmp, buf);

        if (sscanf(tmp, "%f", &set->height) != 1)
            G_fatal_error(_("Map: <%s>, Variable: <%s>: Height must be  "
                            "non-negative numeric lesser than 1 but is: %s"),
                          mapname, set->setname, tmp);

        if (set->height <= 0 || set->height > 1)
            G_fatal_error(_("Map: <%s>, Variable: <%s>: Height must be  "
                            "non-negative numeric lesser than 1 but is: %f"),
                          mapname, set->setname, set->height);

    } /* end check if height is valid */

    return 0;
}
