
/****************************************************************************
 *
 * MODULE:       r.roughset
 * AUTHOR(S):    GRASS module authors ad Rough Set Library (RSL) maintain:
 *		 		G.Massei (g_massa@libero.it)-A.Boggia (boggia@unipg.it)
 *		 		Rough Set Library (RSL) ver. 2 original develop:
 *		 		M.Gawrys - J.Sienkiewicz
 *
 * PURPOSE:      Geographics rough set analisys and knowledge discovery
 *
 * COPYRIGHT:    (C) A.Boggia - G.Massei (2008)
 *
 *               This program is free software under the GNU General Public
 *   	    	 License (>=v2). Read the file COPYING that comes with GRASS
 *   	    	 for details.
 *
 *****************************************************************************/

#include "localproto.h"


int main(int argc, char *argv[])
{
    struct Cell_head cellhd;	/* it stores region information, and header of rasters */
    char *mapset;		/* mapset name */
    int i, j;			/* index and  files number */
    int row, col, nrows, ncols;
    int nattributes;		/*attributes numer */
    int strgy, cls;		/* strategy rules extraction and classifiy index */

    char *result;		/* output raster name */
    int *classify_vect;		/* matrix for classified value storage */
    int outfd;			/* output file descriptor */
    unsigned char *outrast;	/* output buffer */

    RASTER_MAP_TYPE data_type;	/* type of the map (CELL/DCELL/...) */

    /*int value, decvalue; *//*single attribute and decision value */

    struct input *attributes;
    struct History history;	/* holds meta-data (title, comments,..) */

    struct GModule *module;	/* GRASS module for parsing arguments */

    struct Option *attr_map, *dec_map, *dec_txt, *genrules, *clssfy, *output_txt, *output_map;	/* options */

    /*struct Flag *flagQuiet            flags */

    /* initialize GIS environment */
    G_gisinit(argv[0]);		/* reads grass env, stores program name to G_program_name() */

    /* initialize module */
    module = G_define_module();
    module->keywords = _("raster,geographics knowledge discovery");
    module->description = _("Rough set based geographics knowledge ");


    /* Define the different options as defined in gis.h */
    attr_map = G_define_option();	/* Allocates memory for the Option structure and returns a pointer to this memory */
    attr_map->key = "attributes";
    attr_map->type = TYPE_STRING;
    attr_map->required = YES;
    attr_map->multiple = YES;
    attr_map->gisprompt = "old,cell,raster";
    attr_map->description =
        _("Input geographics ATTRIBUTES in information system");

    dec_map = G_define_option();
    dec_map->key = "decision";
    dec_map->type = TYPE_STRING;
    dec_map->required = NO;
    dec_map->gisprompt = "old,cell,raster";
    dec_map->description =
        _("Input geographics DECISION in information system");

    genrules = G_define_option();
    genrules->key = "strgy";
    genrules->type = TYPE_STRING;
    genrules->required = YES;
    genrules->options = "Very fast,Fast,Medium,Best,All,Low,Upp,Normal";
    genrules->answer = "Very fast";
    genrules->description = _("Strategies for generating rules");

    dec_txt = G_define_option();
    dec_txt->key = "sample";
    dec_txt->type = TYPE_STRING;
    dec_txt->required = NO;
    dec_txt->gisprompt = "old_file,file,input";
    dec_txt->description =
        _("Input text file  with  data and decision sample");

    clssfy = G_define_option();
    clssfy->key = "clssfy";
    clssfy->type = TYPE_STRING;
    clssfy->required = YES;
    clssfy->options = "Classify1,Classify2,Classify3";
    clssfy->answer = "Classify1";
    clssfy->description =
        _("Strategies for classified map (conflict resolution)");

    output_txt = G_define_option();
    output_txt->key = "outTXT";
    output_txt->type = TYPE_STRING;
    output_txt->required = YES;
    // output_txt->gisprompt = "new_file,file,output";
    output_txt->answer = "InfoSys";
    output_txt->description = _("Output information system file");

    output_map = G_define_option();
    output_map->key = "outMAP";
    output_map->type = TYPE_STRING;
    output_map->required = YES;
    output_map->answer = "classify";
    output_map->description = _("Output classified map");


    /* options and flags parser */
    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    /* Either decision map or sample file are necesary */
    if (dec_map->answer == NULL && dec_txt->answer == NULL)
        G_fatal_error(_("Either decision map or sample file are necessary!"));

    /***********************************************************************/

    /********Prepare and controlling Information System files **************/

    /***********************************************************************/

    /* number of file (=attributes) */
    nattributes = 0;
    while (attr_map->answers[nattributes] != NULL)
    {
        nattributes++;
    }

    /* store output classified MAP name in variable */
    result = output_map->answer;

    /*Convert strategy rules extraction answer in index.  strcmp return 0 if answer is the passed string */
    if (strcmp(genrules->answer, "Very fast") == 0)
        strgy = 0;
    else if (strcmp(genrules->answer, "Fast") == 0)
        strgy = 1;
    else if (strcmp(genrules->answer, "Medium") == 0)
        strgy = 2;
    else if (strcmp(genrules->answer, "Best") == 0)
        strgy = 3;
    else if (strcmp(genrules->answer, "All") == 0)
        strgy = 4;
    else if (strcmp(genrules->answer, "Low") == 0)
        strgy = 5;
    else if (strcmp(genrules->answer, "Upp") == 0)
        strgy = 6;
    else
        strgy = 7;

    /*Convert strategy map lassify answer in index.  strcmp return 0 if answer is the passed string */

    if (strcmp(clssfy->answer, "Classify1") == 0)
        cls = 0;
    else if (strcmp(clssfy->answer, "Classify2") == 0)
        cls = 1;
    else if (strcmp(clssfy->answer, "Classify3") == 0)
        cls = 2;
    else
        cls = 0;


    /* process the input maps: */
    /* ATTRIBUTES grid */
    attributes = G_malloc((nattributes + 1) * sizeof(struct input));	/*attributes is input struct defined in localproto.h */

    for (i = 0; i < nattributes; i++)
    {
        struct input *p = &attributes[i];

        p->name = attr_map->answers[i];
        p->mapset = G_find_cell(p->name, "");	/* G_find_cell: Looks for the raster map "name" in the database. */

        p->fd = G_open_cell_old(p->name, p->mapset);

        if (!p->mapset)
            G_fatal_error(_("Raster file <%s> not found"), p->name);

        if (p->fd < 0)
            G_fatal_error(_("Unable to open input map <%s> in mapset <%s>"),
                          p->name, p->mapset);

        if (CELL_TYPE != G_raster_map_type(p->name, p->mapset))
            G_fatal_error(_("Input map <%s> in mapset <%s> isn't CELL type"),
                          p->name, p->mapset);

        p->buf = G_allocate_c_raster_buf();	/* Allocate an array of CELL based on the number of columns in the current region. Return DCELL *  */

    }


    /* define the inputmap DECISION type (CELL) */
    data_type = CELL_TYPE;	//
    /* Allocate output buffer, use input map data_type */
    nrows = G_window_rows();
    ncols = G_window_cols();
    outrast = G_allocate_raster_buf(data_type);


    /* DECISION grid (at last column in Information System matrix) */
    if (dec_map->answer != NULL)
    {
        struct input *p = &attributes[nattributes];

        p->name = dec_map->answer;
        p->mapset = G_find_cell(p->name, "");	/* G_find_cell: Looks for the raster map "name" in the database. */
        if (!p->mapset)
            G_fatal_error(_("Raster file <%s> not found"), p->name);
        p->fd = G_open_cell_old(p->name, p->mapset);	/*opens the raster file name in mapset for reading. A nonnegative file descriptor is returned if the open is successful. */
        if (p->fd < 0)
            G_fatal_error(_("Unable to open input map <%s> in mapset <%s>"),
                          p->name, p->mapset);
        p->buf = G_allocate_raster_buf(data_type);	/* Allocate an array of DCELL based on the number of columns in the current region.
							   Return DCELL *  */
        rough_set_library_out(nrows, ncols, nattributes, attributes, output_txt->answer);	/*build RSL standard file */
    }


    classify_vect = G_malloc(sizeof(int) * (nrows * ncols));	/* memory allocation */

    rough_analysis(nrows, ncols, output_txt->answer, classify_vect, attributes, dec_txt->answer, strgy, cls);	/* extract rules from RSL and generate classified vector */

    /* controlling, if we can write the raster */
    if ((outfd = G_open_raster_new(result, CELL_TYPE)) < 0)
        G_fatal_error(_("Unable to create raster map <%s>"), result);

    /* generate classified map */
    G_message("Building calssified map...");
    j = 0;			/* builder map index */
    for (row = 0; row < nrows; row++)
    {
        CELL c;

        G_percent(row, nrows, 2);
        for (col = 0; col < ncols; col++)
        {
            c = ((CELL *) classify_vect[j]);
            ((CELL *) outrast)[col] = c;
	    G_message("%d", c);
            j++;
        }

        if (G_put_raster_row(outfd, outrast, data_type) < 0)
            G_fatal_error(_("Failed writing raster map <%s>"), result);
    }


    /* memory cleanup */
    for (i = 0; i <= nattributes; i++)
        G_close_cell(attributes[i].fd);
    G_close_cell(outfd);

    for (i = 0; i < nattributes; i++)
        G_free(attributes[i].buf);

    //G_free(outrast);

    G_message("End: %s, with %d cells.", G_date(), j);
    /* add command line incantation to history file */
    G_short_history(result, "raster", &history);
    G_command_history(&history);
    G_write_history(result, &history);

    exit(EXIT_SUCCESS);
}

/* dom 07 dic 2008 07:05:15 CET */
