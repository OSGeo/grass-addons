#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <ctype.h>
#include <grass/gis.h>
#include <grass/vector.h>
#include <grass/glocale.h>
#include "local_proto.h"

#define BUFLEN 4000

int read_ascii_item(char *item, int type, int *int_val, double *dbl_val)
{
    if (int_val) {
        if (type == PLY_UCHAR)
            *int_val = (int)(unsigned char)atoi(item);
        else if (type == PLY_CHAR)
            *int_val = (int)(char)atoi(item);
        else if (type == PLY_USHORT)
            *int_val = (int)(unsigned short)atoi(item);
        else if (type == PLY_SHORT)
            *int_val = (int)(short)atoi(item);
        else if (type == PLY_UINT)
            *int_val = (int)strtoul(item, NULL, 10);
        else if (type == PLY_INT)
            *int_val = atoi(item);
    }
    if (dbl_val && (type == PLY_FLOAT || type == PLY_DOUBLE))
        *dbl_val = (double)atof(item);

    return 0;
}

int get_element_data_ascii(struct ply_file *ply, struct prop_data *data)
{
    char buf[BUFLEN], *ptr;
    int i, type;
    char **tokens;
    int ntokens;

    if (G_getl2(buf, BUFLEN - 1, ply->fp) == 0) {
        /* EOF; should not happen */
        G_fatal_error(_("Incomplete PLY file!"));
    }

    ptr = buf;
    /* skip leading spaces and tabs */
    while (*ptr == ' ' || *ptr == '\t')
        ptr++;

    G_debug(3, "tokenize data");
    tokens = G_tokenize2(ptr, " \t", "\"");
    ntokens = G_number_of_tokens(tokens);

    if (ntokens != ply->curr_element->n_properties)
        G_fatal_error(_("Wrong number of properties"));

    G_debug(3, "convert data");
    for (i = 0; i < ply->curr_element->n_properties; i++) {

        if (ply->curr_element->property[i]->is_list)
            G_fatal_error(_("Property can not be list"));

        type = ply->curr_element->property[i]->type;

        data[i].int_val = 0;
        data[i].dbl_val = 0;

        read_ascii_item(tokens[i], type, &data[i].int_val, &data[i].dbl_val);

        G_debug(3, "data: %d, %f", data[i].int_val, data[i].dbl_val);
    }

    G_free_tokens(tokens);

    return 0;
}

int get_element_data_bigendian(struct ply_file *ply, struct prop_data *data)
{
    return 0;
}

int get_element_data_littleendian(struct ply_file *ply, struct prop_data *data)
{
    return 0;
}

int get_element_data(struct ply_file *ply, struct prop_data *data)
{
    if (ply->file_type == PLY_ASCII)
        return get_element_data_ascii(ply, data);
    else if (ply->file_type == PLY_BINARY_BE)
        return get_element_data_bigendian(ply, data);
    else if (ply->file_type == PLY_BINARY_LE)
        return get_element_data_littleendian(ply, data);

    return 0;
}

int get_element_list_ascii(struct ply_file *ply)
{
    char buf[BUFLEN], *ptr;
    int i, type;
    char **tokens;
    int ntokens;

    if (!ply->curr_element->property[0]->is_list)
        G_fatal_error(_("Property must be a list"));

    if (G_getl2(buf, BUFLEN - 1, ply->fp) == 0) {
        /* EOF; should not happen */
        G_fatal_error(_("Incomplete PLY file!"));
    }

    ptr = buf;
    /* skip leading spaces and tabs */
    while (*ptr == ' ' || *ptr == '\t')
        ptr++;

    G_debug(3, "tokenize data");
    tokens = G_tokenize2(ptr, " \t", "\"");
    ntokens = G_number_of_tokens(tokens);

    G_debug(3, "read list");

    type = ply->curr_element->property[0]->type;

    read_ascii_item(tokens[0], type, &(ply->list.n_values), NULL);
    if (ntokens != ply->list.n_values + 1)
        G_fatal_error(_("Broken list"));
    if (ply->list.n_values >= ply->list.n_alloc) {
        ply->list.n_alloc = ply->list.n_values + 10;
        ply->list.index =
            (int *)G_realloc(ply->list.index, sizeof(int) * ply->list.n_alloc);
    }
    for (i = 0; i < ply->list.n_values; i++) {
        read_ascii_item(tokens[i + 1], type, &(ply->list.index[i]), NULL);
    }

    G_free_tokens(tokens);

    return 0;
}

int get_element_list_bigendian(struct ply_file *ply)
{
    return 0;
}

int get_element_list_littleendian(struct ply_file *ply)
{
    return 0;
}

int get_element_list(struct ply_file *ply)
{
    if (ply->file_type == PLY_ASCII)
        return get_element_list_ascii(ply);
    else if (ply->file_type == PLY_BINARY_BE)
        return get_element_list_bigendian(ply);
    else if (ply->file_type == PLY_BINARY_LE)
        return get_element_list_littleendian(ply);

    return 0;
}

int append_vertex(struct Map_info *Map, struct line_pnts *Points, int cat)
{
    int n;
    static struct line_pnts *PPoints = NULL;
    static struct line_cats *CCats = NULL;

    if (!PPoints)
        PPoints = Vect_new_line_struct();
    if (!CCats)
        CCats = Vect_new_cats_struct();

    Vect_rewind(Map);

    while (Vect_read_next_line(Map, PPoints, CCats) >= 0) {
        for (n = 0; n < CCats->n_cats; n++) {
            if (CCats->field[n] == 1 && CCats->cat[n] == cat) {
                Vect_append_point(Points, PPoints->x[0], PPoints->y[0],
                                  PPoints->z[0]);
            }
        }
    }

    return 0;
}
