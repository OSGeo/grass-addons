#include "local_proto.h"

int open_map(MAPS *rast)
{

    int row, col;
    int fd;
    char *mapset;
    struct Cell_head cellhd;
    int bufsize;
    void *tmp_buf;

    mapset = (char *)G_find_raster2(rast->elevname, "");

    if (mapset == NULL)
        G_fatal_error(_("Raster map <%s> not found"), rast->elevname);

    rast->fd = Rast_open_old(rast->elevname, mapset);
    Rast_get_cellhd(rast->elevname, mapset, &cellhd);
    rast->raster_type = Rast_map_type(rast->elevname, mapset);

    if (window.ew_res < cellhd.ew_res || window.ns_res < cellhd.ns_res)
        G_fatal_error(
            _("Region resolution shoudn't be lesser than map %s resolution. "
              "Run g.region raster=%s to set proper resolution"),
            rast->elevname, rast->elevname);

    tmp_buf = Rast_allocate_buf(rast->raster_type);
    rast->elev = (FCELL **)G_malloc((window_size + 1) * sizeof(FCELL *));

    for (row = 0; row < window_size + 1; ++row) {
        rast->elev[row] = Rast_allocate_buf(FCELL_TYPE);
        Rast_get_row(rast->fd, tmp_buf, row, rast->raster_type);
        for (col = 0; col < ncols; ++col)
            get_cell(col, rast->elev[row], tmp_buf, rast->raster_type);
    } /* end elev */

    G_free(tmp_buf);
    return 0;
}

int get_cell(int col, float *buf_row, void *buf, RASTER_MAP_TYPE raster_type)
{

    switch (raster_type) {

    case CELL_TYPE:
        if (Rast_is_null_value(&((CELL *)buf)[col], CELL_TYPE))
            Rast_set_f_null_value(&buf_row[col], 1);
        else
            buf_row[col] = (FCELL)((CELL *)buf)[col];
        break;

    case FCELL_TYPE:
        if (Rast_is_null_value(&((FCELL *)buf)[col], FCELL_TYPE))
            Rast_set_f_null_value(&buf_row[col], 1);
        else
            buf_row[col] = (FCELL)((FCELL *)buf)[col];
        break;

    case DCELL_TYPE:
        if (Rast_is_null_value(&((DCELL *)buf)[col], DCELL_TYPE))
            Rast_set_f_null_value(&buf_row[col], 1);
        else
            buf_row[col] = (FCELL)((DCELL *)buf)[col];
    }
}

int create_maps(void)
{
    int row, col;

    G_begin_distance_calculations();
    if (G_projection() != PROJECTION_LL)
        get_distance(1, 0);

    slope = (FCELL **)G_malloc(window_size * sizeof(FCELL *));
    aspect = (FCELL **)G_malloc(window_size * sizeof(FCELL *));
    for (row = 0; row < window_size; ++row) {

        if (G_projection() == PROJECTION_LL) {
            get_distance(0, row);
            create_distance_aspect_matrix(row);
        }

        slope[row] = Rast_allocate_buf(FCELL_TYPE);
        aspect[row] = Rast_allocate_buf(FCELL_TYPE);
        get_slope_aspect(row);
    }
}

int shift_buffers(int row)
{
    int i;
    int col;
    void *tmp_buf;
    FCELL *tmp_elev_buf, *slope_tmp, *aspect_tmp;

    tmp_buf = Rast_allocate_buf(elevation.raster_type);

    tmp_elev_buf = elevation.elev[0];

    for (i = 1; i < window_size + 1; ++i)
        elevation.elev[i - 1] = elevation.elev[i];

    elevation.elev[window_size] = tmp_elev_buf;
    Rast_get_row(elevation.fd, tmp_buf, row + radius + 1,
                 elevation.raster_type);

    for (col = 0; col < ncols; ++col)
        get_cell(col, elevation.elev[window_size], tmp_buf,
                 elevation.raster_type);

    G_free(tmp_buf);

    slope_tmp = slope[0];
    aspect_tmp = aspect[0];

    for (i = 1; i < window_size; ++i) {
        slope[i - 1] = slope[i];
        aspect[i - 1] = aspect[i];
    }

    slope[window_size - 1] = slope_tmp;
    aspect[window_size - 1] = aspect_tmp;

    if (G_projection() == PROJECTION_LL) {
        get_distance(0, row);
        create_distance_aspect_matrix(row);
    }

    get_slope_aspect(window_size - 1);

    return 0;
}

int free_map(FCELL **map, int n)
{
    int i;

    for (i = 0; i < n; ++i)
        G_free(map[i]);
    G_free(map);
    return 0;
}
