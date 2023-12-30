/****************************************************************************
 *
 * MODULE:       r.mcda.promethee
 * AUTHORS:      Gianluca Massei (g_massa@libero.it) - Antonio Boggia
 *                  (boggia@unipg.it)
 *
 * PURPOSE:      Make a multicriteria decision analysis based on PROMETHEE
 *               algorithm. J.P. Brans and P. Vincke (1985). "A preference
 *               ranking organisation method: The PROMETHEE method for MCDM".
 *               Management Science.
 *
 * COPYRIGHT:    Gianluca Massei (g_massa@libero.it) and (C) GRASS Development
 *               Team (2015)
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include "local_proto.h"

/*
 * main function
 */
int main(int argc, char *argv[])
{
    struct Cell_head cellhd; /* it stores region information,  and header
                                information of rasters */
    char *result_positive_flow, *result_negative_flow; /* outputs raster name */
    /*char *mapset;      mapset name */
    unsigned char *outrast_positive_flow,
        *outrast_negative_flow; /* output buffer */
    int i, j, ncriteria = 0;    /* index and  files number*/
    int nrows, ncols;
    int row1, col1;
    int outfd_positive_flow, outfd_negative_flow; /* output file descriptor */
    /*RASTER_MAP_TYPE data_type;     type of the map (CELL/DCELL/...) */
    double *weight_vect, ***decision_vol, **positive_flow_vol,
        **negative_flow_vol; /* vector and matrix */

    struct History history; /* holds meta-data (title, comments,..) */

    struct GModule *module; /* GRASS module for parsing arguments */

    struct Option *criteria, *weight, *positiveflow,
        *negativeflow; /* options */

    struct input *attributes; /*storage  alla input criteria GRID files and
                                 output concordance and discordance GRID files*/

    /* initialize GIS environment */
    G_gisinit(
        argv[0]); /* reads grass env, stores program name to G_program_name() */

    /* initialize module */
    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("MCDA"));
    module->description =
        _("Multicirtieria decision analysis based on PROMETHEE method");

    /* Define the different options as defined in gis.h */
    criteria = G_define_option(); /* Allocates memory for the Option structure
                                     and returns a pointer to this memory*/
    criteria->key = "criteria";
    criteria->type = TYPE_STRING;
    criteria->required = YES;
    criteria->multiple = YES;
    criteria->gisprompt = "old,cell,raster";
    criteria->description = "Input geographics criteria in information system";

    weight = G_define_option(); /* Allocates memory for the Option structure and
                                   returns a pointer to this memory*/
    weight->key = "weight";
    weight->type = TYPE_DOUBLE;
    weight->required = YES;
    weight->multiple = YES;
    weight->description = _("Criteria weight(s) (w1,w2,..,wn)");

    positiveflow =
        G_define_option(); /* Allocates memory for the Option structure and
                              returns a pointer to this memory */
    positiveflow->key = "positiveflow";
    positiveflow->type = TYPE_STRING;
    positiveflow->required = YES;
    positiveflow->gisprompt = "new,cell,raster";
    positiveflow->answer = "positiveflow";
    positiveflow->description = "positive flow output map";

    negativeflow =
        G_define_option(); /* Allocates memory for the Option structure and
                              returns a pointer to this memory */
    negativeflow->key = "negativeflow";
    negativeflow->type = TYPE_STRING;
    negativeflow->required = YES;
    negativeflow->gisprompt = "new,cell,raster";
    negativeflow->answer = "negativeflow";
    negativeflow->description = "negative flow output map";

    /* options and flags parser */
    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    G_message("Start: %s", G_date()); /*write calculation start time*/

    /* number of file (=criteria) */
    while (criteria->answers[ncriteria] != NULL) {
        ncriteria++;
    }

    /* process the input maps:  stores options and flags to variables */
    /* CRITERIA grid */
    attributes = G_malloc(
        ncriteria *
        sizeof(struct input)); /*attributes is input struct defined in top file
                                  and store alla criteria files*/
    weight_vect = G_malloc(
        ncriteria * sizeof(double)); /*allocate memory fron vector weight*/

    build_weight_vect(ncriteria, weight,
                      weight_vect); /*calcolate weight vector*/

    for (i = 0; i < ncriteria; i++) {
        struct input *p = &attributes[i];
        p->name = criteria->answers[i];
        p->mapset = (char *)G_find_raster2(
            p->name,
            ""); /*  Looks for the raster map "name" in the database. */
        if (p->mapset == NULL) /* returns NULL if the map was not found in any
                                  mapset,   mapset name otherwise */
            G_fatal_error(_("Raster file <%s> not found"), p->name);

        /* determine the inputmap type (CELL/FCELL/DCELL) */
        /*     data_type = Rast_map_type(p->name, p->mapset);*/

        if ((p->infd = Rast_open_old(p->name, p->mapset)) <
            0) /* Rast_open_cell_old - returns file destriptor (>0) */
            G_fatal_error(_("Unable to open input map <%s> in mapset <%s>"),
                          p->name, p->mapset);

        Rast_get_cellhd(p->name, p->mapset,
                        &cellhd); /* controlling, if we can open input raster */
        G_debug(3, "number of rows %d", cellhd.rows);

        p->inrast = Rast_allocate_buf(
            DCELL_TYPE); /* Allocate an array of DCELL based on the number of
                            columns in the current region. Return DCELL   */
    }

    result_positive_flow =
        positiveflow->answer; /* store output name in variables*/
    result_negative_flow = negativeflow->answer;

    if (G_legal_filename(result_positive_flow) <
        0) /* check for legal database file names */
        G_fatal_error(_("<%s> is an illegal file name"), result_positive_flow);

    if (G_legal_filename(result_negative_flow) <
        0) /* check for legal database file names */
        G_fatal_error(_("<%s> is an illegal file name"), result_negative_flow);

    /*values = G_malloc(ncriteria * sizeof(DCELL));*/

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    /*memory allocation for-three dimensional matrix*/
    decision_vol = G_malloc(nrows * sizeof(double *));
    positive_flow_vol = G_calloc(
        nrows, sizeof(double *)); /*Allocates aligned block of memory and
                                     initializes the allocated memory to zero.*/
    negative_flow_vol = G_calloc(nrows, sizeof(double *));

    for (i = 0; i < nrows; ++i) {
        decision_vol[i] = G_malloc(ncols * sizeof(double *));
        positive_flow_vol[i] = G_calloc(
            ncols,
            sizeof(double *)); /*Allocates aligned block of memory and
                                  initializes the allocated memory to zero.*/
        negative_flow_vol[i] = G_calloc(ncols, sizeof(double *));

        for (j = 0; j < ncols; ++j) {
            decision_vol[i][j] = G_malloc(
                (ncriteria + 2) * sizeof(double)); /****NOTE: it's storage ****/
        }
    }

    /* Allocate output buffer, use  DCELL_TYPE */
    outrast_positive_flow = Rast_allocate_buf(
        DCELL_TYPE); /* Allocate memory for a raster map of type DCELL_TYPE. */
    outrast_negative_flow = Rast_allocate_buf(DCELL_TYPE);

    /* controlling, if we can write the raster */
    outfd_positive_flow = Rast_open_new(result_positive_flow, DCELL_TYPE);
    outfd_negative_flow = Rast_open_new(result_negative_flow, DCELL_TYPE);

    /*build a three dimensional matrix for storage all critera maps*/
    G_message("Load data");
    for (i = 0; i < ncriteria; i++) {
        for (row1 = 0; row1 < nrows; row1++) {
            G_percent(row1, nrows, 2);
            Rast_get_row(
                attributes[i].infd, attributes[i].inrast, row1,
                DCELL_TYPE); /* Reads appropriate information into the buffer
                                buf associated with the requested row*/
            /*G_fatal_error(_("Unable to read raster map <%s> row %d"),
             * criteria->answers[i], row);*/
            for (col1 = 0; col1 < ncols; col1++) {
                /* viene letto il valore di cella e lo si attribuisce ad una
                 * variabile di tipo DCELL e poi ad un array*/
                DCELL v1 = ((DCELL *)attributes[i].inrast)[col1];
                decision_vol[row1][col1][i] = (double)(v1);
            }
        }
    }

    G_message("run algorithm");
    build_flow_matrix(
        nrows, ncols, ncriteria, weight_vect, decision_vol, positive_flow_vol,
        negative_flow_vol); /*scan all DCELL, make a pairwise comparatione, buil
                               positive flow matrix*/

    G_message("buil mcda maps");
    for (row1 = 0; row1 < nrows; row1++) {
        G_percent(row1, nrows, 2);
        for (col1 = 0; col1 < ncols; col1++) {
            ((DCELL *)outrast_positive_flow)[col1] = (DCELL)
                positive_flow_vol[row1][col1]; /*write positive flow map*/
            ((DCELL *)outrast_negative_flow)[col1] = (DCELL)
                negative_flow_vol[row1][col1]; /*write negative flow map*/
        }
        Rast_put_row(outfd_positive_flow, outrast_positive_flow, DCELL_TYPE);
        Rast_put_row(outfd_negative_flow, outrast_negative_flow, DCELL_TYPE);
    }

    G_message("End: %s", G_date());

    /* memory cleanup */
    for (i = 0; i < ncriteria; i++)
        G_free(attributes[i].inrast);

    G_free(outrast_positive_flow);
    G_free(outrast_negative_flow);

    G_free(decision_vol);
    G_free(positive_flow_vol);
    G_free(negative_flow_vol);

    /* closing raster maps */
    for (i = 0; i < ncriteria; i++)
        Rast_close(attributes[i].infd);

    Rast_close(outfd_positive_flow);
    Rast_close(outfd_negative_flow);

    /* add command line incantation to history positive file */
    Rast_short_history(result_positive_flow, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(result_positive_flow, &history);

    /* add command line incantation to history negative file */
    Rast_short_history(result_negative_flow, "raster", &history);
    Rast_command_history(&history);
    Rast_write_history(result_negative_flow, &history);

    exit(EXIT_SUCCESS);
}
