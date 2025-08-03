/****************************************************************************
 *
 * MODULE:       i.feo_tio2
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 * PURPOSE:      Calculate FeO or TiO2 content
 *               from various Clementine UVVIS bands
 *               or FeO from Chandrayaan-1 M3
 *
 * COPYRIGHT:    (C) 2014 by the GRASS Development Team
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

#define MAXFILES 8
double feo(double r750, double r950, double theta);
double tio2(double r415, double r750, double y0Ti, double s0Ti);
double feozhang2013(double r750, double r950);

double feolucey2000(double uvvis2, double uvvis4);
double feolawrence2002(double uvvis2, double uvvis4);
double feowilcox2005(double uvvis2, double uvvis4);
double omatlucey2000(double uvvis2, double uvvis4);
double omatwilcox2005(double uvvis2, double uvvis4);
double tio2lucey2000(double uvvis1, double uvvis2);

int main(int argc, char *argv[])
{
    struct Cell_head cellhd; /*region+header info */
    int nrows, ncols;
    int row, col;
    char *equationflag; /*Switch for particular equation */
    char *desc;
    struct GModule *module;
    struct Option *in0, *in1, *output, *param0, *param1, *eqname;
    struct Flag *flag1;
    struct History history; /*metadata */
    struct Colors colors;   /*Color rules */

    int infd0, infd1, outfd;
    int i = 0;
    DCELL *inrast0, *inrast1;
    DCELL *outrast;

    CELL val1, val2;

    /*Default value of theta from Wilcox et al (2005)*/
    double theta = 1.3885;

    double param_0, param_1;
    /************************************/
    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("imagery"));
    G_add_keyword(_("Moon"));
    G_add_keyword(_("Clementine"));
    G_add_keyword(_("Chandrayaan1"));
    G_add_keyword(_("UVVIS"));
    G_add_keyword(_("M3"));
    G_add_keyword(_("FeO"));
    G_add_keyword(_("TiO2"));
    G_add_keyword(_("reflectance"));
    module->description = _("Calculates the FeO or TiO2 contents from the "
                            "Clementine project Moon data.");

    /* Define the different options */
    in0 = G_define_standard_option(G_OPT_R_INPUT);
    in0->key = "band0";
    in0->description = _("reflectance band at 750 nm (UVVIS 2, M3 9)");

    in1 = G_define_standard_option(G_OPT_R_INPUT);
    in1->key = "band1";
    in1->description = _("reflectance band at 950 nm (UVVIS 4 for FeO/OMAT, M3 "
                         "19) or at 415 nm (UVVIS 1 for TiO2)");

    output = G_define_standard_option(G_OPT_R_OUTPUT);

    param0 = G_define_option();
    param0->key = "param0";
    param0->type = TYPE_DOUBLE;
    param0->required = NO;
    param0->description = _("Value of theta (FeO) or y0Ti (TiO2)");
    param0->guisection = _("Parameters");

    param1 = G_define_option();
    param1->key = "param1";
    param1->type = TYPE_DOUBLE;
    param1->required = NO;
    param1->description = _("Value of s0Ti (TiO2)");
    param1->guisection = _("Parameters");

    eqname = G_define_option();
    eqname->key = "eqname";
    eqname->type = TYPE_STRING;
    eqname->required = YES;
    eqname->description = _("Type of equation");
    desc = NULL;
    G_asprintf(
        &desc,
        "feolucey2000;%s;feolawrence2002;%s;feowilcox2005_setparam;%s;"
        "feowilcox2005;%s;feozhang2013;%s;omatlucey2000;%s;omatwilcox2005;%s;"
        "tio2lucey2000_setparam;%s;tio2lucey2000;%s",
        _("FeO (Lucey et al., 2000)"), _("FeO (lawrence et al., 2002)"),
        _("FeO (Wilcox et al., 2005) set parameter theta"),
        _("FeO (Wilcox et al., 2005)"), _("FeO (Zhang et al., 2013)"),
        _("OMAT (Lucey et al., 2000)"), _("OMAT (Wilcox et al., 2005)"),
        _("TiO2 (Lucey et al., 2000) set parameters"),
        _("TiO2 (Lucey et al., 2000)"));
    eqname->descriptions = desc;
    eqname->options = "feolucey2000,feolawrence2002,feowilcox2005_setparam,"
                      "feowilcox2005,feozhang2013,omatlucey2000,omatwilcox2005,"
                      "tio2lucey2000_setparam,tio2lucey2000";
    eqname->answer = "feolucey2000";
    eqname->key_desc = _("type");

    /* Define the different flags */
    flag1 = G_define_flag();
    flag1->key = 't';
    flag1->description = _("TiO2 (refl@415, refl@750 & y0Ti, s0Ti)");

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    equationflag = eqname->answer;

    if (!strcasecmp(equationflag, "feowilcox2005_setparam")) {
        if (param0->answer)
            param_0 = atof(param0->answer);
        else
            G_fatal_error("Please set param0 Theta (FeO Wilcox 2005)");
    }

    if (!strcasecmp(equationflag, "tio2lucey2000_setparam")) {
        if (param0->answer)
            param_0 = atof(param0->answer);
        else
            G_fatal_error("Please set param0 y0Ti (TiO2 Lucey 2000)");
        if (param1->answer)
            param_1 = atof(param1->answer);
        else
            G_fatal_error("Please set param1 s0Ti (TiO2 Lucey 2000)");
    }

    /* Allocate input buffer */
    infd0 = Rast_open_old(in0->answer, "");
    Rast_get_cellhd(in0->answer, "", &cellhd);
    inrast0 = Rast_allocate_d_buf();

    infd1 = Rast_open_old(in1->answer, "");
    Rast_get_cellhd(in1->answer, "", &cellhd);
    inrast1 = Rast_allocate_d_buf();

    /* Allocate output buffer, use input map data_type */
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();
    outrast = Rast_allocate_buf(DCELL_TYPE);

    /* Create New raster files */
    outfd = Rast_open_new(output->answer, 1);

    /* Process pixels */
    for (row = 0; row < nrows; row++) {
        DCELL d0, d1;

        G_percent(row, nrows, 2);
        Rast_get_d_row(infd0, inrast0, row);
        Rast_get_d_row(infd1, inrast1, row);

        /*process the data */
        for (col = 0; col < ncols; col++) {
            d0 = (double)((DCELL *)inrast0)[col]; // UVVIS2
            d1 = (double)((DCELL *)inrast1)[col]; // UVVIS4 or 1
            if (Rast_is_d_null_value(&d0) || Rast_is_d_null_value(&d1)) {
                Rast_set_d_null_value(&outrast[col], 1);
            }
            else {
                if (!strcasecmp(equationflag, "tio2lucey2000_setparam"))
                    outrast[col] = tio2(d1, d0, param_0, param_1);
                else if (!strcasecmp(equationflag, "feowilcox2005_setparam"))
                    outrast[col] = feo(d0, d1, param_0);
                else if (!strcasecmp(equationflag, "tio2lucey2000"))
                    outrast[col] = tio2lucey2000(d1, d0);
                else if (!strcasecmp(equationflag, "feowilcox2005"))
                    outrast[col] = feowilcox2005(d0, d1);
                else if (!strcasecmp(equationflag, "feolawrence2002"))
                    outrast[col] = feolawrence2002(d0, d1);
                else if (!strcasecmp(equationflag, "feolucey2000"))
                    outrast[col] = feolucey2000(d0, d1);
                else if (!strcasecmp(equationflag, "feozhang2013"))
                    outrast[col] = feozhang2013(d0, d1);
                else if (!strcasecmp(equationflag, "omatwilcox2005"))
                    outrast[col] = omatwilcox2005(d0, d1);
                else if (!strcasecmp(equationflag, "omatlucey2000"))
                    outrast[col] = omatlucey2000(d0, d1);
                else {
                    G_fatal_error("Please enter an appropriate equation name");
                }
            }
        }
        Rast_put_d_row(outfd, outrast);
    }
    G_free(inrast0);
    G_free(inrast1);
    Rast_close(infd0);
    Rast_close(infd1);
    G_free(outrast);
    Rast_close(outfd);

    /* Color table from 0.0 to 1.0 */
    Rast_init_colors(&colors);
    val1 = 0;
    val2 = 10;
    Rast_add_c_color_rule(&val1, 0, 0, 0, &val2, 255, 255, 255, &colors);
    /* Metadata */
    Rast_short_history(output->answer, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(output->answer, &history);

    exit(EXIT_SUCCESS);
}
