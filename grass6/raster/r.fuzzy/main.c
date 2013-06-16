/* **************************************************************************
 *
 * MODULE:       r.fuzzy
 * AUTHOR(S):    Jarek Jasiewicz <jarekj amu.edu.pl>
 * PURPOSE:      Calculate membership value of any raster map according user's rules
 * COPYRIGHT:    (C) 1999-2011 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 ****************************************************************************/

#include <grass/gis.h>
#include <grass/glocale.h>
#include "local_proto.h"

char *input, *output;
float shape, height;
int type, side;
double p[4];                     /* inflection points */
int num_points;

int main(int argc, char *argv[])
{
    struct Option *par_input,
	*par_output,
	*par_points, *par_side, *par_type, *par_height, *par_shape;

    struct GModule *module;
    struct Cell_head cellhd;
    struct History history;


    char *mapset;
    int nrows, ncols;
    int row, col;
    int infd, outfd;
    void *in_buf;
    unsigned char *out_buf;
    RASTER_MAP_TYPE raster_type;
    FCELL tmp = 0;

    G_gisinit(argv[0]);

    module = G_define_module();
    module->keywords = _("raster, fuzzy logic");
    module->description = _("Cluster raster maps using fuzzy logic.");

    par_input = G_define_standard_option(G_OPT_R_INPUT);
    par_input->description = _("Raster map to be fuzzified");

    par_output = G_define_standard_option(G_OPT_R_OUTPUT);
    par_output->description = _("Membership map");

    par_points = G_define_option();
    par_points->key = "points";
    par_points->type = TYPE_STRING;
    par_points->answer = "a,b[,c,d]";
    par_points->multiple = YES;
    par_points->required = YES;
    par_points->description = _("Inflection points: a,b[,c,d]");

    par_side = G_define_option();
    par_side->key = "side";
    par_side->type = TYPE_STRING;
    par_side->options = "both,left,right";
    par_side->answer = "both";
    par_side->multiple = NO;
    par_side->description = _("Fuzzy range");

    par_type = G_define_option();
    par_type->key = "boundary";
    par_type->type = TYPE_STRING;
    par_type->options = "Linear,S-shaped,J-shaped,G-shaped";
    par_type->answer = "S-shaped";
    par_type->multiple = NO;
    par_type->description = _("Type of fuzzy boundaries");
    par_type->guisection = _("Default options");

    par_shape = G_define_option();
    par_shape->key = "shape";
    par_shape->type = TYPE_DOUBLE;
    par_shape->options = "-1.0-1.0";
    par_shape->answer = "0.";
    par_shape->multiple = NO;
    par_shape->description = _("Shape modifier: -1 to 1");
    par_shape->guisection = _("Default options");

    par_height = G_define_option();
    par_height->key = "height";
    par_height->type = TYPE_DOUBLE;
    par_height->options = "0.0-1.0";
    par_height->answer = "1";
    par_height->multiple = NO;
    par_height->description = _("Membership height: 0 to 1");
    par_height->guisection = _("Default options");

    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);


    input = par_input->answer;
    output = par_output->answer;

    if (!strcmp(par_type->answer, "Linear"))
	type = LINEAR;
    else if (!strcmp(par_type->answer, "S-shaped"))
	type = SSHAPE;
    else if (!strcmp(par_type->answer, "J-shaped"))
	type = JSHAPE;
    else if (!strcmp(par_type->answer, "G-shaped"))
	type = GSHAPE;

    if (!strcmp(par_side->answer, "both"))
	side = BOTH;
    else if (!strcmp(par_side->answer, "left"))
	side = LEFT;
    else if (!strcmp(par_side->answer, "right"))
	side = RIGHT;

    shape = atof(par_shape->answer);
    if (shape < -1. || shape > 1.)
	G_fatal_error(_("Shape modifier must be between -1 and 1"));

    height = atof(par_height->answer);
    if (height > 1 || height < 0)
	G_fatal_error(_("Height modifier must be between 0 and 1"));

    num_points = sscanf(par_points->answer,
			"%lf,%lf,%lf,%lf", &p[0], &p[1], &p[2], &p[3]);

    if (!side && num_points != 4)
	G_fatal_error(_("Wrong number of values: got %d but need 4"),
		      num_points);

    if (side && num_points != 2)
	G_fatal_error(_("Wrong number of values: got %d but need 2"),
		      num_points);

    if (num_points == 2) {
	if (p[0] > p[1])
	    G_fatal_error(_("Point sequence must be: a <= b"));
    }
    else {
	if (p[0] > p[1]
	    || p[1] > p[2]
	    || p[2] > p[3])
	    G_fatal_error(_("Point sequence must be: a <= b; b <= c; c <= d;"));
    }

    /* end of interface */

    mapset = G_find_cell2(input, "");

    if (mapset == NULL)
	G_fatal_error(_("Raster map <%s> not found"), input);

    if ((infd = G_open_cell_old(input, mapset)) < 0)
	G_fatal_error(_("Unable to open raster map <%s>"), input);

    if (G_get_cellhd(input, mapset, &cellhd) < 0)
	G_fatal_error(_("Unable to read file header of <%s>"), input);


    nrows = G_window_rows();
    ncols = G_window_cols();
    raster_type = G_get_raster_map_type(infd);

    if ((outfd = G_open_raster_new(output, FCELL_TYPE)) < 0)
	G_fatal_error(_("Unable to create raster map <%s>"), output);


    in_buf = G_allocate_raster_buf(raster_type);
    out_buf = G_allocate_raster_buf(FCELL_TYPE);

    /* processing */
    for (row = 0; row < nrows; row++) {
	G_percent(row, nrows, 2);
	CELL c;
	FCELL f;
	DCELL d;

	if (G_get_raster_row(infd, in_buf, row, raster_type) < 0) {
	    G_close_cell(infd);
	    G_fatal_error(_("Cannot to read <%s> at row <%d>"), input, row);
	}

	for (col = 0; col < ncols; col++) {

	    switch (raster_type) {

	    case CELL_TYPE:
		c = ((CELL *) in_buf)[col];
		if (G_is_null_value(&c, CELL_TYPE))
		    G_set_f_null_value(&tmp, 1);
		else {
		    if (0 > (tmp = fuzzy((FCELL) c)))
			G_warning
			    ("Cannot determine memebership at row %d, col %d",
			     row, col);
		    ((FCELL *) out_buf)[col] = tmp;
		}
		break;

	    case FCELL_TYPE:
		f = ((FCELL *) in_buf)[col];
		if (G_is_null_value(&f, FCELL_TYPE))
		    G_set_f_null_value(&tmp, 1);
		else {
		    tmp = fuzzy((FCELL) f);
		    if (0 > (tmp = fuzzy((FCELL) f)))
			G_warning
			    ("Cannot determine memebership at row %d, col %d",
			     row, col);
		    ((FCELL *) out_buf)[col] = tmp;
		}
		break;

	    case DCELL_TYPE:
		d = ((DCELL *) in_buf)[col];
		if (G_is_null_value(&d, DCELL_TYPE))
		    G_set_f_null_value(&tmp, 1);
		else {
		    if (0 > (tmp = fuzzy((FCELL) d)))
			G_warning
			    ("Cannot determine memebership at row %d, col %d",
			     row, col);
		    ((FCELL *) out_buf)[col] = tmp;
		}
		break;
	    }

	}
	if (G_put_raster_row(outfd, out_buf, FCELL_TYPE) < 0)
	    G_fatal_error(_("Failed writing raster map <%s>"), output);
    }				/* end for */

    G_free(in_buf);
    G_free(out_buf);

    G_close_cell(infd);
    G_close_cell(outfd);

    G_short_history(output, "raster", &history);
    G_command_history(&history);
    G_write_history(output, &history);

    exit(EXIT_SUCCESS);
}
