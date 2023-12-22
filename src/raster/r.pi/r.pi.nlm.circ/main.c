/*****************************************************************************
 *
 * MODULE:       r.pi.nlm.circ
 * AUTHOR(S):    Elshad Shirinov, Dr. Martin Wegmann
 *               Markus Metz (update to GRASS 7)
 * PURPOSE:      a simple r.nlm (neutral landscape model) module based on
 *               circular growth
 *
 * COPYRIGHT:    (C) 2009-2011,2017 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/

#include "local_proto.h"

void print_buffer(int *buffer, int sx, int sy)
{
    int x, y;

    fprintf(stderr, "buffer:\n");
    for (y = 0; y < sy; y++) {
        for (x = 0; x < sx; x++) {
            switch (buffer[x + y * sx]) {
            case TYPE_NOTHING:
                fprintf(stderr, " * ");
                break;
            case TYPE_NOGO:
                fprintf(stderr, "X ");
                break;
            default:
                fprintf(stderr, "%d ", buffer[x + y * sx]);
                break;
            }
        }
        fprintf(stderr, "\n");
    }
}

void print_list(int patch_count)
{
    int i, j;
    int cnt;
    Point *list;

    fprintf(stderr, "list_array:\n");
    for (i = 0; i < patch_count; i++) {
        cnt = list_count(i);
        list = list_patch(i);

        fprintf(stderr, "patch %d: ", i);
        for (j = 0; j < cnt; j++)
            fprintf(stderr, "(%d, %d)", list[j].x, list[j].y);
        fprintf(stderr, "\n");
    }
}

/*
   plants new cell for the specified patch
   WARNING:     no tests are performed to determine
   if position is legal
 */
void plant(int *buffer, int sx, int sy, int x, int y, int patch)
{
    int right = x + 1 < sx ? x + 1 : sx - 1;
    int left = x > 0 ? x - 1 : 0;
    int top = y + 1 < sy ? y + 1 : sy - 1;
    int bottom = y > 0 ? y - 1 : 0;

    int ix, iy, index, cell;

    /* remove cell from border list */
    list_remove(patch, list_indexOf(patch, x, y));

    for (ix = left; ix <= right; ix++) {
        for (iy = bottom; iy <= top; iy++) {
            /* don't add the cell itself */
            if (!(ix == x && iy == y)) {
                index = ix + iy * sx;
                cell = buffer[index];
                switch (cell) {
                case TYPE_NOTHING:
                    /* mark cell as owned by patch */
                    buffer[index] = patch;
                    /* if not already on list add cell to border list */
                    index = list_indexOf(patch, ix, iy);
                    if (index < 0)
                        list_add(patch, ix, iy);
                    break;
                case TYPE_NOGO:
                    /* well basically nothing to do here :) */
                    break;
                default:
                    /* test if cell is owned by other patch */
                    if (cell != patch) {
                        /* mark cell as "no go" */
                        buffer[index] = TYPE_NOGO;
                        /* remove cell from owners border list */
                        list_remove(cell, list_indexOf(cell, ix, iy));
                    }
                    break;
                } /* switch */
            }     /* if */
        }         /* for x */
    }             /* for y */
}

void create_patches(int *buffer, int sx, int sy, int patch_count,
                    int pixel_count)
{
    int pixels = pixel_count;
    int i, j;
    int cnt;
    Point *list;

    /* init list_array for border data */
    list_init(patch_count, sx, sy);

    /* create seeds for later patches */
    for (i = 0; i < patch_count; i++) {
        int x, y;

        if (pixels <= 0)
            break;

        /* find appropriate position */
        do {
            x = Random(sx);
            y = Random(sy);
        } while (buffer[x + y * sx] != TYPE_NOTHING);
        buffer[x + y * sx] = i;
        plant(buffer, sx, sy, x, y, i);
        pixels--;

        /*fprintf(stderr, "x = %d, y = %d\n", x, y);
           print_buffer(buffer, sx, sy);
           print_list(patch_count); */
    }

    /* now plant new cells at random but always at the border */
    while (pixels > 0) {
        int patch, pos;
        Point p;
        int flag;

        /* test if there are some free places */
        flag = 0;
        for (patch = 0; patch < patch_count; patch++) {
            cnt = list_count(patch);
            if (cnt > 0) {
                flag = 1;
                break;
            }
        }

        if (!flag)
            return;

        /* find patch with free places at the border */
        do {
            patch = Random(patch_count);
            cnt = list_count(patch);
        } while (cnt <= 0);

        /* pick free position */
        pos = Random(cnt);
        p = list_get(patch, pos);
        plant(buffer, sx, sy, p.x, p.y, patch);
        pixels--;

        /*fprintf(stderr, "x = %d, y = %d\n", p.x, p.y);
           print_buffer(buffer, sx, sy);
           print_list(patch_count); */
    }

    /* remove marked cells, which are still on the list */
    for (i = 0; i < patch_count; i++) {
        cnt = list_count(i);
        list = list_patch(i);
        for (j = 0; j < cnt; j++) {
            int x = list[j].x;
            int y = list[j].y;

            buffer[x + y * sx] = TYPE_NOTHING;
        }
    }
}

int main(int argc, char *argv[])
{
    /* output */
    char *newname;

    /* out file pointer */
    int out_fd;

    /* parameters */
    int sx, sy;
    double landcover;
    int pixel_count;
    int patch_count;
    int rand_seed;

    /* helper variables */
    int *buffer;
    int i, j;
    CELL *result;

    struct GModule *module;
    struct {
        struct Option *output, *size;
        struct Option *landcover, *count;
        struct Option *randseed, *title;
    } parm;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("landscape structure analysis"));
    G_add_keyword(_("neutral landscapes"));
    module->description =
        _("Creates a random landscape with defined attributes.");

    parm.output = G_define_standard_option(G_OPT_R_OUTPUT);

    parm.size = G_define_option();
    parm.size->key = "size";
    parm.size->key_desc = "x,y";
    parm.size->type = TYPE_INTEGER;
    parm.size->required = YES;
    parm.size->description = _("Size of the map");

    parm.landcover = G_define_option();
    parm.landcover->key = "landcover";
    parm.landcover->type = TYPE_DOUBLE;
    parm.landcover->required = YES;
    parm.landcover->description = _("Landcover in percent");

    parm.count = G_define_option();
    parm.count->key = "count";
    parm.count->type = TYPE_INTEGER;
    parm.count->required = YES;
    parm.count->description = _("Number of the patches to create");

    parm.randseed = G_define_option();
    parm.randseed->key = "seed";
    parm.randseed->type = TYPE_INTEGER;
    parm.randseed->required = NO;
    parm.randseed->description = _("Seed for random number generator");

    parm.title = G_define_option();
    parm.title->key = "title";
    parm.title->key_desc = "\"phrase\"";
    parm.title->type = TYPE_STRING;
    parm.title->required = NO;
    parm.title->description = _("Title for resultant raster map");

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    /* check if the new file name is correct */
    newname = parm.output->answer;
    if (G_legal_filename(newname) < 0)
        G_fatal_error(_("<%s> is an illegal file name"), newname);

    /* get size */
    sscanf(parm.size->answers[0], "%d", &sx);
    sscanf(parm.size->answers[1], "%d", &sy);

    /* get landcover */
    sscanf(parm.landcover->answer, "%lf", &landcover);
    pixel_count = Round(landcover * sx * sy / 100);

    /* get patchcount */
    sscanf(parm.count->answer, "%d", &patch_count);

    /* get random seed and init random */
    if (parm.randseed->answer) {
        sscanf(parm.randseed->answer, "%d", &rand_seed);
    }
    else {
        rand_seed = time(NULL);
    }
    srand(rand_seed);

    /* test output */
    fprintf(stderr, "This is a test output:\n\n");
    fprintf(stderr, "output = %s\n", newname);
    fprintf(stderr, "sx = %d, sy = %d\n", sx, sy);
    fprintf(stderr, "landcover = %f, pixel_count = %d\n", landcover,
            pixel_count);
    fprintf(stderr, "patch_count = %d\n", patch_count);
    fprintf(stderr, "rand_seed = %d\n\n", rand_seed);

    /* allocate the cell buffer */
    buffer = (int *)G_malloc(sx * sy * sizeof(int));
    memset(buffer, -1, sx * sy * sizeof(int));
    result = Rast_allocate_c_buf();

    create_patches(buffer, sx, sy, patch_count, pixel_count);

    /* print_buffer(buffer, sx, sy); */

    /* test list */
    /* list_add(1, 10, 20);
       list_add(1, 30, 40);
       list_insert(1, 0, 1, 2);
       list_remove(1, 1);
       list_set(1, 1, 3, 4);

       i = list_indexOf(1, 1, 2);
       fprintf(stderr, "test: %d\n\n", i);

       fprintf(stderr, "list_array:\n");
       for(i = 0; i < patch_count; i++) {
       cnt = list_count(i);
       list = list_patch(i);

       fprintf(stderr, "patch %d: ", i);
       for(j = 0; j < cnt; j++)
       fprintf(stderr, "(%d, %d)", list[j].x, list[j].y);
       fprintf(stderr, "\n");
       } */

    /* write output file */
    out_fd = Rast_open_new(newname, CELL_TYPE);
    if (out_fd < 0)
        G_fatal_error(_("Cannot create raster map <%s>"), newname);

    for (j = 0; j < sy; j++) {
        for (i = 0; i < sx; i++) {
            int cell = buffer[i + j * sx];

            if (cell >= 0) {
                result[i] = 1;
            }
            else {
                Rast_set_c_null_value(result + i, 1);
            }
        }
        Rast_put_c_row(out_fd, result);
    }
    Rast_close(out_fd);

    exit(EXIT_SUCCESS);
}
