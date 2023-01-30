/****************************************************************************
 *
 * MODULE:       r.neigborhoodmatrix
 *
 * AUTHOR(S):    Moritz Lennert (original Python version)
 *               Markus Metz (C version)
 *
 * PURPOSE:      Calculates a neighborhood matrix for a raster map with regions
 *               (e.g. the output of r.clump or i.segment)
 *
 * COPYRIGHT:    (C) 2018 by the GRASS Development Team
 *
 *               This program is free software under the GNU General Public
 *               License (>=v2). Read the file COPYING that comes with GRASS
 *               for details.
 *
 ***************************************************************************/

#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <math.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include "pavl.h"

struct nbp {
    int a, b, cnt;
};

static int cmp_nbp(const void *a, const void *b)
{
    struct nbp *nbpa = (struct nbp *)a;
    struct nbp *nbpb = (struct nbp *)b;

    if (nbpa->a < nbpb->a)
        return -1;
    if (nbpa->a > nbpb->a)
        return 1;

    return (nbpa->b < nbpb->b ? -1 : nbpa->b > nbpb->b);
}

static void free_pavl_item(void *p)
{
    G_free(p);
}

/* compare two cell values
 * return 1 if different */
static int cmp_cells(CELL a, CELL b, int a_null, int b_null)
{
    return (!a_null && !b_null && a != b);
}

int main(int argc, char *argv[])
{
    int row, col, nrows, ncols;

    struct Range range;
    CELL min, max;
    int in_fd;
    int i;
    struct GModule *module;
    struct Option *opt_in;
    struct Option *opt_out;
    struct Option *opt_sep;
    struct Flag *flag_len;
    struct Flag *flag_diag;
    struct Flag *flag_nohead;
    char *sep;
    FILE *out_fp;
    CELL *prev_in, *cur_in, *temp_in;
    CELL cur, ngbr;
    int cur_null, ngbr_null;
    int len;
    struct Cell_head cellhd;
    struct pavl_table *nbptree;
    struct pavl_traverser nbp_trav;
    struct nbp *nbp_found, nbp_search, *nbp_new;

    G_gisinit(argv[0]);

    /* Define the different options */

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("statistics"));
    G_add_keyword(_("reclass"));
    G_add_keyword(_("clumps"));
    module->description =
        _("Calculates geometry parameters for raster objects.");

    opt_in = G_define_standard_option(G_OPT_R_INPUT);
    opt_in->description =
        _("Raster for which to calculate the neighboorhood matrix");

    opt_out = G_define_standard_option(G_OPT_F_OUTPUT);
    opt_out->required = NO;

    opt_sep = G_define_standard_option(G_OPT_F_SEP);

    flag_diag = G_define_flag();
    flag_diag->key = 'd';
    flag_diag->description = _("Also take into account diagonal neighbors");

    flag_len = G_define_flag();
    flag_len->key = 'l';
    flag_len->description =
        _("Also output length of common border (in pixels)");

    flag_nohead = G_define_flag();
    flag_nohead->key = 'c';
    flag_nohead->description =
        _("Include column names in output (meaning will be inversed soon)");

    G_option_exclusive(flag_len, flag_diag, NULL);

    /* parse options */
    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    sep = G_option_to_separator(opt_sep);
    in_fd = Rast_open_old(opt_in->answer, "");

    if (Rast_get_map_type(in_fd) != CELL_TYPE)
        G_fatal_error(_("Input raster must be of type CELL"));

    Rast_read_range(opt_in->answer, "", &range);
    Rast_get_range_min_max(&range, &min, &max);
    if (Rast_is_c_null_value(&min) || Rast_is_c_null_value(&max))
        G_fatal_error(_("Empty input map <%s>"), opt_in->answer);
    if (max == min)
        G_fatal_error(_("Input map <%s> has only one value: %d"),
                      opt_in->answer, max);

    if (opt_out->answer != NULL && strcmp(opt_out->answer, "-") != 0) {
        if (!(out_fp = fopen(opt_out->answer, "w")))
            G_fatal_error(_("Unable to open file <%s> for writing"),
                          opt_out->answer);
    }
    else {
        out_fp = stdout;
    }

    Rast_get_window(&cellhd);
    nrows = cellhd.rows;
    ncols = cellhd.cols;

    /* allocate CELL buffers two columns larger than current window */
    len = (ncols + 2) * sizeof(CELL);
    prev_in = (CELL *)G_malloc(len);
    cur_in = (CELL *)G_malloc(len);

    /* fake a previous row which is all NULL */
    Rast_set_c_null_value(prev_in, ncols + 2);

    /* set left and right edge to NULL */
    Rast_set_c_null_value(&cur_in[0], 1);
    Rast_set_c_null_value(&cur_in[ncols + 1], 1);

    nbptree = pavl_create(cmp_nbp, NULL);
    nbp_new = NULL;

    G_message(_("Calculating neighborhood matrix"));
    for (row = 0; row < nrows; row++) {
        G_percent(row, nrows, 2);

        Rast_get_c_row(in_fd, cur_in + 1, row);
        cur = cur_in[0];
        cur_null = 1;
        for (col = 1; col <= ncols; col++) {

            cur = cur_in[col];
            cur_null = Rast_is_c_null_value(&cur);
            if (cur_null)
                continue;

            /* top */
            ngbr = prev_in[col];
            ngbr_null = Rast_is_c_null_value(&ngbr);
            if (cmp_cells(cur, ngbr, cur_null, ngbr_null)) {
                if (nbp_new == NULL)
                    nbp_new = G_malloc(sizeof(struct nbp));

                if (cur < ngbr) {
                    nbp_new->a = cur;
                    nbp_new->b = ngbr;
                }
                else {
                    nbp_new->b = cur;
                    nbp_new->a = ngbr;
                }
                nbp_new->cnt = 1;
                nbp_found = pavl_insert(nbptree, nbp_new);
                if (nbp_found)
                    nbp_found->cnt++;
                else
                    nbp_new = NULL;
            }

            /* left */
            ngbr = cur_in[col - 1];
            ngbr_null = Rast_is_c_null_value(&ngbr);
            if (cmp_cells(cur, ngbr, cur_null, ngbr_null)) {
                if (nbp_new == NULL)
                    nbp_new = G_malloc(sizeof(struct nbp));

                if (cur < ngbr) {
                    nbp_new->a = cur;
                    nbp_new->b = ngbr;
                }
                else {
                    nbp_new->b = cur;
                    nbp_new->a = ngbr;
                }
                nbp_new->cnt = 1;
                nbp_found = pavl_insert(nbptree, nbp_new);
                if (nbp_found)
                    nbp_found->cnt++;
                else
                    nbp_new = NULL;
            }

            if (flag_diag->answer) {
                /* top left */
                ngbr = prev_in[col - 1];
                ngbr_null = Rast_is_c_null_value(&ngbr);
                if (cmp_cells(cur, ngbr, cur_null, ngbr_null)) {
                    if (nbp_new == NULL)
                        nbp_new = G_malloc(sizeof(struct nbp));

                    if (cur < ngbr) {
                        nbp_new->a = cur;
                        nbp_new->b = ngbr;
                    }
                    else {
                        nbp_new->b = cur;
                        nbp_new->a = ngbr;
                    }
                    nbp_new->cnt = 1;
                    nbp_found = pavl_insert(nbptree, nbp_new);
                    if (nbp_found)
                        nbp_found->cnt++;
                    else
                        nbp_new = NULL;
                }

                /* top right */
                ngbr = prev_in[col + 1];
                ngbr_null = Rast_is_c_null_value(&ngbr);
                if (cmp_cells(cur, ngbr, cur_null, ngbr_null)) {
                    if (nbp_new == NULL)
                        nbp_new = G_malloc(sizeof(struct nbp));

                    if (cur < ngbr) {
                        nbp_new->a = cur;
                        nbp_new->b = ngbr;
                    }
                    else {
                        nbp_new->b = cur;
                        nbp_new->a = ngbr;
                    }
                    nbp_new->cnt = 1;
                    nbp_found = pavl_insert(nbptree, nbp_new);
                    if (nbp_found)
                        nbp_found->cnt++;
                    else
                        nbp_new = NULL;
                }
            }
        }

        /* switch the buffers so that the current buffer becomes the previous */
        temp_in = cur_in;
        cur_in = prev_in;
        prev_in = temp_in;
    }

    G_percent(1, 1, 1);

    Rast_close(in_fd);
    G_free(cur_in);
    G_free(prev_in);

    G_message(_("Writing output"));
    /* print table */

    if (flag_nohead->answer) {
        /* print table header (column names) */
        fprintf(out_fp, "acat%s", sep);
        fprintf(out_fp, "bcat%s", sep);
        if (flag_len->answer)
            fprintf(out_fp, "border_length");
        fprintf(out_fp, "\n");
    }

    /* print table body */
    pavl_t_init(&nbp_trav, nbptree);
    while ((nbp_found = pavl_t_next(&nbp_trav)) != NULL) {
        if (flag_len->answer && !flag_diag->answer) {
            fprintf(out_fp, "%d%s%d%s%d\n", nbp_found->a, sep, nbp_found->b,
                    sep, nbp_found->cnt);
            fprintf(out_fp, "%d%s%d%s%d\n", nbp_found->b, sep, nbp_found->a,
                    sep, nbp_found->cnt);
        }
        else {
            fprintf(out_fp, "%d%s%d\n", nbp_found->a, sep, nbp_found->b);
            fprintf(out_fp, "%d%s%d\n", nbp_found->b, sep, nbp_found->a);
        }
    }
    if (out_fp != stdout)
        fclose(out_fp);

    exit(EXIT_SUCCESS);
}
