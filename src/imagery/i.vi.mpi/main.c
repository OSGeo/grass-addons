/****************************************************************************
 *
 * MODULE:     i.vi.mpi
 * AUTHOR(S):  Shamim Akhter shamimakhter@gmail.com
                 Baburao Kamble baburaokamble@gmail.com
 *                 Yann Chemin - ychemin@gmail.com
 * PURPOSE:    Calculates 13 vegetation indices
 *                  based on biophysical parameters.
 *
 * COPYRIGHT:  (C) 2006 by the Tokyo Institute of Technology, Japan
 *                (C) 2002-2006 by the GRASS Development Team
 *
 *             This program is free software under the GNU General Public
 *             License (>=v2). Read the file COPYING that comes with
 *             GRASS for details.
 *
 * Remark:
 *             These are generic indices that use red and nir for most of them.
 *             Those can be any use by standard satellite having V and IR.
 *                 However arvi uses red, nir and blue;
 *                 GVI uses B,G,R,NIR, chan5 and chan 7 of landsat;
 *                 and GARI uses B,G,R and NIR.
 *
 *****************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "grass/gis.h"
#include "grass/raster.h"
#include "grass/glocale.h"
#include "mpi.h"

int main(int argc, char *argv[])
{
    int me, host_n, nrows, ncols;
    int NUM_HOSTS;
    MPI_Status status;
    MPI_Init(&argc, &argv);
    MPI_Comm_size(MPI_COMM_WORLD, &NUM_HOSTS);
    MPI_Comm_rank(MPI_COMM_WORLD, &me);

    if (!me) {
        struct Cell_head cellhd; /*region+header info */
        char *mapset;            /*mapset name */
        int row, col, row_n;
        char *viflag; /*Switch for particular index */
        struct GModule *module;
        struct Option *input1, *input2, *input3, *input4, *input5, *input6,
            *input7, *input8, *output;
        struct Flag *flag1;
        struct History history; /*metadata */
        struct Colors colors;   /*colors */
        char *name;             /*input raster name */
        char *result;           /*output raster name */
        /*File Descriptors */
        int infd_redchan, infd_nirchan, infd_greenchan, infd_bluechan,
            infd_chan5chan, infd_chan7chan;
        int outfd;
        char *bluechan, *greenchan, *redchan, *nirchan, *chan5chan, *chan7chan;
        int i = 0, j = 0, temp;
        void *inrast_redchan, *inrast_nirchan, *inrast_greenchan,
            *inrast_bluechan, *inrast_chan5chan, *inrast_chan7chan;
        DCELL *outrast;
        RASTER_MAP_TYPE data_type_output = DCELL_TYPE;
        RASTER_MAP_TYPE data_type_redchan;
        RASTER_MAP_TYPE data_type_nirchan;
        RASTER_MAP_TYPE data_type_greenchan;
        RASTER_MAP_TYPE data_type_bluechan;
        RASTER_MAP_TYPE data_type_chan5chan;
        RASTER_MAP_TYPE data_type_chan7chan;
        CELL val1, val2;
        /************************************/
        G_gisinit(argv[0]);

        module = G_define_module();
        G_add_keyword(_("vegetation index"));
        G_add_keyword(_("biophysical parameters"));
        module->label =
            _("Calculates different types of vegetation indices (mpi)");
        module->description =
            _("13 types of vegetation indices from red and nir,"
              "and only some requiring additional bands");

        /* Define the different options */
        input1 = G_define_option();
        input1->key = _("viname");
        input1->type = TYPE_STRING;
        input1->required = YES;
        input1->gisprompt = _("Name of VI");
        input1->description = _("Name of VI");
        input1->descriptions =
            _("dvi;Difference Vegetation Index;"
              "evi;Enhanced Vegetation Index;"
              "gvi;Green Vegetation Index;"
              "gari;Green atmospherically resistant vegetation index;"
              "gemi;Global Environmental Monitoring Index;"
              "ipvi;Infrared Percentage Vegetation Index;"
              "msavi;Modified Soil Adjusted Vegetation Index;"
              "msavi2;second Modified Soil Adjusted Vegetation Index;"
              "ndvi;Normalized Difference Vegetation Index;"
              "pvi;Perpendicular Vegetation Index;"
              "savi;Soil Adjusted Vegetation Index;"
              "sr;Simple Ratio;"
              "vari;Visible Atmospherically Resistant Index;"
              "wdvi;Weighted Difference Vegetation Index;");
        input1->options = "dvi,evi,gvi,gari,gemi,ipvi,msavi,msavi2,ndvi,pvi,"
                          "savi,sr,vari,wdvi";
        input1->answer = "ndvi";

        input2 = G_define_standard_option(G_OPT_R_INPUT);
        input2->key = "red";
        input2->label =
            _("Name of the RED Channel surface reflectance map [0.0;1.0]");
        input2->description = ("Range: [0.0;1.0]");

        input3 = G_define_standard_option(G_OPT_R_INPUT);
        input3->key = "nir";
        input3->label =
            _("Name of the NIR Channel surface reflectance map [0.0;1.0]");
        input3->description = ("Range: [0.0;1.0]");

        input4 = G_define_standard_option(G_OPT_R_INPUT);
        input4->key = "green";
        input4->required = NO;
        input4->label =
            _("Name of the GREEN Channel surface reflectance map [0.0;1.0]");
        input4->description = ("Range: [0.0;1.0]");

        input5 = G_define_standard_option(G_OPT_R_INPUT);
        input5->key = "blue";
        input5->required = NO;
        input5->label =
            _("Name of the BLUE Channel surface reflectance map [0.0;1.0]");
        input5->description = ("Range: [0.0;1.0]");

        input6 = G_define_standard_option(G_OPT_R_INPUT);
        input6->key = "chan5";
        input6->required = NO;
        input6->label =
            _("Name of the CHAN5 Channel surface reflectance map [0.0;1.0]");
        input6->description = ("Range: [0.0;1.0]");

        input7 = G_define_standard_option(G_OPT_R_INPUT);
        input7->key = "chan7";
        input7->required = NO;
        input7->label =
            _("Name of the CHAN7 Channel surface reflectance map [0.0;1.0]");
        input7->description = ("Range: [0.0;1.0]");

        input8 = G_define_option();
        input8->key = "tmp";
        input8->type = TYPE_INTEGER;
        input8->required = NO;
        input8->gisprompt = _("no of operation value");
        input8->label = _("User input for number of operation");

        output = G_define_standard_option(G_OPT_R_OUTPUT);
        output->label = _("Name of the output vi layer");

        /********************/
        if (G_parser(argc, argv))
            exit(EXIT_FAILURE);
        viflag = input1->answer;
        redchan = input2->answer;
        nirchan = input3->answer;
        greenchan = input4->answer;
        bluechan = input5->answer;
        chan5chan = input6->answer;
        chan7chan = input7->answer;
        temp = atoi(input8->answer);

        result = output->answer;

        if (!strcasecmp(viflag, "sr") &&
            (!(input2->answer) || !(input3->answer)))
            G_fatal_error(_("sr index requires red and nir maps"));
        if (!strcasecmp(viflag, "ndvi") &&
            (!(input2->answer) || !(input3->answer)))
            G_fatal_error(_("ndvi index requires red and nir maps"));
        if (!strcasecmp(viflag, "ipvi") &&
            (!(input2->answer) || !(input3->answer)))
            G_fatal_error(_("ipvi index requires red and nir maps"));
        if (!strcasecmp(viflag, "dvi") &&
            (!(input2->answer) || !(input3->answer)))
            G_fatal_error(_("dvi index requires red and nir maps"));
        if (!strcasecmp(viflag, "pvi") &&
            (!(input2->answer) || !(input3->answer)))
            G_fatal_error(_("pvi index requires red and nir maps"));
        if (!strcasecmp(viflag, "wdvi") &&
            (!(input2->answer) || !(input3->answer)))
            G_fatal_error(_("wdvi index requires red and nir maps"));
        if (!strcasecmp(viflag, "savi") &&
            (!(input2->answer) || !(input3->answer)))
            G_fatal_error(_("savi index requires red and nir maps"));
        if (!strcasecmp(viflag, "msavi") &&
            (!(input2->answer) || !(input3->answer)))
            G_fatal_error(_("msavi index requires red and nir maps"));
        if (!strcasecmp(viflag, "msavi2") &&
            (!(input2->answer) || !(input3->answer) || !(input8->answer)))
            G_fatal_error(_("msavi2 index requires red and nir maps, and 3 "
                            "parameters related to soil line"));
        if (!strcasecmp(viflag, "gemi") &&
            (!(input2->answer) || !(input3->answer)))
            G_fatal_error(_("gemi index requires red and nir maps"));
        if (!strcasecmp(viflag, "arvi") &&
            (!(input2->answer) || !(input3->answer) || !(input5->answer)))
            G_fatal_error(_("arvi index requires blue, red and nir maps"));
        if (!strcasecmp(viflag, "evi") &&
            (!(input2->answer) || !(input3->answer) || !(input5->answer)))
            G_fatal_error(_("evi index requires blue, red and nir maps"));
        if (!strcasecmp(viflag, "vari") &&
            (!(input2->answer) || !(input4->answer) || !(input5->answer)))
            G_fatal_error(_("vari index requires blue, green and red maps"));
        if (!strcasecmp(viflag, "gari") &&
            (!(input2->answer) || !(input3->answer) || !(input4->answer) ||
             !(input5->answer)))
            G_fatal_error(
                _("gari index requires blue, green, red and nir maps"));
        if (!strcasecmp(viflag, "gvi") &&
            (!(input2->answer) || !(input3->answer) || !(input4->answer) ||
             !(input5->answer) || !(input6->answer) || !(input7->answer)))
            G_fatal_error(_("gvi index requires blue, green, red, nir, chan5 "
                            "and chan7 maps"));
        /***************************************************/
        infd_redchan = Rast_open_old(redchan, "");
        data_type_redchan = Rast_map_type(redchan, "");
        inrast_redchan = Rast_allocate_buf(data_type_redchan);
        infd_nirchan = Rast_open_old(nirchan, "");
        data_type_nirchan = Rast_map_type(nirchan, "");
        inrast_nirchan = Rast_allocate_buf(data_type_nirchan);
        if (greenchan) {
            infd_greenchan = Rast_open_old(greenchan, "");
            data_type_greenchan = Rast_map_type(greenchan, "");
            inrast_greenchan = Rast_allocate_buf(data_type_greenchan);
        }
        if (bluechan) {
            infd_bluechan = Rast_open_old(bluechan, "");
            data_type_bluechan = Rast_map_type(bluechan, "");
            inrast_bluechan = Rast_allocate_buf(data_type_bluechan);
        }
        if (chan5chan) {
            infd_chan5chan = Rast_open_old(chan5chan, "");
            data_type_chan5chan = Rast_map_type(chan5chan, "");
            inrast_chan5chan = Rast_allocate_buf(data_type_chan5chan);
        }
        if (chan7chan) {
            infd_chan7chan = Rast_open_old(chan7chan, "");
            data_type_chan7chan = Rast_map_type(chan7chan, "");
            inrast_chan7chan = Rast_allocate_buf(data_type_chan7chan);
        }
        nrows = Rast_window_rows();
        ncols = Rast_window_cols();
        /* Create New raster files */
        outfd = Rast_open_new(result, DCELL_TYPE);
        outrast = Rast_allocate_d_buf();
        /***************************************************/
        double db[6][ncols], R[ncols + 1], outputImage[NUM_HOSTS][ncols];
        int I[ncols + 1];
        host_n = 1;
        G_message("tmp=%d", temp);
        for (i = 1; i < NUM_HOSTS; i++) {
            MPI_Send(&temp, 1, MPI_INT, i, 1, MPI_COMM_WORLD);
            MPI_Send(&nrows, 1, MPI_INT, i, 1, MPI_COMM_WORLD);
            MPI_Send(&ncols, 1, MPI_INT, i, 1, MPI_COMM_WORLD);
        }
        /* Process pixels */
        int k, r, nh, cn;
        for (r = 1; r * (NUM_HOSTS - 1) <= nrows; r++) {
            for (k = 1; k < NUM_HOSTS; k++) {
                row = (r - 1) * (NUM_HOSTS - 1) + k - 1;
                DCELL d_bluechan;
                DCELL d_greenchan;
                DCELL d_redchan;
                DCELL d_nirchan;
                DCELL d_chan5chan;
                DCELL d_chan7chan;
                G_percent(row, nrows, 2);
                /* read input maps */
                Rast_get_row(infd_redchan, inrast_redchan, row,
                             data_type_redchan);
                Rast_get_row(infd_nirchan, inrast_nirchan, row,
                             data_type_nirchan);
                if (bluechan) {
                    Rast_get_row(infd_bluechan, inrast_bluechan, row,
                                 data_type_bluechan);
                }
                if (greenchan) {
                    Rast_get_row(infd_greenchan, inrast_greenchan, row,
                                 data_type_greenchan);
                }
                if (chan5chan) {
                    Rast_get_row(infd_chan5chan, inrast_chan5chan, row,
                                 data_type_chan5chan);
                }
                if (chan7chan) {
                    Rast_get_row(infd_chan7chan, inrast_chan7chan, row,
                                 data_type_chan7chan);
                }
                /*process the data */
                for (col = 0; col < ncols; col++) {
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
                    if (greenchan) {
                        switch (data_type_greenchan) {
                        case CELL_TYPE:
                            d_greenchan =
                                (double)((CELL *)inrast_greenchan)[col];
                            break;
                        case FCELL_TYPE:
                            d_greenchan =
                                (double)((FCELL *)inrast_greenchan)[col];
                            break;
                        case DCELL_TYPE:
                            d_greenchan = ((DCELL *)inrast_greenchan)[col];
                            break;
                        }
                    }
                    if (bluechan) {
                        switch (data_type_bluechan) {
                        case CELL_TYPE:
                            d_bluechan = (double)((CELL *)inrast_bluechan)[col];
                            break;
                        case FCELL_TYPE:
                            d_bluechan =
                                (double)((FCELL *)inrast_bluechan)[col];
                            break;
                        case DCELL_TYPE:
                            d_bluechan = ((DCELL *)inrast_bluechan)[col];
                            break;
                        }
                    }
                    if (chan5chan) {
                        switch (data_type_chan5chan) {
                        case CELL_TYPE:
                            d_chan5chan =
                                (double)((CELL *)inrast_chan5chan)[col];
                            break;
                        case FCELL_TYPE:
                            d_chan5chan =
                                (double)((FCELL *)inrast_chan5chan)[col];
                            break;
                        case DCELL_TYPE:
                            d_chan5chan = ((DCELL *)inrast_chan5chan)[col];
                            break;
                        }
                    }
                    if (chan7chan) {
                        switch (data_type_chan7chan) {
                        case CELL_TYPE:
                            d_chan7chan =
                                (double)((CELL *)inrast_chan7chan)[col];
                            break;
                        case FCELL_TYPE:
                            d_chan7chan =
                                (double)((FCELL *)inrast_chan7chan)[col];
                            break;
                        case DCELL_TYPE:
                            d_chan7chan = ((DCELL *)inrast_chan7chan)[col];
                            break;
                        }
                    }

                    db[0][col] = d_redchan;
                    db[1][col] = d_nirchan;
                    db[2][col] = d_greenchan;
                    db[3][col] = d_bluechan;
                    db[4][col] = d_chan5chan;
                    db[5][col] = d_chan7chan;
                    if (Rast_is_d_null_value(&d_redchan)) {
                        i = 0;
                    }
                    else if (Rast_is_d_null_value(&d_nirchan)) {
                        i = 0;
                    }
                    else if ((greenchan) &&
                             Rast_is_d_null_value(&d_greenchan)) {
                        i = 0;
                    }
                    else if ((bluechan) && Rast_is_d_null_value(&d_bluechan)) {
                        i = 0;
                    }
                    else if ((chan5chan) &&
                             Rast_is_d_null_value(&d_chan5chan)) {
                        i = 0;
                    }
                    else if ((chan7chan) &&
                             Rast_is_d_null_value(&d_chan7chan)) {
                        i = 0;
                    }
                    else {
                        /************************************/
                        /*calculate simple_ratio        */
                        if (!strcasecmp(viflag, "sr")) {
                            i = 1;
                        }
                        /*calculate ndvi                    */
                        if (!strcasecmp(viflag, "ndvi")) {
                            i = 2;
                        }
                        /*calculate ipvi                    */
                        if (!strcasecmp(viflag, "ipvi")) {
                            i = 3;
                        }
                        /*calculate dvi             */
                        if (!strcasecmp(viflag, "dvi")) {
                            i = 4;
                        }
                        /*calculate pvi             */
                        if (!strcasecmp(viflag, "pvi")) {
                            i = 5;
                        }
                        /*calculate wdvi                    */
                        if (!strcasecmp(viflag, "wdvi")) {
                            i = 6;
                        }
                        /*calculate savi                    */
                        if (!strcasecmp(viflag, "savi")) {
                            i = 7;
                        }
                        /*calculate msavi                   */
                        if (!strcasecmp(viflag, "msavi")) {
                            i = 8;
                        }
                        /*calculate msavi2            */
                        if (!strcasecmp(viflag, "msavi2")) {
                            i = 9;
                        }
                        /*calculate gemi                    */
                        if (!strcasecmp(viflag, "gemi")) {
                            i = 10;
                        }
                        /*calculate arvi                    */
                        if (!strcasecmp(viflag, "arvi")) {
                            i = 11;
                        }
                        /*calculate gvi            */
                        if (!strcasecmp(viflag, "gvi")) {
                            i = 12;
                        }
                        /*calculate gari                    */
                        if (!strcasecmp(viflag, "gari")) {
                            i = 13;
                        }
                        I[col] = i;

                    } /*else */

                } /*col */
                /*G_message("Row data was generated"); */
                row_n = k - 1;
                I[ncols] = row_n;
                /*MPI_Send(&row_n,1,MPI_INT,k,1,MPI_COMM_WORLD); */
                MPI_Send(I, ncols + 1, MPI_INT, k, 1, MPI_COMM_WORLD);
                MPI_Send(db, 6 * ncols, MPI_DOUBLE, k, 1, MPI_COMM_WORLD);
            } /*k */
            for (k = 1; k < NUM_HOSTS; k++) {
                /*MPI_Recv(&row_n,1,MPI_INT,k,1,MPI_COMM_WORLD,&status); */
                MPI_Recv(R, ncols + 1, MPI_DOUBLE, k, 1, MPI_COMM_WORLD,
                         &status);
                row_n = R[ncols];
                for (cn = 0; cn < ncols; cn++)
                    outputImage[row_n][cn] = R[cn];
            }

            for (k = 0; k < (NUM_HOSTS - 1); k++) {
                for (j = 0; j < ncols; j++)
                    outrast[j] = outputImage[k][j];
                Rast_put_d_row(outfd, outrast);
            }
        } /*r */
        k = 1;
        int lm = 0;

        for (r = row + 1; r < nrows; r++) {
            /* printf("row %d, node %d\n",r,k); */
            DCELL d_bluechan;
            DCELL d_greenchan;
            DCELL d_redchan;
            DCELL d_nirchan;
            DCELL d_chan5chan;
            DCELL d_chan7chan;
            G_percent(row, nrows, 2);

            /* read input maps */
            Rast_get_row(infd_redchan, inrast_redchan, row, data_type_redchan);
            Rast_get_row(infd_nirchan, inrast_nirchan, row, data_type_nirchan);
            if (bluechan) {
                Rast_get_row(infd_bluechan, inrast_bluechan, row,
                             data_type_bluechan);
            }
            if (greenchan) {
                Rast_get_row(infd_greenchan, inrast_greenchan, row,
                             data_type_greenchan);
            }
            if (chan5chan) {
                Rast_get_row(infd_chan5chan, inrast_chan5chan, row,
                             data_type_chan5chan);
            }
            if (chan7chan) {
                Rast_get_row(infd_chan7chan, inrast_chan7chan, row,
                             data_type_chan7chan);
            }

            /*process the data */

            for (col = 0; col < ncols; col++) {
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
                if (greenchan) {
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
                }
                if (bluechan) {
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
                }
                if (chan5chan) {

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
                }
                if (chan7chan) {
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
                }

                db[0][col] = d_redchan;
                db[1][col] = d_nirchan;
                db[2][col] = d_greenchan;
                db[3][col] = d_bluechan;
                db[4][col] = d_chan5chan;
                db[5][col] = d_chan7chan;

                if (Rast_is_d_null_value(&d_redchan)) {
                    i = 0;
                }
                else if (Rast_is_d_null_value(&d_nirchan)) {
                    i = 0;
                }
                else if ((greenchan) && Rast_is_d_null_value(&d_greenchan)) {
                    i = 0;
                }
                else if ((bluechan) && Rast_is_d_null_value(&d_bluechan)) {
                    i = 0;
                }
                else if ((chan5chan) && Rast_is_d_null_value(&d_chan5chan)) {
                    i = 0;
                }
                else if ((chan7chan) && Rast_is_d_null_value(&d_chan7chan)) {
                    i = 0;
                }
                else {
                    /************************************/
                    /*calculate simple_ratio        */
                    if (!strcasecmp(viflag, "sr")) {
                        i = 1;
                    }
                    /*calculate ndvi                    */
                    if (!strcasecmp(viflag, "ndvi")) {
                        i = 2;
                    }
                    /*calculate ipvi                    */
                    if (!strcasecmp(viflag, "ipvi")) {
                        i = 3;
                    }
                    /*calculate dvi             */
                    if (!strcasecmp(viflag, "dvi")) {
                        i = 4;
                    }
                    /*calculate pvi             */
                    if (!strcasecmp(viflag, "pvi")) {
                        i = 5;
                    }
                    /*calculate wdvi                    */
                    if (!strcasecmp(viflag, "wdvi")) {
                        i = 6;
                    }
                    /*calculate savi                    */
                    if (!strcasecmp(viflag, "savi")) {
                        i = 7;
                    }
                    /*calculate msavi                   */
                    if (!strcasecmp(viflag, "msavi")) {
                        i = 8;
                    }
                    /*calculate msavi2            */
                    if (!strcasecmp(viflag, "msavi2")) {
                        i = 9;
                    }
                    /*calculate gemi                    */
                    if (!strcasecmp(viflag, "gemi")) {
                        i = 10;
                    }
                    /*calculate arvi                    */
                    if (!strcasecmp(viflag, "arvi")) {
                        i = 11;
                    }
                    /*calculate gvi            */
                    if (!strcasecmp(viflag, "gvi")) {
                        i = 12;
                    }
                    /*calculate gari                    */
                    if (!strcasecmp(viflag, "gari")) {
                        i = 13;
                    }
                }
                I[col] = i;
            } /*col */
            row_n = k - 1;
            I[ncols] = row_n;
            /*MPI_Send(&row_n,1,MPI_INT,k,1,MPI_COMM_WORLD); */
            MPI_Send(I, ncols + 1, MPI_INT, k, 1, MPI_COMM_WORLD);
            MPI_Send(db, 6 * ncols, MPI_DOUBLE, k, 1, MPI_COMM_WORLD);
            k++;
            lm = 1;
        } /*r */
        if (lm) {
            for (nh = 1; nh < k; nh++) {
                /*MPI_Recv(&row_n,1,MPI_INT,nh,1,MPI_COMM_WORLD,&status); */
                MPI_Recv(R, ncols + 1, MPI_DOUBLE, nh, 1, MPI_COMM_WORLD,
                         &status);
                row_n = R[ncols];
                for (cn = 0; cn < ncols; cn++)
                    outputImage[row_n][cn] = R[cn];
            }
            for (nh = 0; nh < (k - 1); nh++) {
                for (j = 0; j < ncols; j++)
                    outrast[j] = outputImage[nh][j];
                Rast_put_d_row(outfd, outrast);
            }
        }
        MPI_Finalize();
        G_free(inrast_redchan);
        Rast_close(infd_redchan);
        G_free(inrast_nirchan);
        Rast_close(infd_nirchan);
        if (greenchan) {
            G_free(inrast_greenchan);
            Rast_close(infd_greenchan);
        }
        if (bluechan) {
            G_free(inrast_bluechan);
            Rast_close(infd_bluechan);
        }
        if (chan5chan) {
            G_free(inrast_chan5chan);
            Rast_close(infd_chan5chan);
        }
        if (chan7chan) {
            G_free(inrast_chan7chan);
            Rast_close(infd_chan7chan);
        }
        G_free(outrast);
        Rast_close(outfd);

        /* Color from -1.0 to +1.0 in grey */
        Rast_init_colors(&colors);
        val1 = -1;
        val2 = 1;
        Rast_add_c_color_rule(&val1, 0, 0, 0, &val2, 255, 255, 255, &colors);
        Rast_short_history(result, "raster", &history);
        Rast_command_history(&history);
        Rast_write_history(result, &history);

        exit(EXIT_SUCCESS);
    } /*if end */
    else if (me) {

        int col, n_rows, i, row_n, modv, nrows, ncols, t, temp;
        int *I;
        double *a, *b, *c, *d, *e, *f, *r;
        /*double *r; */
        MPI_Recv(&temp, 1, MPI_INT, 0, 1, MPI_COMM_WORLD, &status);
        MPI_Recv(&nrows, 1, MPI_INT, 0, 1, MPI_COMM_WORLD, &status);
        MPI_Recv(&ncols, 1, MPI_INT, 0, 1, MPI_COMM_WORLD, &status);
        /*printf("Slave->%d: nrows=%d, ncols=%d \n",me,nrows,ncols); */

        I = (int *)malloc((ncols + 2) * sizeof(int));
        a = (double *)malloc((ncols + 1) * sizeof(double));
        b = (double *)malloc((ncols + 1) * sizeof(double));
        c = (double *)malloc((ncols + 1) * sizeof(double));
        d = (double *)malloc((ncols + 1) * sizeof(double));
        e = (double *)malloc((ncols + 1) * sizeof(double));
        f = (double *)malloc((ncols + 1) * sizeof(double));

        r = (double *)malloc((ncols + 2) * sizeof(double));
        double db[6][ncols];

        n_rows = nrows / (NUM_HOSTS - 1);
        modv = nrows % (NUM_HOSTS - 1);
        /*temp=10; */
        /*printf("%d\n",temp); */

        /*int temp;     */
        if (modv >= me)
            n_rows++;
        for (i = 0; i < n_rows; i++) {

            /*MPI_Recv(&row_n,1,MPI_INT,0,1,MPI_COMM_WORLD,&status); */
            MPI_Recv(I, ncols + 1, MPI_INT, 0, 1, MPI_COMM_WORLD, &status);
            MPI_Recv(db, 6 * ncols, MPI_DOUBLE, 0, 1, MPI_COMM_WORLD, &status);
            for (col = 0; col < ncols; col++) {
                a[col] = db[0][col];
                b[col] = db[1][col];
                c[col] = db[2][col];
                d[col] = db[3][col];
                e[col] = db[4][col];
                f[col] = db[5][col];
                for (t = 0; t < temp; t++) {
                    if (I[col] == 0)
                        r[col] = -999.99;
                    else if (I[col] == 1) {
                        /*sr */
                        if (a[col] == 0.0) {
                            r[col] = -1.0;
                        }
                        else {
                            r[col] = (b[col] / a[col]);
                        }
                    }
                    else if (I[col] == 2) {
                        /*ndvi */
                        if ((b[col] + a[col]) == 0.0) {
                            r[col] = -1.0;
                        }
                        else {
                            r[col] = (b[col] - a[col]) / (b[col] + a[col]);
                        }
                    }
                    else if (I[col] == 3) {
                        /*ipvi */
                        if ((b[col] + a[col]) == 0.0) {
                            r[col] = -1.0;
                        }
                        else {
                            r[col] = (b[col]) / (b[col] + a[col]);
                        }
                    }
                    else if (I[col] == 4) {
                        /*dvi */
                        if ((b[col] + a[col]) == 0.0) {
                            r[col] = -1.0;
                        }
                        else {
                            r[col] = (b[col] - a[col]);
                        }
                    }
                    else if (I[col] == 5) {
                        /*pvi */
                        if ((b[col] + a[col]) == 0.0) {
                            r[col] = -1.0;
                        }
                        else {
                            r[col] = (sin(1.0) * b[col]) / (cos(1.0) * a[col]);
                        }
                    }
                    else if (I[col] == 6) {
                        /*wdvi */
                        double slope = 1; /*slope of soil line */

                        if ((b[col] + a[col]) == 0.0) {
                            r[col] = -1.0;
                        }
                        else {
                            r[col] = (b[col] - slope * a[col]);
                        }
                    }
                    else if (I[col] == 7) {
                        /*savi */
                        if ((b[col] + a[col]) == 0.0) {
                            r[col] = -1.0;
                        }
                        else {
                            r[col] = ((1 + 0.5) * (b[col] - a[col])) /
                                     (b[col] + a[col] + 0.5);
                        }
                    }
                    else if (I[col] == 8) {
                        /*msavi */
                        if ((b[col] + a[col]) == 0.0) {
                            r[col] = -1.0;
                        }
                        else {
                            r[col] =
                                (1 / 2) *
                                (2 * (b[col] + 1) -
                                 sqrt((2 * b[col] + 1) * (2 * b[col] + 1)) -
                                 (8 * (b[col] - a[col])));
                        }
                    }
                    else if (I[col] == 9) {
                        /*msavi2 */
                        if ((b[col] + a[col]) == 0.0) {
                            r[col] = -1.0;
                        }
                        else {
                            r[col] =
                                (1 / 2) *
                                (2 * (b[col] + 1) -
                                 sqrt((2 * b[col] + 1) * (2 * b[col] + 1)) -
                                 (8 * (b[col] - a[col])));
                        }
                    }
                    else if (I[col] == 10) {
                        /*gemi */
                        if ((b[col] + a[col]) == 0.0) {
                            r[col] = -1.0;
                        }
                        else {
                            r[col] =
                                (((2 * ((b[col] * b[col]) - (a[col] * a[col])) +
                                   1.5 * b[col] + 0.5 * a[col]) /
                                  (b[col] + a[col] + 0.5)) *
                                 (1 - 0.25 *
                                          (2 * ((b[col] * b[col]) -
                                                (a[col] * a[col])) +
                                           1.5 * b[col] + 0.5 * a[col]) /
                                          (b[col] + a[col] + 0.5))) -
                                ((a[col] - 0.125) / (1 - a[col]));
                        }
                    }
                    else if (I[col] == 11) {
                        /*arvi */
                        if ((b[col] + a[col]) == 0.0) {
                            r[col] = -1.0;
                        }
                        else {
                            r[col] = (b[col] - (2 * a[col] - d[col])) /
                                     (b[col] + (2 * a[col] - d[col]));
                        }
                    }
                    else if (I[col] == 12) {
                        /*gvi */
                        if ((b[col] + a[col]) == 0.0) {
                            r[col] = -1.0;
                        }
                        else {
                            r[col] = (-0.2848 * d[col] - 0.2435 * c[col] -
                                      0.5436 * a[col] + 0.7243 * b[col] +
                                      0.0840 * e[col] - 0.1800 * f[col]);
                        }
                    }
                    else if (I[col] == 13) {
                        /*gari */
                        r[col] = (b[col] - (c[col] - (d[col] - a[col]))) /
                                 (b[col] + (c[col] - (d[col] - a[col])));
                    }
                } /*for temp */
            } /*col end */
            r[ncols] = I[ncols];
            /*MPI_Send(&row_n,1,MPI_INT,0,1,MPI_COMM_WORLD); */
            MPI_Send(r, ncols + 1, MPI_DOUBLE, 0, 1, MPI_COMM_WORLD);
        } /*row end */

        free(I);
        free(a);
        free(b);
        free(c);
        free(d);
        free(e);
        free(f);
        free(r);
        MPI_Finalize();
    } /*if end */
} /*main end */
