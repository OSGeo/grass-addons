#include <stdio.h>
#include <sys/stat.h>
#include <stdlib.h>
#include "globals.h"
#include <grass/glocale.h>

void write_map(struct Cell_head *cellhd, char *name, char *mapset, char *dest)
{
    int fd_to, fd_from, row, nrows, ncols;
    CELL *buf;
    char command[500];
    char *lp, *lm;
    char *coldir;
    struct stat statdir;

    G_set_window(cellhd);

    fd_from = Rast_open_old(name, mapset);
    if (fd_from < 0)
        G_fatal_error(_("Error reading raster map <%s> in mapset <%s>"), name,
                      mapset);

    fd_to = Rast_open_c_new(dest);
    if (fd_to < 0)
        G_fatal_error(_("Error writing raster map <%s> in mapset <%s>"), dest,
                      G_mapset());

    buf = Rast_allocate_buf(CELL_TYPE);

    ncols = Rast_window_cols();
    nrows = Rast_window_rows();

    for (row = 0; row < nrows; row++) {
        Rast_get_row(fd_from, buf, row, CELL_TYPE);
        Rast_put_row(fd_to, buf, CELL_TYPE);
    }

    /* memory cleanup */
    G_free(buf);
    Rast_close(fd_to);
    Rast_close(fd_from);

    if ((mapset = G_find_file("colr", name, mapset)) != NULL) {

        lp = G_location_path();
        lm = G_mapset();

        coldir = G_calloc(500, sizeof(char));
        sprintf(coldir, "%s/%s/colr", lp, lm);
        if (stat(coldir, &statdir) == -1) {
            mkdir(coldir, 0755);
        }
        else {
            if (!S_ISDIR(statdir.st_mode)) {
                G_fatal_error("coldir is not a dir");
            }
        }

        sprintf(command, "cp %s/%s/colr/%s %s/%s/colr/%s", lp, mapset, name, lp,
                lm, dest);
        sprintf(command, "cp %s/%s/colr/%s %s/%s/colr/%s", lp, mapset, name, lp,
                lm, dest);
        system(command);
    }
}
