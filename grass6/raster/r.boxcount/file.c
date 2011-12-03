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
 *
 * COPYRIGHT:    (C) 2008 by the authors
 *  
 *               This program is free software under the GNU General Public
 *   	    	 License (>=v2). Read the file COPYING that comes with GRASS
 *   	    	 for details.
 *
 *****************************************************************************/

#include <stdlib.h>
#include <string.h>
#include "file.h"
#include "math.h"


void Strip_path (char*, char*);

/**************************************************************************/

FILE* Create_file (char *name, char *suffix, char *message, int overwrite)
{
  FILE* stream;

  strcat (name, suffix);
  stream = fopen (name, "r");
  if ((stream != NULL) && (!overwrite))
    {
      sprintf (message, "File %s exits ", name);
      fclose (stream);
      return NULL;
    }
  else
    {
      stream = fopen (name, "w");
      if (stream == NULL)
	  sprintf (message, "Can't create file %s ", name);
    }
  
  return (stream);
}


/**************************************************************************/

void Functional_print (FILE *stream, tRecord *record,
		       int k, float *coef)
{
  int m;

  fprintf (stream, "\n  1/Box_size     Occupied    Log_1/Box_Size  Log_Occupied       D");
  for (m = 0; m <= k; m ++)
    {
      if (record [m].size != 0)
	{
	  fprintf (stream, "\n%12lu ", (unsigned long int) (pow (2, k - m)));
	  fprintf (stream, "%12lu ", record [m].occupied);
	  fprintf (stream, "           %6.3f ", record [m].log_reciprocal_size);
	  fprintf (stream, "       %6.3f", record [m].log_occupied);
	  
	  /* Fractal dimension only calculated for pairs
	     of points... */

	  if (m < k)
	    fprintf (stream, "  %6.3f", record [m].d);
	  else

	    /* ...so skip the last one and print a dummy value */

	    fprintf (stream, "  %6.3f", 99.999);
	}
    }
  fflush (stream);
}


/**************************************************************************/

void Pretty_print (FILE *stream, tRecord *record,
		   int k, int r, int points_used,
		   float *coef)
{
  int m;

  fprintf (stream, "\n\nResults:");
  fprintf (stream, "\n  1/Box size     Occupied    Log 1/Box Size  Log Occupied       D");
  for (m = 0; m <= k; m ++)
    {
      fprintf (stream, "\n%12lu ", (unsigned long int) (pow (2, k - m)));
      if (record [m].size == 0)
	fprintf (stream, "   -------------- too few map cells ----------------");
      else
	{
	  fprintf (stream, "%12lu ", record [m].occupied);
	  fprintf (stream, "           %6.3f ", record [m].log_reciprocal_size);
	  fprintf (stream, "       %6.3f", record [m].log_occupied);

	  /* Fractal dimension only calculated for pairs
	     of points... */

	  if (m < k)
	    fprintf (stream, "  %6.3f", record [m].d);
	  else

	    /* ...so skip the last one */

	    fprintf (stream, "  ------");
	}
    }
  if (points_used >= 2)
    {
      fprintf (stream, "\n\nD by regression on 1/box sizes %lu to %lu (inc.) is: %6.3f\n", 
	       (unsigned long int) pow (2, r),
	       (unsigned long int) pow (2, r + points_used - 1),
	       coef [1]);
    }
  fflush (stream);
}


/**************************************************************************/

void Print_gnuplot_commands (FILE *stream,
			     char *out_dat_name,
			     tRecord *record,
			     int k,
			     int r, int points_used,
			     float *coef)
{
  int m;
  float x, y, max;
  char message [196];
  char filename [128];

  /* Strip path from out_dat_name (for tcltkgrass) */

  Strip_path (out_dat_name, filename);

  sprintf (message, "%s  (D by regression on log10 1/s = %5.3f to %5.3f (inc.) is: %6.3f)", 
	   filename,
	   record [k - r].log_reciprocal_size, 
	   record [k - r - points_used + 1].log_reciprocal_size,
	   coef [1]);


  /* Find greatest x val and add a bit to ensure that plot area
     will be large enough to accomodate last label */

  max = 0.0;
  for (m = 0; m <= (k - 1); m ++)
    {
      if (record [m].log_reciprocal_size > max)
	max = record [m].log_reciprocal_size;
    }

  /* Ensure that x axis ends on an integer multiple of 1 or 0.5 */
  
  x = (float) ceil ((double) max + 0.2);
  if ((x - max) > 0.5)
    x -= 0.5;

  /* Setup the x and y axes */

  fprintf (stream, "set xlabel 'log10 1/s'");
  fprintf (stream, "\nset ylabel 'log10 NbE'");
  fprintf (stream, "\nset xrange [0:%f]", x);
  fprintf (stream, "\nset yrange [0:*]");
  

  /* Plot fractal dimensions of pairs of points as labels
     halfway between them.  Skip biggest box since fractal 
     dimension is only calculated for pairs of points */

  for (m = 0; m <= (k - 1); m ++)                    
  {
    if (record [m].size != 0)
      {
	x = record [m + 1].log_reciprocal_size
	  + ((record [m].log_reciprocal_size
	      - record [m + 1].log_reciprocal_size) / 2);
	y = record [m + 1].log_occupied
	  + ((record [m].log_occupied 
	      - record [m + 1].log_occupied) / 2);

	/* Subtract a tiny amount from y to ensure
	   that the label clears the plotted line */

	fprintf (stream, "\nset label '%6.3f' at %f,%f left", 
		 record [m].d, x, y - 0.1);
    }
  }


  /* Issue instructions to plot graph */

  fprintf (stream, "\nplot '%s' using ($3):($4) title '%s' with linespoints",
	   out_dat_name, message);
  fprintf (stream, "\npause -1 'Hit RETURN to delete graph'");
}


/**************************************************************************/

void Terse_print (FILE *stream,
		   int r, int points_used,
		   float *coef)
{
  if (points_used >= 2)
    {
      fprintf (stream, "D by regression on 1/box sizes %lu to %lu (inc.) is: %6.3f\n", 
	       (unsigned long int) pow (2, r),
	       (unsigned long int) pow (2, r + points_used - 1),
	       coef [1]);
    }
  else
    {
	  /* we need 12 tokens in output for r.boxcount.sh ... */
	  fprintf (stream, "D cannot be calculated - using NO DATA value . . -1\n");  
    }
  fflush (stream);
}

/**************************************************************************/

void Strip_path (char *fqfn, char *fn)
{
  int pos, start, end, i;
  
  end = strlen (fqfn);
  pos = end;
  while ((fqfn [pos] != '/') && (pos >= 0))
    pos --;
  if (pos == -1)
    {
      strcpy (fn, fqfn);
    }
  else
    {
      start = pos + 1;
      i = 0;
      for (pos = start; pos <= end; pos ++)
	{
	  fn [i] = fqfn [pos];
	  i ++;
	}
      fn [i] = '\0';
    }
}
  


  
