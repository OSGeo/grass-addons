
/****************************************************************************
 *
 * MODULE:	r.mcda.electre
 * AUTHORS:	 Gianluca Massei (g_massa@libero.it) - Antonio Boggia (boggia@unipg.it)
 *
 * PURPOSE:      Make a multicriteria decision  analysis based on Yager fuzzy algorthm
 *
 * COPYRIGHT:     (C) GRASS Development Team (2008)
 *
 *		        This program is free software under the GNU General Public
 *   	    	License (>=v2). Read the file COPYING that comes with GRASS
 *   	    	for details.
 *
 *****************************************************************************/


#include "local_proto.h"


/*
 * main function
 */
int main(int argc, char *argv[])
{
    struct Cell_head cellhd;	/* it stores region information,  and header information of rasters */
    char *result_and, *result_or, *result_owa;	/* outputs raster name */
    char *mapset;		/* mapset name */
    unsigned char *outrast_and, *outrast_or, *outrast_owa;	/* output buffer */
    int i, j, ncriteria = 0;	/* index and  files number */
    int nrows, ncols;
    int row1, row2, col1, col2;
    int outfd_and, outfd_or, outfd_owa;	/* output file descriptor */
    double *weight_vect, ***decision_vol;


    struct History history;	/* holds meta-data (title, comments,..) */

    struct GModule *module;	/* GRASS module for parsing arguments */

    struct Option *criteria, *weight, *and, *or, *owa;	/* options */

    struct input *attributes;	/*storage  alla input criteria GRID files and output concordance and discordance GRID files */


    /* initialize GIS environment */
    G_gisinit(argv[0]);		/* reads grass env, stores program name to G_program_name() */

    /* initialize module */
    module = G_define_module();
    module->keywords = _("raster,MCDA,fuzzy");
    module->description =
        _("Multicirtieria decision analysis based on Yager fuzzy method");

    /* Define the different options as defined in gis.h */
    criteria = G_define_option();	/* Allocates memory for the Option structure and returns a pointer to this memory */
    criteria->key = "criteria";
    criteria->type = TYPE_STRING;
    criteria->required = YES;
    criteria->multiple = YES;
    criteria->gisprompt = "old,cell,raster";
    criteria->description = "Input geographics criteria in evaluation table";

    weight = G_define_option();	/* Allocates memory for the Option structure and returns a pointer to this memory */
    weight->key = "weight";
    weight->type = TYPE_DOUBLE;
    weight->required = YES;
    weight->multiple = YES;
    weight->description = _("Linguistic modifier (w1,w2,..)");

    and = G_define_option();	/* Allocates memory for the Option structure and returns a pointer to this memory */
    and->key = "AND";
    and->type = TYPE_STRING;
    and->required = YES;
    and->gisprompt = "new,cell,raster";
    and->answer = "intersect";
    and->description = "Intersection output map";

    or = G_define_option();	/* Allocates memory for the Option structure and returns a pointer to this memory */
    or->key = "OR";
    or->type = TYPE_STRING;
    or->required = YES;
    or->gisprompt = "new,cell,raster";
    or->answer = "union";
    or->description = "Union output map";

    owa = G_define_option();	/* Allocates memory for the Option structure and returns a pointer to this memory */
    owa->key = "OWA";
    owa->type = TYPE_STRING;
    owa->required = YES;
    owa->gisprompt = "new,cell,raster";
    owa->answer = "OWA";
    owa->description = "OWA output map";

    /* options and flags parser */
    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    G_message("\n\nstart: %s", G_date());	/*write calculation start time */

    /* number of file (=criteria) */
    while (criteria->answers[ncriteria] != NULL)
    {
        ncriteria++;
    }

    /* process the input maps:  stores options and flags to variables */
    /* CRITERIA grid */
    attributes = G_malloc(ncriteria * sizeof(struct input));	/*attributes is input struct defined in top file and store alla criteria files */
    weight_vect = G_malloc(ncriteria * sizeof(double));	/*allocate memory fron vector weight */



    build_weight_vect(nrows, ncols, ncriteria, weight, weight_vect);	/*calcolate weight vector */

    for (i = 0; i < ncriteria; i++)
    {
        struct input *p = &attributes[i];

        p->name = criteria->answers[i];
        p->mapset = G_find_cell2(p->name, "");	/* G_find_cell: Looks for the raster map "name" in the database. */
        if (p->mapset == NULL)	/* returns NULL if the map was not found in any mapset,   mapset name otherwise */
            G_fatal_error(_("Raster file <%s> not found"), p->name);

        if ((p->infd = G_open_cell_old(p->name, p->mapset)) < 0)	/* G_open_cell_old - returns file destriptor (>0) */
            G_fatal_error(_("Unable to open input map <%s> in mapset <%s>"),
                          p->name, p->mapset);

        if (G_get_cellhd(p->name, p->mapset, &cellhd) < 0)	/* controlling, if we can open input raster */
            G_fatal_error(_("Unable to read file header of <%s>"), p->name);

        p->inrast = G_allocate_d_raster_buf();	/* Allocate an array of DCELL based on the number of columns in the current region. Return DCELL   */
    }

    result_and = and->answer;	/* store outputn name in variables */
    result_or = or->answer;
    result_owa = owa->answer;


    if (G_legal_filename(result_and) < 0)	/* check for legal database file names */
        G_fatal_error(_("<%s> is an illegal file name"), result_and);

    if (G_legal_filename(result_or) < 0)	/* check for legal database file names */
        G_fatal_error(_("<%s> is an illegal file name"), result_or);

    if (G_legal_filename(result_owa) < 0)	/* check for legal database file names */
        G_fatal_error(_("<%s> is an illegal file name"), result_owa);

    /*values = G_malloc(ncriteria * sizeof(DCELL)); */

    nrows = G_window_rows();
    ncols = G_window_cols();


    /*memory allocation for-three dimensional matrix */
    decision_vol = G_malloc(nrows * sizeof(double *));
    for (i = 0; i < nrows; ++i)
    {
        decision_vol[i] = G_malloc(ncols * sizeof(double *));
        for (j = 0; j < ncols; ++j)
        {

            decision_vol[i][j] = G_malloc((ncriteria + 3) * sizeof(double));	     /****NOTE: it's storage enven and, or, owa map*/
        }
    }

    /* Allocate output buffer, use  DCELL_TYPE */
    outrast_and = G_allocate_raster_buf(DCELL_TYPE);	/* Allocate memory for a raster map of type DCELL_TYPE. */
    outrast_or = G_allocate_raster_buf(DCELL_TYPE);
    outrast_owa = G_allocate_raster_buf(DCELL_TYPE);

    /* controlling, if we can write the raster */
    if ((outfd_and = G_open_raster_new(result_and, DCELL_TYPE)) < 0)
        G_fatal_error(_("Unable to create raster map <%s>"), result_and);

    if ((outfd_or = G_open_raster_new(result_or, DCELL_TYPE)) < 0)
        G_fatal_error(_("Unable to create raster map <%s>"), result_or);

    if ((outfd_owa = G_open_raster_new(result_owa, DCELL_TYPE)) < 0)
        G_fatal_error(_("Unable to create raster map <%s>"), result_owa);


    /*build a three dimensional matrix for storage all critera maps */
    for (i = 0; i < ncriteria; i++)
    {
        for (row1 = 0; row1 < nrows; row1++)
        {
            G_get_raster_row(attributes[i].infd, attributes[i].inrast, row1, DCELL_TYPE);	/* Reads appropriate information into the buffer buf associated with the requested row */
            /*G_fatal_error(_("Unable to read raster map <%s> row %d"), criteria->answers[i], row); */
            for (col1 = 0; col1 < ncols; col1++)
            {
                /* viene letto il valore di cella e lo si attribuisce ad una variabile di tipo DCELL e poi ad un array */
                DCELL v1 = ((DCELL *) attributes[i].inrast)[col1];

                decision_vol[row1][col1][i] = (double)(v1);
            }
        }
    }
    build_fuzzy_matrix(nrows, ncols, ncriteria, weight_vect, decision_vol);	/*scan all DCELL, make a pairwise comparatione, buil concordance and discordance matrix and relative index */

    for (row1 = 0; row1 < nrows; row1++)
    {
        G_percent(row1, nrows, 2);
        for (col1 = 0; col1 < ncols; col1++)
        {
            ((DCELL *) outrast_and)[col1] =
                (DCELL) decision_vol[row1][col1][ncriteria];
            ((DCELL *) outrast_or)[col1] =
                (DCELL) decision_vol[row1][col1][ncriteria + 1];
            ((DCELL *) outrast_owa)[col1] =
                (DCELL) decision_vol[row1][col1][ncriteria + 2];
        }

        if (G_put_raster_row(outfd_and, outrast_and, DCELL_TYPE) < 0)
            G_fatal_error(_("Failed writing raster map <%s>"), result_and);

        if (G_put_raster_row(outfd_or, outrast_or, DCELL_TYPE) < 0)
            G_fatal_error(_("Failed writing raster map <%s>"), result_or);

        if (G_put_raster_row(outfd_owa, outrast_owa, DCELL_TYPE) < 0)
            G_fatal_error(_("Failed writing raster map <%s>"), result_owa);
    }


    G_message("end: %s, by!", G_date());

    /* memory cleanup */
    for (i = 0; i < ncriteria; i++)
        G_free(attributes[i].inrast);

    G_free(outrast_and);
    G_free(outrast_or);
    G_free(outrast_owa);

    G_free(decision_vol);



    /* closing raster maps */
    for (i = 0; i < ncriteria; i++)
        G_close_cell(attributes[i].infd);

    G_close_cell(outfd_and);
    G_close_cell(outfd_or);
    G_close_cell(outfd_owa);

    /* add command line incantation to history AND file */
    G_short_history(result_and, "raster", &history);
    G_command_history(&history);
    G_write_history(result_and, &history);

    /* add command line incantation to history OR file */
    G_short_history(result_or, "raster", &history);
    G_command_history(&history);
    G_write_history(result_or, &history);

    /* add command line incantation to history OWA file */
    G_short_history(result_owa, "raster", &history);
    G_command_history(&history);
    G_write_history(result_owa, &history);

    exit(EXIT_SUCCESS);
}
