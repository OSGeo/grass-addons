/****************************************************************************
 *
 * MODULE:       i.eb.deltat
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Calculates the difference of temperature between 2 heights
 *                as seen in Pawan (2004)
 *                This is a SEBAL initialization parameter for sensible heat.
 *
 * COPYRIGHT:    (C) 2006-2016 by the GRASS Development Team
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

double delta_t(double tempk);

int main(int argc, char *argv[])
{
    struct Cell_head cellhd; /*region+header info */
    char *mapset;            /* mapset name */
    int nrows, ncols;
    int row, col;
    int wim = 0;
    struct GModule *module;
    struct Option *input1, *output1;
    struct Flag *flag1, *flag2;
    struct History history; /*metadata */
    char *name;             /*input raster name */
    char *result1;          /*output raster name */
    /*File Descriptors */
    int infd_tempk;
    int outfd1;
    char *tempk;
    char *delta;
    int i = 0, j = 0;
    void *inrast_tempk;

    DCELL *outrast1;
    RASTER_MAP_TYPE data_type_output = DCELL_TYPE;
    RASTER_MAP_TYPE data_type_tempk;

    /************************************/
    G_gisinit(argv[0]);
    module = G_define_module();
    G_add_keyword(_("imagery"));
    G_add_keyword(_("energy balance"));
    G_add_keyword(_("SEBAL"));
    G_add_keyword(_("SEBS"));
    G_add_keyword(_("delta T"));
    module->description = _("Computes the difference of temperature between "
                            "surface skin temperature and air temperature at "
                            "2m as part of sensible heat flux calculations.");

    /* Define the different options */
    input1 = G_define_standard_option(G_OPT_R_INPUT);
    input1->key = _("tempk");
    input1->description =
        _("Name of the surface skin temperature map [Kelvin]");
    input1->answer = _("tempk");
    output1 = G_define_standard_option(G_OPT_R_INPUT);
    output1->key = _("delta");
    output1->description = _("Name of the output delta layer");
    output1->answer = _("delta");
    flag2 = G_define_flag();
    flag2->key = 'w';
    flag2->description = _("Wim's generic table");

    /********************/
    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);
    tempk = input1->answer;
    result1 = output1->answer;
    wim = flag2->answer;

    /***************************************************/
    data_type_tempk = Rast_map_type(tempk, mapset);
    if ((infd_tempk = Rast_open_old(tempk, mapset)) < 0)
        G_fatal_error(_("Cannot open cell file [%s]"), tempk);
    Rast_get_cellhd(tempk, mapset, &cellhd);
    inrast_tempk = Rast_allocate_buf(data_type_tempk);

    /***************************************************/
    G_debug(3, "number of rows %d", cellhd.rows);
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();
    outrast1 = Rast_allocate_buf(data_type_output);

    /* Create New raster files */
    outfd1 = Rast_open_new(result1, data_type_output);

    /* Process pixels */
    for (row = 0; row < nrows; row++) {
        DCELL d;
        DCELL d_tempk;
        G_percent(row, nrows, 2);

        /* read soil input maps */
        Rast_get_row(infd_tempk, inrast_tempk, row, data_type_tempk);

        /*process the data */
        for (col = 0; col < ncols; col++) {
            switch (data_type_tempk) {
            case CELL_TYPE:
                d_tempk = (double)((CELL *)inrast_tempk)[col];
                break;
            case FCELL_TYPE:
                d_tempk = (double)((FCELL *)inrast_tempk)[col];
                break;
            case DCELL_TYPE:
                d_tempk = ((DCELL *)inrast_tempk)[col];
                break;
            }
            if (Rast_is_d_null_value(&d_tempk)) {
                Rast_set_d_null_value(&outrast1[col], 1);
            }
            else {
                /****************************/
                /* calculate delta T        */
                if (wim) {
                    d = 0.3225 * d_tempk - 91.743;
                    if (d < 1) {
                        d = 1.0;
                    }
                    else if (d > 13) {
                        d = 13.0;
                    }
                }
                else {
                    d = delta_t(d_tempk);
                }
                if (abs(d) > 50.0) {
                    Rast_set_d_null_value(&outrast1[col], 1);
                }
                outrast1[col] = d;
            }
        }
        Rast_put_row(outfd1, outrast1, data_type_output);
    }
    free(inrast_tempk);
    Rast_close(infd_tempk);
    free(outrast1);
    Rast_close(outfd1);
    Rast_short_history(result1, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(result1, &history);
    exit(EXIT_SUCCESS);
}
