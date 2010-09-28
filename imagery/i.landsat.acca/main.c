
/****************************************************************************
 *
 * MODULE:       i.landsat.acca
 *
 * AUTHOR(S):    E. Jorge Tizado - ej.tizado@unileon.es
 *
 * PURPOSE:      Landsat TM/ETM+ Automatic Cloud Cover Assessment
 *
 * COPYRIGHT:    (C) 2008 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *   	    	 License (>=v2). Read the file COPYING that comes with GRASS
 *   	    	 for details.
 *
 *****************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/glocale.h>

#include "local_proto.h"

extern int hist_n;

/*----------------------------------------------*
 * Constant threshold of ACCA algorithm
 *----------------------------------------------*/

extern double th_1;
extern double th_1_b;
extern double th_2[];
extern double th_2_b;
extern double th_3;
extern double th_4;
extern double th_4_b;
extern double th_5;
extern double th_6;
extern double th_7;
extern double th_8;

/*----------------------------------------------*
 *
 * Check a raster name y return fd of open file
 *
 *----------------------------------------------*/
int check_raster(char *raster_name)
{
    struct Cell_head cellhd;
    RASTER_MAP_TYPE map_type;
    int raster_fd;
    char *mapset;

    mapset = G_find_cell2(raster_name, "");
    if (mapset == NULL) {
	G_message("cell file [%s] not found", raster_name);
	return -1;
    }
    if (G_legal_filename(raster_name) < 0) {
	G_message("[%s] is an illegal name", raster_name);
	return -1;
    }
    if ((raster_fd = G_open_cell_old(raster_name, mapset)) < 0) {
	G_message("Cannot open cell file [%s]", raster_name);
	return -1;
    }
    if (G_get_cellhd(raster_name, mapset, &cellhd) < 0) {
	G_message("Cannot read file header of [%s]", raster_name);
	return -1;
    }
    if (G_set_window(&cellhd) < 0) {
	G_message("Unable to set region");
	return -1;
    }
    if ((map_type = G_raster_map_type(raster_name, mapset)) != DCELL_TYPE) {
	G_message("Map is not of DCELL_TYPE");
	return -1;
    }
    return raster_fd;
}

/*----------------------------------------------*
 *
 *      MAIN FUNCTION
 *
 *----------------------------------------------*/
int main(int argc, char *argv[])
{
    struct History history;
    struct GModule *module;

    int i, verbose = 1;
    struct Option *input, *output, *hist;
    struct Flag *shadow, *sat5, *filter, *pass2;
    char *in_name, *out_name;
    double p;

    Gfile band[5], out;

    /* initialize GIS environment */
    G_gisinit(argv[0]);

    /* initialize module */
    module = G_define_module();
    module->description =
	_("Landsat TM/ETM+ Automatic Cloud Cover Assessment (ACCA)");

    input = G_define_option();
    input->key = _("band_prefix");
    input->type = TYPE_STRING;
    input->required = YES;
    input->gisprompt = _("input,cell,raster");
    input->description =
	_("Base name of the landsat band rasters ([band_prefix].[band_number])");

    output = G_define_option();
    output->key = _("output");
    output->type = TYPE_STRING;
    output->required = YES;
    output->gisprompt = _("output,cell,raster");
    output->description = _("Output file name");

    hist = G_define_option();
    hist->key = _("histogram");
    hist->type = TYPE_INTEGER;
    hist->required = NO;
    hist->gisprompt = _("input,integer");
    hist->description =
	_("Number of classes in the cloud temperature histogram");
    hist->answer = "100";

    sat5 = G_define_flag();
    sat5->key = '5';
    sat5->description = _("Landsat-5 TM");
    sat5->answer = 0;

    filter = G_define_flag();
    filter->key = 'f';
    filter->description = _("Use final filter holes");
    filter->answer = 0;

    pass2 = G_define_flag();
    pass2->key = '2';
    pass2->description = _("With pass two processing");
    pass2->answer = 0;

    shadow = G_define_flag();
    shadow->key = 's';
    shadow->description = _("Add class for cloud shadows");
    shadow->answer = 0;

    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    /* stores OPTIONS and FLAGS to variables */

    hist_n = atoi(hist->answer);
    if (hist_n < 10)
	hist_n = 10;

    in_name = input->answer;

    for (i = BAND2; i <= BAND6; i++) {
	snprintf(band[i].name, 127, "%s.%d%c", in_name, i + 2,
		 (i == BAND6 && !sat5->answer ? '1' : '\0'));
	if ((band[i].fd = check_raster(band[i].name)) < 0) {
	    G_fatal_error(_("Error in filename [%s]!"), band[i].name);
	}
	band[i].rast = G_allocate_raster_buf(DCELL_TYPE);
    }

    out_name = output->answer;

    snprintf(out.name, 127, "%s", out_name);
    if (G_legal_filename(out_name) < 0)
	G_fatal_error(_("[%s] is an illegal name"), out.name);

    /* --------------------------------------- */

    //     if( sat5 -> answer )
    //     {
    //         th_4 = 205.;
    //     }
    //     acca_test(verbose, &out, band);
    acca_algorithm(verbose, &out, band, pass2->answer, shadow->answer);

    if (filter->answer)
	filter_holes(verbose, &out);
    /* --------------------------------------- */

    for (i = BAND2; i <= BAND6; i++) {
	G_free(band[i].rast);
	G_close_cell(band[i].fd);
    }

    //      struct Categories cats;
    //      G_read_raster_cats(out.name, char *mapset, cats)
    //      G_write_raster_cats(out.name, &cats);

    G_short_history(out.name, "raster", &history);
    G_command_history(&history);
    G_write_history(out.name, &history);

    exit(EXIT_SUCCESS);
}
