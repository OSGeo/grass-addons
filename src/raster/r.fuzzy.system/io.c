#include "local_proto.h"

int open_maps(void)
{

    int i;
    char *mapset;
    struct Cell_head cellhd;

    for (i = 0; i < nmaps; ++i) {
        if (s_maps[i].output) {
            s_maps[i].in_buf = NULL;
            continue;
        }
        mapset = (char *)G_find_raster2(s_maps[i].name, "");

        if (mapset == NULL)
            G_fatal_error(_("Raster map <%s> not found"), s_maps[i].name);

        s_maps[i].cfd = Rast_open_old(s_maps[i].name, mapset);
        Rast_get_cellhd(s_maps[i].name, mapset, &cellhd);

        s_maps[i].raster_type = Rast_map_type(s_maps[i].name, mapset);
        s_maps[i].in_buf = Rast_allocate_buf(s_maps[i].raster_type);
    }
    return 0;
}

int get_rows(int row)
{
    int i;

    for (i = 0; i < nmaps; ++i) {
        if (s_maps[i].output)
            continue;
        Rast_get_row(s_maps[i].cfd, s_maps[i].in_buf, row,
                     s_maps[i].raster_type);
    }
    return 0;
}

int get_cells(int col)
{
    int i;
    CELL c;
    FCELL f;
    DCELL d;

    for (i = 0; i < nmaps; ++i) {

        if (s_maps[i].output)
            continue;

        switch (s_maps[i].raster_type) {

        case CELL_TYPE:
            c = ((CELL *)s_maps[i].in_buf)[col];
            if (Rast_is_null_value(&c, CELL_TYPE))
                return 1;
            else
                s_maps[i].cell = (DCELL)c;
            break;

        case FCELL_TYPE:
            f = ((FCELL *)s_maps[i].in_buf)[col];
            if (Rast_is_null_value(&f, FCELL_TYPE))
                return 1;
            else
                s_maps[i].cell = (DCELL)f;
            break;

        case DCELL_TYPE:
            d = ((DCELL *)s_maps[i].in_buf)[col];
            if (Rast_is_null_value(&d, DCELL_TYPE))
                return 1;
            else
                s_maps[i].cell = (DCELL)d;
            break;
        }
    } /* end for */

    return 0;
}

int create_output_maps(void)
{

    STRING connector = "_";
    int i;

    m_outputs = (OUTPUTS *)G_malloc(nrules * sizeof(OUTPUTS));

    for (i = 0; i < nrules; ++i) {
        strcpy(m_outputs[i].output_name, output);
        strcat(m_outputs[i].output_name, connector);
        strcat(m_outputs[i].output_name, s_rules[i].outname);

        if ((m_outputs[i].ofd =
                 Rast_open_new(m_outputs[i].output_name, FCELL_TYPE)) < 0)
            G_fatal_error(_("Unable to create raster map <%s>"),
                          m_outputs[i].output_name);

        m_outputs[i].out_buf = Rast_allocate_f_buf();
    }
    return 0;
}
