/****************************************************************
 *
 * MODULE:     v.centerpoint
 *
 * AUTHOR(S):  Markus Metz
 *
 * PURPOSE:    Calculates center points
 *
 * COPYRIGHT:  (C) 2013 by the GRASS Development Team
 *
 *             This program is free software under the
 *             GNU General Public License (>=v2).
 *             Read the file COPYING that comes with GRASS
 *             for details.
 *
 ****************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <grass/gis.h>
#include <grass/vector.h>
#include <grass/glocale.h>
#include "local_proto.h"

int main(int argc, char *argv[])
{
    struct Map_info In, Out, *Outp;
    struct line_pnts *Points;
    struct line_cats *Cats;
    int i, type, out3d;
    char *mapset;
    struct GModule *module; /* GRASS module for parsing arguments */
    struct Option *old, *new, *type_opt, *lyr_opt, *cats_opt, *where_opt;
    struct Option *pmode, *lmode, *amode;
    struct Flag *topo_flag;
    char *pdesc, *ldesc, *adesc;
    struct cat_list *cat_list = NULL;
    int layer, itype;
    int nprimitives, npoints, nlines;
    int mode;

    /* initialize GIS environment */
    /* reads grass env, stores program name to G_program_name() */
    G_gisinit(argv[0]);

    /* initialize module */
    module = G_define_module();
    G_add_keyword(_("vector"));
    G_add_keyword(_("geometry"));
    G_add_keyword(_("center"));
    module->description = _("Calculate center points");

    /* Define the different options as defined in gis.h */
    old = G_define_standard_option(G_OPT_V_INPUT);

    new = G_define_standard_option(G_OPT_V_OUTPUT);
    new->required = NO;

    type_opt = G_define_standard_option(G_OPT_V_TYPE);
    type_opt->options = "point,line,area";
    type_opt->answer = "point,line,area";
    type_opt->guisection = _("Selection");

    lyr_opt = G_define_standard_option(G_OPT_V_FIELD);
    lyr_opt->guisection = _("Selection");

    cats_opt = G_define_standard_option(G_OPT_V_CATS);
    cats_opt->guisection = _("Selection");

    where_opt = G_define_standard_option(G_OPT_DB_WHERE);
    where_opt->guisection = _("Selection");

    pmode = G_define_option();
    pmode->type = TYPE_STRING;
    pmode->key = "pcenter";
    pmode->label = _("point center");
    pmode->multiple = YES;
    pmode->options = "mean,median,pmedian";
    pmode->answer = "mean";
    pdesc = NULL;
    G_asprintf(&pdesc,
               "mean;%s;"
               "median;%s;"
               "pmedian;%s;",
               _("Center of gravity"),
               _("Geometric median (point of minimum distance)"),
               _("Point closest to geometric median"));
    pmode->descriptions = pdesc;

    lmode = G_define_option();
    lmode->type = TYPE_STRING;
    lmode->key = "lcenter";
    lmode->label = _("line center");
    lmode->multiple = YES;
    lmode->options = "mid,mean,median";
    lmode->answer = "mid";
    ldesc = NULL;
    G_asprintf(
        &ldesc,
        "mid;%s;"
        "mean;%s;"
        "median;%s;",
        _("Line mid point"), _("Center of gravity"),
        _("Geometric median (point of minimum distance) using line segments"));
    lmode->descriptions = ldesc;

    amode = G_define_option();
    amode->type = TYPE_STRING;
    amode->key = "acenter";
    amode->label = _("area center");
    amode->multiple = YES;
    amode->options = "mean,median,bmedian";
    amode->answer = "mean";
    adesc = NULL;
    G_asprintf(
        &adesc,
        "mean;%s;"
        "median;%s;"
        "bmedian;%s;",
        _("Center of gravity"),
        _("Geometric median (point of minimum distance) using area sizes"),
        _("Geometric median (point of minimum distance) using boundary "
          "segments"));
    amode->descriptions = adesc;

    topo_flag = G_define_standard_flag(G_FLG_V_TOPO);

    /* parse options and flags */
    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    if (!(itype = Vect_option_to_types(type_opt)))
        G_fatal_error(_("No feature types selected"));

    mode = 0;
    for (i = 0; pmode->answers[i]; i++) {
        if (!strcmp(pmode->answers[i], "mean"))
            mode |= P_MEAN;
        else if (!strcmp(pmode->answers[i], "median"))
            mode |= P_MEDIAN;
        else if (!strcmp(pmode->answers[i], "pmedian"))
            mode |= P_MEDIAN_P;
        else
            G_fatal_error(_("Invalid answer '%s' for option '%s'"),
                          pmode->answers[i], pmode->key);
    }
    for (i = 0; lmode->answers[i]; i++) {
        if (!strcmp(lmode->answers[i], "mid"))
            mode |= L_MID;
        else if (!strcmp(lmode->answers[i], "mean"))
            mode |= L_MEAN;
        else if (!strcmp(lmode->answers[i], "median"))
            mode |= L_MEDIAN;
        else
            G_fatal_error(_("Invalid answer '%s' for option '%s'"),
                          lmode->answers[i], lmode->key);
    }
    for (i = 0; amode->answers[i]; i++) {
        if (!strcmp(amode->answers[i], "mean"))
            mode |= A_MEAN;
        else if (!strcmp(amode->answers[i], "median"))
            mode |= A_MEDIAN;
        else if (!strcmp(amode->answers[i], "bmedian"))
            mode |= A_MEDIAN_B;
        else
            G_fatal_error(_("Invalid answer '%s' for option '%s'"),
                          amode->answers[i], amode->key);
    }

    if ((mapset = (char *)G_find_vector2(old->answer, "")) == NULL)
        G_fatal_error(_("Vector map <%s> not found"), old->answer);

    Vect_set_open_level(1);

    if (1 > Vect_open_old(&In, old->answer, mapset))
        G_fatal_error(_("Unable to open vector map <%s>"), old->answer);

    layer = Vect_get_field_number(&In, lyr_opt->answer);

    if (layer < 1)
        G_fatal_error(_("Invalid %s answer: %s"), lyr_opt->key,
                      lyr_opt->answer);

    cat_list = Vect_cats_set_constraint(&In, layer, where_opt->answer,
                                        cats_opt->answer);

    out3d = Vect_is_3d(&In);

    Outp = NULL;
    if (new->answer) {
        Vect_check_input_output_name(old->answer, new->answer, G_FATAL_EXIT);
        Vect_open_new(&Out, new->answer, out3d);

        /* Copy header and history data from old to new map */
        Vect_copy_head_data(&In, &Out);
        Vect_hist_copy(&In, &Out);
        Vect_hist_command(&Out);

        Outp = &Out;
    }

    Points = Vect_new_line_struct();
    Cats = Vect_new_cats_struct();

    i = 1;
    nprimitives = npoints = nlines = 0;

    /* count features */
    while ((type = Vect_read_next_line(&In, Points, Cats)) > 0) {

        nprimitives++;

        if (type == GV_LINE) {
            nlines++;
        }
        if (type == GV_POINT) {
            npoints++;
        }
    }

    /* filter feature count */
    if (!((mode & P_MEAN) | (mode & P_MEDIAN) | (mode & P_MEDIAN_P)))
        npoints = 0;
    if (!((mode & L_MID) | (mode & L_MEAN) | (mode & L_MEDIAN)))
        nlines = 0;

    /* do the work */
    if (npoints) {
        points_center(&In, Outp, layer, cat_list, nprimitives, mode);
    }
    if (nlines) {
        lines_center(&In, Outp, layer, cat_list, nprimitives, mode);
        if (Outp)
            Vect_copy_table(&In, Outp, layer, 1, NULL, GV_1TABLE);
    }

    Vect_close(&In);

    /* areas */
    if (itype & GV_AREA) {
        Vect_set_open_level(2);

        if (1 > Vect_open_old(&In, old->answer, mapset))
            G_warning(_("Unable to open vector map <%s> with topology"),
                      old->answer);
        else {
            if (Vect_get_num_areas(&In) > 0) {
                areas_center(&In, Outp, layer, cat_list, mode);
                if (Outp)
                    Vect_copy_table(&In, Outp, layer, 1, NULL, GV_1TABLE);
            }
            else
                G_warning(_("No areas in input vector <%s>"), old->answer);

            Vect_close(&In);
        }
    }

    if (Outp) {
        if (!topo_flag->answer)
            Vect_build(&Out);
        Vect_close(&Out);
    }

    exit(EXIT_SUCCESS);
}
