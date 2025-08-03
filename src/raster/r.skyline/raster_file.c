/***********************************************************************/
/*
   raster_file.c

   Revised by Mark Lake, 28/07/20017, for r.skyline in GRASS 7.x
   Revised by Mark Lake, 26/07/20017, for r.horizon in GRASS 7.x
   Revised by Mark Lake, 16/07/2007, for r.horizon in GRASS 6.x
   Written by Mark Lake, 15/07/2002, for r.horizon in GRASS 5.x

 */

/***********************************************************************/

#include <math.h>
#include "global_vars.h"
#include "raster_file.h"

/***********************************************************************/
/* Public functions                                                    */

/***********************************************************************/

void *Allocate_raster_buf_with_null(RASTER_MAP_TYPE buf_type)
{
    int row, col;
    int nrows, ncols;
    void *map_buf, *map_buf_ptr;

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    /* Allocate memory */

    map_buf = G_malloc(nrows * ncols * Rast_cell_size(buf_type));

    /* Initialise with NULL values */

    map_buf_ptr = map_buf;
    for (row = nrows - 1; row >= 0; row--)
        for (col = 0; col < ncols; col++) {
            Rast_set_null_value(map_buf_ptr, 1, buf_type);
            map_buf_ptr =
                G_incr_void_ptr(map_buf_ptr, Rast_cell_size(buf_type));
        }
    return map_buf;
}

/***********************************************************************/

void Check_raster_outfile(char *map_name, char *mapset, int overwrite)
{
    const char *mapset_address;
    char message[GMAPSET_MAX + 64];

    mapset_address = G_find_raster(map_name, G_mapset());
    strcpy(mapset, G_mapset());
    if (mapset_address != NULL) {
        if (!overwrite) {
            sprintf(message, _("Raster map <%s> exists "), map_name);
            G_fatal_error("%s", message);
        }
    }
}

/***********************************************************************/

void Close_raster_file(int map_fd)
{
    Rast_close(map_fd);
}

/***********************************************************************/

void Copy_raster_buf(void *in_buf, void *out_buf, RASTER_MAP_TYPE in_type,
                     RASTER_MAP_TYPE out_type)
{
    int row, col, nrows, ncols;
    void *in_buf_ptr, *out_buf_ptr;

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    /* Read data cell by cell */

    in_buf_ptr = in_buf;
    out_buf_ptr = out_buf;
    for (row = nrows - 1; row >= 0; row--) {
        for (col = 0; col < ncols; col++) {
            switch (out_type) {
            case CELL_TYPE:
                Rast_set_c_value(out_buf_ptr,
                                 Rast_get_c_value(in_buf_ptr, in_type),
                                 out_type);
                in_buf_ptr =
                    G_incr_void_ptr(in_buf_ptr, Rast_cell_size(in_type));
                out_buf_ptr =
                    G_incr_void_ptr(out_buf_ptr, Rast_cell_size(out_type));
                break;
            case FCELL_TYPE:
                Rast_set_f_value(out_buf_ptr,
                                 Rast_get_f_value(in_buf_ptr, in_type),
                                 out_type);
                in_buf_ptr =
                    G_incr_void_ptr(in_buf_ptr, Rast_cell_size(in_type));
                out_buf_ptr =
                    G_incr_void_ptr(out_buf_ptr, Rast_cell_size(out_type));
                break;
            case DCELL_TYPE:
                Rast_set_d_value(out_buf_ptr,
                                 Rast_get_d_value(in_buf_ptr, in_type),
                                 out_type);
                in_buf_ptr =
                    G_incr_void_ptr(in_buf_ptr, Rast_cell_size(in_type));
                out_buf_ptr =
                    G_incr_void_ptr(out_buf_ptr, Rast_cell_size(out_type));
            }
        }
    }
}

/***********************************************************************/

void Copy_raster_buf_with_rounding(void *in_buf, void *out_buf,
                                   RASTER_MAP_TYPE in_type,
                                   RASTER_MAP_TYPE out_type)
{
    int row, col, nrows, ncols;
    double value;
    void *in_buf_ptr, *out_buf_ptr;

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    /* Read data cell by cell */

    in_buf_ptr = in_buf;
    out_buf_ptr = out_buf;
    for (row = nrows - 1; row >= 0; row--) {
        for (col = 0; col < ncols; col++) {
            switch (out_type) {
            case CELL_TYPE:
                if (in_type == CELL_TYPE) {
                    Rast_set_c_value(out_buf_ptr,
                                     Rast_get_c_value(in_buf_ptr, in_type),
                                     out_type);
                }
                else {
                    value = Rast_get_d_value(in_buf_ptr, in_type);
                    if ((ceil(value) - value) <= (value - floor(value)))
                        value = ceil(value);
                    else
                        value = floor(value);
                    Rast_set_c_value(out_buf_ptr, (CELL)value, out_type);
                }
                in_buf_ptr =
                    G_incr_void_ptr(in_buf_ptr, Rast_cell_size(in_type));
                out_buf_ptr =
                    G_incr_void_ptr(out_buf_ptr, Rast_cell_size(out_type));
                break;
            case FCELL_TYPE:
                Rast_set_f_value(out_buf_ptr,
                                 Rast_get_f_value(in_buf_ptr, in_type),
                                 out_type);
                in_buf_ptr =
                    G_incr_void_ptr(in_buf_ptr, Rast_cell_size(in_type));
                out_buf_ptr =
                    G_incr_void_ptr(out_buf_ptr, Rast_cell_size(out_type));
                break;
            case DCELL_TYPE:
                Rast_set_d_value(out_buf_ptr,
                                 Rast_get_d_value(in_buf_ptr, in_type),
                                 out_type);
                in_buf_ptr =
                    G_incr_void_ptr(in_buf_ptr, Rast_cell_size(in_type));
                out_buf_ptr =
                    G_incr_void_ptr(out_buf_ptr, Rast_cell_size(out_type));
            }
        }
    }
}

/***********************************************************************/

CELL Get_buffer_value_c_row_col(void *in_buf, RASTER_MAP_TYPE in_buf_type,
                                int row, int col)
{
    void *ptr;

    ptr = in_buf + (row * Rast_window_cols() * Rast_cell_size(in_buf_type)) +
          (col * Rast_cell_size(in_buf_type));

    return Rast_get_c_value(ptr, in_buf_type);
}

/***********************************************************************/

CELL Get_buffer_value_rounded_c_row_col(void *in_buf,
                                        RASTER_MAP_TYPE in_buf_type, int row,
                                        int col)
{
    void *ptr;
    double value = 0.0;

    ptr = in_buf + (row * Rast_window_cols() * Rast_cell_size(in_buf_type)) +
          (col * Rast_cell_size(in_buf_type));

    switch (in_buf_type) {
    case CELL_TYPE:
        return Rast_get_c_value(ptr, in_buf_type);
    case FCELL_TYPE:
        value = Rast_get_d_value(ptr, in_buf_type);
        break;
    case DCELL_TYPE:
        value = Rast_get_d_value(ptr, in_buf_type);
    }

    if ((ceil(value) - value) <= (value - floor(value)))
        value = ceil(value);
    else
        value = floor(value);

    return (CELL)value;
}

/***********************************************************************/

DCELL Get_buffer_value_d_row_col(void *in_buf, RASTER_MAP_TYPE in_buf_type,
                                 int row, int col)
{
    void *ptr;

    ptr = in_buf + (row * Rast_window_cols() * Rast_cell_size(in_buf_type)) +
          (col * Rast_cell_size(in_buf_type));

    return Rast_get_d_value(ptr, in_buf_type);
}

/***********************************************************************/

FCELL Get_buffer_value_f_row_col(void *in_buf, RASTER_MAP_TYPE in_buf_type,
                                 int row, int col)
{
    void *ptr;

    ptr = in_buf + (row * Rast_window_cols() * Rast_cell_size(in_buf_type)) +
          (col * Rast_cell_size(in_buf_type));

    return Rast_get_f_value(ptr, in_buf_type);
}

/***********************************************************************/

int Open_raster_infile(char *map_name, char *mapset, char *search_mapset,
                       RASTER_MAP_TYPE *map_type, char *message)
{
    int map_fd;

    if (G_find_raster(map_name, search_mapset) == NULL) {
        /* G_fatal_error (_("Can't find input map ")); */
        /* message passed to G_fatal_error or G_warning in main.c */
        sprintf(message, _("Can't find <%s> for input "), map_name);
        return -1;
    }

    strcpy(mapset, G_find_raster(map_name, search_mapset));
    if ((map_fd = Rast_open_old(map_name, mapset)) < 0) {
        /* G_fatal_error (_("Can't open  input map ")); */
        /* message passed to G_fatal_error or G_warning in main.c */
        sprintf(message, _("Can't open <%s> for input "), map_name);
        return map_fd;
    }

    *map_type = Rast_map_type(map_name, mapset);
    return map_fd;
}

/***********************************************************************/

int Open_raster_outfile(char *map_name, char *mapset, RASTER_MAP_TYPE cell_type,
                        int overwrite, char *message)
{
    const char *mapset_address;
    int map_fd;

    mapset_address = G_find_raster(map_name, G_mapset());
    strcpy(mapset, G_mapset());
    if (mapset_address != NULL) {
        if (!overwrite) { /* Shouldn't get here if check already performed
                             by parser */
            /* message passed to G_fatal_error or G_warning in main.c */
            sprintf(message, _("Raster map <%s> exists "), map_name);
            return -1;
        }
        else {
            G_message(_("Overwriting output raster map <%s@%s>\n"), map_name,
                      mapset);
        }
    }
    else {
        G_message(_("Opening output raster map <%s@%s>\n"), map_name, mapset);
    }

    if ((map_fd = Rast_open_new(map_name, cell_type)) < 0)
        /* message passed to G_fatal_error or G_warning in main.c */
        sprintf(message, _("Can't create raster map <%s@%s> "), map_name,
                mapset);

    return map_fd;
}

/***********************************************************************/

void Print_raster_buf(void *in_buf, RASTER_MAP_TYPE in_type, FILE *stream)
{
    int row, col, nrows, ncols;
    void *in_buf_ptr;

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    /* Read data cell by cell */

    in_buf_ptr = in_buf;
    for (row = nrows - 1; row >= 0; row--) {
        for (col = 0; col < ncols; col++) {
            switch (in_type) {
            case CELL_TYPE:
                fprintf(stream, "%d ", Rast_get_c_value(in_buf_ptr, in_type));
                in_buf_ptr =
                    G_incr_void_ptr(in_buf_ptr, Rast_cell_size(in_type));
                break;
            case FCELL_TYPE:
                fprintf(stream, "%f ", Rast_get_f_value(in_buf_ptr, in_type));
                in_buf_ptr =
                    G_incr_void_ptr(in_buf_ptr, Rast_cell_size(in_type));
                break;
            case DCELL_TYPE:
                fprintf(stream, "%lf ", Rast_get_d_value(in_buf_ptr, in_type));
                in_buf_ptr =
                    G_incr_void_ptr(in_buf_ptr, Rast_cell_size(in_type));
            }
        }
        fprintf(stream, "\n");
    }
}

/***********************************************************************/

void Print_raster_buf_row_col(void *in_buf, RASTER_MAP_TYPE in_type,
                              FILE *stream)
{
    int row, col, nrows, ncols;
    void *in_buf_ptr;

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    /* Read data cell by cell */

    in_buf_ptr = in_buf;
    for (row = nrows - 1; row >= 0; row--) {
        for (col = 0; col < ncols; col++) {
            switch (in_type) {
            case CELL_TYPE:
                fprintf(stream, "row=%d col=%d cell=%d ", nrows - 1 - row, col,
                        Rast_get_c_value(in_buf_ptr, in_type));
                in_buf_ptr =
                    G_incr_void_ptr(in_buf_ptr, Rast_cell_size(in_type));
                break;
            case FCELL_TYPE:
                fprintf(stream, "row=%d col=%d fcell=%f ", nrows - 1 - row, col,
                        Rast_get_f_value(in_buf_ptr, in_type));
                in_buf_ptr =
                    G_incr_void_ptr(in_buf_ptr, Rast_cell_size(in_type));
                break;
            case DCELL_TYPE:
                fprintf(stream, "row=%d col=%d dcell=%lf ", nrows - 1 - row,
                        col, Rast_get_d_value(in_buf_ptr, in_type));
                in_buf_ptr =
                    G_incr_void_ptr(in_buf_ptr, Rast_cell_size(in_type));
            }
        }
        fprintf(stream, "\n");
    }
}

/***********************************************************************/

void Read_raster_infile(void *map_buf, int map_fd, RASTER_MAP_TYPE buf_type,
                        RASTER_MAP_TYPE map_type)
{
    int row, col, nrows, ncols;
    void *row_buf, *map_buf_ptr, *row_buf_ptr;

    row_buf = Rast_allocate_buf(map_type);
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    /* Read data row by row.  In GRASS raster maps, row zero is at top.
       Normally programs iterate 'for (row=nrows-1; row>=0; row--)', but
       by doing it this way we ensure that the  map remains correctly oriented
       when we retrieve values from and write values to the buffer by simply
       incrementing the pointer to the allocated memory, as is done
       in the 'Get...' and 'Set...' functions provided in this file */

    map_buf_ptr = map_buf;
    for (row = 0; row < nrows; row++) {
        row_buf_ptr = row_buf;
        Rast_get_row(map_fd, row_buf_ptr, row, map_type);
        switch (buf_type) {
        case CELL_TYPE:
            for (col = 0; col < ncols; col++) {
                Rast_set_c_value(map_buf_ptr,
                                 Rast_get_c_value(row_buf_ptr, map_type),
                                 buf_type);
                map_buf_ptr =
                    G_incr_void_ptr(map_buf_ptr, Rast_cell_size(buf_type));
                row_buf_ptr =
                    G_incr_void_ptr(row_buf_ptr, Rast_cell_size(map_type));
            }
            break;
        case FCELL_TYPE:
            for (col = 0; col < ncols; col++) {
                Rast_set_f_value(map_buf_ptr,
                                 Rast_get_f_value(row_buf_ptr, map_type),
                                 buf_type);
                map_buf_ptr =
                    G_incr_void_ptr(map_buf_ptr, Rast_cell_size(buf_type));
                row_buf_ptr =
                    G_incr_void_ptr(row_buf_ptr, Rast_cell_size(map_type));
            }
            break;
        case DCELL_TYPE:
            for (col = 0; col < ncols; col++)
                for (col = 0; col < ncols; col++) {
                    Rast_set_d_value(map_buf_ptr,
                                     Rast_get_d_value(row_buf_ptr, map_type),
                                     buf_type);
                    map_buf_ptr =
                        G_incr_void_ptr(map_buf_ptr, Rast_cell_size(buf_type));
                    row_buf_ptr =
                        G_incr_void_ptr(row_buf_ptr, Rast_cell_size(map_type));
                }
        }
    }
}

/***********************************************************************/

void Set_buffer_value_c_row_col(void *out_buf, CELL value,
                                RASTER_MAP_TYPE out_buf_type, int row, int col)
{
    void *ptr;

    ptr = out_buf + (row * Rast_window_cols() * Rast_cell_size(out_buf_type)) +
          (col * Rast_cell_size(out_buf_type));
    Rast_set_c_value(ptr, value, out_buf_type);
}

/***********************************************************************/

void Set_buffer_value_d_row_col(void *out_buf, DCELL value,
                                RASTER_MAP_TYPE out_buf_type, int row, int col)
{
    void *ptr;

    ptr = out_buf + (row * Rast_window_cols() * Rast_cell_size(out_buf_type)) +
          (col * Rast_cell_size(out_buf_type));
    Rast_set_d_value(ptr, value, out_buf_type);
}

/***********************************************************************/

void Set_buffer_value_f_row_col(void *out_buf, FCELL value,
                                RASTER_MAP_TYPE out_buf_type, int row, int col)
{
    void *ptr;

    ptr = out_buf + (row * Rast_window_cols() * Rast_cell_size(out_buf_type)) +
          (col * Rast_cell_size(out_buf_type));
    Rast_set_f_value(ptr, value, out_buf_type);
}

/***********************************************************************/

void Write_raster_outfile(void *map_buf, int map_fd, RASTER_MAP_TYPE buf_type,
                          RASTER_MAP_TYPE map_type)
{
    int row, col, nrows, ncols;
    void *map_buf_ptr, *row_buf_ptr;

    void *row_buf = Rast_allocate_buf(map_type);

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    /* Write data row by row.  In GRASS raster maps, row zero is at top.
       Normally programs iterate for (row=nrows-1; row>=0; row--), but
       see 'Read_raster_infile' for why we do it this way */

    map_buf_ptr = map_buf;
    for (row = 0; row < nrows; row++) {
        row_buf_ptr = row_buf;
        switch (map_type) {
        case CELL_TYPE:
            for (col = 0; col < ncols; col++) {
                Rast_set_c_value(row_buf_ptr,
                                 Rast_get_c_value(map_buf_ptr, buf_type),
                                 map_type);
                map_buf_ptr =
                    G_incr_void_ptr(map_buf_ptr, Rast_cell_size(buf_type));
                row_buf_ptr =
                    G_incr_void_ptr(row_buf_ptr, Rast_cell_size(map_type));
            }
            Rast_put_row(map_fd, row_buf, map_type);
            break;
        case FCELL_TYPE:
            for (col = 0; col < ncols; col++) {
                Rast_set_f_value(row_buf_ptr,
                                 Rast_get_f_value(map_buf_ptr, buf_type),
                                 map_type);
                map_buf_ptr =
                    G_incr_void_ptr(map_buf_ptr, Rast_cell_size(buf_type));
                row_buf_ptr =
                    G_incr_void_ptr(row_buf_ptr, Rast_cell_size(map_type));
            }
            Rast_put_row(map_fd, row_buf, map_type);
            break;
        case DCELL_TYPE:
            for (col = 0; col < ncols; col++) {
                Rast_set_d_value(row_buf_ptr,
                                 Rast_get_d_value(map_buf_ptr, buf_type),
                                 map_type);
                map_buf_ptr =
                    G_incr_void_ptr(map_buf_ptr, Rast_cell_size(buf_type));
                row_buf_ptr =
                    G_incr_void_ptr(row_buf_ptr, Rast_cell_size(map_type));
            }
            Rast_put_row(map_fd, row_buf, map_type);
        }
    }
}

/***********************************************************************/

void Write_raster_outfile_with_rounding(void *map_buf, int map_fd,
                                        RASTER_MAP_TYPE buf_type,
                                        RASTER_MAP_TYPE map_type)
{
    int row, col, nrows, ncols;
    void *map_buf_ptr, *row_buf_ptr;
    double value;

    void *row_buf = Rast_allocate_buf(map_type);

    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    /* Write data row by row.  In GRASS raster maps, row zero is at top.
       Normally programs iterate for (row=nrows-1; row>=0; row--), but
       see 'Read_raster_infile' for why we do it this way */

    map_buf_ptr = map_buf;
    for (row = 0; row < nrows; row++) {
        row_buf_ptr = row_buf;
        switch (map_type) {

        case CELL_TYPE:
            if (buf_type == CELL_TYPE)
                for (col = 0; col < ncols; col++) {
                    Rast_set_c_value(row_buf_ptr,
                                     Rast_get_c_value(map_buf_ptr, buf_type),
                                     map_type);
                    map_buf_ptr =
                        G_incr_void_ptr(map_buf_ptr, Rast_cell_size(buf_type));
                    row_buf_ptr =
                        G_incr_void_ptr(row_buf_ptr, Rast_cell_size(map_type));
                }
            else
                for (col = 0; col < ncols; col++) {
                    value = Rast_get_d_value(map_buf_ptr, buf_type);
                    if ((ceil(value) - value) <= (value - floor(value)))
                        value = ceil(value);
                    else
                        value = floor(value);
                    Rast_set_c_value(row_buf_ptr, (CELL)value, map_type);
                    map_buf_ptr =
                        G_incr_void_ptr(map_buf_ptr, Rast_cell_size(buf_type));
                    row_buf_ptr =
                        G_incr_void_ptr(row_buf_ptr, Rast_cell_size(map_type));
                }
            Rast_put_row(map_fd, row_buf, map_type);
            break;

        case FCELL_TYPE:
            for (col = 0; col < ncols; col++) {
                Rast_set_f_value(row_buf_ptr,
                                 Rast_get_f_value(map_buf_ptr, buf_type),
                                 map_type);
                map_buf_ptr =
                    G_incr_void_ptr(map_buf_ptr, Rast_cell_size(buf_type));
                row_buf_ptr =
                    G_incr_void_ptr(row_buf_ptr, Rast_cell_size(map_type));
            }
            Rast_put_row(map_fd, row_buf, map_type);
            break;

        case DCELL_TYPE:
            for (col = 0; col < ncols; col++) {
                Rast_set_d_value(row_buf_ptr,
                                 Rast_get_d_value(map_buf_ptr, buf_type),
                                 map_type);
                map_buf_ptr =
                    G_incr_void_ptr(map_buf_ptr, Rast_cell_size(buf_type));
                row_buf_ptr =
                    G_incr_void_ptr(row_buf_ptr, Rast_cell_size(map_type));
            }
            Rast_put_row(map_fd, row_buf, map_type);
        }
    }
}
