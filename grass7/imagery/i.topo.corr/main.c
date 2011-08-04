
/****************************************************************************
 *
 * MODULE:       i.topo.corr
 *
 * AUTHOR(S):    E. Jorge Tizado - ej.tizado@unileon.es
 *
 * PURPOSE:      Topographic corrections
 *
 * COPYRIGHT:    (C) 2002, 2005, 2008 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>

#include "local_proto.h"

int main(int argc, char *argv[])
{
    struct History history;
    struct GModule *module;
    struct Cell_head hd_band, hd_dem, window;

    char bufname[128];		/* TODO: use GNAME_MAX? */

    int i;
    struct Option *base, *output, *input, *zeni, *azim, *metho;
    struct Flag *ilum;

    Gfile dem, out, band;
    double zenith, azimuth;
    int method = COSINE;

    /* initialize GIS environment */
    G_gisinit(argv[0]);

    /* initialize module */
    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("terrain"));
    G_add_keyword(_("topographic correction"));
    module->description = _("Topografic correction of reflectance");

    /* It defines the different parameters */

    input = G_define_option();
    input->key = _("input");
    input->type = TYPE_STRING;
    input->required = NO;
    input->multiple = YES;
    input->gisprompt = _("input,cell,raster");
    input->description =
	_("List of reflectance band maps to correct topographically");

    output = G_define_option();
    output->key = _("output");
    output->type = TYPE_STRING;
    output->required = YES;
    output->gisprompt = _("output,cell,raster");
    output->description =
	_("File name of output (flag -i) or prefix of output files");

    base = G_define_option();
    base->key = _("basemap");
    base->type = TYPE_STRING;
    base->required = YES;
    base->gisprompt = _("base,cell,raster");
    base->description = _("Base map for analysis (elevation or ilumination)");

    zeni = G_define_option();
    zeni->key = _("zenith");
    zeni->type = TYPE_DOUBLE;
    zeni->required = YES;
    zeni->gisprompt = _("zenith,float");
    zeni->description = _("Solar zenith in degrees");

    azim = G_define_option();
    azim->key = _("azimuth");
    azim->type = TYPE_DOUBLE;
    azim->required = NO;
    azim->gisprompt = _("azimuth,float");
    azim->description = _("Solar azimuth in degrees (only if flag -i)");

    metho = G_define_option();
    metho->key = _("method");
    metho->type = TYPE_STRING;
    metho->required = NO;
    metho->options = "cosine,minnaert,c-factor,percent";
    metho->gisprompt = _("topographic correction method");
    metho->description = _("Topographic correction method");
    metho->answer = "c-factor";

    ilum = G_define_flag();
    ilum->key = 'i';
    ilum->description = _("To output sun ilumination terrain model");
    ilum->answer = 0;

    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    if (ilum->answer && azim->answer == NULL)
	G_fatal_error(_("Solar azimuth is necessary to calculate ilumination terrain model"));

    if (!ilum->answer && input->answer == NULL)
	G_fatal_error
	    (_("Reflectance maps are necessary to make topographic correction"));

    zenith = atof(zeni->answer);

    /* Evaluate only cos_i raster file */
    /* i.topo.corr -i out=cosi.on07 base=SRTM_v2 zenith=33.3631 azimuth=59.8897 */
    if (ilum->answer) {
	azimuth = atof(azim->answer);
	/* Warning: make buffers and output after set window */
	dem.fd = Rast_open_old(base->answer, "");
	/* Set window to DEM file */
	Rast_get_window(&window);
	Rast_get_cellhd(dem.name, "", &hd_dem);
	Rast_align_window(&window, &hd_dem);
	Rast_set_window(&window);
	/* Open and buffer of the output file */
	out.fd = Rast_open_new(output->answer, DCELL_TYPE);
	out.rast = Rast_allocate_buf(out.type);
	/* Open and buffer of the elevation file */
	if (dem.type == CELL_TYPE) {
	    dem.rast = Rast_allocate_buf(CELL_TYPE);
	    eval_c_cosi(&out, &dem, zenith, azimuth);
	}
	else if (dem.type == FCELL_TYPE) {
	    dem.rast = Rast_allocate_buf(FCELL_TYPE);
	    eval_f_cosi(&out, &dem, zenith, azimuth);
	}
	else if (dem.type == DCELL_TYPE) {
	    dem.rast = Rast_allocate_buf(DCELL_TYPE);
	    eval_d_cosi(&out, &dem, zenith, azimuth);
	}
	else {
	    G_fatal_error(_("Elevation file of unknown type"));
	}
	/* Close files, buffers, and write history */
	G_free(dem.rast);
	Rast_close(dem.fd);
	G_free(out.rast);
	Rast_close(out.fd);
	Rast_short_history(out.name, "raster", &history);
	Rast_command_history(&history);
	Rast_write_history(out.name, &history);
    }
    /* Evaluate topographic correction for all bands */
    /* i.topo.corr input=on07.toar.1 out=tcor base=cosi.on07 zenith=33.3631 method=c-factor */
    else {
	/*              if (G_strcasecmp(metho->answer, "cosine") == 0)        method = COSINE;
	 *               else if (G_strcasecmp(metho->answer, "percent") == 0)  method = PERCENT;
	 *               else if (G_strcasecmp(metho->answer, "minnaert") == 0) method = MINNAERT;
	 *               else if (G_strcasecmp(metho->answer, "c-factor") == 0) method = C_CORRECT;
	 *               else G_fatal_error(_("Invalid method: %s"), metho->answer);
	 */

	if (metho->answer[1] == 'o')
	    method = COSINE;
	else if (metho->answer[1] == 'e')
	    method = PERCENT;
	else if (metho->answer[1] == 'i')
	    method = MINNAERT;
	else if (metho->answer[1] == '-')
	    method = C_CORRECT;
	else
	    G_fatal_error(_("Invalid method: %s"), metho->answer);

	dem.fd = Rast_open_old(base->answer, "");
	if (dem.type == CELL_TYPE)
	    G_fatal_error(_("Illumination model is of CELL type"));

	for (i = 0; input->answers[i] != NULL; i++) {
	    G_message("\nBand %s: ", input->answers[i]);
	    /* Abre fichero de bandas y el de salida */
	    band.fd = Rast_open_old(input->answers[i], "");
	    if (band.type != DCELL_TYPE) {
		G_warning(_("Reflectance of <%s> is not of DCELL type - ignored."),
			  input->answers[i]);
		Rast_close(band.fd);
		continue;
	    }
	    Rast_get_cellhd(band.name, band.mapset, &hd_band);
	    Rast_set_window(&hd_band);	/* Antes de out_open y allocate para mismo tamaño */
	    /* ----- */
	    snprintf(bufname, 127, "%s.%s", output->answer,
		     input->answers[i]);
	    out.fd = Rast_open_new(bufname, DCELL_TYPE);
	    out.rast = Rast_allocate_buf(out.type);
	    band.rast = Rast_allocate_buf(band.type);
	    dem.rast = Rast_allocate_buf(dem.type);
	    /* ----- */
	    eval_tcor(method, &out, &dem, &band, zenith);
	    /* ----- */
	    G_free(dem.rast);
	    G_free(band.rast);
	    Rast_close(band.fd);
	    G_free(out.rast);
	    Rast_close(out.fd);
	    Rast_short_history(out.name, "raster", &history);
	    Rast_command_history(&history);
	    Rast_write_history(out.name, &history);

	    char command[300];

	    /* TODO: better avoid system() */
	    sprintf(command, "r.colors map=%s color=grey", out.name);
	    system(command);
	}
	Rast_close(dem.fd);
    }

    exit(EXIT_SUCCESS);
}
