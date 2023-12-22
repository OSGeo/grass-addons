/*****************************************************************************
 *
 * MODULE:       r.pi.export
 * AUTHOR(S):    Elshad Shirinov, Dr. Martin Wegmann
 *               Markus Metz (update to GRASS 7)
 * PURPOSE:      Export of patch based raster information
 *
 * COPYRIGHT:    (C) 2009-2011,2017 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

#define MAIN

#include "local_proto.h"

struct statmethod {
    f_statmethod *method; /* routine to compute new value */
    char *name;           /* method name */
    char *text;           /* menu display - full description */
    char *suffix;         /* output suffix */
};

static struct statmethod statmethods[] = {
    {average, "average", "average of values", "avg"},
    {variance, "variance", "variance of values", "var"},
    {std_deviat, "standard deviation", "standard deviation of values", "dev"},
    {median, "median", "median of values", "med"},
    {min, "min", "minimum of values", "min"},
    {max, "max", "maximum of values", "max"},
    {0, 0, 0, 0}};

int main(int argc, char *argv[])
{
    /* input */
    char *oldname;
    const char *oldmapset;

    /* id raster */
    char *idname;

    /* patch raster */
    char *patchname;

    /* in and out file pointers */
    int in_fd;
    FILE *out_fp; /* ASCII - output */

    int out_fd;

    /* parameters */
    int stats[GNAME_MAX];
    int stat_count;
    int neighb_count;

    /* maps */
    DCELL *map;

    /* helper variables */
    int row, col;
    int *result;
    int i, j, n;
    Coords *p;
    char *str;
    int method;
    f_statmethod *perform_method;
    DCELL val;
    DCELL *values;
    int count;
    DCELL area;
    int fragcount;

    struct GModule *module;
    struct {
        struct Option *input, *output;
        struct Option *values, *id_rast;
        struct Option *patch_rast, *stats;
        struct Option *title;
    } parm;
    struct {
        struct Flag *adjacent;
    } flag;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("landscape structure analysis"));
    G_add_keyword(_("patch index"));
    module->description = _("Export of patch based information.");

    parm.input = G_define_standard_option(G_OPT_R_INPUT);

    parm.output = G_define_option();
    parm.output->key = "output";
    parm.output->type = TYPE_STRING;
    parm.output->required = YES;
    parm.output->gisprompt = "new_file,file,output";
    parm.output->description = _("Name for the output ASCII-file");

    parm.values = G_define_option();
    parm.values->key = "values";
    parm.values->type = TYPE_STRING;
    parm.values->required = NO;
    parm.values->gisprompt = "new_file,file,output";
    parm.values->description =
        _("Name for the output ASCII-file with patch values");

    parm.id_rast = G_define_option();
    parm.id_rast->key = "id_raster";
    parm.id_rast->type = TYPE_STRING;
    parm.id_rast->required = NO;
    parm.id_rast->gisprompt = "new,cell,raster";
    parm.id_rast->description = _("Name for the ID raster map");

    parm.patch_rast = G_define_option();
    parm.patch_rast->key = "patch_raster";
    parm.patch_rast->type = TYPE_STRING;
    parm.patch_rast->required = NO;
    parm.patch_rast->gisprompt = "new,cell,raster";
    parm.patch_rast->description = _("Name for the patch raster map");

    parm.stats = G_define_option();
    parm.stats->key = "stats";
    parm.stats->type = TYPE_STRING;
    parm.stats->required = YES;
    parm.stats->multiple = YES;
    str = G_malloc(1024);
    for (n = 0; statmethods[n].name; n++) {
        if (n)
            strcat(str, ",");
        else
            *str = 0;
        strcat(str, statmethods[n].name);
    }
    parm.stats->options = str;
    parm.stats->description = _("Statistical method to perform on the values");

    parm.title = G_define_option();
    parm.title->key = "title";
    parm.title->key_desc = "\"phrase\"";
    parm.title->type = TYPE_STRING;
    parm.title->required = NO;
    parm.title->description = _("Title for resultant raster map");

    flag.adjacent = G_define_flag();
    flag.adjacent->key = 'a';
    flag.adjacent->description =
        _("Set for 8 cell-neighbors. 4 cell-neighbors are default");

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    /* get name of input file */
    oldname = parm.input->answer;

    /* test input files existance */
    oldmapset = G_find_raster2(oldname, "");
    if (oldmapset == NULL)
        G_fatal_error(_("Raster map <%s> not found"), oldname);

    /* get number of cell-neighbors */
    neighb_count = flag.adjacent->answer ? 8 : 4;

    /* check if the id file name is correct */
    idname = parm.id_rast->answer;
    if (G_legal_filename(idname) < 0)
        G_fatal_error(_("<%s> is an illegal file name"), idname);

    /* check if the patch file name is correct */
    patchname = parm.patch_rast->answer;
    if (G_legal_filename(patchname) < 0)
        G_fatal_error(_("<%s> is an illegal file name"), patchname);

    /* get size */
    sx = Rast_window_cols();
    sy = Rast_window_rows();

    /* scan all statmethod answers */
    stat_count = 0;
    while (parm.stats->answers[stat_count] != NULL) {
        /* get actual method */
        for (method = 0; (str = statmethods[method].name); method++)
            if (strcmp(str, parm.stats->answers[stat_count]) == 0)
                break;
        if (!str) {
            G_warning(_("<%s=%s> unknown %s"), parm.stats->key,
                      parm.stats->answers[stat_count], parm.stats->key);
            G_usage();
            exit(EXIT_FAILURE);
        }

        stats[stat_count] = method;

        stat_count++;
    }

    /* allocate map buffers */
    cells = (Coords *)G_malloc(sx * sy * sizeof(Coords));
    fragments = (Coords **)G_malloc(sx * sy * sizeof(Coords *));
    fragments[0] = cells;
    map = (DCELL *)G_malloc(sx * sy * sizeof(DCELL));
    id_map = (int *)G_malloc(sx * sy * sizeof(int));
    result = Rast_allocate_c_buf();

    Rast_set_c_null_value(id_map, sx * sy);

    /* open map */
    in_fd = Rast_open_old(oldname, oldmapset);
    if (in_fd < 0)
        G_fatal_error(_("Unable to open raster map <%s>"), oldname);

    /* read map */
    G_message("Reading map:");
    for (row = 0; row < sy; row++) {
        Rast_get_d_row(in_fd, map + row * sx, row);

        G_percent(row, sy, 2);
    }
    G_percent(1, 1, 2);

    /* close map */
    Rast_close(in_fd);

    /* find fragments */
    fragcount = writeFragments_DCELL(map, sy, sx, neighb_count);

    G_message("Writing output...");

    /* open ASCII-file or use stdout */
    if (parm.values->answer) {
        if (strcmp(parm.values->answer, "-") != 0) {
            if (!(out_fp = fopen(parm.values->answer, "w"))) {
                G_fatal_error(_("Error creating file <%s>"),
                              parm.values->answer);
            }
        }
        else {
            out_fp = stdout;
        }

        /* write values */
        for (i = 0; i < fragcount; i++) {
            area = fragments[i + 1] - fragments[i];

            values = (DCELL *)G_malloc(area * sizeof(DCELL));
            for (p = fragments[i], j = 0; p < fragments[i + 1]; p++, j++) {
                values[j] = p->value;
            }

            /* write patch index */
            fprintf(out_fp, "%d %f", i, area / (sx * sy));

            /* write patch value */
            for (method = 0; method < stat_count; method++) {
                DCELL outval;

                perform_method = statmethods[stats[method]].method;
                outval = perform_method(values, area);

                fprintf(out_fp, " %f", outval);
            }
            fprintf(out_fp, "\n");

            G_free(values);
        }

        /* close file */
        if (out_fp != stdout) {
            fclose(out_fp);
        }
        else {
            fprintf(out_fp, "\n");
        }
    }

    /* open ASCII-file or use stdout */
    if (parm.output->answer && strcmp(parm.output->answer, "-") != 0) {
        if (!(out_fp = fopen(parm.output->answer, "w"))) {
            G_fatal_error(_("Error creating file <%s>"), parm.output->answer);
        }
    }
    else {
        out_fp = stdout;
    }

    /* write method names */
    for (method = 0; method < stat_count; method++) {
        fprintf(out_fp, "%s ", statmethods[stats[method]].suffix);
    }
    fprintf(out_fp, "landcover number\n");

    /* allocate an array for cell values */
    count = fragments[fragcount] - fragments[0];
    values = (DCELL *)G_malloc(count * sizeof(DCELL));
    for (p = fragments[0], j = 0; p < fragments[fragcount]; p++, j++) {
        values[j] = p->value;
    }

    /* write values */
    for (method = 0; method < stat_count; method++) {
        perform_method = statmethods[stats[method]].method;
        val = perform_method(values, count);
        fprintf(out_fp, "%f ", val);
    }

    /* write landcover and number of patches */
    area = fragments[fragcount] - fragments[0];
    fprintf(out_fp, "%f %d\n", (DCELL)area / (DCELL)(sx * sy), fragcount);

    G_free(values);

    /* close file */
    if (parm.output->answer && strcmp(parm.output->answer, "-") != 0) {
        fclose(out_fp);
    }

    /* write id raster */
    if (idname) {
        /* open new cellfile  */
        out_fd = Rast_open_new(idname, CELL_TYPE);
        if (out_fd < 0)
            G_fatal_error(_("Cannot create raster map <%s>"), idname);

        /* write the output file */
        for (row = 0; row < sy; row++) {
            Rast_put_c_row(out_fd, id_map + row * sx);

            G_percent(row + 1, 2 * sy, 1);
        }

        /* close output */
        Rast_close(out_fd);
    }

    /* write patch raster */
    if (patchname) {
        /* open new cellfile  */
        out_fd = Rast_open_new(patchname, CELL_TYPE);
        if (out_fd < 0)
            G_fatal_error(_("Cannot create raster map <%s>"), patchname);

        /* write the output file */
        for (row = 0; row < sy; row++) {
            Rast_set_c_null_value(result, sx);
            for (col = 0; col < sx; col++) {
                if (!Rast_is_c_null_value(id_map + row * sx + col)) {
                    result[col] = 1;
                }
            }
            Rast_put_c_row(out_fd, result);

            G_percent(sy + row + 1, 2 * sy, 1);
        }

        /* close output */
        Rast_close(out_fd);
    }

    /* free allocated resources */
    G_free(map);

    exit(EXIT_SUCCESS);
}
