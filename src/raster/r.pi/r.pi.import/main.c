/*
 ****************************************************************************
 *
 * MODULE:       r.pi.import
 * AUTHOR(S):    Elshad Shirinov, Dr. Martin Wegmann
 * PURPOSE:      Import of patch information based on ID patch raster 
 *                               (Reads a text-file with Patch IDs and values and creates 
 *                               a raster file with these values for patches)
 *
 * COPYRIGHT:    (C) 2009-2011 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

#define MAIN

#include "local_proto.h"

int main(int argc, char *argv[])
{
    /* input */
    char *oldname, *oldmapset;

    /* output */
    char *newname, *newmapset;

    /* in and out file pointers */
    int in_fd;
    int out_fd;

    /* parameters */
    int keyval;
    int id_col;
    int val_col;
    int neighb_count;

    /* maps */
    int *map;

    /* other parameters */
    char *title;

    /* helper variables */
    int row, col;
    DCELL *d_res;
    DCELL *values;
    int *result;
    int i, n;
    int x, y;
    Coords *p;
    char output_name[GNAME_MAX];
    char *str;
    DCELL val;

    RASTER_MAP_TYPE map_type;
    struct Cell_head ch, window;

    struct GModule *module;
    struct
    {
	struct Option *input, *raster, *output;
	struct Option *keyval, *id_col, *val_col;
	struct Option *title;
    } parm;
    struct
    {
	struct Flag *adjacent, *quiet;
    } flag;

    G_gisinit(argv[0]);

    module = G_define_module();
    module->keywords = _("raster");
    module->description = _("Import and generation of patch raster data");

    parm.input = G_define_option();
    parm.input->key = "input";
    parm.input->type = TYPE_STRING;
    parm.input->required = YES;
    parm.input->gisprompt = "old_file,file,input";
    parm.input->description = _("Name of the input ASCII-file");

    parm.raster = G_define_standard_option(G_OPT_R_INPUT);
    parm.raster->key = "raster";

    parm.output = G_define_standard_option(G_OPT_R_OUTPUT);

    parm.keyval = G_define_option();
    parm.keyval->key = "keyval";
    parm.keyval->type = TYPE_INTEGER;
    parm.keyval->required = YES;
    parm.keyval->description = _("Category value of the patches");

    parm.id_col = G_define_option();
    parm.id_col->key = "id_col";
    parm.id_col->type = TYPE_INTEGER;
    parm.id_col->required = YES;
    parm.id_col->description = _("Number of the column with patch IDs");

    parm.val_col = G_define_option();
    parm.val_col->key = "val_col";
    parm.val_col->type = TYPE_INTEGER;
    parm.val_col->required = YES;
    parm.val_col->description = _("Number of the column with patch values");

    parm.title = G_define_option();
    parm.title->key = "title";
    parm.title->key_desc = "\"phrase\"";
    parm.title->type = TYPE_STRING;
    parm.title->required = NO;
    parm.title->description = _("Title for resultant raster map");

    flag.adjacent = G_define_flag();
    flag.adjacent->key = 'a';
    flag.adjacent->description =
	_("Set for 8 cell-neighbors. 4 cell-neighbors are default");

    if (G_parser(argc, argv))
	exit(EXIT_FAILURE);

    /* get name of raster file */
    oldname = parm.raster->answer;

    /* test raster files existance */
    oldmapset = G_find_cell2(oldname, "");
    if (oldmapset == NULL)
        G_fatal_error(_("Raster map <%s> not found"), oldname);

    /* get number of cell-neighbors */
    neighb_count = flag.adjacent->answer ? 8 : 4;

    /* get keyval */
    sscanf(parm.keyval->answer, "%d", &keyval);

    /* get id_col */
    sscanf(parm.id_col->answer, "%d", &id_col);

    /* get val_col */
    sscanf(parm.val_col->answer, "%d", &val_col);

    /* check if the new file name is correct */
    newname = parm.output->answer;
    if (G_legal_filename(newname) < 0)
	    G_fatal_error(_("<%s> is an illegal file name"), newname);
    newmapset = G_mapset();

    /* get size */
    sx = G_window_cols();
    sy = G_window_rows();

    /* allocate map buffers */
    map = (int *)G_malloc(sx * sy * sizeof(int));
    values = (DCELL *) G_malloc(sx * sy * sizeof(DCELL));
    d_res = G_allocate_d_raster_buf();
    result = G_allocate_c_raster_buf();
    cells = (Coords *) G_malloc(sx * sy * sizeof(Coords));
    fragments = (Coords **) G_malloc(sx * sy * sizeof(Coords *));
    fragments[0] = cells;

    memset(map, 0, sx * sy * sizeof(int));

    /* open map */
    in_fd = G_open_cell_old(oldname, oldmapset);
    if (in_fd < 0)
	    G_fatal_error(_("Unable to open raster map <%s>"), oldname);

    /* read map */
    G_message("Reading map file... ");
    for (row = 0; row < sy; row++) {
	G_get_c_raster_row(in_fd, result, row);
	for (col = 0; col < sx; col++) {
	    if (result[col] == keyval)
		map[row * sx + col] = 1;
	}

	G_percent(row, sy, 2);
    }
    G_percent(1, 1, 2);

    /* close map */
    G_close_cell(in_fd);

    /* find fragment values */
    writeFragments(map, sy, sx, neighb_count);

    /* parse input */
    parse(values, parm.input->answer, id_col, val_col);

    G_message("Writing output...");

    /* open new cellfile  */
    out_fd = G_open_raster_new(newname, DCELL_TYPE);
    if (out_fd < 0)
	    G_fatal_error(_("Cannot create raster map <%s>"), newname);

    /* write the output file */
    for (row = 0; row < sy; row++) {
	G_set_d_null_value(d_res, sx);

	for (i = 0; i < fragcount; i++) {
	    for (p = fragments[i]; p < fragments[i + 1]; p++) {
		if (p->y == row) {
		    d_res[p->x] = values[i];
		}
	    }
	}

	G_put_d_raster_row(out_fd, d_res);

	G_percent(row + 1, sy, 1);
    }

    /* close output */
    G_close_cell(out_fd);

    /* free allocated resources */
    G_free(map);
    G_free(values);
    G_free(cells);
    G_free(fragments);

    exit(EXIT_SUCCESS);
}
