#include "local_proto.h"

/* open raster layer */
void open_layer(struct int_par *xD, struct reg_par *reg, struct output *out)
{
    struct write *report = &xD->report;

    /* 2D Raster layer */
    if (xD->i3 == FALSE) {
        out->dcell = (DCELL *)Rast_allocate_buf(DCELL_TYPE);
        out->fd_2d =
            Rast_open_new(out->name, DCELL_TYPE); /* open output raster */
        if (out->fd_2d < 0) {
            report_error(report);
            G_fatal_error(_("Unable to create 2D raster <%s>"), out->name);
        }
    }
    /* 3D Raster layer */
    if (xD->i3 == TRUE) {
        out->fd_3d = (RASTER3D_Map *)Rast3d_open_cell_new(
            out->name, DCELL_TYPE, RASTER3D_USE_CACHE_XYZ,
            &reg->reg_3d); // initialize pointer to 3D region

        if (out->fd_3d == NULL) {
            report_error(report);
            G_fatal_error(_("Unable to create 3D raster <%s>"), out->name);
        }
    }
}

void write2layer(struct int_par *xD, struct reg_par *reg, struct output *out,
                 mat_struct *rslt)
{
    // Local variables
    int i3 = xD->i3;
    int ndeps = reg->ndeps, nrows = reg->nrows, ncols = reg->ncols;
    struct write *report = &xD->report;

    int col, row, dep;
    int pass = 0; /* Number of processed cells */
    double trend, value, r0[3];
    int nulval = 0;

    for (dep = 0; dep < ndeps; dep++) {
        for (row = 0; row < nrows; row++) {
            for (col = 0; col < ncols; col++) {
                value = G_matrix_get_element(rslt, dep * nrows + row, col);
                if (value == 0.) {
                    nulval++;
                }

                switch (i3) {
                case FALSE: /* set value to cell (2D) */
                    out->dcell[col] = (DCELL)(value);
                    break;

                case TRUE: /* set value to voxel (based on part of r3.gwflow
                              (Soeren Gebbert)) */
                    if (Rast3d_put_double(out->fd_3d, col, row, dep, value) ==
                        0) {
                        report_error(report);
                        G_fatal_error(
                            _("Error writing cell (%d,%d,%d) with value %f."),
                            row, col, dep, value);
                    }

                    break;
                }
                pass++;
            } // end col
            if (i3 == FALSE) {
                Rast_put_row(out->fd_2d, out->dcell, DCELL_TYPE);
            }
        } // end row
    }     // end dep

    switch (i3) {
    case TRUE:
        if (!Rast3d_close(out->fd_3d)) { // Close 3D raster map
            G_fatal_error(_("Something went wrong with 3D raster: the pointer "
                            "disappeared before closing..."));
        }
        break;
    case FALSE:
        Rast_close(out->fd_2d); // Close 2D raster map
        break;
    }

    if (nulval > 0) {
        G_message(_("0 values: %d"), nulval);
    }

    if (pass != ndeps * ncols * nrows) {
        G_fatal_error(_("The number of processed cells (%d) is smaller than "
                        "total number of cells (%d)..."),
                      pass, ndeps * ncols * nrows);
    }
}
