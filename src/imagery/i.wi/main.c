/****************************************************************************
 *
 * MODULE:       i.wi
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Calculates water indices
 *
 * COPYRIGHT:    (C) 2016 by the GRASS Development Team
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

double awei_noshadow(double greenchan, double nirchan, double chan5chan);
double awei_shadow(double bluechan, double greenchan, double nirchan,
                   double chan5chan, double band7chan);
double ls_wi(double nirchan, double chan7chan);
double ndwi_mcfeeters(double greenchan, double nirchan);
double ndwi_xu(double greenchan, double chan5chan);
double tcw(double bluechan, double greenchan, double redchan, double nirchan,
           double chan5chan, double band7chan);
double wi(double greenchan, double redchan, double nirchan, double chan5chan,
          double chan7chan);

int main(int argc, char *argv[])
{
    struct Cell_head cellhd; /*region+header info */
    char *mapset = "";       /*mapset name */
    int nrows, ncols;
    int row, col;
    char *wiflag; /*Switch for particular index */
    char *desc;
    struct GModule *module;
    struct {
        struct Option *winame, *red, *nir, *green, *blue, *chan5, *chan7, *bits,
            *output;
    } opt;
    struct Flag *flag1;
    struct History history; /*metadata */
    struct Colors colors;   /*Color rules */
    char *name;             /*input raster name */
    char *result;           /*output raster name */
    int infd_bluechan, infd_greenchan, infd_redchan;
    int infd_nirchan, infd_chan5chan, infd_chan7chan;
    int outfd;
    char *bluechan, *greenchan, *redchan, *nirchan, *chan5chan, *chan7chan;
    int i = 0, j = 0;
    void *inrast_bluechan, *inrast_greenchan, *inrast_redchan;
    void *inrast_nirchan, *inrast_chan5chan, *inrast_chan7chan;

    DCELL *outrast;
    RASTER_MAP_TYPE data_type_output = DCELL_TYPE;
    RASTER_MAP_TYPE data_type_bluechan, data_type_greenchan;
    RASTER_MAP_TYPE data_type_redchan, data_type_nirchan;
    RASTER_MAP_TYPE data_type_chan5chan, data_type_chan7chan;
    /************************************/
    G_gisinit(argv[0]);
    module = G_define_module();
    G_add_keyword(_("imagery"));
    G_add_keyword(_("water"));
    G_add_keyword(_("index"));
    G_add_keyword(_("biophysical"));
    module->description = _("Calculates different types of water indices.");

    /* Define the different options */

    opt.winame = G_define_option();
    opt.winame->key = "winame";
    opt.winame->type = TYPE_STRING;
    opt.winame->required = YES;
    opt.winame->description = _("Type of water index");
    desc = NULL;
    G_asprintf(
        &desc,
        "awei_ns;%s;awei_s;%s;lswi;%s;ndwi_mf;%s;ndwi_x;%s;tcw;%s;wi;%s;",
        _("Automated Water Extraction Index - No Shadow"),
        _("Automated Water Extraction Index - Shadow"),
        _("Land Soil Water Index"),
        _("Normalized Difference Water Index - Mc Feeters"),
        _("Normalized Difference Water Index - Xu"), _("Tasseled Cap Water"),
        _("Water Index"));
    opt.winame->descriptions = desc;
    opt.winame->options = "awei_ns,awei_s,lswi,ndwi_mf,ndwi_x,tcw,wi";
    opt.winame->answer = "lswi";
    opt.winame->key_desc = _("type");

    opt.blue = G_define_standard_option(G_OPT_R_INPUT);
    opt.blue->key = "blue";
    opt.blue->required = NO;
    opt.blue->label = _("Name of input blue channel surface reflectance map");
    opt.blue->description = _("Range: [0.0;1.0]");
    opt.blue->guisection = _("Inputs");

    opt.green = G_define_standard_option(G_OPT_R_INPUT);
    opt.green->key = "green";
    opt.green->required = NO;
    opt.green->label = _("Name of input green channel surface reflectance map");
    opt.green->description = _("Range: [0.0;1.0]");
    opt.green->guisection = _("Inputs");

    opt.red = G_define_standard_option(G_OPT_R_INPUT);
    opt.red->key = "red";
    opt.red->required = NO;
    opt.red->label = _("Name of input red channel surface reflectance map");
    opt.red->description = _("Range: [0.0;1.0]");
    opt.red->guisection = _("Inputs");

    opt.nir = G_define_standard_option(G_OPT_R_INPUT);
    opt.nir->key = "nir";
    opt.nir->required = NO;
    opt.nir->label = _("Name of input nir channel surface reflectance map");
    opt.nir->description = _("Range: [0.0;1.0]");
    opt.nir->guisection = _("Inputs");

    opt.chan5 = G_define_standard_option(G_OPT_R_INPUT);
    opt.chan5->key = "band5";
    opt.chan5->required = NO;
    opt.chan5->label = _("Name of input 5th channel surface reflectance map");
    opt.chan5->description = _("Range: [0.0;1.0]");
    opt.chan5->guisection = _("Inputs");

    opt.chan7 = G_define_standard_option(G_OPT_R_INPUT);
    opt.chan7->key = "band7";
    opt.chan7->required = NO;
    opt.chan7->label = _("Name of input 7th channel surface reflectance map");
    opt.chan7->description = _("Range: [0.0;1.0]");
    opt.chan7->guisection = _("Inputs");

    /* Define the different options */
    opt.output = G_define_standard_option(G_OPT_R_OUTPUT);
    opt.output->description = _("Name of the output wi layer");

    /********************/
    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    wiflag = opt.winame->answer;
    redchan = opt.red->answer;
    nirchan = opt.nir->answer;
    greenchan = opt.green->answer;
    bluechan = opt.blue->answer;
    chan5chan = opt.chan5->answer;
    chan7chan = opt.chan7->answer;
    result = opt.output->answer;

    if (!strcasecmp(wiflag, "awei_ns") &&
        (!(opt.nir->answer) || !(opt.green->answer) || !(opt.chan5->answer)))
        G_fatal_error(_("awei_noshadow requires green, nir and chan5 maps"));

    if (!strcasecmp(wiflag, "awei_s") &&
        (!(opt.blue->answer) || !(opt.nir->answer) || !(opt.green->answer) ||
         !(opt.chan5->answer) || !(opt.chan7->answer)))
        G_fatal_error(
            _("awei_shadow requires blue, green, nir, chan5 and chan7 maps"));

    if (!strcasecmp(wiflag, "lswi") &&
        (!(opt.nir->answer) || !(opt.chan7->answer)))
        G_fatal_error(_("lswi requires nir and chan7 maps"));

    if (!strcasecmp(wiflag, "ndwi_mf") &&
        (!(opt.nir->answer) || !(opt.green->answer)))
        G_fatal_error(_("ndwi_mf requires green, nir maps"));

    if (!strcasecmp(wiflag, "ndwi_x") &&
        (!(opt.chan5->answer) || !(opt.green->answer)))
        G_fatal_error(_("ndwi_x requires green, chan5 maps"));

    if (!strcasecmp(wiflag, "tcw") &&
        (!(opt.blue->answer) || !(opt.red->answer) || !(opt.nir->answer) ||
         !(opt.green->answer) || !(opt.chan5->answer) || !(opt.chan7->answer)))
        G_fatal_error(_("awei_shadow requires blue, green, red,  nir, chan5 "
                        "and chan7 maps"));

    if (!strcasecmp(wiflag, "wi") &&
        (!(opt.nir->answer) || !(opt.green->answer) || !(opt.red->answer) ||
         !(opt.chan5->answer) || !(opt.chan7->answer)))
        G_fatal_error(_("wi requires green, red, nir, chan5 and chan7 maps"));

    /***************************************************/
    if (bluechan) {
        data_type_bluechan = Rast_map_type(bluechan, mapset);
        infd_bluechan = Rast_open_old(bluechan, mapset);
        Rast_get_cellhd(bluechan, mapset, &cellhd);
        inrast_bluechan = Rast_allocate_buf(data_type_bluechan);
    }
    /***************************************************/
    if (greenchan) {
        data_type_greenchan = Rast_map_type(greenchan, mapset);
        infd_greenchan = Rast_open_old(greenchan, mapset);
        Rast_get_cellhd(greenchan, mapset, &cellhd);
        inrast_greenchan = Rast_allocate_buf(data_type_greenchan);
    }
    /***************************************************/
    if (redchan) {
        data_type_redchan = Rast_map_type(redchan, mapset);
        infd_redchan = Rast_open_old(redchan, mapset);
        Rast_get_cellhd(redchan, mapset, &cellhd);
        inrast_redchan = Rast_allocate_buf(data_type_redchan);
    }
    /***************************************************/
    if (nirchan) {
        data_type_nirchan = Rast_map_type(nirchan, mapset);
        infd_nirchan = Rast_open_old(nirchan, mapset);
        Rast_get_cellhd(nirchan, mapset, &cellhd);
        inrast_nirchan = Rast_allocate_buf(data_type_nirchan);
    }
    /***************************************************/
    if (chan5chan) {
        data_type_chan5chan = Rast_map_type(chan5chan, mapset);
        infd_chan5chan = Rast_open_old(chan5chan, mapset);
        Rast_get_cellhd(chan5chan, mapset, &cellhd);
        inrast_chan5chan = Rast_allocate_buf(data_type_chan5chan);
    }
    /***************************************************/
    if (chan7chan) {
        data_type_chan7chan = Rast_map_type(chan7chan, mapset);
        infd_chan7chan = Rast_open_old(chan7chan, mapset);
        Rast_get_cellhd(chan7chan, mapset, &cellhd);
        inrast_chan7chan = Rast_allocate_buf(data_type_chan7chan);
    }
    /***************************************************/
    G_debug(3, "number of rows %d", cellhd.rows);
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();
    outrast = Rast_allocate_buf(data_type_output);
    /* Create New raster files */
    outfd = Rast_open_new(result, data_type_output);
    /* Process pixels */
    for (row = 0; row < nrows; row++) {
        DCELL d;
        DCELL d_bluechan, d_greenchan, d_redchan;
        DCELL d_nirchan, d_chan5chan, d_chan7chan;

        G_percent(row, nrows, 2);

        if (bluechan)
            Rast_get_row(infd_bluechan, inrast_bluechan, row,
                         data_type_bluechan);
        if (greenchan)
            Rast_get_row(infd_greenchan, inrast_greenchan, row,
                         data_type_greenchan);
        if (redchan)
            Rast_get_row(infd_redchan, inrast_redchan, row, data_type_redchan);
        if (nirchan)
            Rast_get_row(infd_nirchan, inrast_nirchan, row, data_type_nirchan);
        if (chan5chan)
            Rast_get_row(infd_chan5chan, inrast_chan5chan, row,
                         data_type_chan5chan);
        if (chan7chan)
            Rast_get_row(infd_chan7chan, inrast_chan7chan, row,
                         data_type_chan7chan);
        /*process the data */
        for (col = 0; col < ncols; col++) {
            if (bluechan)
                switch (data_type_bluechan) {
                case CELL_TYPE:
                    d_bluechan = (double)((CELL *)inrast_bluechan)[col];
                    break;
                case FCELL_TYPE:
                    d_bluechan = (double)((FCELL *)inrast_bluechan)[col];
                    break;
                case DCELL_TYPE:
                    d_bluechan = ((DCELL *)inrast_bluechan)[col];
                    break;
                }

            if (greenchan)
                switch (data_type_greenchan) {
                case CELL_TYPE:
                    d_greenchan = (double)((CELL *)inrast_greenchan)[col];
                    break;
                case FCELL_TYPE:
                    d_greenchan = (double)((FCELL *)inrast_greenchan)[col];
                    break;
                case DCELL_TYPE:
                    d_greenchan = ((DCELL *)inrast_greenchan)[col];
                    break;
                }

            if (redchan)
                switch (data_type_redchan) {
                case CELL_TYPE:
                    d_redchan = (double)((CELL *)inrast_redchan)[col];
                    break;
                case FCELL_TYPE:
                    d_redchan = (double)((FCELL *)inrast_redchan)[col];
                    break;
                case DCELL_TYPE:
                    d_redchan = ((DCELL *)inrast_redchan)[col];
                    break;
                }

            if (nirchan)
                switch (data_type_nirchan) {
                case CELL_TYPE:
                    d_nirchan = (double)((CELL *)inrast_nirchan)[col];
                    break;
                case FCELL_TYPE:
                    d_nirchan = (double)((FCELL *)inrast_nirchan)[col];
                    break;
                case DCELL_TYPE:
                    d_nirchan = ((DCELL *)inrast_nirchan)[col];
                    break;
                }
            if (chan5chan)
                switch (data_type_chan5chan) {
                case CELL_TYPE:
                    d_chan5chan = (double)((CELL *)inrast_chan5chan)[col];
                    break;
                case FCELL_TYPE:
                    d_chan5chan = (double)((FCELL *)inrast_chan5chan)[col];
                    break;
                case DCELL_TYPE:
                    d_chan5chan = ((DCELL *)inrast_chan5chan)[col];
                    break;
                }

            if (chan7chan)
                switch (data_type_chan7chan) {
                case CELL_TYPE:
                    d_chan7chan = (double)((CELL *)inrast_chan7chan)[col];
                    break;
                case FCELL_TYPE:
                    d_chan7chan = (double)((FCELL *)inrast_chan7chan)[col];
                    break;
                case DCELL_TYPE:
                    d_chan7chan = ((DCELL *)inrast_chan7chan)[col];
                    break;
                }
            if ((redchan) && Rast_is_d_null_value(&d_redchan) ||
                ((nirchan) && Rast_is_d_null_value(&d_nirchan)) ||
                ((greenchan) && Rast_is_d_null_value(&d_greenchan)) ||
                ((bluechan) && Rast_is_d_null_value(&d_bluechan)) ||
                ((chan5chan) && Rast_is_d_null_value(&d_chan5chan)) ||
                ((chan7chan) && Rast_is_d_null_value(&d_chan7chan))) {
                Rast_set_d_null_value(&outrast[col], 1);
            }
            else {
                /*calculate awei no shadow          */
                if (!strcasecmp(wiflag, "awei_ns")) {
                    d = awei_noshadow(d_greenchan, d_nirchan, d_chan5chan);
                    ((DCELL *)outrast)[col] = d;
                }
                /*calculate awei shadow             */
                if (!strcasecmp(wiflag, "awei_s")) {
                    d = awei_shadow(d_bluechan, d_greenchan, d_nirchan,
                                    d_chan5chan, d_chan7chan);
                    ((DCELL *)outrast)[col] = d;
                }
                /*calculate lswi                    */
                if (!strcasecmp(wiflag, "lswi")) {
                    if (d_nirchan + d_chan7chan < 0.001) {
                        Rast_set_d_null_value(&outrast[col], 1);
                    }
                    else {
                        d = ls_wi(d_nirchan, d_chan7chan);
                        ((DCELL *)outrast)[col] = d;
                    }
                }
                /*calculate ndwi McFeeters          */
                if (!strcasecmp(wiflag, "ndwi_mf")) {
                    if (d_greenchan + d_nirchan < 0.001) {
                        Rast_set_d_null_value(&outrast[col], 1);
                    }
                    else {
                        d = ndwi_mcfeeters(d_greenchan, d_nirchan);
                        ((DCELL *)outrast)[col] = d;
                    }
                }
                /*calculate ndwi Xu                 */
                if (!strcasecmp(wiflag, "ndwi_x")) {
                    if (d_greenchan + d_chan5chan < 0.001) {
                        Rast_set_d_null_value(&outrast[col], 1);
                    }
                    else {
                        d = ndwi_xu(d_greenchan, d_chan5chan);
                        ((DCELL *)outrast)[col] = d;
                    }
                }
                /*calculate tcw                     */
                if (!strcasecmp(wiflag, "tcw")) {
                    d = tcw(d_bluechan, d_greenchan, d_redchan, d_nirchan,
                            d_chan5chan, d_chan7chan);
                    ((DCELL *)outrast)[col] = d;
                }
                /*calculate wi                      */
                if (!strcasecmp(wiflag, "wi")) {
                    d = wi(d_greenchan, d_redchan, d_nirchan, d_chan5chan,
                           d_chan7chan);
                    ((DCELL *)outrast)[col] = d;
                }
            }
        }
        Rast_put_row(outfd, outrast, data_type_output);
    }
    if (bluechan) {
        free(inrast_bluechan);
        Rast_close(infd_bluechan);
    }
    if (greenchan) {
        free(inrast_greenchan);
        Rast_close(infd_greenchan);
    }
    if (redchan) {
        free(inrast_redchan);
        Rast_close(infd_redchan);
    }
    if (nirchan) {
        free(inrast_nirchan);
        Rast_close(infd_nirchan);
    }
    if (chan5chan) {
        free(inrast_chan5chan);
        Rast_close(infd_chan5chan);
    }
    if (chan7chan) {
        free(inrast_chan7chan);
        Rast_close(infd_chan7chan);
    }
    free(outrast);
    Rast_close(outfd);
    /* Color from -1.0 to +1.0 in grey */
    Rast_short_history(result, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(result, &history);
    exit(EXIT_SUCCESS);
}
