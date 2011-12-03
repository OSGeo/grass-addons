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
    struct Option *par_inputx,
	*par_inputy, *par_output, *par_operation, *par_family;

    struct Cell_head cellhdx;
    struct Cell_head cellhdy;
    struct Range membership_range;
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
    FCELL c_min, c_max;
    int family, operator;

    G_gisinit(argv[0]);

    module = G_define_module();
    module->keywords = _("raster, fuzzy logic");
    module->description =
        _("xxxx");

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
    par_operation->required = YES;
    par_operation->description = _("Fuzzy logic operation");

    par_family = G_define_option();
    par_family->key = "family";
    par_family->type = TYPE_STRING;
    par_family->options = "Zadeh,product,drastic,Lukasiewicz,Fodor,Hamacher";
    par_family->answer = "Zadeh";
    par_family->multiple = NO;
    par_family->required = YES;
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

    if (operator == _NOT && inputy)
	G_warning("Negation is unary operaton ymap is ignored");

    if (operator != _NOT && !inputy)
	G_fatal_error("For binary operation (AND, OR, IMP) ymap is required");

    if (family == DRASTIC && operator == _IMP)
	G_fatal_error("implication is not available for <drastic> family");

    /* end of interface */

    mapsetx = G_find_cell2(inputx, "");

    if (mapsetx == NULL)
	G_fatal_error(_("Raster map <%s> not found"), inputx);

    if ((infdx = G_open_cell_old(inputx, mapsetx)) < 0)
	G_fatal_error(_("Unable to open raster map <%s>"), inputx);

    if (G_get_cellhd(inputx, mapsetx, &cellhdx) < 0)
	G_fatal_error(_("Unable to read file header of <%s>"), inputx);

    if (G_raster_map_type(inputx, mapsetx) != FCELL_TYPE)
	G_fatal_error(_("<%s> is not of type CELL"), inputx);

    G_init_fp_range(&membership_range);
    G_read_fp_range(inputx, mapsetx, &membership_range);
    G_get_fp_range_min_max(&membership_range, &c_min, &c_max);
    if (c_min < 0 || c_max > 1)
	G_fatal_error("Membership out of range");

    in_bufx = G_allocate_raster_buf(FCELL_TYPE);

    if (inputy) {

	mapsety = G_find_cell2(inputy, "");

	if (mapsety == NULL)
	    G_fatal_error(_("Raster map <%s> not found"), inputy);

	if ((infdy = G_open_cell_old(inputy, mapsety)) < 0)
	    G_fatal_error(_("Unable to open raster map <%s>"), inputy);

	if (G_get_cellhd(inputy, mapsety, &cellhdy) < 0)
	    G_fatal_error(_("Unable to read file header of <%s>"), inputy);

	if (G_raster_map_type(inputy, mapsety) != FCELL_TYPE)
	    G_fatal_error(_("<%s> is not of type CELL"), inputy);

	G_init_fp_range(&membership_range);
	G_read_fp_range(inputy, mapsety, &membership_range);
	G_get_fp_range_min_max(&membership_range, &c_min, &c_max);
	if (c_min < 0 || c_max > 1)
	    G_fatal_error("Membership out of range");


	in_bufy = G_allocate_raster_buf(FCELL_TYPE);

    }				/* end if inputy */

    nrows = G_window_rows();
    ncols = G_window_cols();

    if ((outfd = G_open_raster_new(output, FCELL_TYPE)) < 0)
	G_fatal_error(_("Unable to create raster map <%s>"), output);

    out_buf = G_allocate_raster_buf(FCELL_TYPE);


    /* binary processing */
    for (row = 0; row < nrows; row++) {
	G_percent(row, nrows, 2);

	FCELL fx, fy = 0;

	if (G_get_raster_row(infdx, in_bufx, row, FCELL_TYPE) < 0) {
	    G_close_cell(infdx);
	    G_fatal_error(_("Cannot to read <%s> at row <%d>"), inputx, row);
	}

	if (inputy)
	    if (G_get_raster_row(infdy, in_bufy, row, FCELL_TYPE) < 0) {
		G_close_cell(infdy);
		G_fatal_error(_("Cannot to read <%s> at row <%d>"), inputy,
			      row);
	    }

	for (col = 0; col < ncols; col++) {

	    fx = ((FCELL *) in_bufx)[col];
	    if (inputy)
		fy = ((FCELL *) in_bufy)[col];

	    if (G_is_f_null_value(&fx) || G_is_f_null_value(&fy))
		G_set_f_null_value(&tmp, 1);

	    else

		switch (operator) {
		case _AND:
		    //if((row+col)%100==0)
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
		}		/* end switch */

	    ((FCELL *) out_buf)[col] = tmp;
	}

	if (G_put_raster_row(outfd, out_buf, FCELL_TYPE) < 0)
	    G_fatal_error(_("Failed writing raster map <%s>"), output);
    }				/* end for row */

    G_free(in_bufx);
    G_close_cell(infdx);

    if (inputy) {
	G_free(in_bufy);
	G_close_cell(infdy);
    }

    G_free(out_buf);
    G_close_cell(outfd);

    G_short_history(output, "raster", &history);
    G_command_history(&history);
    G_write_history(output, &history);

    exit(EXIT_SUCCESS);
}
