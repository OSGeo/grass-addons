/****************************************************************************
 *
 * MODULE:       i.wavelet
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      A (multi-source) temporal/spectral (de)recomposition.
 *               Decompose 2 levels of a raster in temporal/spectral dimension
 *               producing Hig-Pass 1 and 2 + Low-Pass 1 and 2 (4 outputs)
 *               (-i): Recompose temporal/spectral dimensions
 *               using as input [HP2 + LP2] to recreate LP1
 *               and using as input HP1 along with the recreated LP1
 *               to produced the new data set.
 *
 * COPYRIGHT:    (C) 2013 by the GRASS Development Team
 *
 *               This program is free software under the GNU Lesser General
 *               Public License. Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include <grass/imagery.h>
#include "wt.h"
#include "wt_haar.h"
#include "w_daubechies.h"

#define MAXFILES 10000

int main(int argc, char *argv[])
{
    struct Cell_head cellhd; /*region+header info */
    int nrows, ncols;
    int row, col;
    struct GModule *module;
    struct Option *input, *output;
    struct Option *ihp1, *ihp2, *ilp2;        /*Recompose*/
    struct Option *olp1, *ohp1, *ohp2, *olp2; /*Decompose*/
    struct Option *resolution;                /*wavelet resolution*/
    struct Flag *flag1, *flag2, *flag3;
    struct History history; /*metadata */
    struct Colors colors;   /*Color rules */

    /************************************/
    char *temp;   /*input raster name */
    char *result; /*output raster name */
    /*File Descriptors */
    int nfiles;
    int infd[MAXFILES];
    int outfd[MAXFILES];
    int outfd1[MAXFILES], outfd2[MAXFILES];
    int outfd3[MAXFILES], outfd4[MAXFILES];
    char **names;
    char **ptr;
    int i = 0, n = 0;
    void *outrast[MAXFILES];
    unsigned char *lp1[MAXFILES];
    unsigned char *lp2[MAXFILES];
    unsigned char *hp1[MAXFILES];
    unsigned char *hp2[MAXFILES];

    RASTER_MAP_TYPE in_data_type[MAXFILES]; /* 0=numbers  1=text */
    DCELL **outlp1, **outhp1, **outlp2, **outhp2;
    CELL val1, val2;
    int res = 0;     /*wavelet sample rate option*/
    char buffer[16]; /*create file names with number extensions*/

    /************************************/
    struct Ref ref;                           /*group handling Decompose*/
    struct Ref reflp2, refhp2, refhp1;        /*group handling Recompose*/
    int *fd0, *fd1, *fd2, *fd3, *fd4;         /*file descriptors group rasters*/
    /*DCELL **buf0,*buf1,*buf2,*buf3,*buf4;*/ /*buffers lines group rasters */
    /************************************/
    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("imagery"));
    G_add_keyword(_("wavelet"));
    G_add_keyword(_("fusion"));
    module->description =
        _("Decompostion/Recomposition in temporal dimension using wavelets");

    /* Define the different options for decomposition */
    input = G_define_standard_option(G_OPT_I_GROUP);
    input->key = _("input_group_to_decompose");
    input->required = NO;
    input->guisection = _("Decomposition");

    olp1 = G_define_standard_option(G_OPT_R_OUTPUT);
    olp1->key = _("output_lp1_from_decomposition");
    olp1->required = NO;
    olp1->guisection = _("Decomposition");
    olp2 = G_define_standard_option(G_OPT_R_OUTPUT);
    olp2->key = _("output_lp2_from_decomposition");
    olp2->required = NO;
    olp2->guisection = _("Decomposition");
    ohp1 = G_define_standard_option(G_OPT_R_OUTPUT);
    ohp1->key = _("output_hp1_from_decomposition");
    ohp1->required = NO;
    ohp1->guisection = _("Decomposition");
    ohp2 = G_define_standard_option(G_OPT_R_OUTPUT);
    ohp2->key = _("output_hp2_from_decomposition");
    ohp2->required = NO;
    ohp2->guisection = _("Decomposition");

    /* Define the different options for recomposition */
    ilp2 = G_define_standard_option(G_OPT_I_GROUP);
    ilp2->key = _("input_lp2_group_for_recomposition");
    ilp2->required = NO;
    ilp2->guisection = _("Recomposition");
    ihp1 = G_define_standard_option(G_OPT_I_GROUP);
    ihp1->key = _("input_hp1_group_for_recomposition");
    ihp1->required = NO;
    ihp1->guisection = _("Recomposition");
    ihp2 = G_define_standard_option(G_OPT_I_GROUP);
    ihp2->key = _("input_hp2_group_for_recomposition");
    ihp2->required = NO;
    ihp2->guisection = _("Recomposition");

    output = G_define_standard_option(G_OPT_R_INPUT);
    output->key = _("output_from_recomposition");
    output->required = NO;
    output->guisection = _("Recomposition");

    /* Define the different flags */
    flag1 = G_define_flag();
    flag1->key = 'i';
    flag1->description = _("Recomposition (Default: Decomposition)");
    flag1->guisection = _("Required");

    flag2 = G_define_flag();
    flag2->key = 'H';
    flag2->description = _("Use Haar wavelets");
    flag2->guisection = _("Wavelets");

    flag3 = G_define_flag();
    flag3->key = 'D';
    flag3->description = _(
        "Use Daubechies wavelets (specify resolution=4,6,8,10,12,14,16,18,20");
    flag3->guisection = _("Wavelets");

    /* Define the different values required */
    resolution = G_define_option();
    resolution->key = _("wavelet_sample_rate");
    resolution->key_desc = _("integer");
    resolution->type = TYPE_INTEGER;
    resolution->multiple = NO;
    resolution->description = _("4,6,8,10,12,14,16,18,20");
    resolution->required = NO;
    resolution->guisection = _("Wavelets");

    nfiles = 1;
    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    if (flag3->answer) {
        if (resolution->answer) {
            res = atoi(resolution->answer);
            if (res == 4 || res == 6 || res == 8 || res == 10 || res == 12 ||
                res == 14 || res == 16 || res == 18 || res == 20) {
                /** Good to go with Flag3 => Daubechies **/
            }
            else {
                G_fatal_error(
                    _("To use Daubechies, you need a valid resolution"));
            }
        }
        else {
            G_fatal_error(_("To use Daubechies, you need a valid resolution"));
        }
    }

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();
    DCELL *dc;
    if (!(flag1->answer)) {
        /* ****** DECOMPOSITION ******* */
        if (!I_get_group_ref(input->answer, &ref))
            G_fatal_error(_("Unable to read REF file for group <%s>"),
                          input->answer);
        if (ref.nfiles <= 0)
            G_fatal_error(_("Group <%s> contains no raster maps"),
                          input->answer);
        /* Read Imagery Group */
        fd0 = G_malloc(ref.nfiles * sizeof(int));
        DCELL **buf0 = (DCELL **)G_malloc(ref.nfiles * sizeof(DCELL *));
        for (n = 0; n < ref.nfiles; n++) {
            buf0[n] = Rast_allocate_d_buf();
            fd0[n] = Rast_open_old(ref.file[n].name, ref.file[n].mapset);
        }
        /* create temporal array */
        DCELL *dc = G_malloc(ref.nfiles * sizeof(DCELL *));
        DCELL *buf1 = G_malloc(ref.nfiles * sizeof(DCELL *));
        DCELL *buf2 = G_malloc(ref.nfiles * sizeof(DCELL *));
        DCELL *buf3 = G_malloc(ref.nfiles * sizeof(DCELL *));
        DCELL *buf4 = G_malloc(ref.nfiles * sizeof(DCELL *));
        /* Create New output raster files */
        for (n = 0; n < ref.nfiles; n++) {
            snprintf(buffer, sizeof(buffer), "%d", n);
            temp = strcat(olp1->answer, ".");
            result = strcat(temp, buffer);
            outfd1[n] = Rast_open_new(result, 1);
            outlp1[n] = Rast_allocate_d_buf();
            temp = strcat(ohp1->answer, ".");
            result = strcat(temp, buffer);
            outfd2[n] = Rast_open_new(result, 1);
            outhp1[n] = Rast_allocate_d_buf();
            temp = strcat(olp2->answer, ".");
            result = strcat(temp, buffer);
            outfd3[n] = Rast_open_new(result, 1);
            outlp2[n] = Rast_allocate_d_buf();
            temp = strcat(ohp2->answer, ".");
            result = strcat(temp, buffer);
            outfd4[n] = Rast_open_new(result, 1);
            outhp2[n] = Rast_allocate_d_buf();
        }
        /* read row */
        for (row = 0; row < nrows; row++) {
            for (n = 0; n < ref.nfiles; n++) {
                /* Read one row of the signal input images */
                Rast_get_d_row(fd0[n], buf0[n], row);
            }
            /* Process pixels */
            /* #pragma parallel default(shared) private(col)*/
            for (col = 0; col < ncols; col++) {
                /* Extract temporal array */
                for (n = 0; n < ref.nfiles; n++) {
                    dc[n] = buf0[n][col];
                }
                if (flag2->answer) {
                    dwt_haar_l2(dc, ref.nfiles, buf1, buf2, buf3, buf4);
                }
                else /*if (flag3->answer) which is daubechies only so far*/ {
                    dwt_l2(dc, ref.nfiles, buf1, buf2, buf3, buf4, d[res - 4],
                           d[res - 3], res);
                }
                for (n = 0; n < ref.nfiles; n++) {
                    ((DCELL **)outlp1)[n][col] = buf1[n];
                    ((DCELL **)outhp1)[n][col] = buf2[n];
                    ((DCELL **)outlp2)[n][col] = buf3[n];
                    ((DCELL **)outhp2)[n][col] = buf4[n];
                }
            }
            for (n = 0; n < ref.nfiles; n++) {
                Rast_put_d_row(fd1[n], outlp1[n]);
                Rast_put_d_row(fd2[n], outhp1[n]);
                Rast_put_d_row(fd3[n], outlp2[n]);
                Rast_put_d_row(fd4[n], outhp2[n]);
            }
        }
        for (n = 0; n < ref.nfiles; n++) {
            G_free(outlp1[n]);
            G_free(outlp2[n]);
            G_free(outhp1[n]);
            G_free(outhp2[n]);
            Rast_close(fd1[n]);
            Rast_close(fd2[n]);
            Rast_close(fd3[n]);
            Rast_close(fd4[n]);
        }
        G_free(dc);
        G_free(buf1);
        G_free(buf2);
        G_free(buf3);
        G_free(buf4);
    }
    else {
        /* ****** RECOMPOSITION ******* */
        if (!I_get_group_ref(ilp2->answer, &reflp2))
            G_fatal_error(_("Unable to read REF file for group <%s>"),
                          ilp2->answer);
        if (reflp2.nfiles <= 0)
            G_fatal_error(_("Group <%s> contains no raster maps"),
                          ilp2->answer);
        if (!I_get_group_ref(ihp2->answer, &refhp2))
            G_fatal_error(_("Unable to read REF file for group <%s>"),
                          ihp2->answer);
        if (refhp2.nfiles <= 0)
            G_fatal_error(_("Group <%s> contains no raster maps"),
                          ihp2->answer);
        if (!I_get_group_ref(ihp1->answer, &refhp1))
            G_fatal_error(_("Unable to read REF file for group <%s>"),
                          ihp1->answer);
        if (refhp1.nfiles <= 0)
            G_fatal_error(_("Group <%s> contains no raster maps"),
                          ihp1->answer);

        /* Read LP2 Imagery Group */
        fd0 = G_malloc(reflp2.nfiles * sizeof(int));
        DCELL **ibuf0 = (DCELL **)G_malloc(reflp2.nfiles * sizeof(DCELL *));
        for (n = 0; n < reflp2.nfiles; n++) {
            ibuf0[n] = Rast_allocate_d_buf();
            fd0[n] = Rast_open_old(reflp2.file[n].name, reflp2.file[n].mapset);
        }
        /* Read HP2 Imagery Group */
        fd1 = G_malloc(refhp2.nfiles * sizeof(int));
        DCELL **ibuf1 = (DCELL **)G_malloc(refhp2.nfiles * sizeof(DCELL *));
        for (n = 0; n < refhp2.nfiles; n++) {
            ibuf1[n] = Rast_allocate_d_buf();
            fd1[n] = Rast_open_old(refhp2.file[n].name, refhp2.file[n].mapset);
        }
        /* Read HP1 Imagery Group */
        fd2 = G_malloc(refhp1.nfiles * sizeof(int));
        DCELL **ibuf2 = (DCELL **)G_malloc(refhp1.nfiles * sizeof(DCELL *));
        for (n = 0; n < refhp1.nfiles; n++) {
            ibuf2[n] = Rast_allocate_d_buf();
            fd2[n] = Rast_open_old(refhp1.file[n].name, refhp1.file[n].mapset);
        }
        /* create temporal array */
        DCELL *rc = G_malloc(refhp1.nfiles * sizeof(DCELL *));
        DCELL *buf0 = G_malloc(reflp2.nfiles * sizeof(DCELL *));
        DCELL *buf1 = G_malloc(refhp2.nfiles * sizeof(DCELL *));
        DCELL *buf2 = G_malloc(refhp1.nfiles * sizeof(DCELL *));
        DCELL *buf3 =
            G_malloc(refhp1.nfiles * sizeof(DCELL *)); /*LP1 in functions*/
        /* Create New output raster files */
        DCELL **outbuf = (DCELL **)G_malloc(refhp1.nfiles * sizeof(DCELL *));
        for (n = 0; n < refhp1.nfiles; n++) {
            snprintf(buffer, sizeof(buffer), "%d", n);
            temp = strcat(output->answer, ".");
            result = strcat(temp, buffer);
            outfd[n] = Rast_open_new(result, 1);
            outrast[n] = Rast_allocate_d_buf();
        }
        /* read row */
        for (row = 0; row < nrows; row++) {
            /* Read one row of the input images */
            for (n = 0; n < reflp2.nfiles; n++)
                Rast_get_d_row(fd0[n], ibuf0[n], row);
            for (n = 0; n < refhp2.nfiles; n++)
                Rast_get_d_row(fd1[n], ibuf1[n], row);
            for (n = 0; n < refhp1.nfiles; n++)
                Rast_get_d_row(fd2[n], ibuf2[n], row);
            /* Process pixels */
            /* #pragma parallel default(shared) private(col)*/
            for (col = 0; col < ncols; col++) {
                /* Extract temporal array */
                for (n = 0; n < reflp2.nfiles; n++)
                    buf0[n] = ibuf0[n][col];
                for (n = 0; n < refhp2.nfiles; n++)
                    buf1[n] = ibuf1[n][col];
                for (n = 0; n < refhp1.nfiles; n++)
                    buf2[n] = ibuf2[n][col];
                if (flag2->answer) {
                    idwt_haar_l2(buf3, buf2, buf0, buf1, refhp1.nfiles, rc);
                }
                else /*if (flag3->answer) which is daubechies only so far*/ {
                    idwt_l2(buf3, buf2, buf0, buf1, refhp1.nfiles, rc,
                            d[res - 4], d[res - 3], res);
                }
                for (n = 0; n < refhp1.nfiles; n++)
                    ((DCELL **)outbuf)[n][col] = rc[n];
            }
            for (n = 0; n < refhp1.nfiles; n++)
                Rast_put_d_row(outfd[n], outbuf[n]);
        }
        for (n = 0; n < ref.nfiles; n++) {
            G_free(outlp1[n]);
            G_free(outlp2[n]);
            G_free(outhp1[n]);
            G_free(outhp2[n]);
            Rast_close(fd1[n]);
            Rast_close(fd2[n]);
            Rast_close(fd3[n]);
            Rast_close(fd4[n]);
        }
        G_free(buf0);
        G_free(buf1);
        G_free(buf2);
        G_free(buf3);
    }
    /* Color table from 0.0 to 1.0 */
    Rast_init_colors(&colors);
    val1 = 0;
    val2 = 1;
    Rast_add_c_color_rule(&val1, 0, 0, 0, &val2, 255, 255, 255, &colors);
    /* Metadata */
    Rast_short_history(result, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(result, &history);

    exit(EXIT_SUCCESS);
}
