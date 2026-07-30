/****************************************************************************
 *
 * MODULE:       r.dem.icp
 * AUTHOR(S):    Corey T. White <smortopahri@gmail.com>
 * PURPOSE:      Co-register two DEM surfaces using ICP (point-to-plane)
 * COPYRIGHT:    (C) 2025-2026 by Corey T. White and the GRASS Development
 *               Team
 *
 * SPDX-License-Identifier: GPL-2.0-or-later
 *
 *****************************************************************************/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/raster.h>

#include "rdemicp.h"

int main(int argc, char *argv[])
{
    struct GModule *module;
    struct Option *ref_opt, *src_opt, *out_opt, *mask_opt;
    struct Option *dof_opt, *levels_opt, *stride_opt, *iter_opt;
    struct Option *trim_opt, *huber_opt, *tol_opt, *dist_opt, *slope_opt;
    struct Option *dx_opt, *dy_opt, *dz_opt, *yaw_opt, *roll_opt, *pitch_opt;
    struct Option *xf_out_opt, *stats_opt, *nprocs_opt;

    G_gisinit(argv[0]);
    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("registration"));
    G_add_keyword(_("ICP"));
    G_add_keyword(_("parallel"));
    module->label = _("Co-register DEM surfaces using Iterative Closest Point "
                      "(point-to-plane).");
    module->description = _(
        "Aligns a source DEM to a reference DEM with robust, multi-scale ICP.");

    ref_opt = G_define_standard_option(G_OPT_R_INPUT);
    ref_opt->key = "reference";
    ref_opt->description = _("Reference DEM raster");
    src_opt = G_define_standard_option(G_OPT_R_INPUT);
    src_opt->key = "source";
    src_opt->description = _("Source DEM raster to align");
    out_opt = G_define_standard_option(G_OPT_R_OUTPUT);
    out_opt->key = "output";
    out_opt->description = _("Output aligned DEM raster");
    mask_opt = G_define_standard_option(G_OPT_R_INPUT);
    mask_opt->key = "mask";
    mask_opt->required = NO;
    mask_opt->description = _("Optional stable-terrain mask (non-zero=use)");

    dof_opt = G_define_option();
    dof_opt->key = "dof";
    dof_opt->type = TYPE_INTEGER;
    dof_opt->answer = "4";
    dof_opt->options = "4,6";
    dof_opt->description = _("Degrees of freedom (4: dx,dy,dz,yaw; 6: add "
                             "roll,pitch - experimental)");
    levels_opt = G_define_option();
    levels_opt->key = "levels";
    levels_opt->type = TYPE_INTEGER;
    levels_opt->answer = "3";
    levels_opt->description = _("ICP pyramid levels (coarse to fine)");
    stride_opt = G_define_option();
    stride_opt->key = "stride";
    stride_opt->type = TYPE_INTEGER;
    stride_opt->answer = "2";
    stride_opt->description = _("Base sampling stride (cells) at finest level");
    iter_opt = G_define_option();
    iter_opt->key = "max_iterations";
    iter_opt->type = TYPE_INTEGER;
    iter_opt->answer = "30";
    iter_opt->description = _("Max iterations per level");

    trim_opt = G_define_option();
    trim_opt->key = "trim";
    trim_opt->type = TYPE_DOUBLE;
    trim_opt->answer = "0.80";
    trim_opt->description = _("Trimmed ICP keep fraction [0-1]");
    huber_opt = G_define_option();
    huber_opt->key = "huber";
    huber_opt->type = TYPE_DOUBLE;
    huber_opt->answer = "1.0";
    huber_opt->description = _("Huber delta (m); 0 disables");
    tol_opt = G_define_option();
    tol_opt->key = "tolerance";
    tol_opt->type = TYPE_DOUBLE;
    tol_opt->answer = "1e-5";
    tol_opt->description = _("Convergence threshold on parameter update norm");
    dist_opt = G_define_option();
    dist_opt->key = "distance_max";
    dist_opt->type = TYPE_DOUBLE;
    dist_opt->answer = "10";
    dist_opt->description = _("Max point-to-plane distance (m); 0 disables");
    slope_opt = G_define_option();
    slope_opt->key = "slope_max";
    slope_opt->type = TYPE_DOUBLE;
    slope_opt->answer = "90";
    slope_opt->description = _("Reject target cells with slope > (deg)");

    dx_opt = G_define_option();
    dx_opt->key = "init_dx";
    dx_opt->type = TYPE_DOUBLE;
    dx_opt->answer = "0";
    dx_opt->description = _("Initial dx (m)");
    dy_opt = G_define_option();
    dy_opt->key = "init_dy";
    dy_opt->type = TYPE_DOUBLE;
    dy_opt->answer = "0";
    dy_opt->description = _("Initial dy (m)");
    dz_opt = G_define_option();
    dz_opt->key = "init_dz";
    dz_opt->type = TYPE_DOUBLE;
    dz_opt->answer = "0";
    dz_opt->description = _("Initial dz (m)");
    yaw_opt = G_define_option();
    yaw_opt->key = "init_yaw";
    yaw_opt->type = TYPE_DOUBLE;
    yaw_opt->answer = "0";
    yaw_opt->description = _("Initial yaw (deg)");
    roll_opt = G_define_option();
    roll_opt->key = "init_roll";
    roll_opt->type = TYPE_DOUBLE;
    roll_opt->answer = "0";
    roll_opt->description = _("Initial roll (deg) (6-DoF only)");
    pitch_opt = G_define_option();
    pitch_opt->key = "init_pitch";
    pitch_opt->type = TYPE_DOUBLE;
    pitch_opt->answer = "0";
    pitch_opt->description = _("Initial pitch (deg) (6-DoF only)");

    xf_out_opt = G_define_standard_option(G_OPT_F_OUTPUT);
    xf_out_opt->key = "transform_out";
    xf_out_opt->required = NO;
    xf_out_opt->description = _("Write final transform to file");
    stats_opt = G_define_standard_option(G_OPT_F_OUTPUT);
    stats_opt->key = "stats_out";
    stats_opt->required = NO;
    stats_opt->description = _("Write per-iteration stats to file");

    nprocs_opt = G_define_standard_option(G_OPT_M_NPROCS);

    if (G_parser(argc, argv))
        return EXIT_FAILURE;

    G_set_omp_num_threads(nprocs_opt);

    Params P = {0};
    P.ref_name = ref_opt->answer;
    P.src_name = src_opt->answer;
    P.out_name = out_opt->answer;
    P.mask_name = mask_opt->answer;
    P.transform_out = xf_out_opt->answer;
    P.stats_out = stats_opt->answer;
    P.dof = atoi(dof_opt->answer);
    P.levels = atoi(levels_opt->answer);
    P.stride = atoi(stride_opt->answer);
    P.max_iter = atoi(iter_opt->answer);
    P.trim = atof(trim_opt->answer);
    P.huber_delta = atof(huber_opt->answer);
    P.tolerance = atof(tol_opt->answer);
    P.distance_max = atof(dist_opt->answer);
    P.slope_max = atof(slope_opt->answer);
    P.tx = atof(dx_opt->answer);
    P.ty = atof(dy_opt->answer);
    P.tz = atof(dz_opt->answer);
    P.yaw = deg2rad(atof(yaw_opt->answer));
    P.roll = deg2rad(atof(roll_opt->answer));
    P.pitch = deg2rad(atof(pitch_opt->answer));

    if (P.dof != 4 && P.dof != 6)
        G_fatal_error(_("dof must be 4 or 6"));
    if (P.dof == 6)
        G_warning(
            _("dof=6 (roll/pitch) is experimental: the rigid rotation is "
              "ill-conditioned for height-field DEMs and the 6-DoF "
              "resample is approximate. Use dof=4 and remove any residual "
              "horizontal shift and vertical offset with r.dem.nk."));
    if (P.trim <= 0.0 || P.trim > 1.0)
        G_fatal_error(_("trim must be (0,1]"));

    Grid grid;
    grid_init(&grid);

    RasterD ref = {0}, src = {0}, mask = {0};
    read_fcell_as_double(P.ref_name, &ref);
    read_fcell_as_double(P.src_name, &src);
    if (P.mask_name)
        read_mask_as_bitmap(P.mask_name, &mask);

    Normals Nref = {0};
    G_message(_("Computing target normals..."));
    compute_normals_from_dem(&ref, &grid, &Nref);

    Transform T = {.tx = P.tx,
                   .ty = P.ty,
                   .tz = P.tz,
                   .yaw = P.yaw,
                   .roll = P.roll,
                   .pitch = P.pitch};

    FILE *statsf = NULL;
    if (P.stats_out) {
        statsf = fopen(P.stats_out, "w");
        if (!statsf)
            G_warning(_("Cannot write %s"), P.stats_out);
    }

    G_message(_("Running ICP..."));
    icp_solve(&ref, &Nref, &src, (P.mask_name ? &mask : NULL), &grid, &P, &T,
              statsf);
    if (statsf)
        fclose(statsf);

    if (P.transform_out)
        write_transform(P.transform_out, &T, P.dof);

    G_message(
        _("Resampling source onto reference grid with final transform..."));
    apply_transform_and_resample(&src, &grid, &T, P.dof, P.out_name);

    free_normals(&Nref);
    free_rasterd(&ref);
    free_rasterd(&src);
    if (P.mask_name)
        free_rasterd(&mask);
    return EXIT_SUCCESS;
}
