/* ***************************************************************************
 *
 * MODULE:       r.fuzzy.logic
 * AUTHOR(S):    Jarek Jasiewicz <jarekj amu.edu.pl>
 * PURPOSE:      Performs logical operations on membership images created with
 *                   r.fuzzy or different method. Use families for fuzzy logic
 * COPYRIGHT:    (C) 1999-2010 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 ****************************************************************************
 */

#include <grass/gis.h>
#include <grass/glocale.h>
#include "local_proto.h"

int main(int argc, char *argv[])
{

    struct GModule *module;
    struct Option *par_inputx, *par_inputy, *par_output, *par_operation,
        *par_family;

    struct Cell_head cellhdx;
    struct Cell_head cellhdy;
    struct FPRange membership_range;
    struct History history;

    char *mapsetx, *mapsety;
    char *inputx, *inputy;
    char *output;
    int nrows, ncols;
    int row, col;
    int infdx, infdy, outfd;
    void *in_bufx, *in_bufy;
    unsigned char *out_buf;
    float tmp;
    DCELL c_min, c_max;
    int family, operator;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("fuzzy logic"));
    module->description =
        _("Performs logical operations on membership images created with "
          "r.fuzzy.set or different method. Use families for fuzzy logic.");

    par_inputx = G_define_standard_option(G_OPT_R_INPUT);
    par_inputx->description = _("x operand (membership map)");
    par_inputx->key = "xmap";

    par_inputy = G_define_standard_option(G_OPT_R_INPUT);
    par_inputy->description = _("y operand (membership map)");
    par_inputy->key = "ymap";
    par_inputy->required = NO;

    par_output = G_define_standard_option(G_OPT_R_OUTPUT);
    par_output->description = _("Resulting map");

    par_operation = G_define_option();
    par_operation->key = "operator";
    par_operation->type = TYPE_STRING;
    par_operation->options = "AND,OR,NOT,IMP";
    par_operation->answer = "AND";
    par_operation->multiple = NO;
    par_operation->required = NO;
    par_operation->description = _("Fuzzy logic operation");

    par_family = G_define_option();
    par_family->key = "family";
    par_family->type = TYPE_STRING;
    par_family->options = "Zadeh,product,drastic,Lukasiewicz,Fodor,Hamacher";
    par_family->answer = "Zadeh";
    par_family->multiple = NO;
    par_family->required = NO;
    par_family->description = _("Fuzzy logic family");

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    inputx = par_inputx->answer;
    inputy = par_inputy->answer;
    output = par_output->answer;

    if (!strcmp(par_operation->answer, "AND"))
        operator= _AND;

    else if (!strcmp(par_operation->answer, "OR"))
        operator= _OR;

    else if (!strcmp(par_operation->answer, "NOT"))
        operator= _NOT;

    else if (!strcmp(par_operation->answer, "IMP"))
        operator= _IMP;

    if (!strcmp(par_family->answer, "Zadeh"))
        family = ZADEH;
    else if (!strcmp(par_family->answer, "product"))
        family = PRODUCT;
    else if (!strcmp(par_family->answer, "drastic"))
        family = DRASTIC;
    else if (!strcmp(par_family->answer, "Lukasiewicz"))
        family = LUKASIEWICZ;
    else if (!strcmp(par_family->answer, "Fodor"))
        family = FODOR;
    else if (!strcmp(par_family->answer, "Hamacher"))
        family = HAMACHER;

    if (operator== _NOT && inputy)
        G_warning("Negation is unary operation ymap is ignored");

    if (operator!= _NOT && !inputy)
        G_fatal_error("For binary operation (AND, OR, IMP) ymap is required");

    if (family == DRASTIC && operator== _IMP)
        G_fatal_error("implication is not available for <drastic> family");

    /* end of interface */

    mapsetx = (char *)G_find_raster2(inputx, "");

    if (mapsetx == NULL)
        G_fatal_error(_("Raster map <%s> not found"), inputx);

    infdx = Rast_open_old(inputx, mapsetx);
    Rast_get_cellhd(inputx, mapsetx, &cellhdx);

    if (Rast_map_type(inputx, mapsetx) != FCELL_TYPE)
        G_fatal_error(_("<%s> is not of type FCELL"), inputx);

    Rast_init_fp_range(&membership_range);
    Rast_read_fp_range(inputx, mapsetx, &membership_range);
    Rast_get_fp_range_min_max(&membership_range, &c_min, &c_max);
    if (c_min < 0 || c_max > 1)
        G_fatal_error("Membership out of range");

    in_bufx = Rast_allocate_buf(FCELL_TYPE);

    if (inputy) {

        mapsety = (char *)G_find_raster2(inputy, "");

        if (mapsety == NULL)
            G_fatal_error(_("Raster map <%s> not found"), inputy);

        infdy = Rast_open_old(inputy, mapsety);
        Rast_get_cellhd(inputy, mapsety, &cellhdy);

        if (Rast_map_type(inputy, mapsety) != FCELL_TYPE)
            G_fatal_error(_("<%s> is not of type FCELL"), inputy);

        Rast_init_fp_range(&membership_range);
        Rast_read_fp_range(inputy, mapsety, &membership_range);
        Rast_get_fp_range_min_max(&membership_range, &c_min, &c_max);
        if (c_min < 0 || c_max > 1)
            G_fatal_error("Membership out of range");

        in_bufy = Rast_allocate_buf(FCELL_TYPE);

    } /* end if inputy */

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    outfd = Rast_open_new(output, FCELL_TYPE);
    out_buf = Rast_allocate_buf(FCELL_TYPE);

    /* binary processing */
    for (row = 0; row < nrows; row++) {
        G_percent(row, nrows, 2);

        FCELL fx, fy = 0;

        Rast_get_row(infdx, in_bufx, row, FCELL_TYPE);

        if (inputy)
            Rast_get_row(infdy, in_bufy, row, FCELL_TYPE);

        for (col = 0; col < ncols; col++) {

            fx = ((FCELL *)in_bufx)[col];
            if (inputy)
                fy = ((FCELL *)in_bufy)[col];

            if (Rast_is_f_null_value(&fx) || Rast_is_f_null_value(&fy))
                Rast_set_f_null_value(&tmp, 1);

            else

                switch (operator) {
                case _AND:
                    // if((row+col)%100==0)
                    if (0 > (tmp = f_and(fx, fy, family)))
                        G_warning("Cannot determine result at row %d, col %d",
                                  row, col);
                    break;

                case _OR:
                    if (0 > (tmp = f_or(fx, fy, family)))
                        G_warning("Cannot determine result at row %d, col %d",
                                  row, col);
                    break;

                case _IMP:
                    if ((tmp = f_imp(fx, fy, family)) < 0)
                        G_warning("Cannot determine result at row %d, col %d",
                                  row, col);
                    break;

                case _NOT:
                    if ((tmp = f_not(fx, family)) < 0)
                        G_warning("Cannot determine result at row %d, col %d",
                                  row, col);
                    break;
                } /* end switch */

            ((FCELL *)out_buf)[col] = tmp;
        }
        Rast_put_row(outfd, out_buf, FCELL_TYPE);
    } /* end for row */

    G_free(in_bufx);
    Rast_close(infdx);

    if (inputy) {
        G_free(in_bufy);
        Rast_close(infdy);
    }

    G_free(out_buf);
    Rast_close(outfd);

    Rast_short_history(output, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(output, &history);

    exit(EXIT_SUCCESS);
}
