/****************************************************************************
 *
 * MODULE:       r.boxcount
 * AUTHOR(S):    
 *
 *  Original author:
 *  Mark Lake  14/5/99
 *  
 *  University College London
 *  Institute of Archaeology
 *  31-34 Gordon Square
 *  London.  WC1H 0PY
 *  email: mark.lake@ucl.ac.uk
 * 
 *  Adaptations for grass63:
 *  Florian Kindl, 2006-10-02
 *  University of Innsbruck
 *  Institute of Geography
 *  email: florian.kindl@uibk.ac.at
 *
 * PURPOSE: 
 *  
 *  1) Calculates the capacity, or box-counting, fractal dimension
 *  of a  binary raster map.  The box-counting dimension is 
 *  calculated for each pair of box sizes and by linear
 *  regression over a range of box sizes.
 *  
 *  OPTIONS:
 *  
 *  1) Functional options determine which box sizes are used 
 *  in the linear regression.
 *  
 *  2) Output options allow detailed results to be reported to
 *  stdout, saved to a file and graphed using gnuplot.
 *  
 *  METHOD:
 *  
 *  1) For an introduction to the box-counting method of
 *  calculating fractal dimension see:
 *  Peitgen, Jurgens and Saupe, 1992, 'Chaos and
 *  Fractals: New Frontiers of Science', Springer-Verlag:
 *  New York. Chapt. 4.
 *  
 *  2) This program is based on the algorithm described in:
 *  Liebovitch and Toth, 1989, 'A Fast Algorithm to 
 *  Determine Fractal Dimension by Box Counting'.  In
 *  Physics Letters A, vol. 141, pp.386--390.
 *  
 *  Note, however, that it uses an improved method
 *  the same or similar to that suggested by Daniel Kaplan
 *  (see note on p.389).
 *  
 *  3) For more detailed information see the file 'Method.ps'.
 *  
 *  FILES:
 *  
 *  1) main.c - most of box counting algorithm
 *  and calculates the fractal dimension.
 *  
 *  2) sort.c - a radix exchange sort used during box counting.
 *  
 *  3) bits.c - functions that manipulate bits of a word.
 *  
 *  4) file.c - functions that output the results.
 *  
 *  PORTABILITY:
 *  
 *  1) The functions in 'bits.c' manipuluate individual bits
 *  and might need modification on a Big-Endian machine
 *  (e.g SPARC, 68xxx).  This code was developed on an 80586.
 *
 * COPYRIGHT:    (C) 2008 by the authors
 *  
 *               This program is free software under the GNU General Public
 *   	    	 License (>=v2). Read the file COPYING that comes with GRASS
 *   	    	 for details.
 *
 *****************************************************************************/

#define MAIN

#define kCells_in_block 10000         /* No of cells per block of memory */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <limits.h>
#include <unistd.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include "bits.h"
#include "sort.h"
#include "file.h"
#include "record.h"

/* 
 * global function declaration 
 */
extern CELL f_c(CELL);
extern FCELL f_f(FCELL);
extern DCELL f_d(DCELL);

/*
 * function definitions 
 */

CELL c_calc(CELL x)
{
    /* we do nothing exciting here */
    return x;
}

FCELL f_calc(FCELL x)
{
    /* we do nothing exciting here */
    return x;
}

DCELL d_calc(DCELL x)
{
    /* we do nothing exciting here */
    return x;
}

/*
 * main function
 * it copies raster input raster file, calling the appropriate function for each
 * data type (CELL, DCELL, FCELL)
 */
int main(int argc, char *argv[])
{

/* from r.example */

    struct Cell_head cellhd;	/* it stores region information,
				   and header information of rasters */
    char *name;			/* input raster name */
    char *result;		/* output raster name */
    char *mapset;		/* mapset name */
    void *inrast;		/* input buffer */
    unsigned char *outrast;	/* output buffer */
    int infd, outfd;		/* file descriptor */
    int verbose;
    RASTER_MAP_TYPE data_type;	/* type of the map (CELL/DCELL/...) */
    struct History history;	/* holds meta-data (title, comments,..) */

    struct GModule *module;	/* GRASS module for parsing arguments */

    struct Flag *flag1;		/* flags */

/* from r.boxcount42 */

  FILE *out_dat_str = NULL;
  FILE *out_gnuplot_str = NULL;
  char out_dat_name [128], out_gnuplot_name [128];
  int in_map_fd;
  char *current_mapset;
  int projection;
  int array_south, array_north;
  int array_east, array_west;
  int nrows, ncols, left;
  CELL *row_of_cells;
  tRecord *record;
  unsigned long int no_boxes, occupied_boxes;
  unsigned long int cell, no_cells;
  int cells_in_this_block, no_blocks;
  long int block;
  int r, k, max_k, step, m, i, j, n, max;
  int points_used;
  int col, row;
  unsigned int x, y, M, *keys;
  float row_factor, col_factor;
  float **f, a[2][3], coef[2], t;
  float s;
  int tmp1;
  float tmp2;
  char message [192];
  struct Option *input, *output, *k_opt, *r_opt, *s_opt;
  struct Flag *gnuplot, *now, *overwrite, *terse;


  /***********************************************************************/
  /* Preliminary things                                                  */
  /***********************************************************************/

  /* Initialize the GIS calls */

  G_gisinit(argv[0]);
  G_sleep_on_error (0);

    /* initialize module */
	/*
    module = G_define_module();
    module->keywords = _("keyword1, keyword2, keyword3");
    module->description = _("My first raster module");
*/
    /* Define the different options as defined in gis.h */
    input  = G_define_standard_option(G_OPT_R_INPUT);

  output = G_define_option ();
  output->key = "output";
  output->type = TYPE_STRING;
  output->required = NO;
  output->description = "Output text file for data points";

  k_opt = G_define_option ();
  k_opt->key = "k";
  k_opt->type = TYPE_INTEGER;
  k_opt->required = YES;
  k_opt->description = "Max 1/box size is 2^k ";
  s_opt = G_define_option ();
  s_opt->key = "saturation";
  s_opt->type = TYPE_DOUBLE;
  s_opt->description =
    "Occupied boxes as fraction of data points at saturation";
  s_opt->answer = "0.2";
  r_opt = G_define_option ();
  r_opt->key = "resolution";
  r_opt->type = TYPE_INTEGER;
  r_opt->description =
    "Smallest 1/box size to use in regression (= 1, 2, 4,...)";
  r_opt->answer = "4";

    /* Define the different flags */

  gnuplot = G_define_flag ();
  gnuplot->key = 'g';
  gnuplot->description = "Create file with instructions for Gnuplot ";
  now = G_define_flag ();
  now->key = 'n';
  now->description = "Gnuplot graph now (i.e. on exit from r.boxcount) ";
  overwrite = G_define_flag ();
  overwrite->key = 'o';
  overwrite->description = "Overwrite output file if it exists ";
  terse = G_define_flag ();
  terse->key = 't';
  terse->description = 
    "Terse output only (i.e. only report D calculated by regression) ";

  /* Parse the command line arguments, or get parameters if none */
    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

  /* Check that database is UTM or x-y referenced */
/* fkindl: why is that??  - I kicked it out and it works with M28, too... */

/*
  projection = G_projection ();
  if (projection != PROJECTION_UTM && projection != PROJECTION_XY)
    G_fatal_error ("Can't use database\n\t\t- not UTM or X-Y");
  */

  /* Open the raster map for reading */

    /* returns NULL if the map was not found in any mapset, 
     * mapset name otherwise */
    
	name=input->answer;
    mapset = G_find_cell2(name, "");
    if (mapset == NULL)
	G_fatal_error(_("cell file [%s] not found"), name);
  

    /* determine the inputmap type (CELL/FCELL/DCELL) */
    data_type = G_raster_map_type(name, mapset);

    /* G_open_cell_old - returns file destriptor (>0) */
    if ((in_map_fd = G_open_cell_old(name, mapset)) < 0)
	G_fatal_error(_("Cannot open cell file [%s]"), name);

    /* controlling, if we can open input raster */
    if (G_get_cellhd(name, mapset, &cellhd) < 0)
	G_fatal_error(_("Cannot read file header of [%s]"), name);
    G_debug(3, "number of rows %d", cellhd.rows);



  
  /* If required, open the output files for writing */
    
  if (output->answer != NULL)
    {
      strcpy (out_dat_name, output->answer);
      out_dat_str = Create_file (out_dat_name, ".dat",
				 message, overwrite->answer);
      if (out_dat_str == NULL)
	G_fatal_error (message);


      if (gnuplot->answer)
	{
	  strcpy (out_gnuplot_name, output->answer);
	  out_gnuplot_str = Create_file (out_gnuplot_name, ".gnu",
					 message, overwrite->answer);
	  if (out_gnuplot_str == NULL)
	    G_fatal_error (message);
	}
    }




  /* Calculate array limits */

  array_south = G_window_rows () - 1;
  array_north = 0;
  array_west = 0;
  array_east = G_window_cols () - 1;
  nrows = G_window_rows ();
  ncols = G_window_cols ();


  /* Allocate memory for one row of map */

  row_of_cells = G_allocate_cell_buf ();


  /* Copy the numeric parameters from the parser */

  sscanf (k_opt->answer, "%d", &k);
  sscanf (s_opt->answer, "%f", &s);
  sscanf (r_opt->answer, "%d", &r);

  
  
  /* Convert r to the value of m which produces it.
     I.e. r (as given) = 2^r (as calculated here).
     This value of r determines the lowest value of
     m used when choosing which box sizes to include
     in the linear regression (e.g. m = r, r+1, r+2,..., k) */

  tmp2 = frexp ((double) r, &r);
  r -= 1;                        /* Because frexp returns 0.5 <= exp < 1 */
  if (r < 0)
    G_fatal_error ("Problem with r ");
  else
    if (r > k)
      G_fatal_error ("r must be <= 2^k ");        /* That is, r as given */


  /* Check that k is not too big.  There are two 
     limits:
     1) The no. of bits available in each element
     of the array `keys' 
     2) It must be possible to store the max. no. of
     boxes (2^k * 2^k) in `cell' which, since it is an
     array subscript, must necessarily be an integer
     When an unsigned int and an unsigned long int are
     the same size then 2) is the ultimate limit, but
     we check both 1) and 2) just in case */

  max_k = Bits_in_pwr_two_can_sqr_and_store_in ('l') ;       /* Check 2) */
  if ((Bits_available ('i') / 2) < max_k)
    max_k = Bits_available ('i') / 2;                        /* Check 1) */

  if (k > max_k)
    {
      sprintf (message, "Sorry, k is too big - %d is max. for this machine ",
	       max_k);
      G_fatal_error (message);
    }
  

  /* Allocate memory for structure used to record results */
  
  record = (tRecord*) malloc ((k + 1) * sizeof (tRecord));
  if (record == NULL)
    G_fatal_error ("Unable to allocate memory for record structure ");
				     

  /* Calculate reduction factors for normalisation. 
     N.B., the result of applying these factors is truncated to the 
     integer component.  This results in normalisation
     between 0, ..., 2^k -1.  The reason for subtracting
     a very small value (0.01) here is to ensure that the
     coordinates are spread across all boxes.  If the factors
     were calculated using 2^k - 1 then the box with coordinates
     2^k -1, 2^k -1 would only contain the point with coordinates
     ncols, nrows. */
  
  row_factor = (nrows - 1) / (pow (2, k) - 0.01);
  col_factor = (ncols - 1) / (pow (2, k) - 0.01);


  /***********************************************************************/
  /* Normalise coordinates of every map cell which has a non-zero
     value                                                               */
  /***********************************************************************/

  /* Allocate memory for array of keys to store the normalised
     coordinates of every map cell which has a non-zero value.
     Do this by allocating memory in blocks adequate for kCells_in_block 
     keys.  The rationale here is to avoid reading from disk twice:
     once to count non-zero cells and then again to normalise them
     after having allocated memory according to the number counted.
     A linked-list might seem the obvious solution, but it suffers from 
     two problems: it ultimately requires more memory, and it 
     complicates the sort process. */

  block = kCells_in_block * sizeof (unsigned int);
  keys = (unsigned int*) malloc (block);
  if (keys == NULL)
    G_fatal_error ("Not enough memory");

  
  /* Trawl through disk file, reallocating memory after
     every kCells_in_block non-zero cells */

  if (!terse->answer)
    fprintf (stderr, "\nNormalising coordinates ");
  no_blocks = 1;
  cells_in_this_block = 0;
  cell = 0;
  for  (row = 0; row < nrows; row ++)
    {
      G_get_map_row (in_map_fd, row_of_cells, row);
      for (col = 0; col < ncols; col ++)
	{
	  if (row_of_cells [col] != 0)
	    {
	      x = (unsigned int) (col / col_factor);
	      y = (unsigned int) (row / row_factor);
	      
	      /* Combine coordinates into one string 
		 of 2k bits such that highest bit
		 of x is followed by the highest bit of
		 y, etc. (see bits.c for a detailed
		 explanation) */

	      keys [cell] = Create_cyclic_bit_string (x, y, k);
	      cell ++;
	      
	      /* Check that allocated memory has not been exhausted */

	      cells_in_this_block ++;
	      if (cells_in_this_block ==  kCells_in_block)
		{
		  no_blocks ++;
		  cells_in_this_block = 0;
		  keys = (unsigned int*) realloc ((void*) 
						  keys, no_blocks * block);
		  if (keys == NULL)
		    {
		      sprintf (message, "Not enough memory for cells %d+ ",
			       cell);
		    G_fatal_error (message);
		    }
		}
	    }      
	}	
    }
  no_cells = cell;
  if (!terse->answer)
    fprintf (stderr, "   - done "); fflush (stderr);


  /***********************************************************************/
  /* Sort all keys                                                       */
  /***********************************************************************/

  if (!terse->answer)
    fprintf (stderr, "\nSorting coordinates     ");
  Radix_exchange_sort_array (keys,
				 0, no_cells -1, (2 * k) - 1);

#ifdef DEBUG
  for (cell = 0; cell < no_cells; cell ++)
    fprintf (stdout, "\ncell = %12ld, key = %u ",
	     cell, keys [cell]); fflush (stdout);
#endif

  if (!terse->answer)
    fprintf (stderr, "   - done "); fflush (stderr);
	  

  /***********************************************************************/
  /* Count the minimum number of boxes of size 1/2^m,
     where m=k, k-1, k-2,...,0, required to cover every
     map cell which has a non-zero value.  Note that the 
     minimum resolution, r, and saturation, s, are ignored
     here - they only constrain the box sizes used during
     regression                                                          */
  /***********************************************************************/

  if (!terse->answer)
    fprintf (stderr, "\nCounting occupied boxes ");
  for (m = 0; m <= k; m ++)
    {
      
#ifdef DEBUG
      no_boxes = (unsigned long int) (pow (2, k - m) * pow (2, k - m));
      fprintf (stderr, "\n%12lu boxes ", no_boxes);
#endif

      /* If the number of boxes in a row or column is,
         for this m, greater than the number of map cells... */

      if ((pow (2, k) / pow (2, m) > nrows) ||
	  (pow (2, k) / pow (2, m) > ncols))
	{
	  /* Record that count was skipped for this m */

	  record [m].size = 0;
	}
      else
	{      
	  /* Record 1/box size for this m */

	  record [m].size = pow (2, k - m);

	  /* Calculate mask, M, for each coordinate x and y... */

	  M = 0;
	  for (i = k; i > m; i --)
	    M += pow (2, i - 1);
	  
	  /* ...and combine using same cyclic ordering
	     that was used to create the keys */

	  M = Create_cyclic_bit_string (M, M, k);

#ifdef DEBUG
	  fprintf (stdout, "\n\nm = %d, M = %u ", m, M); fflush (stdout);
#endif	  

	  /* Mask all keys in 'keys' */

	  for (cell = 0; cell < no_cells; cell ++)
	      keys [cell] = keys [cell] & M;

	  /* Count number of changes in the array 'keys'.
             Remember that the cyclic ordering of bits
	     in the keys and mask ensures that progressive 
	     masking, e.g 11111111, 11111100, 11110000,...
	     does not unsort the array */

	  occupied_boxes = 1;
	  for (cell = 1; cell < no_cells; cell ++)
	    {
	      if (keys [cell] != keys [cell - 1])
		occupied_boxes ++;
	    }
	  record [m].occupied = occupied_boxes;
	}
    }
  if (!terse->answer)
    fprintf (stderr, "   - done" );

  /* Free memory */

  free (keys);


  /***********************************************************************/
  /* Calculate log values for all m                                      */
  /***********************************************************************/

  for (m = 0; m <= k; m ++)
    {
      record [m].log_occupied = log10 (record [m].occupied);
      record [m].log_reciprocal_size = log10 (record [m].size);
    }


  /***********************************************************************/
  /* Calculate fractal dimension for each pair of data points            */
  /***********************************************************************/

  if (!terse->answer)
    fprintf (stderr, "\nCalculating dimensions ");
  for (m = 0; m < k; m++)
    {
    record [m].d = (record [m].log_occupied - record [m + 1].log_occupied) / 
      (record [m].log_reciprocal_size - record [m + 1].log_reciprocal_size);
    }


  /***********************************************************************/
  /* Calculate the fractal dimension by least squares regression 
     on box sizes 1/2^m for m = r, r+1, r+2,...,m_max.  m_max
     is determined by the saturation fraction, s, such that 
     m_max = k if s = 1.0, but m_max < k if s < 1.0.                     */
  /***********************************************************************/

  /* Set up arrays for vectors used to calculate matrix for
     Gaussian elimination */

  f = (float**) malloc (3 * sizeof (float*));
  if (f == NULL)
    G_fatal_error ("Not enough memory ");
  else
    for (i = 0; i < 3; i++)
      {
	f[i] = (float*) malloc ((k - r + 1) * sizeof (float));
	if (f == NULL)
	  G_fatal_error ("Not enough memory ");
      }
  
  /* Compute vectors appropriate for function of the form
     y = a*x + b. Ignore data for m < r (resolution too
     poor) and for occupied > no_cells * s (minimum number of boxes
     required to cover non-zero map cells is too close to number 
     of non-zero map cells - i.e. saturation reached) */

  points_used = 0;
  m = k - r;;
  while (( m >= 0) && (record [m].occupied < (no_cells * s))
	 && record [m].size != 0)
    {
      f[0][m] = 1.0;                                                /* b */
      f[1][m] = record [m].log_reciprocal_size;              /* a*x vals */
      f[2][m] = record [m].log_occupied;                       /* y vals */

#ifdef DEBUG
      fprintf (stderr, "\nm = %d  f[0] = %6.3f, f[1] = %6.3f, f[2] = %6.3f", m, f[0][m], f[1][m], f[2][m]); fflush (stderr);
#endif

      m --;
      points_used ++;
    }
  
  if (points_used >= 2)
    {      
      /* Compute matrix for Gaussian elimination */

      for (i = 0; i <= 1; i++)
	{
	  for (j = 0; j <= 2; j++)
	    {
	      t = 0.0;
	      for (n = (k - r); n > m; n --)
		t += f[i][n] * f[j][n];
	      a [i][j] = t;

#ifdef DEBUG
	      fprintf (stderr, "\na[%d][%d] = %f", i, j, a[i][j]); fflush (stderr);
#endif

	    }
	}
      
      /* Forward-elimination phase */
      
      for (i = 0; i <= 1; i++)
	{
	  max = i;
	  for (j = i + 1; j <= 1; j++)
	    {
	      if (abs (a [j][i]) > abs (a [max][i]))
		max = j;
	    }
	  for (n = i; n <= 2; n++)
	    {
	      t = a [i][n];
	      a [i][n] = a [max][n];
	      a [max][n] = t;
	    }
	  for (j = i + 1; j <= 1; j++)
	    for (n = 2; n >= i; n--)
	      a [j][n] -= a [i][n] * a [j][i] / a [i][i];
	}
      
      /* Backward-substitution phase.
	 The coefficients a is returned in coef [1] and
	 the coefficient b in coef [0] */
      
      for (j = 1; j >= 0; j --)
	{
	  t = 0.0;
	  for (n = j + 1; n <= 1; n++)
	    t += a [j][n] * coef [n];
	  coef [j] = (a [j][2] - t) / a [j][j];
	}
      
      if (!terse->answer)
	fprintf (stderr, "    - done ");
    }

  else
    {
      if (!terse->answer)
	{
	  fprintf (stderr, "            - two few data points");
	  fprintf (stderr, 
		   "\n                                     for least squares regression");
	  fprintf (stderr, 
		   "\n                                     (try increasing s) ");
	}
    }

#ifdef DEBUG
  fprintf (stderr, "\n\n eqn is %6.3f x + %6.3f ", coef [1], coef [0]);
  fflush (stderr);
#endif



  /***********************************************************************/
  /* Report results                                                      */
  /***********************************************************************/

  /* If requested, output results to files */

  if (out_dat_str != NULL)
    {
      if (!terse->answer)
	fprintf (stderr, "\nSaving results to file '%s' ", out_dat_name);
      Functional_print (out_dat_str, record, k, coef);
      if (out_gnuplot_str != NULL)
	{
	  if (!terse->answer)
	    fprintf (stderr, "\nSaving commands to file '%s' ",
		 out_gnuplot_name);
	  Print_gnuplot_commands (out_gnuplot_str, out_dat_name,
				record, k, r, points_used, coef);
	}
    }


  /* Output results to screen in pretty or terse form */
  
  if (!terse->answer)
    Pretty_print (stdout, record, k, r, points_used, coef);
  else
    Terse_print (stdout, r, points_used, coef);


  /* Tidy up and, if requested, produce gnuplot graph */

  G_close_cell (in_map_fd);

  if (out_dat_str != NULL)
    {
      fclose (out_dat_str);
      if (out_gnuplot_str != NULL)
	{
	  fclose (out_gnuplot_str);

	  /* Spawn gnuplot in place of this process.
	     Note that we don't get here unless the command file
	     was created */

	  if (now->answer)
	    {

	      /* This is the neat way of spawning Gnuplot
		 because it allows control from the GRASS shell.
		 But we don't use it becuase it isn't compatible
		 with tcltkgrass... */

	      /* fprintf (stderr, "\n");
		 execlp ("gnuplot", "gnuplot", out_gnuplot_name, 0);*/

	      /* ...so we do this instead (which is messy because it
		 adds another xterm). */

	      char command_line [256];
	      sprintf (command_line,
		       "xterm -e gnuplot %s &", out_gnuplot_name);
	      system (command_line);
	    }
	}
    }


  /* We only get here if not doing gnuplot */

  if (!terse->answer)
    fprintf (stderr, "\nJob finished\n");

  return (0);
}
