#include <grass/gis.h>


int do_histogram(char *name, char *mapset)
{
    CELL *cell;
    struct Cell_head cellhd;
    struct Cell_stats statf;
    int nrows, ncols, row;
    int fd;

    if (G_get_cellhd(name, mapset, &cellhd) < 0)
	return 0;

    G_set_window(&cellhd);
    fd = G_open_cell_old(name, mapset);
    if (fd < 0)
	return 0;

    nrows = G_window_rows();
    ncols = G_window_cols();
    cell = G_allocate_cell_buf();

    G_init_cell_stats(&statf);
    for (row = 0; row < nrows; row++) {
	if (G_get_map_row_nomask(fd, cell, row) < 0)
	    break;

	G_update_cell_stats(cell, ncols, &statf);
    }
    G_close_cell(fd);
    G_free(cell);

    if (row == nrows)
	G_write_histogram_cs(name, &statf);

    G_free_cell_stats(&statf);

    return 0;
}
