/*
  The following routines are written and tested by Stefano Merler

  for
  
  open new raster maps
*/

#include <stdlib.h>
#include <grass/gis.h>

int open_new_CELL(name)
     /* 
	open a new raster map of name name in CELL format
     */
     char *name;
{
  int fd;
  char err[400];
    
  if (G_legal_filename (name) < 0)
    {
      sprintf (err, "%s - ** illegal name **", name);
      G_fatal_error (err);
      exit(1);
    }

  fd = G_open_raster_new (name, CELL_TYPE);
  if (fd < 0)
    {
      sprintf (err, "failed in attempt to open %s\n", name);
      G_fatal_error (err);
      exit(1);
    }

  return fd;
}

int open_new_DCELL(name)
     /* 
	open a new raster map of name name in DELL format
     */
     char *name;
{
  int fd;
  char err[400];
    
  if (G_legal_filename (name) < 0)
    {
      sprintf (err, "%s - ** illegal name **", name);
      G_fatal_error (err);
      exit(1);
    }

  fd = G_open_raster_new (name, DCELL_TYPE);
  if (fd < 0)
    {
      sprintf (err, "failed in attempt to open %s\n", name);
      G_fatal_error (err);
      exit(1);
    }

  return fd;
}
