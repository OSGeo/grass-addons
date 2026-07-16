/****************************************************************************
 *
 * MODULE:       r.curvenumber
 *
 * AUTHOR(S):    Abdullah Azzam <mabdazzam@outlook.com>
 *
 * PURPOSE:      Generates the Curve Number raster based on landcover and
 *		 hydrologic soil group rasters
 *
 * SPDX-FileCopyrightText: 2025 Abdullah Azzam
 * SPDX-FileCopyrightText: Other GRASS authors
 * SPDX-License-Identifier: GPL-2.0-or-later
 *****************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <grass/gis.h>
#include <grass/raster.h>
#include <grass/glocale.h>
#include <grass/version.h>
#include "global.h"

int main(int argc, char **argv)
{
    struct GModule *module;
    struct Option *opt_land, *opt_soil, *opt_source, *opt_lookup;
    struct Option *opt_hc, *opt_arc, *opt_out;
    struct Flag *flag_drained;
    struct Cell_head region;

    const char *land_name, *soil_name, *out_name;
    const char *source, *lookup;
    const char *hc_str, *arc_str;

    int land_fd, soil_fd, out_fd;
    int nrows, ncols;
    int row;
    CELL *land_row = NULL;
    CELL *soil_row = NULL;
    CELL *out_row = NULL;

    struct cn_table cn_tbl;
    struct arc_table arc_tbl;
    int hc_idx, arc_idx, drained;
    int null_soil_warned = 0;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("hydrology"));
    G_add_keyword(_("curve number"));
    module->label = _("Generates curve number raster from landcover and "
                      "hydrologic soil group");
    module->description =
        _("Implements scs curve number lookup based on landcover, "
          "hydrologic soil group, hydrologic condition, and antecedent runoff");

    /* module  options */

    opt_land = G_define_standard_option(G_OPT_R_INPUT);
    opt_land->key = "landcover";
    opt_land->description = _("Name of input landcover raster");

    opt_soil = G_define_standard_option(G_OPT_R_INPUT);
    opt_soil->key = "soil";
    opt_soil->description = _("Name of input hydrologic soil group raster");

    opt_source = G_define_option();
    opt_source->key = "landcover_source";
    opt_source->type = TYPE_STRING;
    opt_source->required = YES;
    opt_source->options = "nlcd,esa,custom";
    opt_source->description = _("Lookup table source");

    opt_lookup = G_define_option();
    opt_lookup->key = "lookup";
    opt_lookup->type = TYPE_STRING;
    opt_lookup->required = NO;
    opt_lookup->description =
        _("Path to custom lookup csv (used when landcover_source=custom)");

    opt_hc = G_define_option();
    opt_hc->key = "hydrologic_condition";
    opt_hc->type = TYPE_STRING;
    opt_hc->required = NO;
    opt_hc->options = "poor,fair,good";
    opt_hc->answer = "fair";
    opt_hc->description = _("Hydrologic Condition (groundcover density "
                            "affecting runoff potential)");

    opt_arc = G_define_option();
    opt_arc->key = "antecedent_runoff_condition";
    opt_arc->type = TYPE_STRING;
    opt_arc->required = NO;
    opt_arc->options = "i,ii,iii";
    opt_arc->answer = "ii";
    opt_arc->description = _("Antecedent Runoff Condition (the degree of "
                             "wetness of a watershed before a rainfall event)");

    flag_drained = G_define_flag();
    flag_drained->key = 'd';
    flag_drained->description =
        _("Use drained condition for dual hydrologic soil groups (e.g. A/D)");

    opt_out = G_define_standard_option(G_OPT_R_OUTPUT);
    opt_out->description = _("Name for output curve number raster");

    if (G_parser(argc, argv))
        return (EXIT_FAILURE);

    G_message(_("Computing curve number raster ..."));

    land_name = opt_land->answer;
    soil_name = opt_soil->answer;
    out_name = opt_out->answer;

    source = opt_source->answer;
    lookup = opt_lookup->answer;
    hc_str = opt_hc->answer ? opt_hc->answer : "fair";
    arc_str = opt_arc->answer ? opt_arc->answer : "ii";
    drained = flag_drained->answer;

    /* map hydrologic condition */
    if (G_strcasecmp(hc_str, "poor") == 0)
        hc_idx = HC_POOR;
    else if (G_strcasecmp(hc_str, "fair") == 0)
        hc_idx = HC_FAIR;
    else if (G_strcasecmp(hc_str, "good") == 0)
        hc_idx = HC_GOOD;
    else
        G_fatal_error(_("Unknown hydrologic_condition value: %s"), hc_str);

    /* map arc */
    if (G_strcasecmp(arc_str, "i") == 0)
        arc_idx = ARC_I;
    else if (G_strcasecmp(arc_str, "ii") == 0)
        arc_idx = ARC_II;
    else if (G_strcasecmp(arc_str, "iii") == 0)
        arc_idx = ARC_III;
    else
        G_fatal_error(_("Unknown antecedent_runoff_condition value: %s"),
                      arc_str);

    /* open input rasters */
    land_fd = Rast_open_old(land_name, "");
    if (land_fd < 0)
        G_fatal_error(_("Unable to open landcover raster <%s>"), land_name);

    soil_fd = Rast_open_old(soil_name, "");
    if (soil_fd < 0)
        G_fatal_error(_("Unable to open soil raster <%s>"), soil_name);

    Rast_get_window(&region);
    nrows = Rast_window_rows();
    ncols = Rast_window_cols();

    land_row = Rast_allocate_c_buf();
    soil_row = Rast_allocate_c_buf();
    out_row = Rast_allocate_c_buf();

    init_cn_table(&cn_tbl);
    init_arc_table(&arc_tbl);

    /* load cn lookup */
    if (G_strcasecmp(source, "nlcd") == 0) {
        if (load_nlcd_lut(&cn_tbl) != 0)
            G_fatal_error(_("Failed to load NLCD lookup table"));
    }
    else if (G_strcasecmp(source, "esa") == 0) {
        if (load_esa_lut(&cn_tbl) != 0)
            G_fatal_error(_("Failed to load ESA lookup table"));
    }
    else if (G_strcasecmp(source, "custom") == 0) {
        if (!lookup)
            G_fatal_error(
                _("landcover_source=custom requires 'lookup=' option"));
        if (load_custom_lut(&cn_tbl, lookup) != 0)
            G_fatal_error(_("Failed to load custom lookup from <%s>"), lookup);
    }
    else {
        G_fatal_error(_("Unsupported landcover_source: %s"), source);
    }

    /* load arc conversion table */

    if (load_builtin_arc(&arc_tbl) != 0)
        G_fatal_error(_("Failed to load ARC conversion table"));

    /* open output raster */
    out_fd = Rast_open_new(out_name, CELL_TYPE);

    /* main loop:  iter over rows and columns */
    for (row = 0; row < nrows; row++) {
        int col;

        Rast_get_c_row(land_fd, land_row, row);
        Rast_get_c_row(soil_fd, soil_row, row);

        for (col = 0; col < ncols; col++) {
            CELL lc_val = land_row[col];
            CELL soil_val = soil_row[col];
            int cn_ii, cn;
            int ok;

            if (Rast_is_c_null_value(&lc_val)) {
                Rast_set_c_null_value(&out_row[col], 1);
                continue;
            }

            /* null soil: fall back to HSG D (most conservative) */
            if (Rast_is_c_null_value(&soil_val)) {
                if (!null_soil_warned) {
                    G_verbose_message(
                        _("Null soil value(s) found, falling back to HSG D"));
                    null_soil_warned = 1;
                }
                soil_val = 4;
            }

            /* resolve dual HSG codes (11-14) to single codes (1-4) */
            int resolved = resolve_dual_hsg((int)soil_val, drained);

            if (resolved < 0) {
                G_warning(_("Invalid HSG value %d at row %d col %d"),
                          (int)soil_val, row, col);
                Rast_set_c_null_value(&out_row[col], 1);
                continue;
            }
            soil_val = (CELL)resolved;

            ok = lookup_lut_cn_ii(&cn_tbl, (int)lc_val, (int)soil_val, hc_idx,
                                  &cn_ii);
            if (!ok) {
                Rast_set_c_null_value(&out_row[col], 1);
                continue;
            }

            cn = convert_arc_from_table(&arc_tbl, cn_ii, arc_idx);

            if (cn > 0 && cn < 30)
                cn = 30;

            out_row[col] = (CELL)cn;
        }

        Rast_put_c_row(out_fd, out_row);
        G_percent(row + 1, nrows, 2);
    }
    G_percent(1, 1, 1);

    Rast_close(land_fd);
    Rast_close(soil_fd);
    Rast_close(out_fd);

    G_free(land_row);
    G_free(soil_row);
    G_free(out_row);

    free_cn_table(&cn_tbl);
    free_arc_table(&arc_tbl);

    {
        struct History hist;
        Rast_short_history(out_name, "raster", &hist);
        Rast_command_history(&hist);
        Rast_write_history(out_name, &hist);
    }

    return (EXIT_SUCCESS);
}
