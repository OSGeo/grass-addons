/****************************************************************************
 *
 * MODULE:       r.roughset
 * AUTHOR(S):    GRASS module authors ad Rough Set Library (RSL) maintain:
 *					G.Massei (g_massa@libero.it)-A.Boggia (boggia@unipg.it)		
 *				 Rough Set Library (RSL) ver. 2 original develop:
 *		         	M.Gawrys - J.Sienkiewicz 
 *
 * PURPOSE:      Geographics rough set analisys and knowledge discovery 
 *
 * COPYRIGHT:    (C) GRASS Development Team (2008)
 *
 *               This program is free software under the GNU General Public
 *   	    	 License (>=v2). Read the file COPYING that comes with GRASS
 *   	    	 for details.
 *
 *****************************************************************************/

#include "localproto.h"


void rough_sel_library_out(int nrows, int ncols, int nattribute, struct input *attributes, char *fileOutput);


int main(int argc, char *argv[])
{
    struct Cell_head cellhd;		/* it stores region information, and header of rasters */
    char *mapset;			/* mapset name */
    int i,j, nattribute;	/* index and  files number*/
    int nrows, ncols;
    int strgy;			/* strategy rules extraction index*/

    RASTER_MAP_TYPE data_type;	/* type of the map (CELL/DCELL/...) */
    /*int value, decvalue;*/	/*single attribute and decision value*/

    struct input *attributes;
    struct History history;	/* holds meta-data (title, comments,..) */

    struct GModule *module;	/* GRASS module for parsing arguments */

    struct Option *attribute, *decision, *strategy, *output;	/* options */
    /*struct Flag *flagQuiet		flags */

    /* initialize GIS environment */
    G_gisinit(argv[0]);		/* reads grass env, stores program name to G_program_name() */

    /* initialize module */
    module = G_define_module();
    module->keywords = _("raster,geographics knowledge discovery");
    module->description = _("Rough set based geographics knowledg ");


    /* Define the different options as defined in gis.h */
    attribute = G_define_option() ;
    attribute->key        = "attributes";
    attribute->type       = TYPE_STRING;
    attribute->required   = YES;
    attribute->multiple   = YES;
    attribute->gisprompt  = "old,cell,raster" ;
    attribute->description = "Input geographics attributes in information system";

    decision = G_define_option() ;
    decision->key        = "decision";
    decision->type       = TYPE_STRING;
    decision->required   = YES;
    decision->gisprompt  = "old,cell,raster" ;
    decision->description = "Input geographics decision in information system";

    strategy = G_define_option() ;
    strategy->key        = "strategy";
    strategy->type       = TYPE_STRING;
    strategy->required   = YES;
    strategy->options	 = "Very fast,Fast,Medium,Best,All,Low,Upp,Normal";
    strategy->description = "Choose strategy for generating rules";

    output = G_define_option();
    output->key = "InfoSys";
    output->type = TYPE_STRING;
    output->required = YES;
    output->gisprompt = "new_file,file,output";
    output->answer ="InfoSys";
    output->description = "Output information system file";


    /* options and flags parser */
    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);



/***********************************************************************/
/********Prepare and controlling Information System files **************/
/***********************************************************************/

       /* number of file (=attributes) */
    nattribute=0;
    while (attribute->answers[nattribute]!=NULL)
    	{
    		nattribute++;
    	}


/*Convert strategy answer in index.  strcmp return 0 if answer is the passed string*/
    if(strcmp(strategy->answer,"Very fast")==0)
    	strgy=0;
    else if(strcmp(strategy->answer,"Fast")==0)
    	strgy=1;
    else if(strcmp(strategy->answer,"Medium")==0)
    	strgy=2;
    else if(strcmp(strategy->answer,"Best")==0)
    	strgy=3;
    else if(strcmp(strategy->answer,"All")==0)
    	strgy=4;
    else if(strcmp(strategy->answer,"Low")==0)
    	strgy=5;
    else if(strcmp(strategy->answer,"Upp")==0)
    	strgy=6;
    else
    	strgy=7;

    G_message("choose:%d,%s",strgy,strategy->answer);


    /* process the input maps:*/
    /* ATTRIBUTES grid */
    attributes = G_malloc((nattribute+1) * sizeof(struct input)); /*attributes is input struct defined in localproto.h*/

	for (i = 0; i < nattribute; i++)
	{
		struct input *p = &attributes[i];
		p->name = attribute->answers[i];
		p->mapset = G_find_cell(p->name,""); /* G_find_cell: Looks for the raster map "name" in the database. */
		if (!p->mapset)
			G_fatal_error(_("Raster file <%s> not found"), p->name);
		p->fd = G_open_cell_old(p->name, p->mapset);
		if (p->fd < 0)
			G_fatal_error(_("Unable to open input map <%s> in mapset <%s>"),p->name, p->mapset);
		p->buf = G_allocate_d_raster_buf(); /* Allocate an array of DCELL based on the number of columns in the current region. Return DCELL *  */
	}

   /* DECISION grid (at last column in Information System matrix) */
		struct input *p = &attributes[nattribute];
		p->name = decision->answer;
		p->mapset = G_find_cell(p->name,""); /* G_find_cell: Looks for the raster map "name" in the database. */
		if (!p->mapset)
			G_fatal_error(_("Raster file <%s> not found"), p->name);
		p->fd = G_open_cell_old(p->name, p->mapset);/*opens the raster file name in mapset for reading. A nonnegative file descriptor is returned if the open is successful.*/
		if (p->fd < 0)
			G_fatal_error(_("Unable to open input map <%s> in mapset <%s>"),p->name, p->mapset);
		p->buf = G_allocate_d_raster_buf(); /* Allocate an array of DCELL based on the number of columns in the current region. Return DCELL *  */


	nrows = G_window_rows();
	ncols = G_window_cols();

	rough_sel_library_out(nrows, ncols, nattribute, attributes, output->answer);/*build RSL standard file*/
	RulsExtraction(output->answer,attributes,strgy); /* extract rules from RSL*/

	exit(EXIT_SUCCESS);
}


void rough_sel_library_out(int nrows, int ncols, int nattribute, struct input *attributes, char *fileOutput)

{
	int row, col, i, j;
	int value, decvalue;
	int nobject;
	char cell_buf[300];
	FILE *fp;			/*file pointer for ASCII output*/

	/* open *.sys file for writing or use stdout */
        if(NULL == (fp = fopen(fileOutput, "w")))
        	G_fatal_error("Not able to open file [%s]",fileOutput);

       	fprintf(fp,"NAME: %s\nATTRIBUTES: %d\nOBJECTS: %s\n",fileOutput,nattribute+1,"      ");

	/************** process the data *************/

	nobject=0;

	fprintf (stderr, _("Percent complete ... "));

	for (row = 0; row < nrows; row++)
		{
			G_percent(row, nrows, 2);
			for(i=0;i<=nattribute;i++)
				{
					G_get_d_raster_row (attributes[i].fd, attributes[i].buf, row);/* Reads appropriate information into the buffer buf associated with the requested row*/
				}
				for (col=0;col<ncols;col++)
					{	/*make a cast on the DCELL output value*/
						decvalue=(int)attributes[nattribute].buf[col];
						if(0<decvalue)
						{
							for(j=0;j<nattribute;j++)
							{	/*make a cast on the DCELL output value*/
								value = (int)(attributes[j].buf[col]);
								sprintf(cell_buf, "%d",value);
			      					G_trim_decimal (cell_buf);
			      					fprintf (fp,"%s ",cell_buf);
			      				}
			      				fprintf(fp,"%d \n",decvalue);
			      				nobject++;
			      			}
					}
		}
	/************** write code file*************/

	for(i=0;i<=nattribute;i++)
	{
		fprintf(fp,"\n%s",attributes[i].name);
	}

	/************** write header file*************/

	if(0<fseek(fp,0L,0)) /*move file pointer to header file*/
		G_fatal_error("Not able to write file [%s]",fileOutput);
	else
		fprintf(fp,"NAME: %s\nATTRIBUTES: %d\nOBJECTS: %d\n",fileOutput,nattribute+1,nobject);

	/************** close all and exit ***********/

	for (i = 0; i<=nattribute; i++)
		G_close_cell(attributes[i].fd);

	fclose(fp);
	G_percent(row, nrows, 2);

}





