/****************************************************************************
 *
 * MODULE:       i.rh
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Calculates relative humidity
 *
 * COPYRIGHT:    (C) 2017-2019 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *                        License (>=v2). Read the file COPYING that comes with
 *GRASS for details.
 *
 *****************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>

double rh(double PW, double Pa, double Ta, double dem);
double esat(double tamean);
double eact(double esat, double rh);
double eatm(double eact);

int main(int argc, char *argv[])
{
    struct Cell_head cellhd; /*region+header info */
    char *mapset = "";       /*mapset name */
    int nrows, ncols;
    int row, col;
    struct GModule *module;
    struct Option *input1, *input2, *input3, *input4, *output1;
    struct Flag *flag1, *flag2, *flag3;
    struct History history; /*metadata */
    char *name;             /*input raster name */
    char *result1;          /*output raster name */
    int infd_pw, infd_pa, infd_ta, infd_dem;
    int outfd1;
    char *pw, *pa, *ta, *dem;
    int i = 0, j = 0;
    void *inrast_pw, *inrast_pa, *inrast_ta, *inrast_dem;
    CELL *outrast1;
    RASTER_MAP_TYPE data_type_output = CELL_TYPE;
    RASTER_MAP_TYPE data_type_pw;
    RASTER_MAP_TYPE data_type_pa;
    RASTER_MAP_TYPE data_type_ta;
    RASTER_MAP_TYPE data_type_dem;
    /************************************/
    G_gisinit(argv[0]);
    module = G_define_module();
    G_add_keyword(_("imagery"));
    G_add_keyword(_("atmosphere"));
    G_add_keyword(_("humidity"));
    G_add_keyword(_("water vapour"));
    G_add_keyword(_("precipitable water"));
    module->description = _("Water in atmosphere: relative humidity, water "
                            "vapour (saturated, actual)");

    /* Define the different options */
    input1 = G_define_standard_option(G_OPT_R_INPUT);
    input1->key = "pw";
    input1->description = _("Name of the Precipitable Water layer");
    input2 = G_define_standard_option(G_OPT_R_INPUT);
    input2->key = "pa";
    input2->description = _("Name of the Atmospheric Pressure layer");
    input3 = G_define_standard_option(G_OPT_R_INPUT);
    input3->key = "ta";
    input3->description = _("Name of the mean daily air temperature layer");
    input4 = G_define_standard_option(G_OPT_R_INPUT);
    input4->key = "dem";
    input4->description = _("Name of the elevation layer");

    output1 = G_define_standard_option(G_OPT_R_OUTPUT);
    output1->description = _("Name of the output layer");

    flag1 = G_define_flag();
    flag1->key = 's';
    flag1->description = _("Output the saturated water vapour (esat)");

    flag2 = G_define_flag();
    flag2->key = 'a';
    flag2->description = _("Output the actual water vapour (eact)");

    flag3 = G_define_flag();
    flag3->key = 'e';
    flag3->description = _("Output the atmospheric emissivity (eatm)");
    /********************/
    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);
    pw = input1->answer;
    pa = input2->answer;
    ta = input3->answer;
    dem = input4->answer;
    result1 = output1->answer;
    if (flag1->answer && flag2->answer)
        G_fatal_error(_("Cannot output both esat and eact, please choose"));
    if (flag1->answer && flag3->answer)
        G_fatal_error(_("Cannot output both esat and eatm, please choose"));
    if (flag2->answer && flag3->answer)
        G_fatal_error(_("Cannot output both eact and eatm, please choose"));
    /***************************************************/
    data_type_pw = Rast_map_type(pw, mapset);
    if ((infd_pw = Rast_open_old(pw, mapset)) < 0)
        G_fatal_error(_("Cannot open cell file [%s]"), pw);
    Rast_get_cellhd(pw, mapset, &cellhd);
    inrast_pw = Rast_allocate_buf(data_type_pw);
    /***************************************************/
    data_type_pa = Rast_map_type(pa, mapset);
    if ((infd_pa = Rast_open_old(pa, mapset)) < 0)
        G_fatal_error(_("Cannot open cell file [%s]"), pa);
    Rast_get_cellhd(pa, mapset, &cellhd);
    inrast_pa = Rast_allocate_buf(data_type_pa);
    /***************************************************/
    data_type_ta = Rast_map_type(ta, mapset);
    if ((infd_ta = Rast_open_old(ta, mapset)) < 0)
        G_fatal_error(_("Cannot open cell file [%s]"), ta);
    Rast_get_cellhd(ta, mapset, &cellhd);
    inrast_ta = Rast_allocate_buf(data_type_ta);
    /***************************************************/
    data_type_dem = Rast_map_type(dem, mapset);
    if ((infd_dem = Rast_open_old(dem, mapset)) < 0)
        G_fatal_error(_("Cannot open cell file [%s]"), dem);
    Rast_get_cellhd(dem, mapset, &cellhd);
    inrast_dem = Rast_allocate_buf(data_type_dem);
    /***************************************************/
    G_debug(3, "number of rows %d", cellhd.rows);
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();
    outrast1 = Rast_allocate_buf(data_type_output);
    /* Create New raster files */
    if ((outfd1 = Rast_open_new(result1, data_type_output)) < 0)
        G_fatal_error(_("Could not open <%s>"), result1);
    /* Process pixels */
    for (row = 0; row < nrows; row++) {
        CELL d, d_rh, d_esat, d_eact, d_eatm;
        DCELL d_pw;
        DCELL d_pa;
        DCELL d_ta;
        DCELL d_dem;
        G_percent(row, nrows, 2);
        /* read input maps */
        Rast_get_row(infd_pw, inrast_pw, row, data_type_pw);
        Rast_get_row(infd_pa, inrast_pa, row, data_type_pa);
        Rast_get_row(infd_ta, inrast_ta, row, data_type_ta);
        Rast_get_row(infd_dem, inrast_dem, row, data_type_dem);
        /*process the data */
        for (col = 0; col < ncols; col++) {
            switch (data_type_pw) {
            case CELL_TYPE:
                d_pw = (double)((CELL *)inrast_pw)[col];
                break;
            case FCELL_TYPE:
                d_pw = (double)((FCELL *)inrast_pw)[col];
                break;
            case DCELL_TYPE:
                d_pw = ((DCELL *)inrast_pw)[col];
                break;
            }
            switch (data_type_pa) {
            case CELL_TYPE:
                d_pa = (double)((CELL *)inrast_pa)[col];
                break;
            case FCELL_TYPE:
                d_pa = (double)((FCELL *)inrast_pa)[col];
                break;
            case DCELL_TYPE:
                d_pa = ((DCELL *)inrast_pa)[col];
                break;
            }
            switch (data_type_ta) {
            case CELL_TYPE:
                d_ta = (double)((CELL *)inrast_ta)[col];
                break;
            case FCELL_TYPE:
                d_ta = (double)((FCELL *)inrast_ta)[col];
                break;
            case DCELL_TYPE:
                d_ta = ((DCELL *)inrast_ta)[col];
                break;
            }
            switch (data_type_dem) {
            case CELL_TYPE:
                d_dem = (double)((CELL *)inrast_dem)[col];
                break;
            case FCELL_TYPE:
                d_dem = (double)((FCELL *)inrast_dem)[col];
                break;
            case DCELL_TYPE:
                d_dem = ((DCELL *)inrast_dem)[col];
                break;
            }
            if (Rast_is_d_null_value(&d_pw) || Rast_is_d_null_value(&d_pa) ||
                Rast_is_d_null_value(&d_ta) || Rast_is_d_null_value(&d_dem)) {
                Rast_set_c_null_value(&outrast1[col], 1);
            }
            else {
                d_rh = rh(d_pw, d_pa, d_ta, d_dem);
                d_esat = esat(d_ta);
                d_eact = eact(d_esat, d_rh);
                d_eatm = eatm(d_eact);
                if (flag1->answer)
                    d = d_esat;
                else if (flag2->answer)
                    d = d_eact;
                else if (flag3->answer)
                    d = d_eatm;
                else
                    d = d_rh;
                outrast1[col] = d;
            }
        }
        Rast_put_row(outfd1, outrast1, data_type_output);
    }
    free(inrast_pw);
    free(inrast_pa);
    free(inrast_ta);
    free(inrast_dem);
    free(outrast1);
    Rast_close(infd_pw);
    Rast_close(infd_pa);
    Rast_close(infd_ta);
    Rast_close(infd_dem);
    Rast_close(outfd1);
    Rast_short_history(result1, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(result1, &history);
    exit(EXIT_SUCCESS);
}
