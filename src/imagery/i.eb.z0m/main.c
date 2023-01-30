/****************************************************************************
 *
 * MODULE:       i.eb.z0m
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Calculates the momentum roughness length
 *               as seen in Bastiaanssen (1995), Pawan (2004)
 *
 * COPYRIGHT:    (C) 2002-2013 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with
 *               GRASS for details.
 *
 *****************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>

double z0m_pawan(double sa_vi);
double z0m_bastiaanssen(double ndvi, double ndvi_max, double hv_ndvimax,
                        double hv_desert);

int main(int argc, char *argv[])
{
    struct Cell_head cellhd; /*region+header info */
    char *mapset;            /*mapset name */
    int nrows, ncols;
    int row, col;
    int heat = 0; /*Flag for surf. roughness for heat transport output */
    struct GModule *module;
    struct Option *input1, *input2, *input3, *input4;
    struct Option *output1, *output2;
    struct Flag *flag1, *flag2;
    struct History history; /*metadata */
    /************************************/
    char *name;              /*input raster name */
    char *result1, *result2; /*output raster name */
    /*File Descriptors */
    int infd_ndvi;
    int outfd1, outfd2;
    char *ndvi;
    char *z0m, *z0h;
    double coef_z0h, hv_max, hmr;
    int i = 0, j = 0;
    void *inrast_ndvi;
    DCELL *outrast1, *outrast2;
    RASTER_MAP_TYPE data_type_ndvi;
    /************************************/
    G_gisinit(argv[0]);
    module = G_define_module();
    G_add_keyword(_("imagery"));
    G_add_keyword(_("roughness length"));
    G_add_keyword(_("energy balance"));
    G_add_keyword(_("SEBAL"));
    module->description =
        _("Computes momentum roughness length (z0m) and surface roughness for "
          "heat transport (z0h) after Bastiaanssen (2004).");

    /* Define the different options */
    input1 = G_define_standard_option(G_OPT_R_INPUT);
    input1->description = _("Name of the NDVI map [-1.0;1.0], SAVI if -p flag");

    input2 = G_define_option();
    input2->key = _("coef");
    input2->type = TYPE_DOUBLE;
    input2->required = NO;
    input2->gisprompt = _("parameter,value");
    input2->description = _("Value of the conversion factor from z0m and z0h "
                            "(Bastiaanssen (2005) used 0.1), for -f flag");
    input2->answer = _("0.1");

    input3 = G_define_option();
    input3->key = _("hv_max");
    input3->type = TYPE_DOUBLE;
    input3->required = NO;
    input3->gisprompt = _("parameter,value");
    input3->description =
        _("Value of the vegetation height at max(NDVI) i.e. standard C3 crop "
          "could be 1.5m, not needed for -p flag");
    input3->answer = _("1.5");

    input4 = G_define_option();
    input4->key = _("hmr");
    input4->type = TYPE_DOUBLE;
    input4->required = NO;
    input4->gisprompt = _("parameter,value");
    input4->description =
        _("Value of the micro-relief height (h.m-r.) on flat bare ground, most "
          "references point to 2cm, not need for -p flag");
    input4->answer = _("0.02");

    output1 = G_define_standard_option(G_OPT_R_OUTPUT);
    output1->description = _("Name of the output z0m layer");

    output2 = G_define_standard_option(G_OPT_R_OUTPUT);
    output2->key = _("z0h");
    output2->required = NO;
    output2->description = _("Name of the output z0h layer");

    flag2 = G_define_flag();
    flag2->key = 'p';
    flag2->description = _("Use SAVI input only with equation of Pawan (2004)");

    /********************/
    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);
    ndvi = input1->answer;
    if (input2->answer)
        coef_z0h = atof(input2->answer);
    if (input3->answer)
        hv_max = atof(input3->answer);
    if (input4->answer)
        hmr = atof(input4->answer);
    result1 = output1->answer;
    if (output2->answer)
        result2 = output2->answer;
    /***************************************************/
    data_type_ndvi = Rast_map_type(ndvi, "");
    infd_ndvi = Rast_open_old(ndvi, "");
    Rast_get_cellhd(ndvi, "", &cellhd);
    inrast_ndvi = Rast_allocate_buf(data_type_ndvi);
    /***************************************************/
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();
    /***************************************************/
    outrast1 = Rast_allocate_d_buf();
    outfd1 = Rast_open_new(result1, DCELL_TYPE);
    if (input2->answer && output2->answer) {
        outrast2 = Rast_allocate_d_buf();
        outfd2 = Rast_open_new(result2, DCELL_TYPE);
    }
    DCELL d_ndvi;           /* Input raster */
    DCELL d_ndvi_max = 0.0; /* Generated here */

    /* NDVI Max */
    if (flag2->answer) {
        /* skip it */
    }
    else {
        for (row = 0; row < nrows; row++) {
            G_percent(row, nrows, 2);
            Rast_get_row(infd_ndvi, inrast_ndvi, row, data_type_ndvi);
            for (col = 0; col < ncols; col++) {
                switch (data_type_ndvi) {
                case CELL_TYPE:
                    d_ndvi = (double)((CELL *)inrast_ndvi)[col];
                    break;
                case FCELL_TYPE:
                    d_ndvi = (double)((FCELL *)inrast_ndvi)[col];
                    break;
                case DCELL_TYPE:
                    d_ndvi = (double)((DCELL *)inrast_ndvi)[col];
                    break;
                }
                if (Rast_is_d_null_value(&d_ndvi)) {
                    /* do nothing */
                }
                else if ((d_ndvi) > d_ndvi_max && (d_ndvi) < 0.98) {
                    d_ndvi_max = d_ndvi;
                }
            }
        }
        G_message("ndvi_max=%f\n", d_ndvi_max);
    }
    /* Process pixels */
    for (row = 0; row < nrows; row++) {
        DCELL d;
        DCELL d_z0h;
        G_percent(row, nrows, 2);
        /* read input maps */
        Rast_get_row(infd_ndvi, inrast_ndvi, row, data_type_ndvi);
        /*process the data */
        for (col = 0; col < ncols; col++) {
            switch (data_type_ndvi) {
            case CELL_TYPE:
                d_ndvi = (double)((CELL *)inrast_ndvi)[col];
                break;
            case FCELL_TYPE:
                d_ndvi = (double)((FCELL *)inrast_ndvi)[col];
                break;
            case DCELL_TYPE:
                d_ndvi = (double)((DCELL *)inrast_ndvi)[col];
                break;
            }
            if (Rast_is_d_null_value(&d_ndvi)) {
                Rast_set_d_null_value(&outrast1[col], 1);
                if (input2->answer && output2->answer) {
                    Rast_set_d_null_value(&outrast2[col], 1);
                }
            }
            else {
                /****************************/
                /* calculate z0m            */
                if (flag2->answer) {
                    d = z0m_pawan(d_ndvi);
                }
                else {
                    d = z0m_bastiaanssen(d_ndvi, d_ndvi_max, hv_max, hmr);
                }
                outrast1[col] = d;
                if (input2->answer && output2->answer) {
                    d_z0h = d * coef_z0h;
                    outrast2[col] = d_z0h;
                }
            }
        }
        Rast_put_d_row(outfd1, outrast1);
        if (input2->answer && output2->answer) {
            Rast_put_d_row(outfd2, outrast2);
        }
    }
    G_free(inrast_ndvi);
    Rast_close(infd_ndvi);
    G_free(outrast1);
    Rast_close(outfd1);
    if (input2->answer && output2->answer) {
        G_free(outrast2);
        Rast_close(outfd2);
    }
    Rast_short_history(result1, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(result1, &history);
    if (input2->answer && output2->answer) {
        Rast_short_history(result2, "raster", &history);
        Rast_command_history(&history);
        Rast_write_history(result2, &history);
    }
    exit(EXIT_SUCCESS);
}
