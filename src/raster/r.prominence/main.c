/****************************************************************************
 *
 * MODULE:       r.prominence
 * AUTHOR(S):    Benjamin Ducke, UK
 * PURPOSE:      calculates terain prominence in a DEM
 * COPYRIGHT:    (C) 2009 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the COPYING file that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <math.h>

#include <grass/gis.h>
#include <grass/raster.h>

#define PROGVERSION 1.0

int main(int argc, char *argv[])
{
    struct GModule *module;
    struct {
        struct Option *input;
        struct Option *output;
        struct Option *radius;
    } parm;
    struct {
        struct Flag *localnorm;
        struct Flag *globalnorm;
        struct Flag *rect;
        struct Flag *absolute;
        struct Flag *quiet;
    } flag;
    char *sysstr;
    const char *mapset;
    int i, j, radius, n, x, y;
    int a, b, dist;
    int firstrun;
    int nullvalue;
    double centerval;
    double sum, prominence;
    double min, max;
    double from, to;
    int nrows, ncols;
    int fd, fd_out;
    struct Cell_head region;
    struct Colors colors;
    struct History history;
    DCELL *diskrow = NULL;
    DCELL *outrow = NULL;

    sysstr = G_calloc(512, sizeof(char));

    module = G_define_module();
    module->description = "Calculates Llobera's prominence index";
    /* setup some basic GIS stuff */
    G_gisinit(argv[0]);

    parm.input = G_define_standard_option(G_OPT_R_INPUT);
    parm.input->key = "input";
    parm.input->type = TYPE_STRING;
    parm.input->required = YES;
    parm.input->gisprompt = "old,fcell";
    parm.input->description = "FP raster map for which to calculate index";

    parm.output = G_define_standard_option(G_OPT_R_OUTPUT);
    parm.output->key = "output";
    parm.output->type = TYPE_STRING;
    parm.output->required = YES;
    parm.output->gisprompt = "fcell";
    parm.output->description = "FP raster to store output";

    parm.radius = G_define_option();
    parm.radius->key = "radius";
    parm.radius->type = TYPE_INTEGER;
    parm.radius->required = YES;
    parm.radius->description = "Radius of neighbourhood in map cells";

    flag.absolute = G_define_flag();
    flag.absolute->key = 'a';
    flag.absolute->description = "Calculate absolute differences";

    flag.localnorm = G_define_flag();
    flag.localnorm->key = 'l';
    flag.localnorm->description = "Local data normalisation";

    flag.globalnorm = G_define_flag();
    flag.globalnorm->key = 'g';
    flag.globalnorm->description = "Global data normalisation";

    flag.rect = G_define_flag();
    flag.rect->key = 'r';
    flag.rect->description = "Use quadratic neighbourhood";

    flag.quiet = G_define_flag();
    flag.quiet->key = 'q';
    flag.quiet->description = "Disable on-screen progress display";

    /* parse command line */
    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    G_get_window(&region);
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    /* check parameters for validity */
    radius = atoi(parm.radius->answer);
    if ((radius < 1) || (radius > nrows / 2) || (radius > ncols / 2)) {
        G_fatal_error("Radius in rows/columns must be > 1 and smaller than "
                      "half the map's extent in both directions.");
    }
    if ((flag.localnorm->answer) && (flag.globalnorm->answer)) {
        G_fatal_error("Please choose either local OR global normalisation.");
    }
    mapset = G_calloc(512, sizeof(char));
    mapset = G_find_raster(parm.input->answer, "");
    if (mapset == NULL) {
        G_fatal_error("Input map does not exist in the current location.");
    }
    if (!Rast_map_is_fp(parm.input->answer, mapset)) {
        G_fatal_error("Input map is not a floating point map.\nOnly floating "
                      "point maps are allowed as input maps.");
    }
    fd = Rast_open_old(parm.input->answer, mapset);
    if (fd < 0) {
        G_fatal_error("Could not open input map for reading!\n");
    }
    if (!G_legal_filename(parm.output->answer)) {
        G_fatal_error("%s is not a legal filename for an output map.\n",
                      parm.output->answer);
    }
    fd_out = Rast_open_new(parm.output->answer, DCELL_TYPE);
    if (fd_out < 0) {
        G_fatal_error("Could not open output map for writing!\n");
    }

    diskrow = Rast_allocate_d_buf();
    outrow = Rast_allocate_d_buf();

    /* initialize statistics */
    n = 0;
    firstrun = 1;
    min = 0;
    max = 0;
    sum = 0.0;

    if (!flag.quiet->answer) {
        fprintf(stdout, "Calculating prominence index:\n");
        fflush(stdout);
    }

    /* main loop: read raster row from disk, add to values in neighbourhood */
    i = 0;
    j = 0;
    nullvalue = 0;
    for (y = 0; y < nrows; y++) {
        for (x = 0; x < ncols; x++) {
            Rast_get_d_row(fd, diskrow, y);
            centerval = diskrow[x];
            if (Rast_is_d_null_value(&diskrow[x])) {
                nullvalue = 1;
            }
            else {
                nullvalue = 0;
                for (j = y - radius; j <= y + radius; j++) {
                    if ((j > 0) && (j < nrows)) {
                        Rast_get_d_row(fd, diskrow, j);
                        nullvalue = 0;
                        for (i = x - radius; i <= x + radius; i++) {
                            if (((i != x) || (j != y)) && (i > 0) &&
                                (i < ncols)) {
                                if (!Rast_is_d_null_value(&diskrow[i])) {
                                    if (flag.rect->answer) {
                                        /* use rectangular neighbourhood */
                                        n = n + 1;
                                        if (flag.absolute->answer) {
                                            sum = sum +
                                                  fabs(centerval - diskrow[i]);
                                        }
                                        else {
                                            sum =
                                                sum + (centerval - diskrow[i]);
                                        }
                                    }
                                    else {
                                        /* use circular neighbourhood */
                                        a = abs(x - i);
                                        b = abs(y - j);
                                        dist = (int)sqrt((double)(a * a) +
                                                         (b * b));
                                        if (dist <= radius) {
                                            n = n + 1;
                                            if (flag.absolute->answer) {
                                                sum = sum + fabs(centerval -
                                                                 diskrow[i]);
                                            }
                                            else {
                                                sum = sum +
                                                      (centerval - diskrow[i]);
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            /* write one cell to output map */
            prominence = sum / n;
            if (!nullvalue) {
                outrow[x] = prominence;
            }
            else {
                Rast_set_d_null_value(&outrow[x], 1);
            }
            if (firstrun) {
                min = prominence;
                max = prominence;
                firstrun = 0;
            }
            else {
                if (prominence < min)
                    min = prominence;
                if (prominence > max)
                    max = prominence;
            }
            n = 0;
            sum = 0.0;
        }
        /* write one row to output map on disk */
        Rast_put_row(fd_out, outrow, DCELL_TYPE);

        if (!flag.quiet->answer) {
            G_percent(y, nrows - 1, 1);
            fflush(stdout);
        }
    }

    Rast_close(fd);
    Rast_close(fd_out);

    if (flag.localnorm->answer) {
        if (!flag.quiet->answer) {
            fprintf(stdout, "\nNormalising data by neighbourhood maximum:\n");
            fflush(stdout);
        }
        /* re-open output map for reading */
        fd = Rast_open_old(parm.output->answer, G_mapset());
        if (fd < 0) {
            G_fatal_error(
                "Could not open output map for normalisation pass!\n");
        }
        strcpy(sysstr, parm.output->answer);
        strcat(sysstr, ".localnorm");
        fd_out = Rast_open_new(sysstr, DCELL_TYPE);
        if (fd_out < 0) {
            G_fatal_error("Could not open temporary map for normalisation pass "
                          "(write access)!\n");
        }

        i = 0;
        j = 0;
        for (y = 0; y < nrows; y++) {
            for (x = 0; x < ncols; x++) {
                Rast_get_d_row(fd, diskrow, y);
                centerval = diskrow[x];
                min = diskrow[x];
                max = diskrow[x];
                if (Rast_is_d_null_value(&diskrow[x])) {
                    nullvalue = 1;
                }
                else {
                    nullvalue = 0;
                    for (j = y - radius; j <= y + radius; j++) {
                        if ((j > 0) && (j < nrows)) {
                            Rast_get_d_row(fd, diskrow, j);
                            nullvalue = 0;
                            for (i = x - radius; i <= x + radius; i++) {
                                if (((i != x) || (j != y)) && (i > 0) &&
                                    (i < ncols)) {
                                    if (!Rast_is_d_null_value(&diskrow[i])) {
                                        if (flag.rect->answer) {
                                            /* use rectangular neighbourhood */
                                            if (diskrow[i] > max) {
                                                max = diskrow[i];
                                            }
                                            if (diskrow[i] < min) {
                                                min = diskrow[i];
                                            }
                                        }
                                        else {
                                            /* use circular neighbourhood */
                                            a = abs(x - i);
                                            b = abs(y - j);
                                            dist = (int)sqrt((double)(a * a) +
                                                             (b * b));
                                            if (dist <= radius) {
                                                if (diskrow[i] > max) {
                                                    max = diskrow[i];
                                                }
                                                if (diskrow[i] < min) {
                                                    min = diskrow[i];
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                /* write one cell to output map */
                if (!nullvalue) {
                    if (flag.absolute->answer) {
                        outrow[x] = (centerval - min) / (max - min);
                    }
                    else {
                        if (min < 0) {
                            if (centerval < 0) {
                                outrow[x] = centerval / fabs(min);
                            }
                            if (centerval > 0) {
                                outrow[x] = centerval / max;
                            }
                            if (centerval == 0) {
                                outrow[x] = 0;
                            }
                        }
                        else {
                            outrow[x] = (centerval - min) / (max - min);
                        }
                    }
                }
                else {
                    Rast_set_d_null_value(&outrow[x], 1);
                }
            }
            /* write one row to output map on disk */
            Rast_put_row(fd_out, outrow, DCELL_TYPE);

            if (!flag.quiet->answer) {
                G_percent(y, nrows - 1, 1);
                fflush(stdout);
            }
        }
        Rast_close(fd);
        Rast_close(fd_out);
    }

    if (flag.globalnorm->answer) {
        /* normalise evidence over total map */
        if (!flag.quiet->answer) {
            fprintf(stdout, "\nNormalising data by map maximum:\n");
            fflush(stdout);
        }
        /* re-open output map for reading */
        fd = Rast_open_old(parm.output->answer, G_mapset());
        if (fd < 0) {
            G_fatal_error(
                "Could not open output map for normalisation pass!\n");
        }
        strcpy(sysstr, parm.output->answer);
        strcat(sysstr, ".globalnorm");
        fd_out = Rast_open_new(sysstr, DCELL_TYPE);
        if (fd_out < 0) {
            G_fatal_error("Could not open temporary map for normalisation pass "
                          "(write access)!\n");
        }

        /* normalise evidence within map */
        for (y = 0; y < nrows; y++) {
            Rast_get_d_row(fd, diskrow, y);
            for (x = 0; x < ncols; x++) {
                /* write one cell to output map */
                if (!Rast_is_d_null_value(&diskrow[x])) {
                    if (flag.absolute->answer) {
                        outrow[x] = (diskrow[x] - min) / (max - min);
                    }
                    else {
                        if (min < 0) {
                            if (diskrow[x] < 0) {
                                outrow[x] = diskrow[x] / fabs(min);
                            }
                            if (diskrow[x] > 0) {
                                outrow[x] = diskrow[x] / max;
                            }
                            if (diskrow[x] == 0) {
                                outrow[x] = 0;
                            }
                        }
                        else {
                            outrow[x] = (diskrow[x] - min) / (max - min);
                        }
                    }
                }
                else {
                    Rast_set_d_null_value(&outrow[x], 1);
                }
            }
            /* write one row to output map on disk */
            Rast_put_row(fd_out, outrow, DCELL_TYPE);

            if (!flag.quiet->answer) {
                G_percent(y, nrows - 1, 1);
                fflush(stdout);
            }
        }
        Rast_close(fd);
        Rast_close(fd_out);
    }

    /* if normalisation was done, we delete the original map, and rename the
     * normalised one */
    if ((flag.localnorm->answer) || (flag.globalnorm->answer)) {
        G_remove("cats", parm.output->answer);
        G_remove("cell", parm.output->answer);
        G_remove("cell_hd", parm.output->answer);
        G_remove("cell_misc", parm.output->answer);
        G_remove("colr", parm.output->answer);
        G_remove("colr2", parm.output->answer);
        G_remove("fcell", parm.output->answer);
        G_remove("hist", parm.output->answer);
        G_rename("cats", sysstr, parm.output->answer);
        G_rename("cell", sysstr, parm.output->answer);
        G_rename("cell_hd", sysstr, parm.output->answer);
        G_rename("cell_misc", sysstr, parm.output->answer);
        G_rename("colr", sysstr, parm.output->answer);
        G_rename("colr2", sysstr, parm.output->answer);
        G_rename("fcell", sysstr, parm.output->answer);
        G_rename("hist", sysstr, parm.output->answer);
    }

    /* if the data was normalised, we need to rescale to get a good grey range
     */
    if ((flag.localnorm->answer) || (flag.globalnorm->answer)) {
        if (flag.absolute->answer) {
            min = 0;
            max = 1.0;
        }
        else {
            if (min < 0) {
                min = -1.0;
            }
            else {
                min = 0.0;
            }
            max = 1.0;
        }
    }

    /* write a colormap in grey shades: lowest prominence gets black, highest
     * white */
    Rast_init_colors(&colors);
    if ((flag.absolute->answer)) {
        from = min;
        to = max / 2;
        Rast_add_d_color_rule(&from, 0, 0, 0, &to, 127, 127, 127, &colors);
        from = max / 2;
        to = max;
        Rast_add_d_color_rule(&from, 128, 128, 128, &to, 255, 255, 255,
                              &colors);
    }
    else {
        if (min < 0) {
            from = min;
            to = min / 2;
            Rast_add_d_color_rule(&from, 255, 0, 0, &to, 127, 0, 0, &colors);
            from = min / 2;
            to = 0;
            Rast_add_d_color_rule(&from, 127, 0, 0, &to, 0, 0, 0, &colors);
            from = 0;
        }
        else {
            from = min;
        }
        to = max / 2;
        Rast_add_d_color_rule(&from, 0, 0, 0, &to, 127, 127, 127, &colors);
        from = max / 2;
        to = max;
        Rast_add_d_color_rule(&from, 128, 128, 128, &to, 255, 255, 255,
                              &colors);
    }
    Rast_write_colors(parm.output->answer, G_mapset(), &colors);
    Rast_free_colors(&colors);

    Rast_short_history(parm.output->answer, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(parm.output->answer, &history);

    G_free(diskrow);
    G_free(outrow);

    if (!flag.quiet->answer) {
        fprintf(stdout, "\nDone.\n");
        fflush(stdout);
    }

    exit(EXIT_SUCCESS);
}
