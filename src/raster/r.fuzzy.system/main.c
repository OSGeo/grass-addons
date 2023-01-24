/* ***************************************************************************
 *
 * MODULE:       r.fuzzy.system
 * AUTHOR(S):    Jarek Jasiewicz <jarekj amu.edu.pl>
 * PURPOSE:      Fuzzy logic classification system with several fuzzy logic
 *               families implication and defuzzification and methods.
 * COPYRIGHT:    (C) 1999-2010 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *************************************************************************** */

#include <grass/gis.h>
#include <grass/glocale.h>
#include "local_proto.h"

STRING var_name_file;
STRING rule_name_file;
STRING output;
MAPS *s_maps;
RULES *s_rules;
OUTPUTS *m_outputs;
float **visual_output;
float *universe;
float *antecedents;
float *agregate;
int nmaps, nrules, output_index, multiple, membership_only, coor_proc;
int resolution;
implications implication;
defuzz defuzzification;
logics family;

char **rules;
int HERE;

int main(int argc, char **argv)
{
    struct Option *file_vars, *file_rules, *par_family, *par_resolution,
        *par_defuzzify, *par_implication, *in_coor_opt, *opt_output;

    struct History history;

    struct GModule *module;
    struct Flag *out_multiple, *out_membership;

    int nrows, ncols;
    int row, col;
    int outfd;
    float tmp;
    FCELL *out_buf;

    int i, j, n;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("fuzzy logic"));
    module->description =
        _("Fuzzy logic classification system with multiple fuzzy "
          "logic families implication and defuzzification and methods.");

    file_vars = G_define_standard_option(G_OPT_F_INPUT);
    file_vars->key = "maps";
    file_vars->required = YES;
    file_vars->description = _("Name of fuzzy variable file");

    file_rules = G_define_standard_option(G_OPT_F_INPUT);
    file_rules->key = "rules";
    file_rules->required = NO;
    file_rules->description = _("Name of rules file");

    par_family = G_define_option();
    par_family->key = "family";
    par_family->type = TYPE_STRING;
    par_family->options = "Zadeh,product,drastic,Lukasiewicz,Fodor,Hamacher";
    par_family->answer = "Zadeh";
    par_family->required = NO;
    par_family->description = _("Fuzzy logic family");
    par_family->guisection = _("Advanced options");

    par_defuzzify = G_define_option();
    par_defuzzify->key = "defuz";
    par_defuzzify->type = TYPE_STRING;
    par_defuzzify->options =
        "centroid,bisector,min_of_highest,max_of_highest,mean_of_highest";
    par_defuzzify->answer = "bisector";
    par_defuzzify->required = NO;
    par_defuzzify->description = _("Defuzzification method");
    par_defuzzify->guisection = _("Advanced options");

    par_implication = G_define_option();
    par_implication->key = "imp";
    par_implication->type = TYPE_STRING;
    par_implication->options = "minimum,product";
    par_implication->answer = "minimum";
    par_implication->required = NO;
    par_implication->description = _("Implication method");
    par_implication->guisection = _("Advanced options");

    par_resolution = G_define_option();
    par_resolution->key = "res";
    par_resolution->type = TYPE_INTEGER;
    par_resolution->answer = "100";
    par_resolution->required = NO;
    par_resolution->description = _("Universe resolution");
    par_resolution->guisection = _("Advanced options");

    in_coor_opt = G_define_option(); /* input coordinates */
    in_coor_opt->key = "coors";
    in_coor_opt->type = TYPE_STRING;
    in_coor_opt->key_desc = "x,y";
    in_coor_opt->answer = NULL;
    in_coor_opt->required = NO;
    in_coor_opt->multiple = NO;
    in_coor_opt->description =
        "Coordinate of cell for detail data (print end exit)";
    in_coor_opt->guisection = _("Visual Output");

    out_membership = G_define_flag();
    out_membership->key = 'o';
    out_membership->description = _("Print only membership values and exit");
    out_membership->guisection = _("Visual Output");

    out_multiple = G_define_flag();
    out_multiple->key = 'm';
    out_multiple->description =
        _("Create additional fuzzy output maps for every rule");

    opt_output = G_define_standard_option(G_OPT_R_OUTPUT);
    opt_output->description = _("Name of output file");
    opt_output->required = NO;

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    var_name_file = file_vars->answer;
    rule_name_file = file_rules->answer;
    output = opt_output->answer;
    multiple = (out_multiple->answer != 0);
    membership_only = (out_membership->answer != 0);
    coor_proc = (in_coor_opt->answer) ? 1 : 0;

    if (!membership_only & (!output | !rule_name_file))
        G_fatal_error(
            _("for standard analysis both output and rule file are required"));

    resolution = atoi(par_resolution->answer);
    if (resolution < 10)
        G_fatal_error(_("Universe resolution too small, choose greater value"));
    if (resolution > 500)
        G_warning(_("Universe resolution is very high, computation may take a "
                    "long time"));

    if (!strcmp(par_family->answer, "Zadeh"))
        family = l_ZADEH;
    else if (!strcmp(par_family->answer, "product"))
        family = l_PRODUCT;
    else if (!strcmp(par_family->answer, "drastic"))
        family = l_DRASTIC;
    else if (!strcmp(par_family->answer, "Lukasiewicz"))
        family = l_LUKASIEWICZ;
    else if (!strcmp(par_family->answer, "Fodor"))
        family = l_FODOR;
    else if (!strcmp(par_family->answer, "Hamacher"))
        family = l_HAMACHER;

    if (!strcmp(par_implication->answer, "minimum"))
        implication = i_MIN;
    else if (!strcmp(par_implication->answer, "product"))
        implication = i_PROD;

    if (!strcmp(par_defuzzify->answer, "centroid"))
        defuzzification = d_CENTEROID;
    else if (!strcmp(par_defuzzify->answer, "bisector"))
        defuzzification = d_BISECTOR;
    else if (!strcmp(par_defuzzify->answer, "min_of_highest"))
        defuzzification = d_MINOFHIGHEST;
    else if (!strcmp(par_defuzzify->answer, "max_of_highest"))
        defuzzification = d_MAXOFHIGHEST;
    else if (!strcmp(par_defuzzify->answer, "mean_of_highest"))
        defuzzification = d_MEANOFHIGHEST;

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    parse_map_file(var_name_file);
    if (membership_only)
        show_membership();

    parse_rule_file(rule_name_file);
    get_universe();
    open_maps();

    antecedents = (float *)G_malloc(nrules * sizeof(float));
    agregate = (float *)G_calloc(resolution, sizeof(float));
    if (coor_proc)
        process_coors(in_coor_opt->answer);

    outfd = Rast_open_new(output, FCELL_TYPE);
    out_buf = Rast_allocate_f_buf();

    if (multiple)
        create_output_maps();

    G_message("Calculate...");

    for (row = 0; row < nrows; ++row) {
        G_percent(row, nrows, 2);
        get_rows(row);
        for (col = 0; col < ncols; ++col) {
            if (get_cells(col)) {
                Rast_set_f_null_value(&out_buf[col], 1);

                if (multiple) {
                    for (i = 0; i < nrules; ++i)
                        Rast_set_f_null_value(&m_outputs[i].out_buf[col], 1);
                }
            }
            else {
                out_buf[col] = implicate();
                if (out_buf[col] == -9999)
                    Rast_set_f_null_value(&out_buf[col], 1);

                if (multiple) {
                    for (i = 0; i < nrules; ++i)
                        m_outputs[i].out_buf[col] = antecedents[i];
                }
            }
        }
        Rast_put_row(outfd, out_buf, FCELL_TYPE);

        if (multiple)
            for (i = 0; i < nrules; ++i)
                Rast_put_row(m_outputs[i].ofd, m_outputs[i].out_buf,
                             FCELL_TYPE);
    }
    G_percent(row, nrows, 2);

    G_message("Close...");

    Rast_close(outfd);
    Rast_short_history(output, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(output, &history);
    set_cats();
    /* free */
    for (i = 0; i < nmaps; ++i) {
        G_free(s_maps[i].sets);
        if (s_maps[i].output)
            continue;
        G_free(s_maps[i].in_buf);
        Rast_close(s_maps[i].cfd);
    }
    G_free(antecedents);
    G_free(agregate);
    G_free(out_buf);
    G_free(s_maps);
    G_free(s_rules);

    if (multiple)
        for (i = 0; i < nrules; ++i) {
            G_free(m_outputs[i].out_buf);
            Rast_close(m_outputs[i].ofd);
            Rast_short_history(m_outputs[i].output_name, "raster", &history);
            Rast_command_history(&history);
            Rast_write_history(m_outputs[i].output_name, &history);
        }

    G_message("Done!");
    exit(EXIT_SUCCESS);
}
