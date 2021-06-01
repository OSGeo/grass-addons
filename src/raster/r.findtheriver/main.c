/**
\file main.c

\brief r.findtheriver - Finds the nearest stream pixel to a
coordinate pair using an upstream accumulating area map.

(C) 2013 by the University of North Carolina at Chapel Hill

This program is free software under the
GNU General Public License (>=v2).
Read the file COPYING that comes with GRASS
for details.

\author Brian Miles - brian_miles@unc.edu

\date May, 20 2013
*/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <math.h>

#include <grass/config.h>
#include <grass/gis.h>
#include <grass/glocale.h>

#include "point_list.h"

#define THRESHOLD_DISTANCE 100
#define DEFAULT_COORD_SEP ' '

/*
 * global function declaration
 */
 /**
\brief Find stream pixels in a given window of the UAA raster

\param[in] fd UAA raster file descriptor
\param[in] name Name of UAA raster map
\param[in] mapset Name of the GRASS mapset from which UAA raster should be read
\param[in] dataType Data type of UAA raster
\param[in] windowSize Size of the search window, must be an odd integer >= 3
\param[in] threshold to use for distinguishing stream pixels by comparing log(UAA) values
\param[in] nrows_less_one Number of rows in the current window, minus 1
\param[in] ncols_less_one Number of columns in the current window, minus 1
\param[in] currRow, Row of pixel that will be compared to pixels in the window
\param[in] currCol, Column of pixel that will be compared to pixels in the window

\return Pointer to PointList_t representing a list of stream pixels found in the window
*/
PointList_t *find_stream_pixels_in_window(int fd, char *name, char *mapset, RASTER_MAP_TYPE dataType,
		int windowSize, double threshold,
		int nrows_less_one, int ncols_less_one,
		int currRow, int currCol);

/*
 * global variables
 */
int quiet;

int main(int argc, char *argv[])
{
	struct Cell_head cellhd;	/* it stores region information,
				   and header information of rasters */
	char name[GNAME_MAX];			/* input raster name */
	char *mapset;		/* mapset name */
	int nrows, ncols;
	int rowIdx, colIdx, nrows_less_one, ncols_less_one;
	int infd;		/* file descriptor */
	RASTER_MAP_TYPE data_type;	/* type of the map (CELL/DCELL/...) */
	struct GModule *module;	/* GRASS module for parsing arguments */

	struct Flag *flag1;		/* flags */
	struct Option *optInput, *optWindow, *optThreshold, *optE, *optN, *optSep;
	double E, N;
	struct Cell_head window;
	char *buff;
	int windowSize;
	double threshold;
	size_t SEP_SIZE = 2;
	char *sep = (char *)G_malloc(SEP_SIZE * sizeof(char));

	/* initialize GIS environment */
	G_gisinit(argv[0]);		/* reads grass env, stores program name to G_program_name() */

	/* initialize module */
	module = G_define_module();
	module->keywords = _("raster, keyword2, keyword3");
	module->description = _("Find the stream pixel nearest the input coordinate");

	/* Define command options */
	optInput = G_define_option();
	optInput->key = "accumulation";
	optInput->type = TYPE_STRING;
	optInput->required = YES;
	optInput->gisprompt = "old,cell,raster";
	optInput->description = _("Name of input upstream accumulation area raster map");

	optWindow = G_define_option();
	optWindow->key = "window";
	optWindow->type = TYPE_INTEGER;
	optWindow->key_desc = "x";
	optWindow->multiple = NO;
	optWindow->required = NO;
	optWindow->description = _("The size of the window, in pixels, to search in for stream\n\t pixels.  Must be an odd integer.  If not supplied, window will be\n\t inferred based on raster resolution.");

	optThreshold = G_define_option();
	optThreshold->key = "threshold";
	optThreshold->type = TYPE_DOUBLE;
	optThreshold->key_desc = "x";
	optThreshold->multiple = NO;
	optThreshold->required = NO;
	optThreshold->description = _("The threshold for distinguishing log(UAA) values of stream and\n\t non-stream pixels.  If not supplied, threshold will be inferred from \n\t minimum and maximum raster values.");

	optE = G_define_option();
	optE->key = "easting";
	optE->type = TYPE_STRING;
	optE->key_desc = "x";
	optE->multiple = NO;
	optE->required = YES;
	optE->description = _("The map E grid coordinates");

	optN = G_define_option();
	optN->key = "northing";
	optN->type = TYPE_STRING;
	optN->key_desc = "y";
	optN->multiple = NO;
	optN->required = YES;
	optN->description = _("The map N grid coordinates");

	optSep = G_define_option();
	optSep->key = "separator";
	optSep->type = TYPE_STRING;
	optSep->key_desc = "y";
	optSep->multiple = NO;
	optSep->required = NO;
	optSep->description = _("Coordinate separator. Defaults to ' '. Must be 1 character\n\t in length.");

	/* Define the different flags */
	flag1 = G_define_flag();
	flag1->key = 'q';
	flag1->description = _("Quiet");

	/* options and flags parser */
	if (G_parser(argc, argv))
		exit(EXIT_FAILURE);

	if (G_get_window(&window) < 0) {
		G_asprintf(&buff, _("Unable to read current window parameters"));
		G_fatal_error(buff);
	}

	/* stores options and flags to variables */
	strncpy(name, optInput->answer, GNAME_MAX);
	quiet = (flag1->answer);

	/* returns NULL if the map was not found in any mapset,
	 * mapset name otherwise */
	mapset = G_find_cell2(name, "");
	if (mapset == NULL) {
		G_fatal_error(_("Raster map <%s> not found"), name);
	}

	/* Get raster metadata */
	if (G_get_cellhd(name, mapset, &cellhd) < 0) {
		G_fatal_error(_("Unable to read file header of <%s>"), name);
	}

	if ( NULL != optWindow->answer ) {
		windowSize = atoi(optWindow->answer);
	} else {
		/* Determine window size */
		double cellRes = (cellhd.ew_res + cellhd.ns_res) / 2;
		windowSize = THRESHOLD_DISTANCE / cellRes;
		if ( !(windowSize & 1)  ) windowSize++;
	}
	if ( (windowSize < 2) || !(windowSize & 1) ) {
		G_warning(_("Invalid window size %s.  Window size must be an odd integer >= 3\n"), optWindow->answer);
		G_usage();
		exit(EXIT_FAILURE);
	}
	if ( !quiet ) {
		G_message(_("Stream search window size %d\n"), windowSize);
	}
	if ( NULL != optThreshold->answer ) {
		threshold = atof(optThreshold->answer);
	} else {
		/* Automatically determine the threshold */
		threshold = -1.0;
	}
	if ( threshold != -1.0 && threshold <= 0.0 ) {
		G_warning(_("Invalid threshold %s.  Threshold must be > 0.0\n"), optThreshold->answer);
		G_usage();
		exit(EXIT_FAILURE);
	}

	if (!G_scan_easting(*optE->answers, &E, G_projection())) {
		G_warning(_("Illegal east coordinate <%s>\n"), optE->answer);
		G_usage();
		exit(EXIT_FAILURE);
	}
	if (!G_scan_northing(*optN->answers, &N, G_projection())) {
		G_warning(_("Illegal north coordinate <%s>\n"), optN->answer);
		G_usage();
		exit(EXIT_FAILURE);
	}
	if ( !quiet ) {
		G_message(_("Input coordinates, easting %f, northing %f\n"), E, N);
	}

	if ( NULL == optSep->answer) {
	  sep[0] = DEFAULT_COORD_SEP;
	} else {
	  if ( strlen(optSep->answer) != 1 ) {
	    G_warning(_("Separator must be 1 character in length\n"));
	    G_usage();
	    exit(EXIT_FAILURE);
	  }
	  strncpy(sep, optSep->answer, SEP_SIZE);
	}

	/* Determine the inputmap type (CELL/FCELL/DCELL) */
	data_type = G_raster_map_type(name, mapset);

	/* Open the raster - returns file descriptor (>0) */
	if ((infd = G_open_cell_old(name, mapset)) < 0)
		G_fatal_error(_("Unable to open raster map <%s>"), name);

	G_get_set_window(&window);
	nrows = G_window_rows();
	ncols = G_window_cols();
	nrows_less_one = nrows - 1;
	ncols_less_one = ncols - 1;

	rowIdx = (int)G_northing_to_row(N, &window);
	colIdx = (int)G_easting_to_col(E, &window);

	//double currNearestE, prevNearestE, currNearestN, prevNearestN;
	PointList_t *streamPixels = find_stream_pixels_in_window(infd, (char *)&name, mapset, data_type,
			windowSize, threshold,
			nrows_less_one, ncols_less_one,
			rowIdx, colIdx);
#ifdef DEBUG
	fprintf(stderr, "Stream pixels: ");
	print_list(stderr, streamPixels, " ");
	fprintf(stderr, "\n");
	fflush(stderr);
#endif
	PointList_t *nearestStreamPixel = find_nearest_point(streamPixels, colIdx, rowIdx);

	if ( NULL != nearestStreamPixel ) {

#ifdef DEBUG
		double nearestValue;
		void *tmpRow = G_allocate_raster_buf(data_type);
		int currCol = nearestStreamPixel->col;
		int currRow = nearestStreamPixel->row;

		fprintf(stderr, "Nearest pixel col: %d, row: %d\n", currCol, currRow);
		fflush(stderr);

		/* Get value of central cell */
		if (G_get_raster_row(infd, tmpRow, currRow, data_type) < 0) {
			G_fatal_error(_("Unable to read raster row %d"), currRow);
		}

		switch (data_type) {
		case FCELL_TYPE:
			nearestValue = (double)((FCELL *) tmpRow)[currCol];
			break;
		case DCELL_TYPE:
			nearestValue = (double)((DCELL *) tmpRow)[currCol];
			break;
		default:
		        nearestValue = (double)((CELL *) tmpRow)[currCol];
			break;
		}

		fprintf(stderr, "Nearest stream pixel UAA value: %f\n", nearestValue);
		fflush(stderr);
		G_free(tmpRow);
#endif

		/* Get center of each column */
		double nearestEasting = G_col_to_easting(nearestStreamPixel->col+0.5, &window);
		double nearestNorthing = G_row_to_northing(nearestStreamPixel->row+0.5, &window);

		/* Print snapped coordinates */
		fprintf(stdout, _("%f%s%f\n"), nearestEasting, sep, nearestNorthing);
		fflush(stdout);
		
	}

	/* Clean up */
	destroy_list(streamPixels);

	/* closing raster maps */
	G_close_cell(infd);

	exit(EXIT_SUCCESS);
}

/*
 * function definitions
 */
PointList_t *find_stream_pixels_in_window(int fd, char *name, char *mapset, RASTER_MAP_TYPE dataType,
		int windowSize, double threshold,
		int nrows_less_one, int ncols_less_one,
		int currRow, int currCol) {
	assert( DCELL_TYPE == dataType );
	assert( windowSize & 1 );

	PointList_t *streamPixels = NULL;
	DCELL centralValue, tmpValue;
	double logCentralValue, logTmpValue;
	void *tmpRow = G_allocate_raster_buf(dataType);

	/* Get value of central cell */
	if (G_get_raster_row(fd, tmpRow, currRow, dataType) < 0) {
		G_fatal_error(_("Unable to read raster row %d"), currRow);
	}
	switch (dataType) {
	case CELL_TYPE:
		centralValue = (double)((CELL *) tmpRow)[currCol];
		break;
	case FCELL_TYPE:
		centralValue = (double)((FCELL *) tmpRow)[currCol];
		break;
	case DCELL_TYPE:
		centralValue = (double)((DCELL *) tmpRow)[currCol];
		break;
	}
	if ( centralValue <= 0 ) centralValue = 1;
	logCentralValue = log10(centralValue);
#ifdef DEBUG
	fprintf(stderr, "logCentralValue: %f\n", logCentralValue);
	fflush(stderr);
#endif

	/* Determine threshold if need be */
	if ( -1.0 == threshold ) {
		struct FPRange *range = (struct FPRange *)G_malloc(sizeof(struct FPRange));
		if ( G_read_fp_range(name, mapset, range) < 0 ) {
			G_fatal_error(_("Unable to determine range of raster map <%s>"), name);
		}
		double max = range->max;
		G_free(range); // eggs or is it chicken?
		if ( max == centralValue ) return streamPixels;

		double logMax = log10(max);
		threshold = floor(logMax - logCentralValue);
		if (threshold <= 0.0) {
		  threshold = 1.0;
		} else if (threshold > 2.0) {
		  threshold = 2.0;
		}

#ifdef DEBUG
		fprintf(stderr, "logMax: %f\n", logMax);
		fflush(stderr);
#endif

	}

	if ( !quiet ) {
		G_message(_("threshold: %f\n"), threshold);
	}

	/* Define window bounds */
	int windowOffset = ( windowSize - 1 ) / 2;
	int minCol = currCol - windowOffset;
	if ( minCol < 0 ) minCol = 0;
	int maxCol = currCol + windowOffset;
	if ( maxCol > ncols_less_one ) maxCol = ncols_less_one;
	int minRow = currRow - windowOffset;
	if ( minRow < 0 ) minRow = 0;
	int maxRow = currRow + windowOffset;
	if ( maxRow > nrows_less_one ) maxRow = nrows_less_one;
#ifdef DEBUG
	fprintf(stderr, "currCol: %d, currRow: %d\n", currCol, currRow);
	fprintf(stderr, "min. col: %d, max. col: %d\n", minCol, maxCol);
	fprintf(stderr, "min. row: %d, max. row: %d\n", minRow, maxRow);
	fflush(stderr);
#endif

	/* Search for stream pixels within the window */
	int row, col;
	for ( row = minRow ; row <= maxRow ; row++ ) {
#ifdef DEBUG
		fprintf(stderr, "row: %d\n", row);
		fflush(stderr);
#endif
		/* Get the current row */
		if (G_get_raster_row(fd, tmpRow, row, dataType) < 0) {
				G_fatal_error(_("Unable to read raster row %d"), row);
		}
		for ( col = minCol ; col <= maxCol ; col++ ) {
#ifdef DEBUG
			fprintf(stderr, "\tcol: %d\n", col);
			fflush(stderr);
#endif
			switch (dataType) {
			case CELL_TYPE:
				tmpValue = (double)((CELL *) tmpRow)[col];
				break;
			case FCELL_TYPE:
				tmpValue = (double)((FCELL *) tmpRow)[col];
				break;
			case DCELL_TYPE:
				tmpValue = (double)((DCELL *) tmpRow)[col];
				break;
			}
			logTmpValue = log10(tmpValue);
			/* Test for nearby pixels that are stream pixels when compared to the central pixel */
#ifdef DEBUG
			fprintf(stderr, "\t\tlogTmpValue: %f, logCentralValue: %f\n",
					logTmpValue, logCentralValue);
			fflush(stderr);
#endif
			if ( (logTmpValue - logCentralValue) > threshold ) {
				/* Add to list of stream pixels */
				if ( NULL == streamPixels ) {
					streamPixels = create_list(col, row);
				} else {
					append_point(streamPixels, col, row);
				}
			}
		}
	}
	G_free(tmpRow);
	return streamPixels;
}
