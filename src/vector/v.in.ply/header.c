#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <ctype.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include "local_proto.h"

int get_ply_datatype(char *desc)
{
    if (strcmp(desc, "char") == 0 || strcmp(desc, "int8") == 0)
        return PLY_CHAR;
    else if (strcmp(desc, "uchar") == 0 || strcmp(desc, "uint8") == 0)
        return PLY_UCHAR;
    else if (strcmp(desc, "short") == 0 || strcmp(desc, "int16") == 0)
        return PLY_SHORT;
    else if (strcmp(desc, "ushort") == 0 || strcmp(desc, "uint16") == 0)
        return PLY_USHORT;
    else if (strcmp(desc, "int") == 0 || strcmp(desc, "int32") == 0)
        return PLY_INT;
    else if (strcmp(desc, "uint") == 0 || strcmp(desc, "uint32") == 0)
        return PLY_UINT;
    else if (strcmp(desc, "float") == 0 || strcmp(desc, "float32") == 0)
        return PLY_FLOAT;
    else if (strcmp(desc, "double") == 0 || strcmp(desc, "float64") == 0)
        return PLY_DOUBLE;

    return PLY_INVALID; /* invalid type */
}

int add_element(struct ply_file *ply, char **tokens, int ntokens)
{
    struct ply_element *element;

    if (ntokens != 3)
        G_fatal_error(_("Invalid PLY element description"));

    /* create the new element */
    element = (struct ply_element *)G_malloc(sizeof(struct ply_element));
    element->name = G_store(tokens[1]);
    element->n = atoi(tokens[2]);
    element->n_properties = 0;
    element->property = NULL;

    if (strcmp(tokens[1], "vertex") == 0)
        element->type = PLY_VERTEX;
    else if (strcmp(tokens[1], "face") == 0)
        element->type = PLY_FACE;
    else if (strcmp(tokens[1], "edge") == 0)
        element->type = PLY_EDGE;
    else
        element->type = PLY_OTHER;

    /* add new element to ply struct */
    ply->n_elements++;
    ply->element = (struct ply_element **)G_realloc(
        ply->element, sizeof(struct ply_element *) * ply->n_elements);

    ply->element[ply->n_elements - 1] = element;

    return 0;
}

int add_property(struct ply_file *ply, char **tokens, int ntokens)
{
    struct ply_property *property;
    struct ply_element *element;
    int type;

    if (ntokens < 3)
        G_fatal_error(_("Invalid PLY property syntax"));

    /* create the new property */
    property = (struct ply_property *)G_malloc(sizeof(struct ply_property));

    /* init property */
    property->name = NULL;
    property->type = 0;
    property->is_list = 0;
    property->list_type = 0;

    /* expected syntax:
     * property <data-type> <property-name>
     * property list <numerical-type> <numerical-type> <property-name> */

    if (strcmp(tokens[1], "list") == 0) {
        if (ntokens != 5) {
            G_warning(_("Invalid PLY list syntax"));
            return 0;
        }
        property->is_list = 1;
        type = get_ply_datatype(tokens[2]);
        if (!PLY_IS_INT(type))
            G_fatal_error(_("List count must be integer, is %s"), tokens[1]);
        property->type = type;
        type = get_ply_datatype(tokens[3]);
        if (!PLY_IS_INT(type))
            G_fatal_error(_("List index must be integer, is %s"), tokens[2]);
        property->list_type = type;
        property->name = G_store(tokens[4]);
    }
    else if ((type = get_ply_datatype(tokens[1])) > 0) {
        property->type = type;
        property->name = G_store(tokens[2]);
    }
    else {
        G_fatal_error(_("Invalid PLY property syntax"));
    }

    element = ply->element[ply->n_elements - 1];

    element->n_properties++;
    element->property = (struct ply_property **)G_realloc(
        element->property,
        sizeof(struct ply_property *) * (element->n_properties + 1));

    element->property[element->n_properties - 1] = property;

    return 0;
}

int add_comment(struct ply_file *ply, char *buf)
{
    char *ptr = &buf[7];

    while (*ptr == ' ' || *ptr == '\t')
        ptr++;

    ply->comment = (char **)G_realloc(ply->comment,
                                      sizeof(char *) * (ply->n_comments + 1));

    ply->comment[ply->n_comments++] = G_store(ptr);

    return 0;
}

int read_ply_header(struct ply_file *ply)
{
    int buflen = 4000;
    char *buf = (char *)G_malloc(buflen);
    char *buf_raw = (char *)G_malloc(buflen);
    char *ptr;
    char **tokens;
    int ntokens;
    int magic_word = 0;

    while (1) {
        if (G_getl2(buf, buflen - 1, ply->fp) == 0) {
            /* EOF; should not happen */
            G_fatal_error(_("Incomplete PLY file!"));
        }

        if (buf[0] == '\0') {
            /* empty row, should not happen */
            continue;
        }
        /* G_tokenize() will modify the buffer, so we make a copy */
        strcpy(buf_raw, buf);

        ptr = buf;
        /* skip leading spaces and tabs */
        while (*ptr == ' ' || *ptr == '\t')
            ptr++;

        tokens = G_tokenize2(ptr, " \t", "\"");
        ntokens = G_number_of_tokens(tokens);

        if (!magic_word) {
            if (ntokens == 1 && strcmp(tokens[0], "ply") == 0) {
                magic_word = 1;
                continue;
            }
            else
                G_fatal_error(_("This is not a PLY file!"));
        }

        if (strcmp(tokens[0], "format") == 0) {
            if (ntokens != 3)
                G_fatal_error(_("Incomplete format description!"));
            if (strcmp(tokens[1], "ascii") == 0)
                ply->file_type = PLY_ASCII;
            else if (strcmp(tokens[1], "binary_big_endian") == 0)
                ply->file_type = PLY_BINARY_BE;
            else if (strcmp(tokens[1], "binary_little_endian") == 0)
                ply->file_type = PLY_BINARY_LE;
            else
                G_fatal_error(_("Unknown PLY format <%s>!"), tokens[1]);
            ply->version = G_store(tokens[2]);

            if (ply->file_type != PLY_ASCII)
                G_fatal_error(_("Binary PLY format is not yet supported"));
        }
        else if (strcmp(tokens[0], "element") == 0)
            add_element(ply, tokens, ntokens);
        else if (strcmp(tokens[0], "property") == 0)
            add_property(ply, tokens, ntokens);
        else if (strcmp(tokens[0], "comment") == 0)
            add_comment(ply, buf_raw);
        else if (strcmp(tokens[0], "end_header") == 0) {
            ply->header_size = G_ftell(ply->fp);
            G_free_tokens(tokens);
            break;
        }

        G_free_tokens(tokens);
    }

    G_free(buf);
    G_free(buf_raw);

    return 0;
}
