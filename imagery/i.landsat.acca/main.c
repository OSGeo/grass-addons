
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
	G_warning(_("Raster map <%s> not found"), raster_name);
	return -1;
    }
    if (G_legal_filename(raster_name) < 0) {
	G_warning(_("<%s> is an illegal file name"), raster_name);
	return -1;
    }
    if ((raster_fd = G_open_cell_old(raster_name, mapset)) < 0) {
	G_warning(_("Unable to open raster map <%s>"), raster_name);
	return -1;
    }
    /* Uncomment to work in full raster map
       if (G_get_cellhd(raster_name, mapset, &cellhd) < 0) {
       G_warning(_("Unable to read header of raster map <%s>"), raster_name);
       return -1;
       }
       if (G_set_window(&cellhd) < 0) {
       G_warning(_("Cannot reset current region"));
       return -1;
       }
     */
    if ((map_type = G_raster_map_type(raster_name, mapset)) != DCELL_TYPE) {
	G_warning(_("Map is not DCELL type (process DN to radiance first)"));
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
    struct Option *input, *output, *hist, *b56c, *b45r;
    struct Flag *shadow, *filter, *sat5, *pass2, *csig;
    char *in_name, *out_name;
    struct Categories cats;
    char title[RECORD_LEN];

    Gfile band[5], out;

    /* initialize GIS environment */
    G_gisinit(argv[0]);

    /* initialize module */
    module = G_define_module();
    module->description =
	_("Landsat TM/ETM+ Automatic Cloud Cover Assessment (ACCA)");

    input = G_define_option();
    input->key = "band_prefix";
    input->type = TYPE_STRING;
    input->required = YES;
    input->gisprompt = "input,cell,raster";
    input->description =
	_("Base name of the landsat band rasters ([band_prefix].[band_number])");

    output = G_define_standard_option(G_OPT_R_OUTPUT);

    b56c = G_define_option();
    b56c->key = "b56composite";
    b56c->type = TYPE_DOUBLE;
    b56c->required = NO;
    b56c->description = _("B56composite (step 6)");
    b56c->answer = "225.";

    b45r = G_define_option();
    b45r->key = "b45ratio";
    b45r->type = TYPE_DOUBLE;
    b45r->required = NO;
    b45r->description = _("B45ratio: Desert detection (step 10)");
    b45r->answer = "1.";

    hist = G_define_option();
    hist->key = "histogram";
    hist->type = TYPE_INTEGER;
    hist->required = NO;
    hist->description =
	_("Number of classes in the cloud temperature histogram");
    hist->answer = "100";

    sat5 = G_define_flag();
    sat5->key = '5';
    sat5->label = _("Data is Landsat-5 TM");
    sat5->description = _("(i.e. thermal band is '.6' not '.61')");

    filter = G_define_flag();
    filter->key = 'f';
    filter->description =
	_("Apply post-processing filter to remove small holes");

    csig = G_define_flag();
    csig->key = 'x';
    csig->description = _("Always use cloud signature (step 14)");

    pass2 = G_define_flag();
    pass2->key = '2';
    pass2->description =
	_("Bypass second-pass processing, and merge warm (not ambiguous) and cold clouds");

    shadow = G_define_flag();
    shadow->key = 's';
    shadow->description = _("Include a category for cloud shadows");

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
	    G_fatal_error(_("Error in map name <%s>!"), band[i].name);
	}
	band[i].rast = G_allocate_raster_buf(DCELL_TYPE);
    }

    out_name = output->answer;

    snprintf(out.name, 127, "%s", out_name);
    if (G_legal_filename(out_name) < 0)
	G_fatal_error(_("<%s> is an illegal file name"), out.name);

    /* --------------------------------------- */
    th_4 = atof(b56c->answer);
    th_7 = atof(b45r->answer);
    acca_algorithm(verbose, &out, band, pass2->answer, shadow->answer,
		   csig->answer);

    if (filter->answer)
	filter_holes(verbose, &out);
    /* --------------------------------------- */

    for (i = BAND2; i <= BAND6; i++) {
	G_free(band[i].rast);
	G_close_cell(band[i].fd);
    }

    /* write out map title and category labels */
    G_init_cats((CELL) 0, "", &cats);
    sprintf(title, "LANDSAT-%s Automatic Cloud Cover Assessment",
	    sat5->answer ? "5 TM" : "7 ETM+");
    G_set_raster_cats_title(title, &cats);

    G_set_cat(IS_SHADOW, "Shadow", &cats);
    G_set_cat(IS_COLD_CLOUD, "Cold cloud", &cats);
    G_set_cat(IS_WARM_CLOUD, "Warm cloud", &cats);

    if (G_write_cats(out.name, &cats) <= 0)
	G_warning(_("Cannot write category file for raster map <%s>"),
		  out.name);
    G_free_cats(&cats);

    /* write out command line opts */
    G_short_history(out.name, "raster", &history);
    G_command_history(&history);
    G_write_history(out.name, &history);

    exit(EXIT_SUCCESS);
}
