#include <grass/gis.h>
#include <grass/raster.h>

int do_histogram(const char *name, const char *mapset)
{
    CELL *cell;
    struct Cell_head cellhd;
    struct Cell_stats statf;
    int nrows, ncols, row;
    int fd;
    struct Cell_head region;

    Rast_get_cellhd(name, mapset, &cellhd);
    /*    if (Rast_get_cellhd (name, mapset, &cellhd) < 0)
       return 0;
     */

    G_set_window(&cellhd);
    fd = Rast_open_old(name, mapset);
    if (fd < 0)
        return 0;

    G_get_window(&region);

    nrows = region.rows;
    ncols = region.cols;

    /*    nrows = G_window_rows ();
       ncols = G_window_cols ();
     */
    cell = Rast_allocate_c_buf();

    Rast_init_cell_stats(&statf);
    for (row = 0; row < nrows; row++) {
        Rast_get_c_row_nomask(fd, cell, row);
        /* break; */

        Rast_update_cell_stats(cell, ncols, &statf);
    }
    Rast_close(fd);
    G_free(cell);

    if (row == nrows)
        Rast_write_histogram_cs(name, &statf);

    Rast_free_cell_stats(&statf);

    return 0;
}
