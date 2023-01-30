/****************************************************************************
 *
 * MODULE:       r.jpdf
 * AUTHOR(S):    Thomas Huld <thomas.huld@jrc.ec.europa.eu> (original
 *                  contributor)
 * PURPOSE:
 * COPYRIGHT:    (C) 2015 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <math.h>

#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/stats.h>

void findBins(double start, double end, int numBins, double val, int *pos)
{
    int i;
    double step;

    if (val < start)
        *pos = 0;
    else if (val > end)
        *pos = numBins + 1;
    else {
        step = (end - start) / numBins;
        i = 1;
        while (val > start + i * step)
            i++;
        *pos = i;
    }
}

int main(int argc, char *argv[])
{
    struct GModule *module;
    struct {
        struct Option *input1, *input2, *output, *bins1, *bins2;
    } parm;
    struct {
        /* please, remove before GRASS 7 released */
        struct Flag *quiet;
    } flag;
    /*
            char *mapset1, *mapset2;
    */
    int i, j, l;
    int numdigits1, numdigits2;
    int fd1, fd2;
    int *output_fd;
    int num_inputs;
    int offset;
    int num_outputs;
    struct History history;
    double *jpdf;
    int nrows, ncols, ncells;
    int *counts;
    int row, col;
    int pos1, pos2;
    int nbins1, nbins2;
    double startVal1, endVal1, startVal2, endVal2;
    char output_format[16];
    char outputName[1024];
    double **raster1 = NULL, **raster2 = NULL;
    DCELL *data1cell, *data2cell;
    DCELL *cell1 = NULL;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("series"));
    module->description =
        _("From two series of input raster maps, calculates the joint "
          "probability function and outputs the probabilities of occurrence in "
          "the specified bins.");

    parm.output = G_define_standard_option(G_OPT_R_OUTPUT);
    parm.output->required = YES;
    parm.output->description =
        _("Prefix of output raster name, will be followed by bin numbers");
    parm.output->multiple = NO;
    parm.output->guisection = _("Output_options");

    parm.input1 = G_define_option();
    parm.input1->key = "input1";
    parm.input1->type = TYPE_STRING;
    parm.input1->required = YES;
    parm.input1->description = _("First set of input rasters");
    parm.input1->multiple = YES;
    parm.input1->guisection = _("Input_options");

    parm.input2 = G_define_option();
    parm.input2->key = "input2";
    parm.input2->type = TYPE_STRING;
    parm.input2->required = YES;
    parm.input2->description = _("Second set of input rasters");
    parm.input2->multiple = YES;
    parm.input2->guisection = _("Input_options");

    parm.bins1 = G_define_option();
    parm.bins1->key = "bins1";
    parm.bins1->type = TYPE_STRING;
    parm.bins1->required = YES;
    parm.bins1->description =
        _("Start value, end value, and number of bins for first independent "
          "variable (from first set of inputs)");
    parm.bins1->multiple = YES;

    parm.bins2 = G_define_option();
    parm.bins2->key = "bins2";
    parm.bins2->type = TYPE_STRING;
    parm.bins2->required = YES;
    parm.bins2->description =
        _("Start value, end value, and number of bins for second independent "
          "variable (from second set of inputs)");
    parm.bins2->multiple = YES;

    /* please, remove before GRASS 7 released */
    flag.quiet = G_define_flag();
    flag.quiet->key = 'q';
    flag.quiet->description = _("Run quietly");

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    /* please, remove before GRASS 7 released */
    if (flag.quiet->answer) {
        putenv("GRASS_VERBOSE=0");
        G_warning(_("The '-q' flag is superseded and will be removed "
                    "in future. Please use '--quiet' instead."));
    }

    /* process the input maps */
    for (i = 0; parm.input1->answers[i]; i++)
        ;
    num_inputs = i;

    /* The number of maps processed is the number in the shortest list */
    for (i = 0; parm.input2->answers[i]; i++)
        ;
    num_inputs = (i < num_inputs) ? i : num_inputs;

    if (num_inputs < 1)
        G_fatal_error(_("No input raster map(s) specified"));

    /*
            for (i = 0; i < num_inputs; i++) {
            struct input *p = &inputs[i];

            p->name = parm.input->answers[i];
            p->mapset = G_find_cell2(p->name, "");
            if (!p->mapset)
                    G_fatal_error(_("Raster map <%s> not found"), p->name);
            else
                    G_message(_("Reading raster map <%s>..."), p->name);
            p->fd = Rast_open_old(p->name, p->mapset);
            if (p->fd < 0)
                    G_fatal_error(_("Unable to open raster map <%s> in mapset
       <%s>"), p->name, p->mapset); p->buf = Rast_allocate_d_buf();
            }
    */

    /* process the output maps */

    if (sscanf(parm.bins1->answers[0], "%lf", &startVal1) != 1)
        G_fatal_error(
            _("Could not read starting value of first independent value."));
    if (sscanf(parm.bins1->answers[1], "%lf", &endVal1) != 1)
        G_fatal_error(
            _("Could not read end value of first independent value."));
    if (sscanf(parm.bins1->answers[2], "%d", &nbins1) != 1)
        G_fatal_error(
            _("Could not read number of bins for first independent value."));
    if (sscanf(parm.bins2->answers[0], "%lf", &startVal2) != 1)
        G_fatal_error(
            _("Could not read starting value of second independent value."));
    if (sscanf(parm.bins2->answers[1], "%lf", &endVal2) != 1)
        G_fatal_error(
            _("Could not read end value of second independent value."));
    if (sscanf(parm.bins2->answers[2], "%d", &nbins2) != 1)
        G_fatal_error(
            _("Could not read number of bins for second independent value."));

    if (nbins1 <= 0) {
        G_fatal_error(_("Number of bins for first independent must be >0."));
    }
    if (nbins2 <= 0) {
        G_fatal_error(
            _("Number of bins for second independent value must be >0."));
    }

    numdigits1 = (int)(log10(1.0 * nbins1)) + 1;
    numdigits2 = (int)(log10(1.0 * nbins2)) + 1;

    sprintf(output_format, "%%s_%%0%dd_%%0%dd", numdigits1, numdigits2);

    num_outputs =
        (nbins1 + 2) * (nbins2 + 2); /* Extra rasters for bins containing values
                                        outside the range given by the user */

    output_fd = G_malloc(num_outputs * sizeof(int));

    for (i = 0; i < nbins1 + 2; i++) {
        for (j = 0; j < nbins2 + 2; j++) {
            sprintf(outputName, output_format, parm.output->answer, i, j);
            output_fd[i * (nbins2 + 2) + j] =
                Rast_open_new(outputName, DCELL_TYPE);
        }
    }

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();
    ncells = nrows * ncols;

    counts = (int *)G_malloc(nrows * ncols * sizeof(int));
    memset(counts, 0, nrows * ncols * sizeof(int));

    jpdf =
        G_malloc((nbins1 + 2) * (nbins2 + 2) * nrows * ncols * sizeof(DCELL));
    memset(jpdf, 0,
           (nbins1 + 2) * (nbins2 + 2) * nrows * ncols * sizeof(DCELL));

    /* process the data */
    G_verbose_message(_("Percent complete..."));

    if (raster1 == NULL) {

        data1cell = Rast_allocate_d_buf();
        data2cell = Rast_allocate_d_buf();

        raster1 = (double **)G_malloc(sizeof(double *) * (nrows));
        raster2 = (double **)G_malloc(sizeof(double *) * (nrows));

        for (l = 0; l < nrows; l++) {
            raster1[l] = (double *)G_malloc(sizeof(double) * (ncols));
            raster2[l] = (double *)G_malloc(sizeof(double) * (ncols));
        }
    }

    for (i = 0; i < num_inputs; i++) {
        /*
                        mapset1 = G_find_cell2(parm.input1->answers[i], "");
                        mapset2 = G_find_cell2(parm.input2->answers[i], "");
                        if (!mapset1)
                                        G_fatal_error(_("Raster map <%s> not
           found"), parm.input1->answers[i]); else if (!mapset2)
                                        G_fatal_error(_("Raster map <%s> not
           found"), parm.input2->answers[i]);
        */
        G_message(_("Processing raster map <%s> and <%s>..."),
                  parm.input1->answers[i], parm.input2->answers[i]);
        fd1 = Rast_open_old(parm.input1->answers[i], "");
        if (fd1 < 0)
            G_fatal_error(_("Unable to open raster map <%s> "),
                          parm.input1->answers[i]);
        fd2 = Rast_open_old(parm.input2->answers[i], "");
        if (fd2 < 0)
            G_fatal_error(_("Unable to open raster map <%s> "),
                          parm.input2->answers[i]);

        for (row = 0; row < nrows; row++) {
            Rast_get_d_row(fd1, data1cell, row);
            Rast_get_d_row(fd2, data2cell, row);
            for (col = 0; col < ncols; col++) {

                raster1[row][col] = (double)data1cell[col];

                raster2[row][col] = (double)data2cell[col];
            }
        }
        Rast_close(fd1);
        Rast_close(fd2);
        for (row = 0; row < nrows; row++) {
            for (col = 0; col < ncols; col++) {
                if (!Rast_is_d_null_value(&(raster1[row][col])) &&
                    !Rast_is_d_null_value(&(raster2[row][col]))) {
                    findBins(startVal1, endVal1, nbins1, raster1[row][col],
                             &pos1);
                    findBins(startVal2, endVal2, nbins2, raster2[row][col],
                             &pos2);
                    offset = ncells * ((nbins2 + 2) * pos1 + pos2);
                    jpdf[offset + row * ncols + col]++;
                    counts[row * ncols + col]++;
                }
            }
        }
    }

    offset = 0;
    for (i = 0; i < (nbins1 + 2) * (nbins2 + 2); i++) {
        offset = i * nrows * ncols;
        for (j = 0; j < nrows * ncols; j++)
            jpdf[offset + j] /= counts[j];
    }

    cell1 = Rast_allocate_d_buf();

    offset = 0;
    for (i = 0; i < nbins1 + 2; i++) {
        for (j = 0; j < nbins2 + 2; j++) {
            for (row = 0; row < nrows; row++) {

                for (col = 0; col < ncols; col++) {
                    cell1[col] = (DCELL)jpdf[offset + row * ncols + col];
                }
                Rast_put_d_row(output_fd[i * (nbins2 + 2) + j], cell1);

            } /* End loop over rows. */
            Rast_close(output_fd[i * (nbins2 + 2) + j]);

            offset += ncells;
        }
    }

    /*
    G_short_history(out->name, "raster", &history);
    G_write_history(out->name, &history);
    */
    Rast_command_history(&history);

    exit(EXIT_SUCCESS);
}
