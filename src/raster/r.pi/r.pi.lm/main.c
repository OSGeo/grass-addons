/*****************************************************************************
 *
 * MODULE:       r.pi.lm
 * AUTHOR(S):    Elshad Shirinov, Dr. Martin Wegmann
 *               Markus Metz (update to GRASS 7)
 * PURPOSE:      Linear regression analysis for patches (not pixel based)
 *
 * COPYRIGHT:    (C) 2009-2011,2017 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

#include "local_proto.h"

int main(int argc, char *argv[])
{
    /* input */
    char *newname, *oldname1, *oldname2;
    const char *oldmapset1, *oldmapset2;

    /* in and out file pointers */
    int in_fd;
    int out_fd;

    /* parameters */
    int nbr_count;
    int patch_values;

    /* map_type and categories */
    RASTER_MAP_TYPE map_type;

    /* helpers */
    int i;
    DCELL *result;
    DCELL *map;
    int row, col;
    int nrows, ncols;
    DCELL *x, *y;
    int *flagbuf;
    int value_count;
    DCELL offset, slope, correlation, *residuals;

    struct GModule *module;
    struct {
        struct Option *input1, *input2, *output;
    } parm;
    struct {
        struct Flag *adjacent, *patch_values;
    } flag;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    module->description = _("Linear regression analysis for patches.");

    parm.input1 = G_define_standard_option(G_OPT_R_INPUT);
    parm.input1->key = "input1";

    parm.input2 = G_define_standard_option(G_OPT_R_INPUT);
    parm.input2->key = "input2";

    parm.output = G_define_standard_option(G_OPT_R_OUTPUT);

    flag.adjacent = G_define_flag();
    flag.adjacent->key = 'a';
    flag.adjacent->description =
        _("Set for 8 cell-neighbors. 4 cell-neighbors are default");

    flag.patch_values = G_define_flag();
    flag.patch_values->key = 'p';
    flag.patch_values->description = _("Set to use patch values");

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    /* get names of input files */
    oldname1 = parm.input1->answer;
    oldname2 = parm.input2->answer;

    /* test input files existance */
    oldmapset1 = G_find_raster2(oldname1, "");
    if (oldmapset1 == NULL)
        G_fatal_error(_("Raster map <%s> not found"), oldname1);
    oldmapset2 = G_find_raster2(oldname2, "");
    if (oldmapset2 == NULL)
        G_fatal_error(_("Raster map <%s> not found"), oldname2);

    /* check if the new file name is correct */
    newname = parm.output->answer;
    if (G_legal_filename(newname) < 0)
        G_fatal_error(_("<%s> is an illegal file name"), newname);

    /* get size */
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    /* get map type */
    map_type = DCELL_TYPE; /* G_raster_map_type(oldname, oldmapset); */

    /* get number of cell-neighbors */
    nbr_count = flag.adjacent->answer ? 8 : 4;

    /* get patch_values flag */
    patch_values = flag.patch_values->answer;

    /* allocate the cell buffers */
    map = (DCELL *)G_malloc(nrows * ncols * sizeof(DCELL));

    G_message("Loading patches...");

    /* open first cell file */
    in_fd = Rast_open_old(oldname1, oldmapset1);
    if (in_fd < 0)
        G_fatal_error(_("Unable to open raster map <%s>"), oldname1);

    /* read map */
    for (row = 0; row < nrows; row++) {
        Rast_get_d_row(in_fd, map + row * ncols, row);

        G_percent(row + 1, nrows, 1);
    }

    /*    G_message("Map:");
       for (row = 0; row < nrows; row++) {
       for (col = 0; col < ncols; col++) {
       fprintf(stderr, "%0.1f ", map[row * ncols + col]);
       }
       fprintf(stderr, "\n");
       } */

    /* close cell file */
    Rast_close(in_fd);

    /* open second cell file */
    in_fd = Rast_open_old(oldname2, oldmapset2);
    if (in_fd < 0)
        G_fatal_error(_("Unable to open raster map <%s>"), oldname2);

    /* gather pixel or patch values */
    /* TODO: patch values */
    result = Rast_allocate_d_buf();
    x = (DCELL *)malloc(nrows * ncols * sizeof(DCELL));
    y = (DCELL *)malloc(nrows * ncols * sizeof(DCELL));
    flagbuf = (int *)malloc(nrows * ncols * sizeof(int));

    /* initialize flag buffer with -1 */
    for (i = 0; i < nrows * ncols; i++) {
        flagbuf[i] = -1;
    }
    value_count = 0;

    for (row = 0; row < nrows; row++) {
        Rast_get_d_row(in_fd, result, row);

        for (col = 0; col < ncols; col++) {
            DCELL val = map[row * ncols + col];

            if (!Rast_is_d_null_value(&val)) {
                x[value_count] = val;
                y[value_count] = result[col];

                flagbuf[row * ncols + col] = value_count;

                if (patch_values) {
                    clearPatch(map, flagbuf, value_count, row, col, nrows,
                               ncols, nbr_count);

                    /*                    int r, c;
                       G_message("Map:");
                       for (r = 0; r < nrows; r++) {
                       for (c = 0; c < ncols; c++) {
                       fprintf(stderr, "%0.1f ", map[r * ncols + c]);
                       }
                       fprintf(stderr, "\n");
                       } */
                }

                value_count++;
            }
        }
    }

    printf("Values:\n");
    printf("X:");
    for (i = 0; i < value_count; i++) {
        printf(" %0.2f", x[i]);
    }
    printf("\n");
    printf("Y:");
    for (i = 0; i < value_count; i++) {
        printf(" %0.2f", y[i]);
    }
    printf("\n");

    residuals = (DCELL *)malloc(value_count * sizeof(DCELL));

    /* calculate data */
    linear_regression(x, y, value_count, &offset, &slope, residuals,
                      &correlation);

    /* free memory */
    G_free(x);
    G_free(y);

    /* close cell file */
    Rast_close(in_fd);

    /* write output */
    G_message("Writing output...");

    G_message("Offset: %f, Slope: %f, Correlation: %f\n", offset, slope,
              correlation);

    /* ==================================
       ============  output  ============
       ================================== */

    /* open the new cellfile  */
    out_fd = Rast_open_new(newname, map_type);
    if (out_fd < 0)
        G_fatal_error(_("Cannot create raster map <%s>"), newname);

    /* write values */
    for (row = 0; row < nrows; row++) {
        Rast_set_d_null_value(result, ncols);

        for (col = 0; col < ncols; col++) {
            int flagval = flagbuf[row * ncols + col];

            if (flagval >= 0) {
                result[col] = residuals[flagval];
            }
        }

        Rast_put_d_row(out_fd, result);

        G_percent(row + 1, nrows, 1);
    }

    /* close output file */
    Rast_close(out_fd);

    /* =====================
       ==== free memory ====
       ===================== */
    G_free(map);
    G_free(result);
    G_free(residuals);

    exit(EXIT_SUCCESS);
}
