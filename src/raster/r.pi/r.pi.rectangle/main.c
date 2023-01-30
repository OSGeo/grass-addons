/*****************************************************************************
 *
 * MODULE:       r.pi.rectangle
 * AUTHOR(S):    Elshad Shirinov, Dr. Martin Wegmann
 *               Markus Metz (update to GRASS 7)
 * PURPOSE:      Delineation of rectangular study areas based on GPS location
 *                               of the respective corners
 *
 * COPYRIGHT:    (C) 2009-2011,2017 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

#include "local_proto.h"

struct alignment {
    char *name; /* method name */
    char *text; /* menu display - full description */
    int index;
};

static struct alignment alignments[] = {
    {"center", "Key pixel will be the center of the buffer.", 0},
    {"top-left", "Key pixel will be top-left of the buffer.", 1},
    {"top-right", "Key pixel will be the top-right of the buffer.", 2},
    {"bottom-left", "Key pixel will be the bottom-left of the buffer.", 3},
    {"bottom-right", "Key pixel will be the bottom-right of the buffer.", 4},
    {0, 0, 0}};

int main(int argc, char *argv[])
{
    /* input */
    char *oldname;
    const char *oldmapset;

    /* input */
    char *newname;

    /* in and out file pointers */
    int in_fd;
    int out_fd;

    /* parameters */
    int keyval;
    int x, y;
    int align;
    int sx, sy;

    /* maps */
    CELL *map, *newmap;

    /* helper variables */
    int row, col;
    CELL *result;
    char *str;
    int n;

    struct GModule *module;
    struct {
        struct Option *input, *output;
        struct Option *keyval, *x, *y;
        struct Option *alignment;
        struct Option *title;
    } parm;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    module->description =
        _("Generates a rectangle based on a corner coordinate.");

    parm.input = G_define_standard_option(G_OPT_R_INPUT);
    parm.input->description =
        _("Raster map with single pixels representing sampling points");

    parm.output = G_define_standard_option(G_OPT_R_OUTPUT);

    parm.keyval = G_define_option();
    parm.keyval->key = "keyval";
    parm.keyval->type = TYPE_INTEGER;
    parm.keyval->required = YES;
    parm.keyval->description = _("Pixel value in the input raster to be used");

    parm.x = G_define_option();
    parm.x->key = "x";
    parm.x->type = TYPE_INTEGER;
    parm.x->required = YES;
    parm.x->description =
        _("Extent of generated area on the x axis (width) in pixel");

    parm.y = G_define_option();
    parm.y->key = "y";
    parm.y->type = TYPE_INTEGER;
    parm.y->required = YES;
    parm.y->description =
        _("Extent of generated area on the y axis (height) in pixel");

    parm.alignment = G_define_option();
    parm.alignment->key = "alignment";
    parm.alignment->type = TYPE_STRING;
    parm.alignment->required = YES;
    str = G_malloc(1024);
    for (n = 0; alignments[n].name; n++) {
        if (n)
            strcat(str, ",");
        else
            *str = 0;
        strcat(str, alignments[n].name);
    }
    parm.alignment->options = str;
    parm.alignment->description =
        _("Alignment of the rectangle relative to the input pixel. options: "
          "center, top-left, top-right, bottom");

    parm.title = G_define_option();
    parm.title->key = "title";
    parm.title->key_desc = "\"phrase\"";
    parm.title->type = TYPE_STRING;
    parm.title->required = NO;
    parm.title->description = _("Title for resultant raster map");

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    /* get name of input file */
    oldname = parm.input->answer;

    /* test input files existence */
    oldmapset = G_find_raster2(oldname, "");
    if (oldmapset == NULL)
        G_fatal_error(_("Raster map <%s> not found"), oldname);

    /* check if the new file name is correct */
    newname = parm.output->answer;
    if (G_legal_filename(newname) < 0)
        G_fatal_error(_("<%s> is an illegal file name"), newname);

    /* read keyval */
    sscanf(parm.keyval->answer, "%d", &keyval);

    /* read x */
    sscanf(parm.x->answer, "%d", &x);

    /* read y */
    sscanf(parm.y->answer, "%d", &y);

    /* get size */
    sx = Rast_window_cols();
    sy = Rast_window_rows();

    /* find alignment */
    for (n = 0; (str = alignments[n].name); n++)
        if (strcmp(str, parm.alignment->answer) == 0)
            break;
    if (str) {
        align = alignments[n].index;
    }
    else {
        G_warning(_("<%s=%s> unknown %s"), parm.alignment->key,
                  parm.alignment->answer, parm.alignment->key);
        G_usage();
        exit(EXIT_FAILURE);
    }

    /* allocate map buffers */
    map = (CELL *)G_malloc(sx * sy * sizeof(CELL));
    newmap = (CELL *)G_malloc(sx * sy * sizeof(CELL));
    result = Rast_allocate_c_buf();

    /* fill newmap with null */
    Rast_set_c_null_value(newmap, sx * sy);

    /* open map */
    in_fd = Rast_open_old(oldname, oldmapset);
    if (in_fd < 0)
        G_fatal_error(_("Unable to open raster map <%s>"), oldname);

    /* read map */
    G_message("Reading map:");
    for (row = 0; row < sy; row++) {
        Rast_get_c_row(in_fd, map + row * sx, row);

        G_percent(row + 1, sy, 1);
    }

    /* create buffers */
    for (row = 0; row < sy; row++) {
        for (col = 0; col < sx; col++) {
            if (map[row * sx + col] == keyval) {
                set_buffer(newmap, col, row, x, y, sx, sy, align);
            }
        }
    }

    /* close map */
    Rast_close(in_fd);

    /* write the output file */
    G_message("Writing output...");

    /* open new cell file  */
    out_fd = Rast_open_new(newname, CELL_TYPE);
    if (out_fd < 0)
        G_fatal_error(_("Cannot create raster map <%s>"), newname);

    /* write output */
    for (row = 0; row < sy; row++) {
        Rast_set_c_null_value(result, sx);

        for (col = 0; col < sx; col++) {
            result[col] = newmap[row * sx + col];
        }

        Rast_put_c_row(out_fd, result);

        G_percent(row + 1, sy, 1);
    }

    /* close new file */
    Rast_close(out_fd);

    /* free allocated resources */
    G_free(map);
    G_free(newmap);
    G_free(result);

    exit(EXIT_SUCCESS);
}
