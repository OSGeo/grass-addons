/****************************************************************************
 *
 * MODULE:       r.out.netcdf
 * AUTHOR(S):    Alessandro Frigeri - afrigeri@unipg.it
 *               
 * PURPOSE:      Exports a raster map in a netCDF file.  
 *               Exported map can be imported easly into IBM data Explorer
 *               or Generic Mapping Tools (GMT)
 *
 * COPYRIGHT:    (C) 2003 Alessandro Frigeri for the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *   	    	 License (>=v2). Read the file COPYING that comes with GRASS
 *   	    	 for details.
 *
 * LAST UPDATE:  10th Feb 2003 
 *
 * HISTORY:	 11th Feb 2003  - r.out.necdf is out			
 *
 *	         16th Mar 2003	- support for FCELL and DCELL added
 *****************************************************************************/
 
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <netcdf.h>

#include <grass/gis.h>
#include <grass/glocale.h>

extern CELL  f_c(CELL);
extern FCELL f_f(FCELL);
extern DCELL f_d(DCELL);

/* Stuff to make calculation on the raster values */

CELL c_calc(CELL x)
{
  return x;
}

FCELL f_calc(FCELL x)
{
  return x;
}

DCELL d_calc(DCELL x)
{
  return x;
}

int
main(int argc, char *argv[])
{
	struct Cell_head cellhd;
	struct Cell_head region;
	char *name, *result, *mapset;
	void *inrast;
	unsigned char *outrast;
	int nrows, ncols;
	int row,col;
	int infd;
	int dx,gmt;
	RASTER_MAP_TYPE data_type;
	struct GModule *module;
	struct Option *input, *output;
	struct Flag *flag1, *flag2;

	/* netcdf stuff */
	int ncols_dim,nrows_dim,naxes_dim,height_id,ndeltas_dim;
	int errnc,ncID,zid,xrangeid,yrangeid,zrangeid,spacingid,dimensionid;
	int fieldid,fielddimid;
	int locations_id;
	char title1[NC_MAX_NAME]="GRASS GIS raster map",history[NC_MAX_NAME];
	static char title[] = "netCDF output from GRASS GIS";
	static char remark[] = "netCDF output from GRASS GIS";
	static char degrees[] = "degrees";
	static char meter[] = "Meter";
	static float scale_factor[]={1};
	static int add_offset[]={0};
	static int node_offset[]={1};
	int sideid,xysizeid;
	static size_t a[] = {0};
	static size_t b[] = {1};
	int xysize;
	int vali;
	float valf;
	double vald;
	size_t zstart[1];
	size_t zcount[1];
	double fmin,fmax;
	double domin,domax;
	int dmin,dmax;	
	struct FPRange fprange;
	struct Range range;
	float longitude,latitude;	

	
	int locations_dims[2];
	
	int height_dims[2];
			
	static size_t index_height[]={0,0};
	static size_t index_locations[]={0,0};

	double ns;
	
	G_gisinit(argv[0]);

	module = G_define_module();
	module->description =
		_("GRASS module for exporting netCDF data");
					        
	/* Define options */

	input = G_define_standard_option(G_OPT_R_INPUT);

	output = G_define_standard_option(G_OPT_R_OUTPUT);
	output->gisprompt = "new_file,file,output";
	output->description= "File name for new netCDF file";

	/* Define the different flags */		
	flag1 = G_define_flag() ;
	flag1->key         = 'd' ;
	flag1->description = _("OpenDX output") ;
	
	flag2 = G_define_flag() ;
	flag2->key         = 'g' ;
	flag2->description = _("GMT output") ;
	
	if (G_parser(argc, argv))
		exit (EXIT_FAILURE);
		
	name    = input->answer;
	result  = output->answer;
	dx = flag1->answer;
	gmt = flag2->answer;

	/* find map in mapset */
	mapset = G_find_cell2 (name, "");
        if (mapset == NULL)
                G_fatal_error ("cell file [%s] not found", name);

        if (G_legal_filename (result) < 0)
                G_fatal_error ("[%s] is an illegal name", result); 

	/* determine the inputmap type (CELL/FCELL/DCELL) */
	data_type = G_raster_map_type(name, mapset);

	if ( (infd = G_open_cell_old (name, mapset)) < 0)
		G_fatal_error ("Cannot open cell file [%s]", name);

	if (G_get_cellhd (name, mapset, &cellhd) < 0)
		G_fatal_error ("Cannot read file header of [%s]", name);

	/* Allocate input buffer */
	inrast = G_allocate_raster_buf(data_type);
	
	/* Allocate output buffer, use input map data_type */
	
	nrows = G_window_rows();
	ncols = G_window_cols();
	outrast = G_allocate_raster_buf(data_type);

	/* Get window boundaries */ 
	G_get_window(&region);
	
	/* Create the new netCDF file */
	
	errnc = nc_create(result, NC_WRITE, &ncID);
  	if (errnc == NC_EEXIST)
    		printf("Couldn't create NC file %s, NC file with that name already exists\n",result);
	
	
	
	/* Dimensions: xysize, side */ 
	ncols=region.cols;
	nrows=region.rows;
	
	xysize=ncols*nrows;
	
	if(gmt){	
	nc_def_dim(ncID, "xysize", xysize, &xysizeid);
	nc_def_dim(ncID, "side", 2, &sideid);
	nc_def_var(ncID, "x_range", NC_DOUBLE,1, &sideid,&xrangeid);
	nc_put_att_text(ncID, xrangeid, "units",strlen(degrees), degrees);
	nc_def_var(ncID, "y_range", NC_DOUBLE,1, &sideid,&yrangeid);
	nc_put_att_text(ncID, yrangeid, "units",strlen(degrees), degrees);
	nc_def_var(ncID, "z_range", NC_DOUBLE,1, &sideid,&zrangeid);
	nc_put_att_text(ncID, zrangeid, "units",strlen(meter), meter);
	nc_def_var(ncID, "spacing", NC_DOUBLE,1, &sideid,&spacingid);
	nc_def_var(ncID, "dimension", NC_INT,1, &sideid,&dimensionid);
	
	switch (data_type)
			{
			case CELL_TYPE:	
				nc_def_var(ncID, "z", NC_INT,1, &xysizeid,&zid);
				break;
			case FCELL_TYPE:
				nc_def_var(ncID, "z", NC_FLOAT,1, &xysizeid,&zid);
				break;
			case DCELL_TYPE:	
				nc_def_var(ncID, "z", NC_DOUBLE,1, &xysizeid,&zid);
				break;
			}
				
	scale_factor[0]=1;
	
	nc_put_att_text(ncID, NC_GLOBAL, "title",strlen(title), title);
	nc_put_att_text(ncID, NC_GLOBAL, "source",strlen(title), title);
	nc_put_att_text(ncID, zid, "long_name",strlen(title), title);
	nc_put_att_float(ncID, zid, "scale_factor",NC_FLOAT,1, scale_factor);
	nc_put_att_int(ncID, zid, "add_offset",NC_INT,1, add_offset);
	nc_put_att_int(ncID, zid, "node_offset",NC_INT,1, node_offset);
	}

	if(dx){
	nc_def_dim(ncID, "lon", ncols , &ncols_dim); 
	nc_def_dim(ncID, "lat", nrows , &nrows_dim);
	nc_def_dim(ncID, "naxes",2, &naxes_dim);
	nc_def_dim(ncID, "ndeltas",2, &ndeltas_dim);
	
    	locations_dims[0]=naxes_dim;
	locations_dims[1]=ndeltas_dim;
	nc_def_var(ncID, "locations",NC_FLOAT,2,locations_dims,&locations_id);
	
	height_dims[0]=ncols_dim;
	height_dims[1]=nrows_dim;
	
	switch (data_type)
			{
			case CELL_TYPE:	
				nc_def_var(ncID, "height",NC_INT,2,height_dims,&height_id);
				break;
			case FCELL_TYPE:
				nc_def_var(ncID, "height",NC_FLOAT,2,height_dims,&height_id);
				break;
			case DCELL_TYPE:	
				nc_def_var(ncID, "height",NC_DOUBLE,2,height_dims,&height_id);
				break;
			}
	
	
	nc_put_att_text(ncID, height_id, "field",14,"height, scalar");
	nc_put_att_text(ncID, height_id, "positions",18,"locations, regular");
	
	}
	nc_enddef(ncID);
	
	if(gmt){
	nc_put_var1_double(ncID,xrangeid,a,&region.west);
	nc_put_var1_double(ncID,xrangeid,b,&region.east);
	nc_put_var1_double(ncID,yrangeid,a,&region.south);
	nc_put_var1_double(ncID,yrangeid,b,&region.north);
	nc_put_var1_double(ncID,spacingid,a,&region.ew_res);
	nc_put_var1_double(ncID,spacingid,b,&region.ns_res);	
	nc_put_var1_int(ncID,dimensionid,a,&ncols);
	nc_put_var1_int(ncID,dimensionid,b,&nrows);
	}	
	
	if(dx){
	
	index_locations[0]=0;
	index_locations[1]=0;
	nc_put_var1_double(ncID,locations_id,index_locations,&region.west);
	index_locations[0]=0;
	index_locations[1]=1;
	nc_put_var1_double(ncID,locations_id,index_locations,&region.ew_res);
	
	index_locations[0]=1;
	index_locations[1]=0;
	nc_put_var1_double(ncID,locations_id,index_locations,&region.north);
	index_locations[0]=1;
	index_locations[1]=1;
	ns=-region.ns_res;
	nc_put_var1_double(ncID,locations_id,index_locations,&ns);
	
	}
        		
	
	for (row = 0; row < nrows; row++)
	{
		CELL c;
		FCELL f;
		DCELL d;

		G_percent (row, nrows, 2);
		
		/* read input map */
		if (G_get_raster_row (infd, inrast, row, data_type) < 0)
			G_fatal_error (_("Could not read from <%s>"),name);
		
		
		/*  put the NetCDF data 
		    CELL  -> int
		    FCELL -> float
		    DCELL -> double
		*/
		for (col=0; col < ncols; col++)
		{
			longitude=region.west+col*region.ew_res;
			latitude=region.south+row*region.ns_res;
			index_height[0]=col;
			index_height[1]=row;
				
			switch (data_type)
			{
			case CELL_TYPE:
				c = ((CELL *) inrast)[col];
				c = c_calc(c);			/* calculate */
				zstart[0]=col+(row*ncols);	/* position  */
				zcount[0]=1;		 	/* extension */
							
				vali=c;
				if(gmt){
				nc_put_vara_int(ncID,zid,zstart,zcount,&vali);
				}
				if(dx){																
				nc_put_var1_int(ncID,height_id,index_height,&vali);
				}												
				break;
			case FCELL_TYPE:
				f = ((FCELL *) inrast)[col];
				f = f_calc(f); 			/* calculate */
				zstart[0]=col+(row*ncols);	/* position  */
				zcount[0]=1;			/* extension */
				valf=f;
				if(gmt){
				nc_put_vara_float(ncID,zid,zstart,zcount,&valf);
				}
				if(dx){																
				nc_put_var1_float(ncID,height_id,index_height,&valf);
				}
				break;
			case DCELL_TYPE:
				d = ((DCELL *) inrast)[col];
				d = d_calc(d); 			/* calculate */
				zstart[0]=col+(row*ncols);	/* position  */
				zcount[0]=1;			/* extension */
				vald=d;
				if(gmt){
				nc_put_vara_double(ncID,zid,zstart,zcount,&vald);
				}
				if(dx){																
				nc_put_var1_double(ncID,height_id,index_height,&vald);
				}
				break;
			}
		}

	}


	if(gmt)
	{
	switch(data_type)	
	{
		case CELL_TYPE:
			G_read_range(name, mapset, &range);
      			G_get_range_min_max(&range, &dmin, &dmax);
			nc_put_var1_int(ncID,zrangeid,a,&dmin);
			nc_put_var1_int(ncID,zrangeid,b,&dmax);
		case FCELL_TYPE:
			G_read_fp_range(name, mapset, &fprange);
      			G_get_fp_range_min_max(&fprange, &fmin, &fmax);
			nc_put_var1_double(ncID,zrangeid,a,&fmin);
			nc_put_var1_double(ncID,zrangeid,b,&fmax);
		case DCELL_TYPE:
			G_read_fp_range(name, mapset, &fprange);
      			G_get_fp_range_min_max(&fprange, &domin, &domax);
			nc_put_var1_double(ncID,zrangeid,a,&domin);
		        nc_put_var1_double(ncID,zrangeid,b,&domax);
	}

	}
		
	/* Close the netcdf file */	
	nc_close(ncID);

	G_free(inrast);
	G_close_cell (infd);
	
	exit(EXIT_SUCCESS);
}
