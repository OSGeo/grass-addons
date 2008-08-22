
/****************************************************************************
 *
 * MODULE:       r.gaswap
 * AUTHOR(S):    Yann Chemin - yann.chemin@gmail.com
 *		 Shamim Akhter - shamimakhter@gmail.com
 * PURPOSE:      Run SWAP model in an optimization mode from a real-coded
 *               genetic algorithm (Michalewicz,1996).
 *
 * COPYRIGHT:    (C) 2002-2007 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *   	    	 License (>=v2). Read the file COPYING that comes with GRASS
 *   	    	 for details.
 *
 *****************************************************************************/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include "gaswap.h"

#define MAXFILES 180		/* input ETa max layers */
#define NVAR 6			/* output file number */

extern DCELL f_f(DCELL);

/* satellite ETa is in mm/day, swapETa in cm/day */
/* This converts sat ETa to cm/day */
DCELL f_calc1(DCELL x)
{
    return (x * 0.1);
}

int main(int argc, char *argv[])
{
    struct GModule *module;

    struct
    {
	struct Option *input1, *input2, *input3, *input4, *input5, *input6,
	    *input7, *input8, *input9, *input10, *input11, *input12, *input13,
	    *input14, *input15, *input16, *input17, *output1, *output2,
	    *output3, *output4, *output5, *output6;
    } param;

    struct Cell_head cellhd;

    char *name, *mapset;

    int nrows, ncols;

    int row, col;

    name = "";

	/************************************/
    /* FMEO Declarations**************** */
    int nfiles = MAXFILES;

    int infd[nfiles], infd_doy[nfiles], infd_psand, infd_psilt, infd_pclay,
	infd_pomat;
    int outfd[NVAR + 1];

    int SSRUN_Year, ESRUN_Year, year;

    char *METFILE;

    double Lat, Alt;

    char **names;

    char **ptr;

    char **doy_names;

    char **doy_ptr;

    char *psand, *psilt, *pclay, *pomat;

    char *result[NVAR + 1];

    double pmute, pxover, target_fitness;

    /*char *pmute, *pxover, *target_fitness; */
    int pop, maxgen;

    int ok;

    int i = 0, j = 0;

    void *inrast[nfiles], *inrast_doy[nfiles];

    void *inrast_psand, *inrast_psilt, *inrast_pclay, *inrast_pomat;

    FCELL *outrast[NVAR + 2];

    RASTER_MAP_TYPE data_type[nfiles];

    RASTER_MAP_TYPE data_type_doy[nfiles];

    RASTER_MAP_TYPE data_type_psand;

    RASTER_MAP_TYPE data_type_psilt;

    RASTER_MAP_TYPE data_type_pclay;

    RASTER_MAP_TYPE data_type_pomat;

    double sat[nfiles];

    double sat_doy[nfiles];

    double grass_cell[NVAR + 2];

	/************************************/

    G_gisinit(argv[0]);

    module = G_define_module();
    module->description =
	"Genetic Algorithms and Soil-Water-Air-Plant [GA+SWAP]";

    /* Define the different options */

    param.input1 = G_define_standard_option(G_OPT_R_INPUTS);
    param.input1->key = "input_eta";
    param.input1->description = "Names of satellite ETa layers";
    param.input1->guisection = "IN";

    param.input2 = G_define_standard_option(G_OPT_R_INPUTS);
    param.input2->key = "input_doy";
    param.input2->description = "Names of satellite Doy layers";
    param.input2->guisection = "IN";

    param.input3 = G_define_standard_option(G_OPT_R_INPUT);
    param.input3->key = "psand";
    param.input3->description =
	"Name of the Soil sand fraction map [0.0-1.0]";
    param.input3->answer = "psand";
    param.input3->guisection = "IN";

    param.input4 = G_define_standard_option(G_OPT_R_INPUT);
    param.input4->key = "psilt";
    param.input4->description =
	"Name of the Soil silt fraction map [0.0-1.0]";
    param.input4->answer = "psilt";
    param.input4->guisection = "IN";

    param.input5 = G_define_standard_option(G_OPT_R_INPUT);
    param.input5->key = "pclay";
    param.input5->description =
	"Name of the Soil clay fraction map [0.0-1.0]";
    param.input5->answer = "pclay";
    param.input5->guisection = "IN";

    param.input6 = G_define_standard_option(G_OPT_R_INPUT);
    param.input6->key = "pomat";
    param.input6->description =
	"Name of the Soil Organic Matter map [0.0-1.0]";
    param.input6->answer = "pomat";
    param.input6->guisection = "IN";

    param.input7 = G_define_option();
    param.input7->key = "pop";
    param.input7->key_desc = "count";
    param.input7->type = TYPE_INTEGER;
    param.input7->required = YES;
    param.input7->description = "Number of Populations in GAreal";
    param.input7->answer = "20";
    param.input7->guisection = "param_GA";

    param.input8 = G_define_option();
    param.input8->key = "max_gen";
    param.input8->key_desc = "count";
    param.input8->type = TYPE_INTEGER;
    param.input8->required = YES;
    param.input8->description = "Number of Generations in GAreal";
    param.input8->answer = "200";
    param.input8->guisection = "param_GA";

    param.input9 = G_define_option();
    param.input9->key = "pmute";
    param.input9->key_desc = "count";
    param.input9->type = TYPE_DOUBLE;
    param.input9->required = YES;
    param.input9->description = "Probability of Mutation in GAreal";
    param.input9->answer = "0.3";
    param.input9->guisection = "param_GA";

    param.input10 = G_define_option();
    param.input10->key = "pxover";
    param.input10->key_desc = "count";
    param.input10->type = TYPE_DOUBLE;
    param.input10->required = YES;
    param.input10->description = "Probability of Crossover in GAreal";
    param.input10->answer = "0.8";
    param.input10->guisection = "param_GA";

    param.input11 = G_define_option();
    param.input11->key = "target_fitness";
    param.input11->key_desc = "count";
    param.input11->type = TYPE_DOUBLE;
    param.input11->required = YES;
    param.input11->description = "Target Fitness in GAreal";
    param.input11->answer = "20.0";
    param.input11->guisection = "param_GA";

    param.input12 = G_define_option();
    param.input12->key = "year";
    param.input12->key_desc = "count";
    param.input12->type = TYPE_INTEGER;
    param.input12->required = NO;
    param.input12->description = "Data Processing Year";
    param.input12->answer = "2002";
    param.input12->guisection = "param_SWAP";

    param.input13 = G_define_option();
    param.input13->key = "SSRUN_Year";
    param.input13->key_desc = "count";
    param.input13->type = TYPE_INTEGER;
    param.input13->required = NO;
    param.input13->description = "Starting Crop Year";
    param.input13->answer = "2002";
    param.input13->guisection = "param_SWAP";

    param.input14 = G_define_option();
    param.input14->key = "ESRUN_Year";
    param.input14->key_desc = "count";
    param.input14->type = TYPE_INTEGER;
    param.input14->required = NO;
    param.input14->description = "Ending Crop Year";
    param.input14->answer = "2002";
    param.input14->guisection = "param_SWAP";

    param.input15 = G_define_option();
    param.input15->key = "METFILE";
    param.input15->key_desc = "count";
    param.input15->type = TYPE_STRING;
    param.input15->required = NO;
    param.input15->description = "Meteorological File Name";
    param.input15->answer = "U-T";
    param.input15->guisection = "param_SWAP";


    param.input16 = G_define_option();
    param.input16->key = "Lat";
    param.input16->key_desc = "count";
    param.input16->type = TYPE_DOUBLE;
    param.input16->required = NO;
    param.input16->description = "Latitude of MET Station";
    param.input16->answer = "14.338";
    param.input16->guisection = "param_SWAP";


    param.input17 = G_define_option();
    param.input17->key = "Alt";
    param.input17->key_desc = "count";
    param.input17->type = TYPE_DOUBLE;
    param.input17->required = NO;
    param.input17->description = "Altitude of MET Station";
    param.input17->answer = "10.0";
    param.input17->guisection = "param_SWAP";



    param.output1 = G_define_standard_option(G_OPT_R_OUTPUT);
    param.output1->key = "DEC";
    param.output1->description =
	"Name of an output Date of Emergence of Crop layer";
    param.output1->answer = "gaswap_DEC";
    param.output1->guisection = "OUT";

    param.output2 = G_define_standard_option(G_OPT_R_OUTPUT);
    param.output2->key = "FEC";
    param.output2->description = "Name of an output Forced End of Crop layer";
    param.output2->answer = "gaswap_FEC";
    param.output2->guisection = "OUT";

    param.output3 = G_define_standard_option(G_OPT_R_OUTPUT);
    param.output3->key = "STS";
    param.output3->description =
	"Name of an output Scheduled Time of Irrigation layer";
    param.output3->answer = "gaswap_STS";
    param.output3->guisection = "OUT";

    param.output4 = G_define_standard_option(G_OPT_R_OUTPUT);
    param.output4->key = "GWJan";
    param.output4->description =
	"Name of the Ground Water Depth in January output layer";
    param.output4->answer = "gaswap_GWJan";
    param.output4->guisection = "OUT";

    param.output5 = G_define_standard_option(G_OPT_R_OUTPUT);
    param.output5->key = "GWDec";
    param.output5->description =
	"Name of the Ground Water Depth in December output layer";
    param.output5->answer = "gaswap_GWDec";
    param.output5->guisection = "OUT";

    param.output6 = G_define_standard_option(G_OPT_R_OUTPUT);
    param.output6->key = "fitness";
    param.output6->description = "Name of the fitness output layer";
    param.output6->answer = "gaswap_fitness";
    param.output6->guisection = "OUT";

    /* FMEO init nfiles */
    nfiles = 1;

	/********************/

	/********************/
    if (G_parser(argc, argv))
	exit(-1);

    ok = 1;
    names = param.input1->answers;
    ptr = param.input1->answers;
    doy_names = param.input2->answers;
    doy_ptr = param.input2->answers;
    psand = param.input3->answer;
    psilt = param.input4->answer;
    pclay = param.input5->answer;
    pomat = param.input6->answer;
    pop = atoi(param.input7->answer);
    maxgen = atof(param.input8->answer);
    pmute = atof(param.input9->answer);
    pxover = atof(param.input10->answer);
    target_fitness = atof(param.input11->answer);
    year = atoi(param.input12->answer);
    SSRUN_Year = atoi(param.input13->answer);
    ESRUN_Year = atoi(param.input14->answer);
    METFILE = param.input15->answer;
    Lat = atof(param.input16->answer);
    Alt = atof(param.input17->answer);

    result[1] = param.output1->answer;
    result[2] = param.output2->answer;
    result[3] = param.output3->answer;
    result[4] = param.output4->answer;
    result[5] = param.output5->answer;
    result[6] = param.output6->answer;

    /*Satellite dates... */
    for (; *doy_ptr != NULL; doy_ptr++) {
	if (nfiles >= MAXFILES)
	    G_fatal_error("%s - too many ETa files. Only %d allowed",
			  G_program_name(), MAXFILES);
	name = *doy_ptr;
	/* find map in mapset */
	mapset = G_find_cell2(name, "");
	if (mapset == NULL) {
	    G_fatal_error("cell file [%s] not found", name);
	    sleep(3);
	    ok = 0;
	}
	for (i = 1; i < NVAR + 1; i++) {
	    if (G_legal_filename(result[i]) < 0) {
		G_fatal_error("[%s] is an illegal name", result[i]);
		sleep(3);
		ok = 0;
	    }
	}
	if (!ok)
	    continue;
	infd_doy[nfiles] = G_open_cell_old(name, mapset);
	if (infd_doy[nfiles] < 0) {
	    ok = 0;
	    continue;
	}
	/* Allocate input buffer */
	data_type_doy[nfiles] = G_raster_map_type(name, mapset);
	if ((infd_doy[nfiles] = G_open_cell_old(name, mapset)) < 0)
	    G_fatal_error("Cannot open cell file [%s]", name);
	if (G_get_cellhd(name, mapset, &cellhd) < 0)
	    G_fatal_error("Cannot read file header of [%s]", name);
	inrast_doy[nfiles] = G_allocate_raster_buf(data_type_doy[nfiles]);
	nfiles++;
    }
    nfiles--;
    if (nfiles <= 1)
	G_fatal_error("The min specified input map is two");

    nfiles = 1;

	/*****************************************************/
    /*satellite eta */
    for (; *ptr != NULL; ptr++) {
	if (nfiles >= MAXFILES)
	    G_fatal_error("%s - too many ETa files. Only %d allowed",
			  G_program_name(), MAXFILES);
	name = *ptr;
	/* find map in mapset */
	mapset = G_find_cell2(name, "");
	if (mapset == NULL) {
	    G_fatal_error("cell file [%s] not found", name);
	    sleep(3);
	    ok = 0;
	}
	for (i = 1; i < NVAR + 1; i++) {
	    if (G_legal_filename(result[i]) < 0) {
		G_fatal_error("[%s] is an illegal name", result[i]);
		sleep(3);
		ok = 0;
	    }
	}
	if (!ok)
	    continue;
	infd[nfiles] = G_open_cell_old(name, mapset);
	if (infd[nfiles] < 0) {
	    ok = 0;
	    continue;
	}
	/* Allocate input buffer */
	data_type[nfiles] = G_raster_map_type(name, mapset);
	if ((infd[nfiles] = G_open_cell_old(name, mapset)) < 0)
	    G_fatal_error("Cannot open cell file [%s]", name);
	if (G_get_cellhd(name, mapset, &cellhd) < 0)
	    G_fatal_error("Cannot read file header of [%s]", name);
	inrast[nfiles] = G_allocate_raster_buf(data_type[nfiles]);
	nfiles++;
    }
    nfiles--;
    if (nfiles <= 1)
	G_fatal_error("The min specified input map is two");

    /*Load soil files now */

	/***************************************************/
    mapset = G_find_cell2(psand, "");
    if (mapset == NULL) {
	G_fatal_error("cell file [%s] not found", psand);
	sleep(3);
	ok = 0;
    }
    data_type_psand = G_raster_map_type(psand, mapset);
    if ((infd_psand = G_open_cell_old(psand, mapset)) < 0)
	G_fatal_error("Cannot open cell file [%s]", psand);
    if (G_get_cellhd(psand, mapset, &cellhd) < 0)
	G_fatal_error("Cannot read file header of [%s]", psand);
    inrast_psand = G_allocate_raster_buf(data_type_psand);

	/***************************************************/
    mapset = G_find_cell2(psilt, "");
    if (mapset == NULL) {
	G_fatal_error("cell file [%s] not found", psilt);
	sleep(3);
	ok = 0;
    }
    data_type_psilt = G_raster_map_type(psilt, mapset);
    if ((infd_psilt = G_open_cell_old(psilt, mapset)) < 0)
	G_fatal_error("Cannot open cell file [%s]", psilt);
    if (G_get_cellhd(psilt, mapset, &cellhd) < 0)
	G_fatal_error("Cannot read file header of [%s]", psilt);
    inrast_psilt = G_allocate_raster_buf(data_type_psilt);

	/***************************************************/
    mapset = G_find_cell2(pclay, "");
    if (mapset == NULL) {
	G_fatal_error("Cell file [%s] not found", pclay);
	sleep(3);
	ok = 0;
    }
    data_type_pclay = G_raster_map_type(pclay, mapset);
    if ((infd_pclay = G_open_cell_old(psilt, mapset)) < 0)
	G_fatal_error("Cannot open cell file [%s]", pclay);
    if (G_get_cellhd(pclay, mapset, &cellhd) < 0)
	G_fatal_error("Cannot read file header of [%s]", pclay);
    inrast_pclay = G_allocate_raster_buf(data_type_pclay);

	/***************************************************/
    mapset = G_find_cell2(pomat, "");
    if (mapset == NULL) {
	G_fatal_error("Cell file [%s] not found", pomat);
	sleep(3);
	ok = 0;
    }
    data_type_pomat = G_raster_map_type(pomat, mapset);
    if ((infd_pomat = G_open_cell_old(pomat, mapset)) < 0)
	G_fatal_error("Cannot open cell file [%s]", pomat);
    if (G_get_cellhd(pomat, mapset, &cellhd) < 0)
	G_fatal_error("Cannot read file header of [%s]", pomat);
    inrast_pomat = G_allocate_raster_buf(data_type_pomat);

	/***************************************************/
    //printf("here1\n");
    nrows = G_window_rows();
    ncols = G_window_cols();

    //printf("No of rows=%d\nNo of Col=%d\n",nrows,ncols);
    for (i = 1; i < NVAR + 2; i++) {
	outrast[i] = G_allocate_raster_buf(1);
    }
    /* Create New raster files */
    for (i = 1; i < NVAR + 1; i++) {
	if ((outfd[i] = G_open_raster_new(result[i], 1)) < 0)
	    G_fatal_error("Could not open <%s>", result[i]);
    }
    /* Process pixels */
    for (row = 0; row < nrows; row++) {
	FCELL f;

	FCELL fe[NVAR + 2];
	double tex[4] = { 0.0, 0.0, 0.0, 0.0 };
	G_percent(row, nrows, 2);
	/* read input map */
	for (i = 1; i < nfiles + 1; i++) {
	    sat[i] = 0.0;
	    sat_doy[i] = 0.0;
	    if (G_get_raster_row(infd[i], inrast[i], row, data_type[i]) < 0)
		G_fatal_error("Could not read from <%s>", name);
	    if (G_get_raster_row
		(infd_doy[i], inrast_doy[i], row, data_type[i]) < 0)
		G_fatal_error("Could not read from <%s>", name);
	}
	/* read soil input maps */
	if (G_get_raster_row(infd_psand, inrast_psand, row, 1) < 0)
	    G_fatal_error("Could not read from <%s>", name);
	if (G_get_raster_row(infd_psilt, inrast_psilt, row, 1) < 0)
	    G_fatal_error("Could not read from <%s>", name);
	if (G_get_raster_row(infd_pclay, inrast_pclay, row, 1) < 0)
	    G_fatal_error("Could not read from <%s>", name);
	if (G_get_raster_row(infd_pomat, inrast_pomat, row, 1) < 0)
	    G_fatal_error("Could not read from <%s>", name);
	/*process the data */
	for (col = 0; col < ncols; col++) {
	    switch (data_type_psand) {
	    case CELL_TYPE:
		f = (float)((CELL *) inrast_psand)[col];
		break;
	    case FCELL_TYPE:
		f = ((FCELL *) inrast_psand)[col];
		break;
	    case DCELL_TYPE:
		f = (float)((DCELL *) inrast_psand)[col];
		break;
	    }
	    tex[0] = f;
	    switch (data_type_psilt) {
	    case CELL_TYPE:
		f = (float)((CELL *) inrast_psilt)[col];
		break;
	    case FCELL_TYPE:
		f = ((FCELL *) inrast_psilt)[col];
		break;
	    case DCELL_TYPE:
		f = (float)((DCELL *) inrast_psilt)[col];
		break;
	    }
	    tex[1] = f;
	    switch (data_type_pclay) {
	    case CELL_TYPE:
		f = (float)((CELL *) inrast_pclay)[col];
		break;
	    case FCELL_TYPE:
		f = ((FCELL *) inrast_pclay)[col];
		break;
	    case DCELL_TYPE:
		f = (float)((DCELL *) inrast_pclay)[col];
		break;
	    }
	    tex[2] = f;
	    switch (data_type_pomat) {
	    case CELL_TYPE:
		f = (float)((CELL *) inrast_pomat)[col];
		break;
	    case FCELL_TYPE:
		f = ((FCELL *) inrast_pomat)[col];
		break;
	    case DCELL_TYPE:
		f = (float)((DCELL *) inrast_pomat)[col];
		break;
	    }
	    tex[3] = f;

			/************************************/
	    for (j = 1; j < nfiles + 1; j++) {
		f = ((FCELL *) inrast[j])[col];
		f = f_calc1(f);	/* convert to cm/day */
		sat[j] = f;
		f = ((FCELL *) inrast_doy[j])[col];
		sat_doy[j] = f;
	    }
	    gaswap(tex, sat, sat_doy, NVAR, nfiles, year, pop, maxgen, pmute,
		   pxover, target_fitness, SSRUN_Year, ESRUN_Year, METFILE,
		   Lat, Alt, grass_cell);

	    for (j = 1; j < NVAR + 2; j++) {
		fe[j] = grass_cell[j];
		outrast[j][col] = fe[j];
	    }
	}
	for (i = 1; i < NVAR + 1; i++) {
	    if (G_put_raster_row(outfd[i], outrast[i], data_type[i]) < 0)
		G_fatal_error("Cannot write to output raster file");
	}
    }
    for (i = 1; i < nfiles + 1; i++) {
	G_free(inrast[i]);
	G_close_cell(infd[i]);
	G_free(inrast_doy[i]);
	G_close_cell(infd_doy[i]);
    }

    G_free(inrast_psand);
    G_free(inrast_psilt);
    G_free(inrast_pclay);
    G_free(inrast_pomat);
    G_close_cell(infd_psand);
    G_close_cell(infd_psilt);
    G_close_cell(infd_pclay);
    G_close_cell(infd_pomat);

    for (i = 1; i < NVAR + 2; i++) {
	G_free(outrast[i]);
	G_close_cell(outfd[i]);
    }
    return 0;
}
