#include "local_proto.h"

/* open raster layer */
void open_layer(struct int_par *xD, struct reg_par *reg, struct output *out)
{
  struct write *report = &xD->report;
  /* 2D Raster layer */
  if (xD->i3 == FALSE) {
    out->dcell = (DCELL *) Rast_allocate_buf(DCELL_TYPE);
    out->fd_2d = Rast_open_new(out->name, DCELL_TYPE);	/* open output raster */
    if (out->fd_2d < 0) {
      if (report->write2file == TRUE) { // close report file
	fprintf(report->fp, "Error (see standard output). Process killed...");
	fclose(report->fp);
      }
      G_fatal_error(_("Unable to create 2D raster <%s>"), out->name);
    }
  }
  /* 3D Raster layer */
  if (xD->i3 == TRUE) {
    out->fd_3d = (RASTER3D_Map *) Rast3d_open_cell_new(out->name, DCELL_TYPE, RASTER3D_USE_CACHE_XYZ, &reg->reg_3d); // initialize pointer to 3D region
    if (out->fd_3d == NULL) {
      if (report->write2file == TRUE) { // close report file
	fprintf(report->fp, "Error (see standard output). Process killed...");
	fclose(report->fp);
      }
      G_fatal_error(_("Unable to create 3D raster <%s>"), out->name);
    }
  }
}

int write2layer(struct int_par *xD, struct reg_par *reg, struct output *out, unsigned int col, unsigned int row, unsigned int dep, double rslt_OK)
{
  // Local variables
  int i3 = xD->i3;
  struct write *report = &xD->report;

  int pass = 0; /* Number of processed cells */
  switch (i3) {
  case FALSE: /* set value to cell (2D) */
    out->dcell[col] = (DCELL) (rslt_OK); 
    pass++;
    if (col == reg->ncols-1)
      Rast_put_row(out->fd_2d, out->dcell, DCELL_TYPE);
    break;

  case TRUE: /* set value to voxel (based on part of r3.gwflow (Soeren Gebbert)) */
    if (Rast3d_put_double(out->fd_3d, col, row, dep, rslt_OK) == 0) {
      if (report->write2file == TRUE) { // close report file
	fprintf(report->fp, "Error (see standard output). Process killed...");
	fclose(report->fp);
      }
      G_fatal_error(_("Error writing cell (%d,%d,%d) with value %f, nrows = %d"), row, col, dep, rslt_OK, reg->nrows);
    }
    pass++;
    break;
  }
  return pass;
}

