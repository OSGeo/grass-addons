/****************************************************************************
 *
 * MODULE:       i.water
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Calculates if water is there (value=1)
 *                  two versions, 1) generic (albedo,ndvi)
 *                  2) Modis (surf_refl_7,ndvi)
 *
 * COPYRIGHT:    (C) 2008-2016 by the GRASS Development Team
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

double water(double albedo, double ndvi);
double water_modis(double surf_ref_7, double ndvi);

int main(int argc, char *argv[])
{
    struct Cell_head cellhd; /*region+header info */
    char *mapset = "";       /*mapset name */
    int nrows, ncols;
    int row, col;
    struct GModule *module;
    struct Option *input1, *input2, *input3, *output1;
    struct Flag *flag1;
    struct History history; /*metadata */
    char *name;             /*input raster name */
    char *result1;          /*output raster name */
    int infd_ndvi, infd_albedo, infd_ref7;
    int outfd1;
    char *ndvi, *albedo, *ref7;
    int i = 0, j = 0;
    void *inrast_ndvi, *inrast_albedo, *inrast_ref7;
    CELL *outrast1;
    RASTER_MAP_TYPE data_type_output = CELL_TYPE;
    RASTER_MAP_TYPE data_type_ndvi;
    RASTER_MAP_TYPE data_type_albedo;
    RASTER_MAP_TYPE data_type_ref7;
    /************************************/
    G_gisinit(argv[0]);
    module = G_define_module();
    G_add_keyword(_("imagery"));
    G_add_keyword(_("water"));
    G_add_keyword(_("detection"));
    module->description = _("Water detection from satellite data derived "
                            "indices, 1 if found, 0 if not");

    /* Define the different options */
    input1 = G_define_standard_option(G_OPT_R_INPUT);
    input1->key = "ndvi";
    input1->description = _("Name of the NDVI layer [-]");
    input2 = G_define_standard_option(G_OPT_R_INPUT);
    input2->key = "albedo";
    input2->required = NO;
    input2->description = _("Name of the Albedo layer [-]");
    input3 = G_define_standard_option(G_OPT_R_INPUT);
    input3->key = "modref7";
    input3->required = NO;
    input3->description =
        _("Name of the Modis surface reflectance band 7 layer [-]");
    output1 = G_define_standard_option(G_OPT_R_OUTPUT);
    output1->description = _("Name of the output water layer [0/1]");

    /********************/
    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);
    ndvi = input1->answer;
    if (input2->answer)
        albedo = input2->answer;
    if (input3->answer)
        ref7 = input3->answer;
    if (!input2->answer && !input3->answer) {
        G_fatal_error(_("ERROR: needs either Albedo or Modis surface "
                        "reflectance in band 7, bailing out."));
    }
    result1 = output1->answer;

    /***************************************************/
    data_type_ndvi = Rast_map_type(ndvi, mapset);
    if ((infd_ndvi = Rast_open_old(ndvi, mapset)) < 0)
        G_fatal_error(_("Cannot open cell file [%s]"), ndvi);
    Rast_get_cellhd(ndvi, mapset, &cellhd);
    inrast_ndvi = Rast_allocate_buf(data_type_ndvi);
    /***************************************************/
    if (input2->answer) {
        data_type_albedo = Rast_map_type(albedo, mapset);
        if ((infd_albedo = Rast_open_old(albedo, mapset)) < 0)
            G_fatal_error(_("Cannot open cell file [%s]"), albedo);
        Rast_get_cellhd(albedo, mapset, &cellhd);
        inrast_albedo = Rast_allocate_buf(data_type_albedo);
    }
    /***************************************************/
    if (input3->answer) {
        data_type_ref7 = Rast_map_type(ref7, mapset);
        if ((infd_ref7 = Rast_open_old(ref7, mapset)) < 0)
            G_fatal_error(_("Cannot open cell file [%s]"), ref7);
        Rast_get_cellhd(ref7, mapset, &cellhd);
        inrast_ref7 = Rast_allocate_buf(data_type_ref7);
    }
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
        CELL d;
        DCELL d_ndvi;
        DCELL d_albedo;
        DCELL d_ref7;
        G_percent(row, nrows, 2);
        /* read input maps */
        Rast_get_row(infd_ndvi, inrast_ndvi, row, data_type_ndvi);
        if (input2->answer) {
            Rast_get_row(infd_albedo, inrast_albedo, row, data_type_albedo);
        }
        if (input3->answer) {
            Rast_get_row(infd_ref7, inrast_ref7, row, data_type_ref7);
        }
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
                d_ndvi = ((DCELL *)inrast_ndvi)[col];
                break;
            }
            if (input2->answer) {
                switch (data_type_albedo) {
                case CELL_TYPE:
                    d_albedo = (double)((CELL *)inrast_albedo)[col];
                    break;
                case FCELL_TYPE:
                    d_albedo = (double)((FCELL *)inrast_albedo)[col];
                    break;
                case DCELL_TYPE:
                    d_albedo = ((DCELL *)inrast_albedo)[col];
                    break;
                }
            }
            if (input3->answer) {
                switch (data_type_ref7) {
                case CELL_TYPE:
                    d_ref7 = (double)((CELL *)inrast_ref7)[col];
                    break;
                case FCELL_TYPE:
                    d_ref7 = (double)((FCELL *)inrast_ref7)[col];
                    break;
                case DCELL_TYPE:
                    d_ref7 = ((DCELL *)inrast_ref7)[col];
                    break;
                }
            }
            if (Rast_is_d_null_value(&d_ndvi) ||
                (input2->answer && Rast_is_d_null_value(&d_albedo)) ||
                (input3->answer && Rast_is_d_null_value(&d_ref7))) {
                Rast_set_c_null_value(&outrast1[col], 1);
            }
            else {
                /************************************/
                /* calculate water detection        */
                if (input2->answer) {
                    d = water(d_albedo, d_ndvi);
                }
                else if (input3->answer) {
                    d = water_modis(d_ref7, d_ndvi);
                }
                outrast1[col] = d;
            }
        }
        Rast_put_row(outfd1, outrast1, data_type_output);
    }
    free(inrast_ndvi);
    Rast_close(infd_ndvi);
    if (input2->answer) {
        free(inrast_albedo);
        Rast_close(infd_albedo);
    }
    if (input3->answer) {
        free(inrast_ref7);
        Rast_close(infd_ref7);
    }
    free(outrast1);
    Rast_close(outfd1);
    Rast_short_history(result1, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(result1, &history);
    exit(EXIT_SUCCESS);
}
