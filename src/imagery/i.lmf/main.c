/****************************************************************************
 *
 * MODULE:       i.lmf
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Clean temporal signature using what is called
 *                  Local Maximum Fitting (LMF)
 *                  Initially created for Vegetation Indices from AVHRR.
 *
 *               Translated from Fortran, unconfused, removed unused and
 *               other redundant variables. Removed BSQ Binary loading.
 *
 *                  SHORT HISTORY OF THE CODE
 *                  -------------------------
 *               Original Fortran Beta-level code was written
 *               by Yoshito Sawada (2000), in OpenMP Fortran
 *               for SGI Workstation. Recovered broken code from
 *               their website in 2003, regenerated missing code and
 *               made it work in Linux.
 *               ORIGINAL WEBSITE
 *               ----------------
 *               http://www.affrc.go.jp/ANDES/sawady/index.html
 *               ENGLISH WEBSITE
 *               ---------------
 *               http://www.rsgis.ait.ac.th/~honda/lmf/lmf.html
 *
 * COPYRIGHT:    (C) 2008 by the GRASS Development Team
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

#define MAXFILES 366

int lmf(int nbands, int npoint, double *inpix, double *outpix);
int main(int argc, char *argv[])
{
    struct Cell_head cellhd; /*region+header info */
    char *mapset;            /*mapset name */
    int nrows, ncols;
    int row, col;
    struct GModule *module;
    struct Option *input, *ndate, *output;
    struct History history; /*metadata */
    char *name;             /*input raster name */
    char *result[MAXFILES]; /*output raster name */
    /*File Descriptors */
    int nfiles;
    int infd[MAXFILES];
    int outfd[MAXFILES];
    char **names;
    char **ptr;
    int ok;
    int i = 0, j = 0;
    void *inrast[MAXFILES];
    DCELL *outrast[MAXFILES];
    int data_format; /* 0=double  1=float  2=32bit signed int  5=8bit unsigned
                        int (ie text) */
    RASTER_MAP_TYPE in_data_type[MAXFILES]; /* 0=numbers  1=text */
    RASTER_MAP_TYPE out_data_type = DCELL_TYPE;
    int ndates;
    double inpix[MAXFILES] = {0.0};
    double outpix[MAXFILES] = {0.0};
    /************************************/

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("imagery"));
    G_add_keyword(_("LMF"));
    G_add_keyword(_("Vegetation Indices"));
    G_add_keyword(_("Atmospheric correction"));
    G_add_keyword(_("Temporal"));
    module->description =
        _("Performs Temporal Local Maximum Fitting of vegetation indices, "
          "works also for surface reflectance data.");

    /* Define the different options */

    input = G_define_standard_option(G_OPT_R_INPUTS);
    input->description = _("Names of input layers");

    ndate = G_define_option();
    ndate->key = _("ndate");
    ndate->type = TYPE_INTEGER;
    ndate->required = YES;
    ndate->gisprompt = _("parameter, integer");
    ndate->description = _("Number of map layers per year");

    output = G_define_standard_option(G_OPT_R_OUTPUT);
    output->description = _("Name of the output layer");

    nfiles = 1;
    /********************/
    if (G_parser(argc, argv))
        exit(-1);

    ok = 1;
    names = input->answers;
    ptr = input->answers;

    ndates = atoi(ndate->answer);

    for (; *ptr != NULL; ptr++) {
        if (nfiles >= MAXFILES)
            G_fatal_error(_("%s - too many ETa files. Only %d allowed"),
                          G_program_name(), MAXFILES);
        name = *ptr;
        if (!ok) {
            continue;
        }
        infd[nfiles] = Rast_open_old(name, "");
        if (infd[nfiles] < 0) {
            ok = 0;
            continue;
        }
        /* Allocate input buffer */
        in_data_type[nfiles] = Rast_map_type(name, "");
        infd[nfiles] = Rast_open_old(name, "");
        Rast_get_cellhd(name, "", &cellhd);
        inrast[nfiles] = Rast_allocate_buf(in_data_type[nfiles]);
        nfiles++;
    }
    nfiles--;
    if (nfiles <= 10) {
        G_fatal_error(_("The min specified input map is ten"));
    }

    /***************************************************/
    /* Allocate output buffer, use input map data_type */
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();
    for (i = 0; i < nfiles; i++) {
        sprintf(result[i], output->answer, ".", i + 1);
        outrast[i] = Rast_allocate_buf(out_data_type);
        /* Create New raster files */
        outfd[i] = Rast_open_new(result[i], 1);
    }
    /*******************/
    /* Process pixels */
    for (row = 0; row < nrows; row++) {
        DCELL de;
        DCELL d[MAXFILES];

        G_percent(row, nrows, 2);
        /* read input map */
        for (i = 1; i <= nfiles; i++) {
            Rast_get_row(infd[i], inrast[i], row, in_data_type[i]);
        }
        /*process the data */
        for (col = 0; col < ncols; col++) {
            for (i = 1; i <= nfiles; i++) {
                switch (in_data_type[i]) {
                case CELL_TYPE:
                    inpix[i - 1] = (double)((CELL *)inrast[i])[col];
                    break;
                case FCELL_TYPE:
                    inpix[i - 1] = (double)((FCELL *)inrast[i])[col];
                    break;
                case DCELL_TYPE:
                    inpix[i - 1] = (double)((DCELL *)inrast[i])[col];
                    break;
                }
            }
            lmf(nfiles, ndates, inpix, outpix);
            /* Put the resulting temporal curve
             * in the output layers */
            for (i = 0; i < nfiles; i++) {
                outrast[i][col] = outpix[i];
            }
        }
        for (i = 0; i < nfiles; i++) {
            Rast_put_row(outfd[i], outrast[i], out_data_type);
        }
    }
    for (i = 1; i <= nfiles; i++) {
        G_free(inrast[i]);
        Rast_close(infd[i]);
        G_free(outrast[i]);
        Rast_close(outfd[i]);
    }
    return 0;
}
