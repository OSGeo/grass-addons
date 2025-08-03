/***************************************************************************
 *
 * MODULE:    r.colors.contrast
 * AUTHOR(S): Yann Chemin
 * PURPOSE:   Change the contrast of a band
 *
 * COPYRIGHT: (C) 2017 by the GRASS Development Team
 *
 *            This program is free software under the GPL (>=v2)
 *            Read the file COPYING that comes with GRASS for details.
 *
 ****************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>

int main(int argc, char *argv[])
{
    int nrows, ncols, row, col;

    /* GRASS region properties */
    struct Cell_head cellhd, region;
    struct History hist;

    /* GRASS module options */
    struct GModule *module;
    struct {
        struct Option *input, *output, *contrast, *f_offset, *min, *max;
    } parm;

    /* program settings */
    char *input;
    char *output;
    double contrast = 1.0;
    double brightness = 1.0;
    double min = 0.0;
    double max = 0.0;

    /* file handlers */
    int in_fd;
    int out_fd;
    CELL *inrastc, *outrastc;
    FCELL *inrastf, *outrastf;
    DCELL *inrastd, *outrastd;
    DCELL pix = 0.0;
    DCELL pixout = 0.0;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("imagery"));
    G_add_keyword(_("contrast"));
    G_add_keyword(_("brightness"));
    module->description = _("Change the contrast/brightness of a raster.");

    /* parameters */

    parm.input = G_define_standard_option(G_OPT_R_INPUT);
    parm.input->key = "input";
    parm.input->required = YES;
    parm.input->description = _("Raster map to change the contrast of.");

    parm.output = G_define_standard_option(G_OPT_R_OUTPUT);
    parm.output->required = YES;
    parm.output->key = "output";

    parm.min = G_define_option();
    parm.min->key = "minimum";
    parm.min->key_desc = "value";
    parm.min->required = YES;
    parm.min->type = TYPE_DOUBLE;
    parm.min->description = _("Minimum input/output data value");

    parm.max = G_define_option();
    parm.max->key = "maximum";
    parm.max->key_desc = "value";
    parm.max->required = YES;
    parm.max->type = TYPE_DOUBLE;
    parm.max->description = _("Maximum input/output data value");

    parm.contrast = G_define_option();
    parm.contrast->key = "contrast";
    parm.contrast->key_desc = "value";
    parm.contrast->required = YES;
    parm.contrast->type = TYPE_DOUBLE;
    parm.contrast->answer = "1.0";
    parm.contrast->description = _("Contrast (gain, 8bit=>[1.0-3.0] ");

    parm.f_offset = G_define_option();
    parm.f_offset->key = "brightness";
    parm.f_offset->key_desc = "value";
    parm.f_offset->required = YES;
    parm.f_offset->type = TYPE_DOUBLE;
    parm.f_offset->answer = "0.0";
    parm.f_offset->description = _("Brightness (bias, 8bit=>[0.0-100.0])");

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    input = parm.input->answer;
    output = parm.output->answer;

    /* get setting of current GRASS region */
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    /* get user parameters */
    contrast = strtod(parm.contrast->answer, 0);
    brightness = strtod(parm.f_offset->answer, 0);
    min = strtod(parm.min->answer, 0);
    max = strtod(parm.max->answer, 0);

    /* open raster input map and get its storage type */
    Rast_get_cellhd(input, "", &cellhd);
    in_fd = Rast_open_old(input, "");
    RASTER_MAP_TYPE IN_TYPE = Rast_get_map_type(in_fd);

    /* Open output map with right data type */
    out_fd = Rast_open_new(output, IN_TYPE);
    if (out_fd < 0) {
        G_fatal_error("Cannot open output map.");
        exit(EXIT_FAILURE);
    }

    switch (IN_TYPE) {
    case CELL_TYPE:
        inrastc = Rast_allocate_c_buf();
        outrastc = Rast_allocate_c_buf();
        for (row = 0; row < nrows; row++) {
            G_percent(row, nrows, 2);
            Rast_get_c_row(in_fd, inrastc, row);
            for (col = 0; col < ncols; col++) {
                pix = (double)inrastc[col];
                if (Rast_is_d_null_value(&pix)) {
                    Rast_set_c_null_value(&outrastc[col], 1);
                }
                else {
                    pixout = contrast * pix + brightness;
                    if (pixout < min)
                        pixout = min;
                    if (pixout > max)
                        pixout = max;
                    outrastc[col] = (int)pixout;
                }
            }
            Rast_put_c_row(out_fd, outrastc);
        }
        G_free(inrastc);
        G_free(outrastc);
        break;
    case FCELL_TYPE:
        inrastf = Rast_allocate_f_buf();
        outrastf = Rast_allocate_f_buf();
        for (row = 0; row < nrows; row++) {
            G_percent(row, nrows, 2);
            Rast_get_f_row(in_fd, inrastf, row);
            for (col = 0; col < ncols; col++) {
                pix = (double)inrastf[col];
                if (Rast_is_d_null_value(&pix)) {
                    Rast_set_f_null_value(&outrastf[col], 1);
                }
                else {
                    pixout = contrast * pix + brightness;
                    if (pixout < min)
                        pixout = min;
                    if (pixout > max)
                        pixout = max;
                    outrastf[col] = (float)pixout;
                }
            }
            Rast_put_f_row(out_fd, outrastf);
        }
        G_free(inrastf);
        G_free(outrastf);
        break;
    case DCELL_TYPE:
        inrastd = Rast_allocate_d_buf();
        outrastd = Rast_allocate_d_buf();
        for (row = 0; row < nrows; row++) {
            G_percent(row, nrows, 2);
            Rast_get_d_row(in_fd, inrastd, row);
            for (col = 0; col < ncols; col++) {
                pix = inrastd[col];
                if (Rast_is_d_null_value(&pix)) {
                    Rast_set_d_null_value(&outrastd[col], 1);
                }
                else {
                    pixout = contrast * pix + brightness;
                    if (pixout < min)
                        pixout = min;
                    if (pixout > max)
                        pixout = max;
                    outrastd[col] = pixout;
                }
            }
            Rast_put_d_row(out_fd, outrastd);
        }
        G_free(inrastd);
        G_free(outrastd);
        break;
    }

    /* close all maps */
    Rast_close(out_fd);
    Rast_close(in_fd);

    /* write metadata into result and error maps */
    Rast_short_history(parm.output->answer, "raster", &hist);
    Rast_put_cell_title(parm.output->answer, "Result from r.colors.contrast");
    switch (IN_TYPE) {
    case CELL_TYPE:
        Rast_append_format_history(&hist, "          min=%d, max=%d", (int)min,
                                   (int)max);
        break;
    case FCELL_TYPE:
        Rast_append_format_history(&hist, "          min=%.3f, max=%.3f", min,
                                   max);
        break;
    case DCELL_TYPE:
        Rast_append_format_history(&hist, "          min=%.3f, max=%.3f", min,
                                   max);
        break;
    }
    Rast_write_history(parm.output->answer, &hist);

    return (EXIT_SUCCESS);
}
