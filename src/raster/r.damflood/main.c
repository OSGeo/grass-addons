/*****************************************************************************
*
* MODULE:	r.damflood
*
* AUTHOR:	Roberto Marzocchi - roberto.marzocchi[]supsi.ch (2008)
*		Massimiliano Cannata - massimiliano.cannata[]supsi.ch (2008)
*
* PURPOSE:	Estimate the area potentially inundated in case of dam breaking
*
*
* COPYRIGHT:	(C) 2008 by Istituto Scienze della Terra-SUPSI
*
*		This program is free software under the GNU General Public
*		Licence (>=2). Read the file COPYING that cames with GRASS
*		for details.
*
***************************************************************************/



/* libraries*/
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include <grass/config.h>
#include <math.h>
#include <grass/gmath.h>
#include <grass/dbmi.h>
#include <grass/linkm.h>
#include <grass/bitmap.h>
/* function here defined */
#include "SWE.h" /*function that solves the shallow water equations*/

//#include <grass/interpf.h>




/* simple functions*/
#define min(A,B) ((A) < (B) ? (A):(B))
#define max(A,B) ((A) > (B) ? (A):(B))
#define min4(A,B,C,D) min(min(A,B),min(C,D))
#define max4(A,B,C,D) max(max(A,B),max(C,D))

#define ALLOC_DIM 10000
#define PI 3.14159265
#define g 9.81


//#define hmin 0.01
/* lo calcolo dopo in funzione della velocita' massima 
   (Calculated later as a function of maximum velocity)
#define timestep 0.1 */

/* 
 * global function declaration 

extern CELL f_c(CELL);
extern FCELL f_f(FCELL);
extern DCELL f_d(DCELL);

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
 */


int **G_alloc_imatrix(int rows, int cols)
{
	int **mmm;
   int i;
   mmm = (int **)G_calloc(rows, sizeof(int *));
	mmm[0] = (int *)G_calloc(rows * cols, sizeof(int));
	for (i = 1; i < rows; i++)
		mmm[i] = mmm[i - 1] + cols;
 	return mmm;
}

void G_free_imatrix(int **mmm)
{
	G_free(mmm[0]);
	G_free(mmm);
	mmm = NULL;
	return;
}


float **G_alloc_fmatrix(int rows, int cols)
{
	float **m;
   int i;
   m = (float **)G_calloc(rows, sizeof(float *));
	m[0] = (float *)G_calloc(rows * cols, sizeof(float));
	for (i = 1; i < rows; i++)
		m[i] = m[i - 1] + cols;
 	return m;
}

void G_free_fmatrix(float **m)
{
	G_free(m[0]);
	G_free(m);
	m = NULL;
	return;
}

double *G_alloc_vector(size_t n)
{
	return (double *)G_calloc(n, sizeof(double));
}


double **G_alloc_dmatrix(int rows, int cols)
{
	double **mm;
	int i;

	mm = (double **)G_calloc(rows, sizeof(double *));
	mm[0] = (double *)G_calloc(rows * cols, sizeof(double));
	for (i = 1; i < rows; i++)
	mm[i] = mm[i - 1] + cols;

	return mm;
}

void G_free_dmatrix(double **mm)
{
	G_free(mm[0]);
	G_free(mm);
	mm = NULL;
 	return;
}

void G_free_vector(double *v)
{
	G_free(v);
	v = NULL;
	return;
}


//*********************************************************************************************
/* main program */
int main(int argc, char *argv[]){

  /* typedef struct
  {
    double sx, sy, sz, dir;
  } startpt;

  startpt *a_start,*tmp_start;*/
  struct Cell_head cellhd; /* it stores region information and header information of rasters */
  struct Cell_head window;
  //struct History history;  /* holds metadata */

  /* input-output raster file descriptor */
  int infd_ELEV,infd_LAKE,infd_DAMBREAK, infd_MANNING, infd_U, infd_V;
  int outfd_H,outfd_VEL,outfd_VEL_DIR,outfd_HMAX,outfd_T_HMAX,outfd_I_HMAX;
  int outfd_VMAX,outfd_T_VMAX,outfd_I_VMAX,outfd_DIR_VMAX,outfd_IMAX,outfd_T_IMAX,outfd_WAVEFRONT;
  //float g=9.81; define iniziale!
  
  /* mapset name locator */
  char *mapset_ELEV,*mapset_LAKE,*mapset_DAMBREAK,*mapset_MANNING,*mapset_U,*mapset_V;

  /* buffer for input-output raster */
  FCELL *inrast_ELEV;			/* elevation map [m]*/
  DCELL *inrast_LAKE;			/* water elevation in the map [m]*/
  FCELL *inrast_DAMBREAK;		/* break in the dam*/
  FCELL *inrast_MANNING;		/* manning*/
  DCELL *inrast_U;
  DCELL *inrast_V;
  DCELL *outrast_VEL;		   /* velocity [m/s] */
  DCELL *outrast_VEL_DIR;
  DCELL *outrast_H;	         /* water elevation output [m]*/
  DCELL *outrast_HMAX;
  DCELL *outrast_I_HMAX;
  DCELL *outrast_T_HMAX;
  DCELL *outrast_VMAX;
  DCELL *outrast_I_VMAX;
  DCELL *outrast_T_VMAX;
  DCELL *outrast_DIR_VMAX;
  DCELL *outrast_IMAX;
  DCELL *outrast_T_IMAX;
  DCELL *outrast_WAVEFRONT;
  /* cell counters */
  int nrows, ncols;
  int row, col;
  int num_cell, num_break;
  int method;
  int reg_lim=0, warn1=0;
  float Q=0.0, vol_res,fall, volume=0.0;
  float res_ew ,res_ns;

  /* memory matrix */
  double **m_h1, **m_h2, **m_u1, **m_u2, **m_v1, **m_v2;
  float **m_z, **m_DAMBREAK, **m_m;
  float **m_hmax, **m_t_hmax, **m_i_hmax, **m_vmax, **m_t_vmax, **m_i_vmax, **m_dir_vmax, **m_imax, **m_t_imax, **m_wavefront;
  int ** m_lake;
  /*  other variables  */
  double water_elevation, profondita_soglia;
  double hmin=0.1;
  int pippo;
  int temp_i;
  double temp_d, v_tot;

  int m=1, M=1;
  int i, i_cont;
  double vel_0=0.0, vel_max=0.0, t;
  /**********************************************************************************/
  // Parameters for the optimization of timestep using the CFL stability condition
  float timestep, velocity;
  float timestep_ct, timestep_ct_temp;
  /**********************************************************************************/
  int DELTAT, TSTOP;
  char name1[20],name2[20],name3[20],name4[20],name5[20],name6[20],name7[20],name8[20],name9[20];
  int tmp_int;
  char tmp[15];
  /********************/
  // optional instants//
  int ntimes, pp;
  double *times;
  double opt_t, time;
  /********************/

  /* variables to handle user inputs and outputs */
  char *ELEV, *LAKE, *DAMBREAK, *MANNING, *U, *V, *OUT_VEL, *OUT_H, *OUT_HMAX, *OUT_VMAX, *OUT_IMAX, *OUT_WAVEFRONT;


  /***********************************************************************************************************************/
  /* GRASS structure */
  struct GModule *module;
  struct Option *input_ELEV, *input_LAKE, *input_DAMBREAK,*input_MANNING, *input_DELTAT, *input_TSTOP, *input_TIMESTEP, *input_U, *input_V;
  struct
    {
	struct Option *opt_t;
    }
    parm;
  struct Option *output_VEL,*output_H,*output_HMAX, *output_VMAX, *output_IMAX, *output_WAVEFRONT;
  struct Flag *flag_d;
  struct {
		struct Option *met;
	} opt;
 /* initialize GRASS */
  G_gisinit(argv[0]);

  //pgm_name = argv[0];

  module = G_define_module();
  G_add_keyword(_("raster"));
  G_add_keyword(_("dambreak")); 
  G_add_keyword(_("model"));
  module->description = _("Estimate the area potentially inundated in case of dam break");

  //OPTIONS

  flag_d = G_define_flag();
  flag_d->key = 'd';
  flag_d->description = _("Flow direction additional output (aspect visualization)");
  //flag_d ->guisection  = _("Options");

  opt.met = G_define_option();
  opt.met->key = "method";
  opt.met->type = TYPE_STRING;
  opt.met->required = NO;
  opt.met->description = _("Computational method for initial velocity estimation");
  opt.met->options = "dambreak-without_hypotesis,uniform drop in of lake,small dam breach";
  opt.met->answer = "dambreak-without_hypotesis";
  //opt.met->guisection  = _("Options");

  /* LEGENDA
  total_dambreak-without_hypotesis = nessuna ipotesi sulla velocita' iniziale
  total_dambreak = Hp altezza critica --> velocita' iniziale (h critica) = 0.93*sqrt(h);
  small_dam_breach = Hp stramazzo --> velocita' iniziale = 0.4*sqrt(2*g*h)
  */

  input_TIMESTEP = G_define_option();
  input_TIMESTEP->key	= "timestep";
  input_TIMESTEP->type = TYPE_DOUBLE;
  input_TIMESTEP->required = NO;
  input_TIMESTEP->multiple   = NO;
  input_TIMESTEP->answer     = "0.01";
  input_TIMESTEP->description = _("Initial computational time step [s] - CFL condition");
  //input_TIMESTEP->guisection  = _("Options");


  /* Define different options */
  input_ELEV = G_define_option();
  input_ELEV->key	= "elev";
  input_ELEV->type = TYPE_STRING;
  input_ELEV->required = YES;
  input_ELEV->gisprompt = "old,cell,raster";
  input_ELEV->description = _("Name of elevation raster map (including lake bathymetry and dam)");
  input_ELEV->guisection  = _("Input options");

  input_LAKE = G_define_option();
  input_LAKE->key	= "lake";
  input_LAKE->type = TYPE_STRING;
  input_LAKE->required = YES;
  input_LAKE->gisprompt = "old,cell,raster";
  input_LAKE->description = _("Name of water depth raster map");
  input_LAKE->guisection  = _("Input options");

  input_DAMBREAK = G_define_option();
  input_DAMBREAK->key = "dambreak";
  input_DAMBREAK->type = TYPE_STRING;
  input_DAMBREAK->required = YES;
  input_DAMBREAK->gisprompt = "old,cell,raster";
  input_DAMBREAK->description = _("Name of dam breach width raster map");
  input_DAMBREAK->guisection  = _("Input options");

  input_MANNING = G_define_option();
  input_MANNING->key = "manning";
  input_MANNING->type = TYPE_STRING;
  input_MANNING->required = YES;
  input_MANNING->gisprompt = "old,cell,raster";
  input_MANNING->description = _("Name of Manning's roughness coefficient raster map");
  input_MANNING->guisection  = _("Input options");

  input_TSTOP = G_define_option();
  input_TSTOP->key	= "tstop";
  input_TSTOP->type = TYPE_INTEGER;
  input_TSTOP->required = YES;
  input_TSTOP->multiple   = NO;
  input_TSTOP->description = _("Simulation time duration [s]");
  input_TSTOP->guisection  = _("Input options");
  
  input_U = G_define_option();
  input_U->key	= "u";
  input_U->type = TYPE_STRING;
  input_U->required = NO;
  input_U->gisprompt = "old,cell,raster";
  input_U->description = _("Initial velocity along the east direction [m/s]");
  input_U->guisection  = _("Input options");
  
  input_V = G_define_option();
  input_V->key	= "v";
  input_V->type = TYPE_STRING;
  input_V->required = NO;
  input_V->gisprompt = "old,cell,raster";
  input_V->description = _("Initial velocity along the north direction [m/s]");
  input_V->guisection  = _("Input options");
	
  /*OUTPUTS options*/
  input_DELTAT = G_define_option();
  input_DELTAT->key	= "deltat";
  input_DELTAT->type = TYPE_INTEGER;
  input_DELTAT->required = NO;
  input_DELTAT->multiple   = NO;
  input_DELTAT->description = _("Time-lag for output generation [s]");
  input_DELTAT->guisection  = _("Output options");

  parm.opt_t = G_define_option();
  parm.opt_t->key	= "opt_t";
  parm.opt_t->type = TYPE_DOUBLE;
  parm.opt_t->required = NO;
  //parm.opt_t->multiple   = NO;
  parm.opt_t->multiple   = YES;
  parm.opt_t->description = _("Additional instants for output map generation [s]");
  parm.opt_t->guisection  = _("Output options");

  output_H = G_define_option();
  output_H ->key = "h";
  output_H ->type = TYPE_STRING;
  output_H ->required = NO;
  output_H ->gisprompt = "new,cell,raster";
  output_H ->description = _("Prefix for water depth output raster maps");
  output_H ->guisection  = _("Output options");

  output_VEL = G_define_option();
  output_VEL ->key = "vel";
  output_VEL ->type = TYPE_STRING;
  output_VEL ->required = NO;
  output_VEL ->gisprompt = "new,cell,raster";
  output_VEL ->description = _("Prefix for water velocity output raster maps");
  output_VEL ->guisection  = _("Output options");

  output_HMAX = G_define_option();
  output_HMAX ->key = "hmax";
  output_HMAX ->type = TYPE_STRING;
  output_HMAX ->required = NO;
  output_HMAX ->gisprompt = "new,cell,raster";
  output_HMAX ->description = _("Name of output maximum water depth raster map; relative intensity [h*v] and time map are also generated");
  output_HMAX ->guisection  = _("Output options");

  output_VMAX = G_define_option();
  output_VMAX ->key = "vmax";
  output_VMAX ->type = TYPE_STRING;
  output_VMAX ->required = NO;
  output_VMAX ->gisprompt = "new,cell,raster";
  output_VMAX ->description = _("Name of output maximum water velocity raster map; relative intensity [h*v] and time map are also generated");
  output_VMAX ->guisection  = _("Output options");

  output_IMAX = G_define_option();
  output_IMAX ->key = "imax";
  output_IMAX ->type = TYPE_STRING;
  output_IMAX ->required = NO;
  output_IMAX ->gisprompt = "new,cell,raster";
  output_IMAX ->description = _("Name of output maximum intensity [h*v] raster map; relative time map are also generated");
  output_IMAX ->guisection  = _("Output options");

  output_WAVEFRONT = G_define_option();
  output_WAVEFRONT ->key = "wavefront";
  output_WAVEFRONT ->type = TYPE_STRING;
  output_WAVEFRONT ->required = NO;
  output_WAVEFRONT ->gisprompt = "new,cell,raster";
  output_WAVEFRONT ->description = _("Name of output wave front time[s] raster map");
  output_WAVEFRONT ->guisection  = _("Output options");
  

  if (G_parser(argc, argv))
    exit(EXIT_FAILURE);


  /***********************************************************************************************************************/
  /* get entered parameters */
  ELEV=input_ELEV->answer;
  LAKE=input_LAKE->answer;
  DAMBREAK=input_DAMBREAK->answer;
  MANNING=input_MANNING->answer;
  sscanf(input_TIMESTEP->answer, "%f", &timestep);
  //timestep=input_TIMESTEP->answer;
  if (input_U->answer != NULL && input_V->answer != NULL ) {
	U=input_U->answer;
	V=input_V->answer;
  } else if (input_U->answer != NULL && input_V->answer == NULL ) {
	U=input_U->answer;
	G_warning("Initial velocity only along the east direction");
  } else if (input_V->answer != NULL && input_U->answer == NULL ) {
	V=input_V->answer;
	G_warning("Initial velocity only along the north direction");
  }
  
  pp = 0;
  ntimes = 0;
  if (parm.opt_t->answer != NULL) {
	  for (i = 0; parm.opt_t->answers[i]; i++) ;
	  ntimes=i;
	  times = G_alloc_vector(ntimes);
     for (i = 0; i < ntimes; i++) {
		  sscanf(parm.opt_t->answers[i], "%lf", &opt_t);
		  times[i]=opt_t;
	  }
  }
  	OUT_H=output_H->answer;
  	OUT_VEL=output_VEL->answer;
  	OUT_HMAX=output_HMAX->answer;
  	OUT_VMAX=output_VMAX->answer;
	OUT_IMAX=output_IMAX->answer;
        OUT_WAVEFRONT=output_WAVEFRONT->answer;
  	if (input_DELTAT->answer!= NULL){
		DELTAT = atoi(input_DELTAT->answer);
	}
	//DELTAT = atoi(input_DELTAT->answer);
  	TSTOP = atoi(input_TSTOP->answer);



  /* find maps in mapset */
  mapset_ELEV = (char *) G_find_raster2(ELEV, "");
  if (mapset_ELEV == NULL)
    G_fatal_error (_("cell file [%s] not found"), ELEV);

  mapset_LAKE = (char *) G_find_raster2(LAKE, "");
  if (mapset_LAKE == NULL)
    G_fatal_error (_("cell file [%s] not found"), LAKE);

  mapset_DAMBREAK = (char *) G_find_raster2(DAMBREAK, "");
  if (mapset_DAMBREAK == NULL)
    G_fatal_error (_("cell file [%s] not found"), DAMBREAK);

  mapset_MANNING = (char *) G_find_raster2(MANNING, "");
  if (mapset_MANNING == NULL)
    G_fatal_error (_("cell file [%s] not found"), MANNING);
  
  if (input_U->answer != NULL && input_V->answer != NULL ) {
	mapset_U = (char *) G_find_raster2(U, "");
  	if (mapset_U == NULL)
   	  G_fatal_error (_("cell file [%s] not found"), U);
	mapset_V = (char *) G_find_raster2(V, "");
  	if (mapset_V == NULL)
   	  G_fatal_error (_("cell file [%s] not found"), V);
  } else if (input_U->answer != NULL && input_V->answer == NULL ) {
	mapset_U = (char *) G_find_raster2(U, "");
  	if (mapset_U == NULL)
   	  G_fatal_error (_("cell file [%s] not found"), U);
 } else if (input_V->answer != NULL && input_U->answer == NULL ) {
	mapset_V = (char *) G_find_raster2(V, "");
  	if (mapset_V == NULL)
   	  G_fatal_error (_("cell file [%s] not found"), V);
  }

  /* open input raster files */
  if ( (infd_ELEV = Rast_open_old (ELEV, mapset_ELEV)) < 0)
    G_fatal_error (_("Cannot open cell file [%s]"), ELEV);
  if ( (infd_LAKE = Rast_open_old (LAKE, mapset_LAKE)) < 0)
    G_fatal_error (_("Cannot open cell file [%s]"), LAKE);
  if ( (infd_DAMBREAK = Rast_open_old (DAMBREAK, mapset_DAMBREAK)) < 0)
    G_fatal_error (_("Cannot open cell file [%s]"), DAMBREAK);
  if ( (infd_MANNING = Rast_open_old (MANNING, mapset_MANNING)) < 0)
    G_fatal_error (_("Cannot open cell file [%s]"), MANNING);

  if (input_U->answer != NULL && input_V->answer != NULL ) {
	if ( (infd_U = Rast_open_old (U, mapset_U)) < 0)
	    G_fatal_error (_("Cannot open cell file [%s]"), U);
        if ( (infd_V = Rast_open_old (V, mapset_V)) < 0)
	    G_fatal_error (_("Cannot open cell file [%s]"), V);
  } else if (input_U->answer != NULL && input_V->answer == NULL ) {
	if ( (infd_U = Rast_open_old (U, mapset_U)) < 0)
	    G_fatal_error (_("Cannot open cell file [%s]"), U);
  } else if (input_V->answer != NULL && input_U->answer == NULL ) {
	if ( (infd_V = Rast_open_old (V, mapset_V)) < 0)
	    G_fatal_error (_("Cannot open cell file [%s]"), V);
  }
	



  /* Check for some output map */
    if ((output_H->answer == NULL)
    && (output_VEL->answer == NULL)
    && (output_HMAX->answer == NULL)
    && (output_VMAX->answer == NULL)
    && (output_IMAX->answer == NULL)
    && (output_WAVEFRONT->answer == NULL)){
  		G_fatal_error(_("Sorry, you must choose an output map."));
    }

    if (flag_d->answer && (output_H->answer == NULL) ) {
    	G_fatal_error("You choose flow direction map without flow velocity prefix name");
    }

	/* Check legal output name */
	if (OUT_H) {
	 if (G_legal_filename (OUT_H) < 0)
		G_fatal_error (_("[%s] is an illegal name"), OUT_H);
	}
	if (OUT_VEL) {
	 if (G_legal_filename (OUT_VEL) < 0)
		G_fatal_error (_("[%s] is an illegal name"), OUT_VEL);
	}
	if (OUT_HMAX) {
	 if (G_legal_filename (OUT_HMAX) < 0)
		G_fatal_error (_("[%s] is an illegal name"), OUT_HMAX);
	}
	if (OUT_VMAX) {
	 if (G_legal_filename (OUT_VMAX) < 0)
		G_fatal_error (_("[%s] is an illegal name"), OUT_VMAX);
	}
	if (OUT_IMAX) {
	 if (G_legal_filename (OUT_IMAX) < 0)
		G_fatal_error (_("[%s] is an illegal name"), OUT_IMAX);
	}
        if (OUT_WAVEFRONT) {
	 if (G_legal_filename (OUT_WAVEFRONT) < 0)
		G_fatal_error (_("[%s] is an illegal name"), OUT_WAVEFRONT);
	}
  /* Type of dam failure*/
  if (strcmp(opt.met->answer, "uniform drop in of lake") == 0)
  	method=1;
  else if (strcmp(opt.met->answer, "small dam breach") == 0)
	method=2;
  else if (strcmp(opt.met->answer, "dambreak-without_hypotesis") == 0)
  	method=3;
  else
	G_fatal_error(_("Unknown method. Please, select a computational method"));

  /* Allocate input buffer */
  //inrast_ELEV = Rast_allocate_buf(Rast_map_type(ELEV, mapset_ELEV));
  inrast_ELEV = Rast_allocate_f_buf();
  //inrast_LAKE = Rast_allocate_buf(Rast_map_type(LAKE, mapset_LAKE));
  inrast_LAKE = Rast_allocate_d_buf();
  //inrast_DAMBREAK = Rast_allocate_buf(Rast_map_type(DAMBREAK, mapset_DAMBREAK));
  inrast_DAMBREAK = Rast_allocate_f_buf();
  //inrast_MANNING = Rast_allocate_buf(Rast_map_type(MANNING, mapset_MANNING));
  inrast_MANNING = Rast_allocate_f_buf();
  if (input_U->answer != NULL && input_V->answer != NULL ) {
	inrast_U = Rast_allocate_d_buf();
	inrast_V = Rast_allocate_d_buf();
  } else if (input_U->answer != NULL && input_V->answer == NULL ) {
	inrast_U = Rast_allocate_d_buf();
  } else if (input_V->answer != NULL && input_U->answer == NULL ) {
	inrast_V = Rast_allocate_d_buf();
  }
  /* Get windows rows & cols */
  nrows = Rast_window_rows();
  ncols = Rast_window_cols();
  G_get_window(&window);
  res_ew = window.ew_res;
  res_ns = window.ns_res;

  /* Allocate memory matrix */
  m_DAMBREAK = G_alloc_fmatrix(nrows,ncols);
  m_m = G_alloc_fmatrix(nrows,ncols);
  m_z = G_alloc_fmatrix(nrows,ncols);
  m_h1 = G_alloc_dmatrix(nrows,ncols);
  m_h2 = G_alloc_dmatrix(nrows,ncols);
  m_u1 = G_alloc_dmatrix(nrows,ncols);
  m_u2 = G_alloc_dmatrix(nrows,ncols);
  m_v1 = G_alloc_dmatrix(nrows,ncols);
  m_v2 = G_alloc_dmatrix(nrows,ncols);
  m_lake = G_alloc_imatrix(nrows,ncols);
  if (OUT_HMAX) {
  		m_hmax = G_alloc_fmatrix(nrows,ncols);
  		m_t_hmax = G_alloc_fmatrix(nrows,ncols);
  		m_i_hmax = G_alloc_fmatrix(nrows,ncols);
  }
  if (OUT_VMAX) {
  		m_vmax = G_alloc_fmatrix(nrows,ncols);
  		m_t_vmax = G_alloc_fmatrix(nrows,ncols);
  		m_i_vmax = G_alloc_fmatrix(nrows,ncols);
  		if (flag_d->answer) {
  			m_dir_vmax = G_alloc_fmatrix(nrows,ncols);
  		}
  }
  if (OUT_IMAX) {
  		m_imax = G_alloc_fmatrix(nrows,ncols);
  		m_t_imax = G_alloc_fmatrix(nrows,ncols);
  }
  if (OUT_WAVEFRONT) {
  		m_wavefront = G_alloc_fmatrix(nrows,ncols);
  }
  G_message("Reading input maps");
  for (row = 0; row < nrows; row++)
  	{
	  G_percent (row, nrows, 2);

	  /* Read a line input maps into buffers*/
	  Rast_get_f_row (infd_ELEV, inrast_ELEV, row);
	  Rast_get_d_row (infd_LAKE, inrast_LAKE, row);
	  Rast_get_f_row (infd_DAMBREAK, inrast_DAMBREAK, row);
	  Rast_get_f_row (infd_MANNING, inrast_MANNING, row); 
	  if (input_U->answer != NULL && input_V->answer != NULL ) {
		Rast_get_d_row (infd_U, inrast_U, row);
		Rast_get_d_row (infd_V, inrast_V, row);
	  } else if (input_U->answer != NULL && input_V->answer == NULL ) {
		Rast_get_d_row (infd_U, inrast_U, row);
	  } else if (input_V->answer != NULL && input_U->answer == NULL ) {
		Rast_get_d_row (infd_V, inrast_V, row);
	  }     
	      /*if (G_get_f_raster_row (infd_ELEV, inrast_ELEV, row) < 0)
		G_fatal_error (_("Could not read from <%s>"),ELEV);
	      if (G_get_d_raster_row (infd_LAKE, inrast_LAKE, row) < 0)
		G_fatal_error (_("Could not read from <%s>"),LAKE);
	      if (G_get_f_raster_row (infd_DAMBREAK, inrast_DAMBREAK, row) < 0)
		G_fatal_error (_("Could not read from <%s>"),DAMBREAK);
	      if (G_get_f_raster_row (infd_MANNING, inrast_MANNING, row) < 0)
		G_fatal_error (_("Could not read from <%s>"),MANNING);*/

	      /* Read every cell in the line buffers */
	      for (col = 0; col < ncols; col++)
		{
  			/* Store values in memory matrix (attenzione valori nulli!) (attention null values!)*/
		  	m_DAMBREAK[row][col] = ((FCELL *) inrast_DAMBREAK)[col];
		  	m_m[row][col] = ((FCELL *) inrast_MANNING)[col];
		  	m_z[row][col] = ((FCELL *) inrast_ELEV)[col];
		  	m_h1[row][col] = ((DCELL *) inrast_LAKE)[col];
		  	m_h2[row][col] = m_h1[row][col];
			if (input_U->answer != NULL && input_V->answer != NULL ) {
				m_u1[row][col] = ((DCELL *) inrast_U)[col];
				m_v1[row][col] = ((DCELL *) inrast_V)[col];
	  		} else if (input_U->answer != NULL && input_V->answer == NULL ) {
				m_u1[row][col] = ((DCELL *) inrast_U)[col];
				m_v1[row][col] = 0.0;
	  		} else if (input_V->answer != NULL && input_U->answer == NULL ) {
				m_u1[row][col] = 0.0;
				m_v1[row][col] = ((DCELL *) inrast_V)[col];
	  		} else {
				m_u1[row][col] = 0.0;
 				m_v1[row][col] = 0.0;
			}
		  	m_u2[row][col] = 0.0;
	  	  	m_v2[row][col] = 0.0;
	  		if (OUT_HMAX) {
	  	  		m_hmax[row][col] = m_h1[row][col];
	  	  		m_t_hmax[row][col] = 0.0;
	  	  		m_i_hmax[row][col]=0.0;
	  	  	}
	  	  	if (OUT_VMAX) {
	  	  		m_vmax[row][col] = 0.0;
	  	  		m_t_vmax[row][col] = 0.0;
	  	  		m_i_vmax[row][col]=0.0;
	  	  		if (flag_d->answer) {
	  	  			m_dir_vmax[row][col]=0.0;
	  	  		}
	  	  	}
	  	  	if (OUT_IMAX) {
	  	  		m_imax[row][col] = 0.0;
	  	  		m_t_imax[row][col] = 0.0;
	  	  	}
			if (OUT_WAVEFRONT) {
	  	  		m_wavefront[row][col] = 0.0;
	  	  	}
		}
    	}


  G_free(inrast_ELEV);
  G_free(inrast_LAKE);
  G_free(inrast_DAMBREAK);
  G_free(inrast_MANNING);
  Rast_close(infd_ELEV);
  Rast_close(infd_LAKE);
  Rast_close (infd_DAMBREAK);
  Rast_close (infd_MANNING);
  if (input_U->answer != NULL && input_V->answer != NULL ) {
	G_free(inrast_U);
  	G_free(inrast_V);
  	Rast_close(infd_U);
  	Rast_close(infd_V);
  } else if (input_U->answer != NULL && input_V->answer == NULL ) {
	G_free(inrast_U);
  	Rast_close(infd_U);
  } else if (input_V->answer != NULL && input_U->answer == NULL ) {
  	G_free(inrast_V);
  	Rast_close(infd_V);
  } 

	if (method==1 || method==2) {
		num_cell=0;
		/* Search for lakes (cerco il lago) */
		for (row = 0; row < nrows; row++)
			{
			for (col = 0; col < ncols; col++)
				{
				if (m_h1[row][col] != 0 ){
					water_elevation = m_h1[row][col] + m_z[row][col];
					m_lake[row][col]=1;
					num_cell++;
				}else {
					m_lake[row][col]=0;
				}
		}}
		num_break=0;
		G_message("Searching dam breach");
		for (row = 0; row < nrows; row++)
			{
			for (col = 0; col < ncols; col++)
				{
				/*  Dam break (rottura diga) */
				if (m_DAMBREAK[row][col] > 0){
					num_break++;
					G_message("(%d,%d)Cell Dam Breach n° %d",row,col,num_break);
					//printf("ho trovato la rottura diga (%d,%d)=\n", row,col);
					//while(!getchar()){ }
					profondita_soglia = water_elevation-(m_z[row][col] - m_DAMBREAK[row][col]) ;
					vel_0=velocita_breccia(method,profondita_soglia);
					volume = volume + profondita_soglia * res_ew * res_ns;
					//printf("Q=%.2f\n",Q);
					//vel_0 = 0.93 * sqrt(profondita_soglia);
					if (vel_0 > vel_max)
					vel_max=vel_0;
				} else {
					G_fatal_error(_("Didn't find the dambreak. Please select a correct map or adjust the computational region."));
				}

				if (m_DAMBREAK[row][col] > 0) {
					//cambio il DTM inserendo la rottura della diga
					m_z[row][col]=m_z[row][col]-m_DAMBREAK[row][col];
					m_lake[row][col]=0;
					m_h1[row][col]=profondita_soglia;
					//printf("la velocità vel_max vale: %f\n",vel_max);
					//while(!getchar()){ }
					}
		  	}
		}
		G_message("The number of lake cell is': %d\n", num_cell);

		/**************************************/
		/* timestep in funzione di V_0 e res */
		/* timestep as a function of V_0 and res */
		/**************************************/
		//timestep=0.01;
		//timestep= ((res_ns+res_ew)/2.0)/(vel_max*50.0);
		// DEVELOPEMENT
		//*****************************************************************************
	 	G_message("vel on the dam break cells is %.2f, and timestep is %.2f",vel_max, timestep);
	 }

      		//*****************************************************************************
		// Uniform drop in of lake (method=1 or method =2) 
		//*****************************************************************************
		if (method==1 || method==2){
			/* calcolo l'abbassamento sul lago (Calculation of the lowering of the lake) */
			if (num_cell!=0) {
				fall = (volume) / (num_cell * res_ew * res_ns);
				//printf("volume=%f, fall=%f\n",volume,fall);
				//while(!getchar()){ }
			}

			for (row = 1; row < nrows-1; row++)
		   {
				for (col = 1; col < ncols-1; col++)
				{
					if (m_DAMBREAK[row][col]>0){
						// ragiona se ha senso (I think it makes sense)
						m_h2[row][col]=m_h1[row][col]-fall;
						if (m_h2[row][col]<=0) {
							m_h2[row][col]=0.0;
							if (m_h1[row][col]>0) {
							// questo warning va modificato perchè vale per ogni cella ---> bisogna metterne uno generico che valga quando tutte le celle sono con h=0
							// (This warning must be modified since it is valid for every cell) ---> (You have to put a generic one that is valid when all cells have h=0)
								num_break--;
								if (num_break==0){
									if (warn1==0){
										G_warning("At the time %.0fs no water go out from lake",t);
									}
								}
							}
						}
					}
					if (m_lake[row][col]==1){
						m_h2[row][col]=m_h1[row][col]-fall;
						if (m_h2[row][col]<=0) {
							vol_res = vol_res-m_h2[row][col]*res_ew * res_ns;
							m_lake[row][col]=-1;
							m_h2[row][col]=0.0;
							num_cell--;
						}
					}
			}}//end two for cicles
		} //end if
	// There isn't interest to find where is the lake --> everywhere m_lake[row][col]=0 
	if (method==3){
	 	for (row = 0; row < nrows; row++)
			{
			for (col = 0; col < ncols; col++)
				{
				/*  Dam break (rottura diga) */
				if (m_DAMBREAK[row][col] > 0){
					m_z[row][col]=m_z[row][col]-m_DAMBREAK[row][col];
					m_DAMBREAK[row][col]=-1.0;
					//timestep=0.01;
					m_lake[row][col]=0;
				} else {
					m_lake[row][col]=0;
	 }}}}

  	G_percent(nrows, nrows, 1);	/* finish it */

  	G_message("Model running");
	
	/* Calculate time step loop */
	for(t=0; t<=TSTOP; t+=timestep){
	//printf("************************************************\n");
	//while(!getchar()){ }
	//G_percent(t, TSTOP, timestep);
	// ciclo sui tempi
        //G_message("timestep =%f,t=%f",timestep,t);
		   if (t>M*100){
		   	if (M*100!=(m-1)*DELTAT)
		   		G_percent(ceil(t), TSTOP, 2);
		   		G_message("t:%d",M*100);
		   	M++;
		   }
		  	//printf("t:%lf\n",t);


		   //G_message("Function SWE - t=%f, TSTOP=%d",t,TSTOP);  
		   
		   shallow_water(m_h1,m_u1,m_v1,m_z,m_DAMBREAK,m_m,m_lake,m_h2,m_u2,m_v2,row,col,nrows,ncols,timestep,res_ew,res_ns,method,num_cell, num_break,t);
		   

    //*************************************** overwriting *********************************************
    timestep_ct=0;
    if (t<TSTOP){   
    /* open new cicle */
    	for (row = 1; row < nrows-1; row++) {
	   	for (col = 1; col < ncols-1; col++) {
		 	if( (row==1 || row==(nrows-2) || col==1 || col==(ncols-2)) && (m_v2[1][col]>0 || m_v2[nrows-2][col]<0 || m_u1[row][1]<0 || m_u1[row][ncols-2]>0 )) {
				if (reg_lim==0) {
					G_warning("At the time %.3f the computational region is smaller than inundation",t);
					reg_lim=1;
				} /* Warning  message only a time */
	    		} /* velocities at the limit of computational region */
				
            	//********************************************************************				
		// timestep optimization using the CFL stability condition 
		if (m_h2[row][col]>=hmin ){
              		timestep_ct_temp = max( (fabs(m_u2[row][col])+sqrt(g*m_h2[row][col]))/res_ew , (fabs(m_v2[row][col])+sqrt(g*m_h2[row][col]))/res_ns );
			if(timestep_ct_temp>timestep_ct) {
				timestep_ct=timestep_ct_temp;
				//G_message("t=%f,row=%d,col=%d,timestep_ct=%f,m_u2=%f m_v2=%f m_h2=%f",t,row,col,timestep_ct,m_u2[row][col],m_v2[row][col],m_h2[row][col]);
			}
		}
		//********************************************************************
				 
	 	m_u1[row][col] =  m_u2[row][col];
		m_v1[row][col] =  m_v2[row][col];
		if (OUT_HMAX) {
			if (m_hmax[row][col]<m_h2[row][col]){
				m_hmax[row][col]=m_h2[row][col];
				m_t_hmax[row][col]=t;
				velocity=sqrt(pow(m_u1[row][col],2.0) + pow(m_v1[row][col],2.0));
				m_i_hmax[row][col]=velocity*m_h2[row][col];
			}
		}
		if (OUT_VMAX) {
			velocity=sqrt(pow(m_u1[row][col],2.0) + pow(m_v1[row][col],2.0));
			if (m_vmax[row][col]<velocity){
				m_vmax[row][col]=velocity;
				m_i_vmax[row][col]=velocity*m_h2[row][col];
				m_t_vmax[row][col]=t;
				if (flag_d->answer) {
				   if (m_u1[row][col]==0 && m_v1[row][col]==0){
						m_dir_vmax[row][col] =0;
					} else if (m_u1[row][col]>0 && m_v1[row][col]>0) {
						m_dir_vmax[row][col] = 180/PI*atan(fabs(m_v1[row][col])/fabs(m_u1[row][col]));
					} else if (m_u1[row][col]==0 && m_v1[row][col]>0) {
						m_dir_vmax[row][col] = 90.0;
					} else if (m_u1[row][col]<0 && m_v1[row][col]>0) {
						m_dir_vmax[row][col] = 90.0 + 180/PI*atan(fabs(m_u1[row][col])/fabs(m_v1[row][col]));
					} else if (m_u1[row][col]<0 && m_v1[row][col]==0) {
						m_dir_vmax[row][col] = 180.0;
					} else if (m_u1[row][col]<0 && m_v1[row][col]<0) {
						m_dir_vmax[row][col] = 180.0 + 180/PI*atan(fabs(m_v1[row][col])/fabs(m_u1[row][col]));
					} else if (m_u1[row][col]==0 && m_v1[row][col]<0) {
						m_dir_vmax[row][col] = 270.0;
					} else if (m_u1[row][col]>0 && m_v1[row][col]<0) {
						m_dir_vmax[row][col] = 270.0 + 180/PI*atan(fabs(m_u1[row][col])/fabs(m_v1[row][col]));
					} else if (m_u1[row][col]>0 && m_v1[row][col]==0) {
						m_dir_vmax[row][col] = 0.0;
					}
				}
			}
		}
		if (OUT_IMAX) {
			velocity=sqrt(pow(m_u1[row][col],2.0) + pow(m_v1[row][col],2.0));
			i=velocity*m_h2[row][col];
			if (m_imax[row][col]<i){
				m_imax[row][col]=i;
				m_t_imax[row][col]=t;
			}
		}
                if (OUT_WAVEFRONT) {
			if (m_wavefront[row][col]==0.0 && m_h2[row][col]>hmin){
				m_wavefront[row][col]=t;
			}
		}

		m_h1[row][col] =  m_h2[row][col];
	}}}
	
	/*------------------------------   new timestep   -------------------------------------*/
	timestep=0.1/timestep_ct;
	/*-------------------------------------------------------------------------------------*/
   	//G_message("timestep =%f,m=%d, t=%f",timestep,m, t);
	
	/*----------------------------------------------------------------------------------------------*/
	/* qualcosa non va in questo if  								*/        
	/*----------------------------------------------------------------------------------------------*/
	
	/* controllo se devo scrivere outputs (Check if we need to write outputs) */
	if ((input_DELTAT->answer != NULL)||(parm.opt_t->answer != NULL)) {
		if ((((m*DELTAT-t) <= timestep && (m*DELTAT) < TSTOP) && (input_DELTAT->answer != NULL)) || ((pp < ntimes && (times[pp]-t) < timestep) && (parm.opt_t->answer != NULL))) {
	     	 	if ((m*DELTAT-t) <= timestep && m*DELTAT < TSTOP) {   /* devo cambiare il nome del raster e aggiungere ogni volta _timestep (We need to change the raster name and add _timestep at each time)*/
				if (OUT_H) {
					sprintf(name1,"%s%d",OUT_H,m*DELTAT);
				}
				if (OUT_VEL){
					sprintf(name2,"%s%d",OUT_VEL,m*DELTAT);
					sprintf(name3,"%s%s%d","dir_",OUT_VEL,m*DELTAT);
				}
				G_message("Time: %d, writing the output maps",m*DELTAT);
				m++;
			} else {
				pp++;
				sprintf(name1,"%s%s%d","opt_",OUT_H,pp);
				sprintf(name2,"%s%s%d","opt_",OUT_VEL,pp);
				sprintf(name3,"%s%s%s%d","opt_","dir_",OUT_VEL,pp);
				G_message("Time: %lf, writing an optional output maps %d",t, pp);
			}
			/* Controlling if we can write the raster */
			if (OUT_H) {
				if ( (outfd_H = Rast_open_new (name1,DCELL_TYPE)) < 0) {
					G_fatal_error (_("Could not open <%s>"),name1);
				}
			}
			if (OUT_VEL) {
				if ( (outfd_VEL = Rast_open_new (name2,DCELL_TYPE)) < 0) {
					G_fatal_error (_("Could not open <%s>"),name2);
				}
			}
			if (flag_d->answer) {
				if ( (outfd_VEL_DIR = Rast_open_new (name3,DCELL_TYPE)) < 0) {
					G_fatal_error (_("Could not open <%s>"),name3);
				}
			}
			/* Allocate output buffer */
			if (OUT_VEL) {
				outrast_VEL = Rast_allocate_d_buf();
			}
			if (OUT_H) {
				outrast_H = Rast_allocate_d_buf();
			}
			if (flag_d->answer) {
				outrast_VEL_DIR = Rast_allocate_d_buf();
			}
		 	for (row = 0; row < nrows; row++) 
				{
			 	for (col = 0; col < ncols; col++) 
					{
					/* Copy matrix in buffer */
					if (OUT_VEL) {
						((DCELL *) outrast_VEL)[col] = sqrt(pow(m_u1[row][col],2.0) + pow(m_v1[row][col],2.0));
					}
					if (flag_d->answer) {
						if (m_u1[row][col]==0 && m_v1[row][col]==0){
							Rast_set_d_null_value(&outrast_VEL_DIR[col],1);
						} else if (m_u1[row][col]>0 && m_v1[row][col]>0) {
							((DCELL *) outrast_VEL_DIR)[col] = 180/PI*atan(fabs(m_v1[row][col])/fabs(m_u1[row][col]));
						} else if (m_u1[row][col]==0 && m_v1[row][col]>0) {
							((DCELL *) outrast_VEL_DIR)[col] = 90.0;
						} else if (m_u1[row][col]<0 && m_v1[row][col]>0) {
							((DCELL *) outrast_VEL_DIR)[col] = 90.0 + 180/PI*atan(fabs(m_u1[row][col])/fabs(m_v1[row][col]));
						} else if (m_u1[row][col]<0 && m_v1[row][col]==0) {
							((DCELL *) outrast_VEL_DIR)[col] = 180.0;
						} else if (m_u1[row][col]<0 && m_v1[row][col]<0) {
							((DCELL *) outrast_VEL_DIR)[col] = 180.0 + 180/PI*atan(fabs(m_v1[row][col])/fabs(m_u1[row][col]));
						} else if (m_u1[row][col]==0 && m_v1[row][col]<0) {
							((DCELL *) outrast_VEL_DIR)[col] = 270.0;
						} else if (m_u1[row][col]>0 && m_v1[row][col]<0) {
							((DCELL *) outrast_VEL_DIR)[col] = 270.0 + 180/PI*atan(fabs(m_u1[row][col])/fabs(m_v1[row][col]));
						} else if (m_u1[row][col]>0 && m_v1[row][col]==0) {
							((DCELL *) outrast_VEL_DIR)[col] = 0.0;
						}
					}
					if (OUT_H) {
						((DCELL *) outrast_H)[col] = m_h1[row][col];
					}

				} /* end_col*/
				 /*copia righe (Copy lines)!!! */
				 if (OUT_VEL) {
				 	Rast_put_d_row(outfd_VEL,outrast_VEL);
				 }
				 if (OUT_H) {
				 	Rast_put_d_row(outfd_H,outrast_H);
				 }
				 if (flag_d->answer) {
				 	Rast_put_d_row(outfd_VEL_DIR,outrast_VEL_DIR);
				 }
			}  /* end row */
			/* Memory cleanup */
			if (OUT_VEL) {
				G_free(outrast_VEL);
			}
			if (OUT_H) {
				G_free(outrast_H);
			}
			if (flag_d->answer) {
				G_free(outrast_VEL_DIR);
			}
			/* Close the raster maps */
			if (OUT_VEL) { 
				Rast_close (outfd_VEL);
			}
	  		if (OUT_H) {
	  			Rast_close (outfd_H);
	  		}
	  		if (flag_d->answer) {
	  			Rast_close (outfd_VEL_DIR);
	  		}
			//timestep=0.1/timestep_ct;	
		} 
	}/* end if write outputs*/
	/* else {
		//G_message("timestep =%f,t=%f",timestep,t);
		//pippo=1;
		G_message("Function SWE - t=%f, TSTOP=%d",t,TSTOP);
		//G_percent(t, TSTOP, timestep);
	} */
	//G_message("Function SWE applied - t=%f, TSTOP=%d",t,TSTOP);
   //G_message("timestep =%f,t=%f",timestep,t);
} /* end time loop*/


//*******************************************************************
// Write final flooding map
if(OUT_H) {
	sprintf(name1,"%s%d",OUT_H,TSTOP);
}
if(OUT_VEL) {
	sprintf(name2,"%s%d",OUT_VEL,TSTOP);
	sprintf(name3,"%s%s%d","dir_",OUT_VEL,TSTOP);
}
if(OUT_H) {
	if ( (outfd_H = Rast_open_new (name1,DCELL_TYPE)) < 0)
		G_fatal_error (_("Could not open <%s>"),name1);
}
if(OUT_VEL) {
	if ( (outfd_VEL = Rast_open_new (name2,DCELL_TYPE)) < 0)
		G_fatal_error (_("Could not open <%s>"),name2);
}
if (flag_d->answer) {
	if ( (outfd_VEL_DIR = Rast_open_new (name3,DCELL_TYPE)) < 0)
		G_fatal_error (_("Could not open <%s>"),name3);
}

if (OUT_HMAX){
	sprintf(name4,"%s%s",OUT_HMAX,"_time");
	sprintf(name5,"%s%s",OUT_HMAX,"_intensity");
	if ( (outfd_HMAX = Rast_open_new (OUT_HMAX,DCELL_TYPE)) < 0)
		G_fatal_error (_("Could not open <%s>"),OUT_HMAX);
	if ( (outfd_T_HMAX = Rast_open_new (name4,DCELL_TYPE)) < 0)
		G_fatal_error (_("Could not open <%s>"),OUT_HMAX);
	if ( (outfd_I_HMAX = Rast_open_new (name5,DCELL_TYPE)) < 0)
		G_fatal_error (_("Could not open <%s>"),OUT_HMAX);
}

if (OUT_VMAX){
	sprintf(name6,"%s%s",OUT_VMAX,"_time");
	sprintf(name7,"%s%s",OUT_VMAX,"_intensity");
	if (flag_d->answer) {
		sprintf(name8,"%s%s",OUT_VMAX,"_dir");
	}
	if ( (outfd_VMAX = Rast_open_new (OUT_VMAX,DCELL_TYPE)) < 0)
		G_fatal_error (_("Could not open <%s>"),OUT_VMAX);
	if ( (outfd_T_VMAX = Rast_open_new (name6,DCELL_TYPE)) < 0)
		G_fatal_error (_("Could not open <%s>"),OUT_VMAX);
	if ( (outfd_I_VMAX = Rast_open_new (name7,DCELL_TYPE)) < 0)
		G_fatal_error (_("Could not open <%s>"),OUT_VMAX);
	if (flag_d->answer) {
		if ( (outfd_DIR_VMAX = Rast_open_new (name8,DCELL_TYPE)) < 0)
			G_fatal_error (_("Could not open <%s>"),OUT_VMAX);
	}
}
if (OUT_IMAX){
	sprintf(name9,"%s%s",OUT_IMAX,"_time");
	if ( (outfd_IMAX = Rast_open_new (OUT_IMAX,DCELL_TYPE)) < 0)
		G_fatal_error (_("Could not open <%s>"),OUT_IMAX);
	if ( (outfd_T_IMAX = Rast_open_new (name9,DCELL_TYPE)) < 0)
		G_fatal_error (_("Could not open <%s>"),OUT_IMAX);
}
if (OUT_WAVEFRONT){
	if ( (outfd_WAVEFRONT = Rast_open_new (OUT_WAVEFRONT,DCELL_TYPE)) < 0)
		G_fatal_error (_("Could not open <%s>"),OUT_WAVEFRONT);
}

/* Allocate output buffer */
if (OUT_H) {
	outrast_H = Rast_allocate_d_buf();
}
if (OUT_VEL) {
	outrast_VEL = Rast_allocate_d_buf();
}
if(flag_d->answer) {
	outrast_VEL_DIR = Rast_allocate_d_buf();
}

if (OUT_HMAX){
	outrast_HMAX = Rast_allocate_d_buf();
	outrast_I_HMAX = Rast_allocate_d_buf();
	outrast_T_HMAX = Rast_allocate_d_buf();
}
if (OUT_VMAX){
	outrast_VMAX = Rast_allocate_d_buf();
	outrast_I_VMAX = Rast_allocate_d_buf();
	outrast_T_VMAX = Rast_allocate_d_buf();
	if(flag_d->answer) {
		outrast_DIR_VMAX = Rast_allocate_d_buf();
	}
}

if (OUT_IMAX){
	outrast_IMAX = Rast_allocate_d_buf();
	outrast_T_IMAX = Rast_allocate_d_buf();
}
if (OUT_WAVEFRONT){
	outrast_WAVEFRONT = Rast_allocate_d_buf();
}

G_percent(nrows, nrows, 1);	/* finish it */

for (row = 0; row < nrows; row++){
   G_percent (row, nrows, 2);
	for (col = 0; col < ncols; col++) {
		/* Copy matrix in buffer */
		if (OUT_H) {
			((DCELL *) outrast_H)[col] = m_h1[row][col];
		}
		if (OUT_VEL) {
			((DCELL *) outrast_VEL)[col] = sqrt(pow(m_u1[row][col],2.0) + pow(m_v1[row][col],2.0));
		}
		if (flag_d->answer) {
			if (m_u1[row][col]==0 && m_v1[row][col]==0){
				Rast_set_d_null_value(&outrast_VEL_DIR[col],1);
			} else if (m_u1[row][col]>0 && m_v1[row][col]>0) {
				((DCELL *) outrast_VEL_DIR)[col] = 180/PI*atan(fabs(m_v1[row][col])/fabs(m_u1[row][col]));
			} else if (m_u1[row][col]==0 && m_v1[row][col]>0) {
				((DCELL *) outrast_VEL_DIR)[col] = 90.0;
			} else if (m_u1[row][col]<0 && m_v1[row][col]>0) {
				((DCELL *) outrast_VEL_DIR)[col] = 90.0 + 180/PI*atan(fabs(m_u1[row][col])/fabs(m_v1[row][col]));
			} else if (m_u1[row][col]<0 && m_v1[row][col]==0) {
				((DCELL *) outrast_VEL_DIR)[col] = 180.0;
			} else if (m_u1[row][col]<0 && m_v1[row][col]<0) {
				((DCELL *) outrast_VEL_DIR)[col] = 180.0 + 180/PI*atan(fabs(m_v1[row][col])/fabs(m_u1[row][col]));
			} else if (m_u1[row][col]==0 && m_v1[row][col]<0) {
				((DCELL *) outrast_VEL_DIR)[col] = 270.0;
			} else if (m_u1[row][col]>0 && m_v1[row][col]<0) {
				((DCELL *) outrast_VEL_DIR)[col] = 270.0 + 180/PI*atan(fabs(m_u1[row][col])/fabs(m_v1[row][col]));
			} else if (m_u1[row][col]>0 && m_v1[row][col]==0) {
				((DCELL *) outrast_VEL_DIR)[col] = 0.0;
			}
		}

		// output HMAX
		if (OUT_HMAX){
			if(m_hmax[row][col]==0){
				Rast_set_d_null_value(&outrast_HMAX[col], 1);
			} else {
				((DCELL *) outrast_HMAX)[col] = m_hmax[row][col];
			}
			if(m_hmax[row][col]==0){
				Rast_set_d_null_value(&outrast_T_HMAX[col], 1);
			} else {
				((DCELL *) outrast_T_HMAX)[col] = m_t_hmax[row][col];
			}
			if(m_hmax[row][col]==0){
				Rast_set_d_null_value(&outrast_I_HMAX[col], 1);
			} else {
				((DCELL *) outrast_I_HMAX)[col] = m_i_hmax[row][col];
			}
		}
		// output VMAX
		if (OUT_VMAX){
			if(m_vmax[row][col]==0){
				Rast_set_d_null_value(&outrast_VMAX[col], 1);
			} else {
				((DCELL *) outrast_VMAX)[col] = m_vmax[row][col];
			}
		   if(m_vmax[row][col]==0){
				Rast_set_d_null_value(&outrast_I_VMAX[col], 1);
			} else {
				((DCELL *) outrast_I_VMAX)[col] = m_i_vmax[row][col];
			}
			if(m_vmax[row][col]==0){
				Rast_set_d_null_value(&outrast_T_VMAX[col], 1);
			} else {
				((DCELL *) outrast_T_VMAX)[col] = m_t_vmax[row][col];
			}
			if (flag_d->answer) {
				if(m_vmax[row][col]==0){
					Rast_set_d_null_value(&outrast_DIR_VMAX[col], 1);
				} else {
					((DCELL *) outrast_DIR_VMAX)[col] = m_dir_vmax[row][col];
				}
			}
		}
		// output IMAX
		if (OUT_IMAX){
			if(m_imax[row][col]==0){
				Rast_set_d_null_value(&outrast_IMAX[col], 1);
			} else {
				((DCELL *) outrast_IMAX)[col] = m_imax[row][col];
			}
		   if(m_imax[row][col]==0){
				Rast_set_d_null_value(&outrast_T_IMAX[col], 1);
			} else {
				((DCELL *) outrast_T_IMAX)[col] = m_t_imax[row][col];
			}
		}
		// output WAVEFRONT
		if (OUT_WAVEFRONT){
			if(m_wavefront[row][col]==0){
				Rast_set_d_null_value(&outrast_WAVEFRONT[col], 1);
			} else {
				((DCELL *) outrast_WAVEFRONT)[col] = m_wavefront[row][col];
			}
		}

	} /* end_col*/
	if(OUT_H) {
	Rast_put_row (outfd_H, outrast_H, TYPE_DOUBLE);
 		/*if (G_put_raster_row (outfd_H, outrast_H, TYPE_DOUBLE) < 0)
			G_fatal_error (_("Cannot write to <%s>"),name2);*/
	}
	if (OUT_VEL) {
		Rast_put_row (outfd_VEL,outrast_VEL, TYPE_DOUBLE);
 	}
	if (flag_d->answer) {
		Rast_put_row (outfd_VEL_DIR, outrast_VEL_DIR, TYPE_DOUBLE);
	}

	if (OUT_HMAX){
		Rast_put_row (outfd_HMAX, outrast_HMAX, TYPE_DOUBLE);
		Rast_put_row (outfd_T_HMAX, outrast_T_HMAX, TYPE_DOUBLE);
		Rast_put_row  (outfd_I_HMAX, outrast_I_HMAX, TYPE_DOUBLE);
	}

	if (OUT_VMAX){
		Rast_put_row (outfd_VMAX, outrast_VMAX, TYPE_DOUBLE);
		Rast_put_row (outfd_T_VMAX, outrast_T_VMAX, TYPE_DOUBLE);
		Rast_put_row (outfd_I_VMAX, outrast_I_VMAX, TYPE_DOUBLE);
		if (flag_d->answer) {
			Rast_put_row (outfd_DIR_VMAX, outrast_DIR_VMAX, TYPE_DOUBLE);
		}
	}

	if (OUT_IMAX){
		Rast_put_row (outfd_IMAX, outrast_IMAX, TYPE_DOUBLE);
		Rast_put_row (outfd_T_IMAX, outrast_T_IMAX, TYPE_DOUBLE);
	}
        
        if (OUT_WAVEFRONT){
		Rast_put_row (outfd_WAVEFRONT, outrast_WAVEFRONT, TYPE_DOUBLE);
	}
 	//G_message("pippo, row=%d e nrows=%d", row, nrows);
}	// end row
/* chiudi i file (Close files) */


  	if (OUT_H) {
  		G_message("Writing the output final map %s", name1);
  	}
  	if (OUT_VEL) {
    		G_message("Writing the output final map %s",name2);
  	}
	if (OUT_HMAX) {
  		G_message("Writing the output final map %s, corresponding time and intensity", OUT_HMAX);
  	}
	if (OUT_VMAX) {
  		G_message("Writing the output final map %s, corresponding time and intensity", OUT_VMAX);
  	}
	if (OUT_IMAX) {
  		G_message("Writing the output final map %s and corresponding time", OUT_IMAX);
  	}
	if (OUT_WAVEFRONT) {
  		G_message("Writing the output final map %s", OUT_WAVEFRONT);
  	}

G_percent(nrows, nrows, 1);	/* Finish it */
if (OUT_VEL) {
	G_free(outrast_VEL);
	Rast_close (outfd_VEL);
}
if (OUT_H) {
	G_free(outrast_H);
	Rast_close (outfd_H);
}
if (flag_d->answer) {
	G_free(outrast_VEL_DIR);
	Rast_close (outfd_VEL_DIR);
}

if (OUT_HMAX){
	G_free(outrast_HMAX);
	Rast_close (outfd_HMAX);
	G_free(outrast_I_HMAX);
	Rast_close (outfd_I_HMAX);
	G_free(outrast_T_HMAX);
	Rast_close (outfd_T_HMAX);
}
if (OUT_VMAX){
	G_free(outrast_VMAX);
	Rast_close (outfd_VMAX);
	G_free(outrast_I_VMAX);
	Rast_close (outfd_I_VMAX);
	G_free(outrast_T_VMAX);
	Rast_close (outfd_T_VMAX);
	if (flag_d->answer) {
		G_free(outrast_DIR_VMAX);
		Rast_close (outfd_DIR_VMAX);
	}
}
if (OUT_IMAX){
	G_free(outrast_IMAX);
	Rast_close (outfd_IMAX);
	G_free(outrast_T_IMAX);
	Rast_close (outfd_T_IMAX);
}
if (OUT_WAVEFRONT){
	G_free(outrast_WAVEFRONT);
	Rast_close (outfd_WAVEFRONT);
}

//************************************************************************
// da sistemare (TODO/To fix)
//************************************************************************
/* Add command line incantation to history file */
//G_short_history(result, "raster", &history);
//G_command_history(&history);
//G_write_history(result, &history);


/* deallocate memory matrix */
G_free_fmatrix(m_DAMBREAK);
G_free_fmatrix(m_m);
G_free_fmatrix(m_z);
G_free_dmatrix(m_h1);
G_free_dmatrix(m_h2);
G_free_dmatrix(m_u1);
G_free_dmatrix(m_u2);
G_free_dmatrix(m_v1);
G_free_dmatrix(m_v2);
G_free_imatrix(m_lake);
if( parm.opt_t->answer != NULL){
	G_free_vector(times);pp=0;
}
if (OUT_HMAX){
	G_free_fmatrix(m_hmax);
	G_free_fmatrix(m_t_hmax);
	G_free_fmatrix(m_i_hmax);
}
if (OUT_VMAX){
	G_free_fmatrix(m_vmax);
	G_free_fmatrix(m_i_vmax);
	G_free_fmatrix(m_t_vmax);
	if (flag_d->answer) {
		G_free_fmatrix(m_dir_vmax);
	}
}
if (OUT_IMAX){
	G_free_fmatrix(m_imax);
	G_free_fmatrix(m_t_imax);
}
if (OUT_WAVEFRONT){
	G_free_fmatrix(m_wavefront);
}

exit(EXIT_SUCCESS);

} //END MAIN.C







