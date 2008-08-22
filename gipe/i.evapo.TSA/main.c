
/*****************************************************************************
*
* MODULE:	i.evapo.TSA
* AUTHOR:	Yann Chemin yann.chemin@gmail.com 
*
* PURPOSE:	To estimate the daily actual evapotranspiration by means
*		of of a Two-Source Algorithm from Chen et al. (2005).
*		IJRS, 26(8):1755-1762
*
* COPYRIGHT:	(C) 2007-2008 by the GRASS Development Team
*
*		This program is free software under the GNU General Public
*		Licence (>=2). Read the file COPYING that cames with GRASS
*		for details.
*
***************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>


/*protos Net radiation */
double rn_g(double rnet, double fv);

double rn_v(double rnet, double fv);

/*protos temperature fractions */
double tempk_g(double tempk, double tempk_v, double fv);

double tempk_v(double tempk, double fv);

/*protos soil heat flux */
double g_0g(double rnet);

double g_0v(double bbalb, double ndvi, double tempk_v, double rnet);

/*protos sensible heat flux */
double h_g(double tempk_g, double tempk_v, double tempk_a, double r_g,
	   double r_v, double r_a);
double h_v(double tempk_g, double tempk_v, double tempk_a, double r_g,
	   double r_v, double r_a);
/*protos necessary for sensible heat flux calculations */
double ra(double d, double z0, double h, double z, double u_z, double tempk_a,
	  double tempk_v);
double rg(double d, double z0, double z0s, double h, double z, double w,
	  double u_z, double tempk_a, double tempk_v);
double rv(double d, double z0, double h, double z, double w, double u_z,
	  double tempk_a, double tempk_v);
/*proto ET */
double daily_et(double et_instantaneous, double time, double sunshine_hours);


int main(int argc, char *argv[])
{
    /* buffer for input-output rasters */
    void *inrast_FV, *inrast_TEMPK, *inrast_TEMPKA, *inrast_ALB, *inrast_NDVI,
	*inrast_RNET;
    void *inrast_UZ, *inrast_DISP, *inrast_Z0, *inrast_HV;

    void *inrast_Z0S, *inrast_W, *inrast_TIME, *inrast_SUNH;

    DCELL *outrast;

    /* pointers to input-output raster files */
    int infd_FV, infd_TEMPK, infd_TEMPKA, infd_ALB, infd_NDVI, infd_RNET;

    int infd_UZ, infd_DISP, infd_Z0, infd_HV;

    int infd_Z0S, infd_W, infd_TIME, infd_SUNH, outfd;

    /* mapsets for input raster files */
    char *mapset_FV, *mapset_TEMPK, *mapset_TEMPKA, *mapset_ALB, *mapset_NDVI,
	*mapset_RNET;
    char *mapset_UZ, *mapset_DISP, *mapset_Z0, *mapset_HV;

    char *mapset_Z0S, *mapset_W, *mapset_TIME, *mapset_SUNH;

    /* names of input-output raster files */
    char *RNET, *FV, *TEMPK, *TEMPKA, *ALB, *NDVI;

    char *UZ, *DISP, *Z0, *HV, *W, *TIME, *SUNH, *Z0S, *ETa;

    /* input-output cell values */
    DCELL d_fv, d_tempk, d_tempka, d_alb, d_ndvi, d_rnet;

    DCELL d_uz, d_z, d_disp, d_z0, d_hv, d_w, d_daily_et;

    DCELL d_rn_g, d_rn_v;

    DCELL d_tempk_g, d_tempk_v;

    DCELL d_g0_g, d_g0_v;

    DCELL d_ra;

    DCELL d_z0s;

    DCELL d_rg, d_rv;

    DCELL d_h_g, d_h_v;

    DCELL d_le_inst_g, d_le_inst_v, d_le_inst;

    DCELL d_time, d_sunh;

    /* region informations and handler */
    struct Cell_head cellhd;

    int nrows, ncols;

    int row, col;

    /* parser stuctures definition */
    struct GModule *module;

    struct Option *input_RNET, *input_FV, *input_TEMPK, *input_TEMPKA,
	*input_ALB, *input_NDVI;
    struct Option *input_UZ, *input_Z, *input_DISP, *input_Z0, *input_HV;

    struct Option *input_Z0S, *input_W, *input_TIME, *input_SUNH, *output;

    struct Flag *zero;

    struct Colors color;

    struct History history;

    RASTER_MAP_TYPE data_type_output = DCELL_TYPE;

    RASTER_MAP_TYPE data_type_fv;

    RASTER_MAP_TYPE data_type_tempk;

    RASTER_MAP_TYPE data_type_tempka;

    RASTER_MAP_TYPE data_type_alb;

    RASTER_MAP_TYPE data_type_ndvi;

    RASTER_MAP_TYPE data_type_rnet;

    RASTER_MAP_TYPE data_type_uz;

    RASTER_MAP_TYPE data_type_disp;

    RASTER_MAP_TYPE data_type_z0;

    RASTER_MAP_TYPE data_type_hv;

    RASTER_MAP_TYPE data_type_w;

    RASTER_MAP_TYPE data_type_time;

    RASTER_MAP_TYPE data_type_sunh;

    RASTER_MAP_TYPE data_type_z0s;

    RASTER_MAP_TYPE data_type_eta;

    /* Initialize the GIS calls */
    G_gisinit(argv[0]);

    module = G_define_module();
    module->description =
	_("Actual Evapotranspiration Calculation "
	  "Two-Source Algorithm formulation, after Chen et al., 2005.");

    /* Define different options */
    input_RNET = G_define_standard_option(G_OPT_R_INPUT);
    input_RNET->key = "RNET";
    input_RNET->key_desc = "[W/m2]";
    input_RNET->description = _("Name of Net Radiation raster layer");

    input_FV = G_define_standard_option(G_OPT_R_INPUT);
    input_FV->key = "FV";
    input_FV->key_desc = "[-]";
    input_FV->description = _("Name of Vegetation Fraction raster layer");

    input_TEMPK = G_define_standard_option(G_OPT_R_INPUT);
    input_TEMPK->key = "TEMPK";
    input_TEMPK->key_desc = "[K]";
    input_TEMPK->description = _("Name of surface temperature raster layer");

    input_TEMPKA = G_define_standard_option(G_OPT_R_INPUT);
    input_TEMPKA->key = "TEMPKA";
    input_TEMPKA->key_desc = "[K]";
    input_TEMPKA->description = _("Name of air temperature raster layer");

    input_ALB = G_define_standard_option(G_OPT_R_INPUT);
    input_ALB->key = "ALB";
    input_ALB->key_desc = "[-]";
    input_ALB->description = _("Name of Albedo raster layer");

    input_NDVI = G_define_standard_option(G_OPT_R_INPUT);
    input_NDVI->key = "NDVI";
    input_NDVI->key_desc = "[-]";
    input_NDVI->description = _("Name of NDVI raster layer");

    input_UZ = G_define_standard_option(G_OPT_R_INPUT);
    input_UZ->key = "UZ";
    input_UZ->key_desc = "[m/s]";
    input_UZ->description =
	_("Name of wind speed (at z ref. height) raster layer");

    input_Z = G_define_option();
    input_Z->key = "Z";
    input_Z->key_desc = "[m]";
    input_Z->type = TYPE_DOUBLE;
    input_Z->required = YES;
    input_Z->answer = "2.0";
    input_Z->gisprompt = "value,parameter";
    input_Z->description = _("Value of reference height for UZ");

    input_DISP = G_define_standard_option(G_OPT_R_INPUT);
    input_DISP->key = "DISP";
    input_DISP->key_desc = "[m]";
    input_DISP->required = NO;
    input_DISP->description = _("Name of displacement height raster layer");

    input_Z0 = G_define_standard_option(G_OPT_R_INPUT);
    input_Z0->key = "Z0";
    input_Z0->key_desc = "[m]";
    input_Z0->required = NO;
    input_Z0->description =
	_("Name of surface roughness length raster layer");

    input_HV = G_define_standard_option(G_OPT_R_INPUT);
    input_HV->key = "HV";
    input_HV->key_desc = "[m]";
    input_HV->required = NO;
    input_HV->description =
	_("Name of vegetation height raster layer (one out of DISP, Z0 or HV should be given!)");

    input_Z0S = G_define_standard_option(G_OPT_R_INPUT);
    input_Z0S->key = "Z0S";
    input_Z0S->key_desc = "[m]";
    input_Z0S->description =
	_("Name of bare soil surface roughness length raster layer");

    input_W = G_define_standard_option(G_OPT_R_INPUT);
    input_W->key = "W";
    input_W->key_desc = "[g]";
    input_W->description = _("Name of leaf weight raster layer");

    input_TIME = G_define_standard_option(G_OPT_R_INPUT);
    input_TIME->key = "TIME";
    input_TIME->key_desc = "[HH.HH]";
    input_TIME->description =
	_("Name of local Time at satellite overpass raster layer");

    input_SUNH = G_define_standard_option(G_OPT_R_INPUT);
    input_SUNH->key = "SUNH";
    input_SUNH->key_desc = "[HH.HH]";
    input_SUNH->description = _("Name of Sunshine hours raster layer");

    output = G_define_standard_option(G_OPT_R_OUTPUT);
    output->key_desc = "[mm/d]";
    output->description = _("Name of output Actual Evapotranspiration layer");

    /* Define the different flags */
    zero = G_define_flag();
    zero->key = 'z';
    zero->description = _("set negative ETa to zero");

    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    /* get entered parameters */
    RNET = input_RNET->answer;
    FV = input_FV->answer;
    TEMPK = input_TEMPK->answer;
    TEMPKA = input_TEMPKA->answer;
    ALB = input_ALB->answer;
    NDVI = input_NDVI->answer;
    UZ = input_UZ->answer;
    d_z = atof(input_Z->answer);
    DISP = input_DISP->answer;
    Z0 = input_Z0->answer;
    HV = input_HV->answer;
    Z0S = input_Z0S->answer;
    W = input_W->answer;
    TIME = input_TIME->answer;
    SUNH = input_SUNH->answer;

    ETa = output->answer;

    /* find maps in mapset */
    mapset_RNET = G_find_cell2(RNET, "");
    if (mapset_RNET == NULL)
	G_fatal_error(_("cell file [%s] not found"), RNET);
    mapset_FV = G_find_cell2(FV, "");
    if (mapset_FV == NULL)
	G_fatal_error(_("cell file [%s] not found"), FV);
    mapset_TEMPK = G_find_cell2(TEMPK, "");
    if (mapset_TEMPK == NULL)
	G_fatal_error(_("cell file [%s] not found"), TEMPK);
    mapset_TEMPKA = G_find_cell2(TEMPKA, "");
    if (mapset_TEMPKA == NULL)
	G_fatal_error(_("cell file [%s] not found"), TEMPKA);
    mapset_ALB = G_find_cell2(ALB, "");
    if (mapset_ALB == NULL)
	G_fatal_error(_("cell file [%s] not found"), ALB);
    mapset_NDVI = G_find_cell2(NDVI, "");
    if (mapset_NDVI == NULL)
	G_fatal_error(_("cell file [%s] not found"), NDVI);
    mapset_UZ = G_find_cell2(UZ, "");
    if (mapset_UZ == NULL)
	G_fatal_error(_("cell file [%s] not found"), UZ);
    if (DISP != NULL) {
	mapset_DISP = G_find_cell2(DISP, "");
	if (mapset_DISP == NULL)
	    G_fatal_error(_("cell file [%s] not found"), DISP);
    }
    if (Z0 != NULL) {
	mapset_Z0 = G_find_cell2(Z0, "");
	if (Z0 && mapset_Z0 == NULL)
	    G_fatal_error(_("cell file [%s] not found"), Z0);
    }
    if (HV != NULL) {
	mapset_HV = G_find_cell2(HV, "");
	if (HV && mapset_HV == NULL)
	    G_fatal_error(_("cell file [%s] not found"), HV);
    }
    mapset_Z0S = G_find_cell2(Z0S, "");
    if (mapset_Z0S == NULL)
	G_fatal_error(_("cell file [%s] not found"), Z0S);
    mapset_W = G_find_cell2(W, "");
    if (mapset_W == NULL)
	G_fatal_error(_("cell file [%s] not found"), W);
    mapset_TIME = G_find_cell2(TIME, "");
    if (mapset_TIME == NULL)
	G_fatal_error(_("cell file [%s] not found"), TIME);
    mapset_SUNH = G_find_cell2(SUNH, "");
    if (mapset_SUNH == NULL)
	G_fatal_error(_("cell file [%s] not found"), SUNH);

    /* check legal output name */
    if (G_legal_filename(ETa) < 0)
	G_fatal_error(_("[%s] is an illegal name"), ETa);

    /* determine the input map type (CELL/FCELL/DCELL) */
    data_type_rnet = G_raster_map_type(RNET, mapset_RNET);
    data_type_fv = G_raster_map_type(FV, mapset_FV);
    data_type_tempk = G_raster_map_type(TEMPK, mapset_TEMPK);
    data_type_tempka = G_raster_map_type(TEMPKA, mapset_TEMPKA);
    data_type_alb = G_raster_map_type(ALB, mapset_ALB);
    data_type_ndvi = G_raster_map_type(NDVI, mapset_NDVI);
    data_type_uz = G_raster_map_type(UZ, mapset_UZ);
    if (DISP != NULL) {
	data_type_disp = G_raster_map_type(DISP, mapset_DISP);
    }
    if (Z0 != NULL) {
	data_type_z0 = G_raster_map_type(Z0, mapset_Z0);
    }
    if (HV != NULL) {
	data_type_hv = G_raster_map_type(HV, mapset_HV);
    }
    data_type_z0s = G_raster_map_type(Z0S, mapset_Z0S);
    data_type_w = G_raster_map_type(W, mapset_W);
    data_type_time = G_raster_map_type(TIME, mapset_TIME);
    data_type_sunh = G_raster_map_type(SUNH, mapset_SUNH);

    /* open pointers to input raster files */
    if ((infd_RNET = G_open_cell_old(RNET, mapset_RNET)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), RNET);
    if ((infd_FV = G_open_cell_old(FV, mapset_FV)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), FV);
    if ((infd_TEMPK = G_open_cell_old(TEMPK, mapset_TEMPK)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), TEMPK);
    if ((infd_TEMPKA = G_open_cell_old(TEMPKA, mapset_TEMPKA)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), TEMPKA);
    if ((infd_ALB = G_open_cell_old(ALB, mapset_ALB)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), ALB);
    if ((infd_NDVI = G_open_cell_old(NDVI, mapset_NDVI)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), NDVI);
    if ((infd_UZ = G_open_cell_old(UZ, mapset_UZ)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), UZ);
    if ((DISP != NULL) &&
	(infd_DISP = G_open_cell_old(DISP, mapset_DISP)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), DISP);
    if ((Z0 != NULL) && (infd_Z0 = G_open_cell_old(Z0, mapset_Z0)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), Z0);
    if ((HV != NULL) && (infd_HV = G_open_cell_old(HV, mapset_HV)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), HV);
    if ((infd_Z0S = G_open_cell_old(Z0S, mapset_Z0S)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), SUNH);
    if ((infd_W = G_open_cell_old(W, mapset_W)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), W);
    if ((infd_TIME = G_open_cell_old(TIME, mapset_TIME)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), TIME);
    if ((infd_SUNH = G_open_cell_old(SUNH, mapset_SUNH)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), SUNH);

    /* read headers of raster files */
    if (G_get_cellhd(RNET, mapset_RNET, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), RNET);
    if (G_get_cellhd(FV, mapset_FV, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), FV);
    if (G_get_cellhd(TEMPK, mapset_TEMPK, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), TEMPK);
    if (G_get_cellhd(TEMPKA, mapset_TEMPKA, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), TEMPKA);
    if (G_get_cellhd(ALB, mapset_ALB, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), ALB);
    if (G_get_cellhd(NDVI, mapset_NDVI, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), NDVI);
    if (G_get_cellhd(UZ, mapset_UZ, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), UZ);
    if ((DISP != NULL) && G_get_cellhd(DISP, mapset_DISP, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), DISP);
    if ((Z0 != NULL) && G_get_cellhd(Z0, mapset_Z0, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), Z0);
    if ((HV != NULL) && G_get_cellhd(HV, mapset_HV, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), HV);
    if (G_get_cellhd(Z0S, mapset_Z0S, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), Z0S);
    if (G_get_cellhd(W, mapset_W, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), W);
    if (G_get_cellhd(TIME, mapset_TIME, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), TIME);
    if (G_get_cellhd(SUNH, mapset_SUNH, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), SUNH);

    /* Allocate input buffer */
    inrast_RNET = G_allocate_raster_buf(data_type_rnet);
    inrast_FV = G_allocate_raster_buf(data_type_fv);
    inrast_TEMPK = G_allocate_raster_buf(data_type_tempk);
    inrast_TEMPKA = G_allocate_raster_buf(data_type_tempka);
    inrast_ALB = G_allocate_raster_buf(data_type_alb);
    inrast_NDVI = G_allocate_raster_buf(data_type_ndvi);
    inrast_UZ = G_allocate_raster_buf(data_type_uz);
    if (DISP != NULL) {
	inrast_DISP = G_allocate_raster_buf(data_type_disp);
    }
    if (Z0 != NULL) {
	inrast_Z0 = G_allocate_raster_buf(data_type_z0);
    }
    if (HV != NULL) {
	inrast_HV = G_allocate_raster_buf(data_type_hv);
    }
    inrast_Z0S = G_allocate_raster_buf(data_type_z0s);
    inrast_W = G_allocate_raster_buf(data_type_w);
    inrast_TIME = G_allocate_raster_buf(data_type_time);
    inrast_SUNH = G_allocate_raster_buf(data_type_sunh);

    /* get rows and columns number of the current region */
    nrows = G_window_rows();
    ncols = G_window_cols();

    /* allocate output buffer */
    outrast = G_allocate_raster_buf(data_type_output);

    /* open pointers to output raster files */
    if ((outfd = G_open_raster_new(ETa, data_type_output)) < 0)
	G_fatal_error(_("Could not open <%s>"), ETa);


    /* start the loop through cells */
    for (row = 0; row < nrows; row++) {
	G_percent(row, nrows, 2);

	/* read input raster row into line buffer */
	if (G_get_raster_row(infd_RNET, inrast_RNET, row, data_type_rnet) < 0)
	    G_fatal_error(_("Could not read from <%s>"), RNET);
	if (G_get_raster_row(infd_FV, inrast_FV, row, data_type_fv) < 0)
	    G_fatal_error(_("Could not read from <%s>"), FV);
	if (G_get_raster_row(infd_TEMPK, inrast_TEMPK, row, data_type_tempk) <
	    0)
	    G_fatal_error(_("Could not read from <%s>"), TEMPK);
	if (G_get_raster_row
	    (infd_TEMPKA, inrast_TEMPKA, row, data_type_tempka) < 0)
	    G_fatal_error(_("Could not read from <%s>"), TEMPKA);
	if (G_get_raster_row(infd_ALB, inrast_ALB, row, data_type_alb) < 0)
	    G_fatal_error(_("Could not read from <%s>"), ALB);
	if (G_get_raster_row(infd_NDVI, inrast_NDVI, row, data_type_ndvi) < 0)
	    G_fatal_error(_("Could not read from <%s>"), NDVI);
	if (G_get_raster_row(infd_UZ, inrast_UZ, row, data_type_uz) < 0)
	    G_fatal_error(_("Could not read from <%s>"), UZ);
	if ((DISP != NULL) &&
	    G_get_raster_row(infd_DISP, inrast_DISP, row, data_type_disp) < 0)
	    G_fatal_error(_("Could not read from <%s>"), DISP);
	if ((Z0 != NULL) &&
	    G_get_raster_row(infd_Z0, inrast_Z0, row, data_type_z0) < 0)
	    G_fatal_error(_("Could not read from <%s>"), Z0);
	if ((HV != NULL) &&
	    G_get_raster_row(infd_HV, inrast_HV, row, data_type_hv) < 0)
	    G_fatal_error(_("Could not read from <%s>"), HV);
	if (G_get_raster_row(infd_Z0S, inrast_Z0S, row, data_type_z0s) < 0)
	    G_fatal_error(_("Could not read from <%s>"), Z0S);
	if (G_get_raster_row(infd_W, inrast_W, row, data_type_w) < 0)
	    G_fatal_error(_("Could not read from <%s>"), W);
	if (G_get_raster_row(infd_TIME, inrast_TIME, row, data_type_time) < 0)
	    G_fatal_error(_("Could not read from <%s>"), TIME);
	if (G_get_raster_row(infd_SUNH, inrast_SUNH, row, data_type_sunh) < 0)
	    G_fatal_error(_("Could not read from <%s>"), SUNH);

	for (col = 0; col < ncols; col++) {
	    /* read current cell from line buffer */
	    switch (data_type_rnet) {
	    case CELL_TYPE:
		d_rnet = (double)((CELL *) inrast_RNET)[col];
		break;
	    case FCELL_TYPE:
		d_rnet = (double)((FCELL *) inrast_RNET)[col];
		break;
	    case DCELL_TYPE:
		d_rnet = ((DCELL *) inrast_RNET)[col];
		break;
	    }
	    switch (data_type_fv) {
	    case CELL_TYPE:
		d_fv = (double)((CELL *) inrast_FV)[col];
		break;
	    case FCELL_TYPE:
		d_fv = (double)((FCELL *) inrast_FV)[col];
		break;
	    case DCELL_TYPE:
		d_fv = ((DCELL *) inrast_FV)[col];
		break;
	    }
	    switch (data_type_tempk) {
	    case CELL_TYPE:
		d_tempk = (double)((CELL *) inrast_TEMPK)[col];
		break;
	    case FCELL_TYPE:
		d_tempk = (double)((FCELL *) inrast_TEMPK)[col];
		break;
	    case DCELL_TYPE:
		d_tempk = ((DCELL *) inrast_TEMPK)[col];
		break;
	    }
	    switch (data_type_tempka) {
	    case CELL_TYPE:
		d_tempka = (double)((CELL *) inrast_TEMPKA)[col];
		break;
	    case FCELL_TYPE:
		d_tempka = (double)((FCELL *) inrast_TEMPKA)[col];
		break;
	    case DCELL_TYPE:
		d_tempka = ((DCELL *) inrast_TEMPKA)[col];
		break;
	    }
	    switch (data_type_alb) {
	    case CELL_TYPE:
		d_alb = (double)((CELL *) inrast_ALB)[col];
		break;
	    case FCELL_TYPE:
		d_alb = (double)((FCELL *) inrast_ALB)[col];
		break;
	    case DCELL_TYPE:
		d_alb = ((DCELL *) inrast_ALB)[col];
		break;
	    }
	    switch (data_type_ndvi) {
	    case CELL_TYPE:
		d_ndvi = (double)((CELL *) inrast_NDVI)[col];
		break;
	    case FCELL_TYPE:
		d_ndvi = (double)((FCELL *) inrast_NDVI)[col];
		break;
	    case DCELL_TYPE:
		d_ndvi = ((DCELL *) inrast_NDVI)[col];
		break;
	    }
	    switch (data_type_uz) {
	    case CELL_TYPE:
		d_uz = (double)((CELL *) inrast_UZ)[col];
		break;
	    case FCELL_TYPE:
		d_uz = (double)((FCELL *) inrast_UZ)[col];
		break;
	    case DCELL_TYPE:
		d_uz = ((DCELL *) inrast_UZ)[col];
		break;
	    }
	    if (DISP != NULL) {
		switch (data_type_tempk) {
		case CELL_TYPE:
		    d_disp = (double)((CELL *) inrast_DISP)[col];
		    break;
		case FCELL_TYPE:
		    d_disp = (double)((FCELL *) inrast_DISP)[col];
		    break;
		case DCELL_TYPE:
		    d_disp = ((DCELL *) inrast_DISP)[col];
		    break;
		}
	    }
	    else {
		d_disp = -10.0;	/*negative, see inside functions */
	    }
	    if (Z0 != NULL) {
		switch (data_type_z0) {
		case CELL_TYPE:
		    d_z0 = (double)((CELL *) inrast_Z0)[col];
		    break;
		case FCELL_TYPE:
		    d_z0 = (double)((FCELL *) inrast_Z0)[col];
		    break;
		case DCELL_TYPE:
		    d_z0 = ((DCELL *) inrast_Z0)[col];
		    break;
		}
	    }
	    else {
		d_z0 = -10.0;	/*negative, see inside functions */
	    }
	    if (HV != NULL) {
		switch (data_type_hv) {
		case CELL_TYPE:
		    d_hv = (double)((CELL *) inrast_HV)[col];
		    break;
		case FCELL_TYPE:
		    d_hv = (double)((FCELL *) inrast_HV)[col];
		    break;
		case DCELL_TYPE:
		    d_hv = ((DCELL *) inrast_HV)[col];
		    break;
		}
	    }
	    else {
		d_hv = -10.0;	/*negative, see inside functions */
	    }
	    switch (data_type_z0s) {
	    case CELL_TYPE:
		d_z0s = (double)((CELL *) inrast_Z0S)[col];
		break;
	    case FCELL_TYPE:
		d_z0s = (double)((FCELL *) inrast_Z0S)[col];
		break;
	    case DCELL_TYPE:
		d_z0s = ((DCELL *) inrast_Z0S)[col];
		break;
	    }
	    switch (data_type_w) {
	    case CELL_TYPE:
		d_w = (double)((CELL *) inrast_W)[col];
		break;
	    case FCELL_TYPE:
		d_w = (double)((FCELL *) inrast_W)[col];
		break;
	    case DCELL_TYPE:
		d_w = ((DCELL *) inrast_W)[col];
		break;
	    }
	    switch (data_type_time) {
	    case CELL_TYPE:
		d_time = (double)((CELL *) inrast_TIME)[col];
		break;
	    case FCELL_TYPE:
		d_time = (double)((FCELL *) inrast_TIME)[col];
		break;
	    case DCELL_TYPE:
		d_time = ((DCELL *) inrast_TIME)[col];
		break;
	    }
	    switch (data_type_sunh) {
	    case CELL_TYPE:
		d_sunh = (double)((CELL *) inrast_SUNH)[col];
		break;
	    case FCELL_TYPE:
		d_sunh = (double)((FCELL *) inrast_SUNH)[col];
		break;
	    case DCELL_TYPE:
		d_sunh = ((DCELL *) inrast_SUNH)[col];
		break;
	    }

	    /*Calculate Net radiation fractions */
	    d_rn_g = rn_g(d_rnet, d_fv);
	    d_rn_v = rn_v(d_rnet, d_fv);

	    /*Calculate temperature fractions */
	    d_tempk_v = tempk_v(d_tempk, d_fv);
	    d_tempk_g = tempk_g(d_tempk, d_tempk_v, d_fv);

	    /*Calculate soil heat flux fractions */
	    d_g0_g = g_0g(d_rnet);
	    d_g0_v = g_0v(d_alb, d_ndvi, d_tempk_v, d_rnet);

	    /*Data necessary for sensible heat flux calculations */
	    if (d_disp < 0.0 && d_z0 < 0.0 && d_hv < 0.0) {
		G_fatal_error(_("DISP, Z0 and HV are all negative, cannot continue, bailing out... Check your optional input files again"));
	    }
	    else {
		d_ra = ra(d_disp, d_z0, d_hv, d_z, d_uz, d_tempka, d_tempk_v);
		d_rg =
		    rg(d_disp, d_z0, d_z0s, d_hv, d_z, d_w, d_uz, d_tempka,
		       d_tempk_v);
		d_rv =
		    rv(d_disp, d_z0, d_hv, d_z, d_w, d_uz, d_tempka,
		       d_tempk_v);
	    }
	    /*Calculate sensible heat flux fractions */
	    d_h_g = h_g(d_tempk_g, d_tempk_v, d_tempka, d_rg, d_rv, d_ra);
	    d_h_v = h_v(d_tempk_g, d_tempk_v, d_tempka, d_rg, d_rv, d_ra);

	    /*Calculate LE */
	    d_le_inst_v = d_rn_v - d_g0_v - d_h_v;
	    d_le_inst_g = d_rn_g - d_g0_g - d_h_g;
	    d_le_inst = d_le_inst_v + d_le_inst_g;

	    /*Calculate ET */
	    d_daily_et = daily_et(d_le_inst, d_time, d_sunh);


	    if (zero->answer && d_daily_et < 0)
		d_daily_et = 0.0;

	    /* write calculated ETP to output line buffer */
	    outrast[col] = d_daily_et;
	}


	/* write output line buffer to output raster file */
	if (G_put_raster_row(outfd, outrast, data_type_output) < 0)
	    G_fatal_error(_("Cannot write to <%s>"), ETa);

    }
    /* free buffers and close input maps */

    G_free(inrast_RNET);
    G_free(inrast_FV);
    G_free(inrast_TEMPK);
    G_free(inrast_TEMPKA);
    G_free(inrast_ALB);
    G_free(inrast_NDVI);
    G_free(inrast_UZ);
    if (DISP != NULL) {
	G_free(inrast_DISP);
    }
    if (Z0 != NULL) {
	G_free(inrast_Z0);
    }
    if (HV != NULL) {
	G_free(inrast_HV);
    }
    G_free(inrast_TIME);
    G_free(inrast_SUNH);
    G_close_cell(infd_RNET);
    G_close_cell(infd_FV);
    G_close_cell(infd_TEMPK);
    G_close_cell(infd_TEMPKA);
    G_close_cell(infd_ALB);
    G_close_cell(infd_NDVI);
    G_close_cell(infd_UZ);
    if (DISP != NULL) {
	G_close_cell(infd_DISP);
    }
    if (Z0 != NULL) {
	G_close_cell(infd_Z0);
    }
    if (HV != NULL) {
	G_close_cell(infd_HV);
    }
    G_close_cell(infd_TIME);
    G_close_cell(infd_SUNH);

    /* generate color table between -20 and 20 */
    G_make_rainbow_colors(&color, -20, 20);
    G_write_colors(ETa, G_mapset(), &color);

    G_short_history(ETa, "raster", &history);
    G_command_history(&history);
    G_write_history(ETa, &history);

    /* free buffers and close output map */
    G_free(outrast);
    G_close_cell(outfd);

    return (0);
}
