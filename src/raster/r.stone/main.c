/****************************************************************************
 *
 * MODULE:       r.stone
 * AUTHORS:      Fausto Guzzetti and Massimiliano Alvioli
 *               port to GRASS by Andrea Antonello
 * PURPOSE:      This program tries to model tri-dimensional paths
 *               of stones falling down a DTM.
 *               Input DTM is a square fixed spaced DTM, but it is used
 *               as a Triangular Regular Network. Triangles are
 *               built on the fly during run-time.
 *               Paths are evaluated using parametric 2nd order equations after
 *               a roto-translation of the coordinate system to the run-time
 *               triangle.
 *
 *               A very small matrix package is used to perform
 *               3D geomtery operations.
 *
 * COPYRIGHT:    Fausto Guzzetti and Massimiliano Alvioli
 *
 *               This program is free software under the GNU General Public
 *               License (>=v3). Read the file COPYING that comes with GRASS
 *               for details.
 *
 *****************************************************************************/
#define MAIN

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <grass/config.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/raster.h>

#include "fixed_parameters.h"
#include "future_parameters.h"
#include "stone.h"

/*
 * main function
 */
int main(int argc, char *argv[])
{
    struct {
        struct Option *demOpt, *sourcesOpt, *nrestOpt, *trestOpt, *frictionOpt;
    } inputRaster;

    struct {
        struct Option *countersOpt, *maxvelOpt, *maxdzOpt;
    } outputRaster;

    struct {
        struct Option *angStochRangeOpt, *vrestStochRangeOpt,
            *hrestStochRangeOpt, *frictStochRangeOpt, *stocasticFunctionAngOpt,
            *stocasticFunctionVrestOpt;
        struct Option *stopvelOpt, *startvelOpt;
    } params;

    struct GModule *module;

    G_gisinit(argv[0]);

    module = G_define_module();
    G_add_keyword(_("raster"));
    G_add_keyword(_("stone"));
    G_add_keyword(_("rockfall"));
    module->description = _("The STONE rockfall module");

    inputRaster.demOpt = G_define_standard_option(G_OPT_R_INPUT);
    inputRaster.demOpt->key = "dem";
    inputRaster.demOpt->label = _("Elevation raster map");
    inputRaster.demOpt->description = _("The input elevation raster map");
    inputRaster.demOpt->required = YES;
    inputRaster.demOpt->guisection = _("Input maps");

    inputRaster.sourcesOpt = G_define_standard_option(G_OPT_R_INPUT);
    inputRaster.sourcesOpt->key = "sources";
    inputRaster.sourcesOpt->label = _("Start/stop raster map");
    inputRaster.sourcesOpt->description =
        _("The input start/stop integer raster file."
          "Shows the source areas of rock fall (value > 0)."
          "Shows the areas where rock falls must stop, e.g. a lake (value = "
          "-1).");
    inputRaster.sourcesOpt->required = YES;
    inputRaster.sourcesOpt->guisection = _("Input maps");

    inputRaster.nrestOpt = G_define_standard_option(G_OPT_R_INPUT);
    inputRaster.nrestOpt->key = "nrest";
    inputRaster.nrestOpt->label = _("Normal Elasticity raster map");
    inputRaster.nrestOpt->description =
        _("Contains values of normal (vertical) restitution coefficient, used "
          "at impact points."
          "Accepted values are from 0 (total energy dumping) to 100 (elastic "
          "restitution)"
          "Values are in integer percentage.");
    inputRaster.nrestOpt->required = YES;
    inputRaster.nrestOpt->guisection = _("Input maps");

    inputRaster.trestOpt = G_define_standard_option(G_OPT_R_INPUT);
    inputRaster.trestOpt->key = "trest";
    inputRaster.trestOpt->label = _("Tangential Elasticity raster map");
    inputRaster.trestOpt->description =
        _("Contains values of tangential (horizontal) restitution coefficient, "
          "used at impact points."
          "Accepted values are from 0 (total energy dumping) to 100 (elastic "
          "restitution)"
          "Values are in integer percentage.");
    inputRaster.trestOpt->required = YES;
    inputRaster.trestOpt->guisection = _("Input maps");

    inputRaster.frictionOpt = G_define_standard_option(G_OPT_R_INPUT);
    inputRaster.frictionOpt->key = "friction";
    inputRaster.frictionOpt->label = _("Friction raster map");
    inputRaster.frictionOpt->description =
        _("Contains values of rolling friction angle (tan(beta)), used where "
          "rolling."
          "Example Friction for alluvial deposit is high, beta = 40.4, "
          "tan(beta) = 0.85."
          "Example Friction for bedrock is low, beta = 16.7, tan(beta) = 0.30");
    inputRaster.frictionOpt->required = YES;
    inputRaster.frictionOpt->guisection = _("Input maps");

    params.stocasticFunctionVrestOpt = G_define_option();
    params.stocasticFunctionVrestOpt->key = "stoch_funct";
    params.stocasticFunctionVrestOpt->type = TYPE_INTEGER;
    params.stocasticFunctionVrestOpt->required = NO;
    params.stocasticFunctionVrestOpt->description =
        _("The stocastic simulation function to use for VElas, HElas, "
          "Frict (0 = Gaussian, 1 = Cauchy, 2 = Uniform)");
    params.stocasticFunctionVrestOpt->guisection = _("Stochastic functions");
    params.stocasticFunctionVrestOpt->answer = "0";

    params.stocasticFunctionAngOpt = G_define_option();
    params.stocasticFunctionAngOpt->key = "stoch_funct_ang";
    params.stocasticFunctionAngOpt->type = TYPE_INTEGER;
    params.stocasticFunctionAngOpt->required = NO;
    params.stocasticFunctionAngOpt->description =
        _("The stocastic simulation function to use for the range of starting "
          "angles (0 = Gaussian, 1 = Cauchy, 2 = Uniform)");
    params.stocasticFunctionAngOpt->guisection = _("Stochastic functions");
    params.stocasticFunctionAngOpt->answer = "0";

    params.angStochRangeOpt = G_define_option();
    params.angStochRangeOpt->key = "ang_stoch_range";
    params.angStochRangeOpt->type = TYPE_INTEGER;
    params.angStochRangeOpt->required = YES;
    params.angStochRangeOpt->description =
        _("Percent variability of detachment angle");
    params.angStochRangeOpt->guisection = _("Stochastic functions");
    params.angStochRangeOpt->answer = "10";

    params.vrestStochRangeOpt = G_define_option();
    params.vrestStochRangeOpt->key = "vrest_stoch_range";
    params.vrestStochRangeOpt->type = TYPE_INTEGER;
    params.vrestStochRangeOpt->required = YES;
    params.vrestStochRangeOpt->description =
        _("Percent variability of normal restitution");
    params.vrestStochRangeOpt->guisection = _("Stochastic functions");
    params.vrestStochRangeOpt->answer = "10";

    params.hrestStochRangeOpt = G_define_option();
    params.hrestStochRangeOpt->key = "hrest_stoch_range";
    params.hrestStochRangeOpt->type = TYPE_INTEGER;
    params.hrestStochRangeOpt->required = YES;
    params.hrestStochRangeOpt->description =
        _("Percent variability of tangential restitution");
    params.hrestStochRangeOpt->guisection = _("Stochastic functions");
    params.hrestStochRangeOpt->answer = "10";

    params.frictStochRangeOpt = G_define_option();
    params.frictStochRangeOpt->key = "frict_stoch_range";
    params.frictStochRangeOpt->type = TYPE_INTEGER;
    params.frictStochRangeOpt->required = YES;
    params.frictStochRangeOpt->description =
        _("Percent variability of the friction coefficient");
    params.frictStochRangeOpt->guisection = _("Stochastic functions");
    params.frictStochRangeOpt->answer = "10";

    params.startvelOpt = G_define_option();
    params.startvelOpt->key = "start_vel";
    params.startvelOpt->type = TYPE_DOUBLE;
    params.startvelOpt->required = YES;
    params.startvelOpt->label = _("Start velocity");
    params.startvelOpt->description = _("The start velocity of a rock [m/s].");
    params.startvelOpt->guisection = _("Parameters");
    params.startvelOpt->answer = "1.0";

    params.stopvelOpt = G_define_option();
    params.stopvelOpt->key = "stop_vel";
    params.stopvelOpt->type = TYPE_DOUBLE;
    params.stopvelOpt->required = YES;
    params.stopvelOpt->label = _("Stop velocity");
    params.stopvelOpt->description =
        _("Parameter used to define the minimum velocity for a rock fall."
          "A velocity lower than the one specified here causes the boulder to "
          "stop. [m/s]");
    params.stopvelOpt->guisection = _("Parameters");
    params.stopvelOpt->answer = "3.0";

    outputRaster.countersOpt = G_define_standard_option(G_OPT_R_OUTPUT);
    outputRaster.countersOpt->key = "counter";
    outputRaster.countersOpt->description =
        _("The resulting counters raster output map");
    outputRaster.countersOpt->required = YES;
    outputRaster.countersOpt->guisection = _("Output maps");

    outputRaster.maxvelOpt = G_define_standard_option(G_OPT_R_OUTPUT);
    outputRaster.maxvelOpt->key = "maxvel";
    outputRaster.maxvelOpt->description =
        _("The optional maxvel raster output map");
    outputRaster.maxvelOpt->required = NO;
    outputRaster.maxvelOpt->guisection = _("Output maps");

    outputRaster.maxdzOpt = G_define_standard_option(G_OPT_R_OUTPUT);
    outputRaster.maxdzOpt->key = "maxdz";
    outputRaster.maxdzOpt->description =
        _("The optional maxdz raster output map");
    outputRaster.maxdzOpt->required = NO;
    outputRaster.maxdzOpt->guisection = _("Output maps");

    if (G_parser(argc, argv))
        exit(EXIT_FAILURE);

    /***********************/
    /*    check options   */
    /***********************/

    /* mandatory input maps exist ? */
    if (!G_find_raster2(inputRaster.demOpt->answer, ""))
        G_fatal_error(_("Raster map <%s> not found"),
                      inputRaster.demOpt->answer);
    if (!G_find_raster2(inputRaster.sourcesOpt->answer, ""))
        G_fatal_error(_("Raster map <%s> not found"),
                      inputRaster.sourcesOpt->answer);
    if (!G_find_raster2(inputRaster.frictionOpt->answer, ""))
        G_fatal_error(_("Raster map <%s> not found"),
                      inputRaster.frictionOpt->answer);
    if (!G_find_raster2(inputRaster.nrestOpt->answer, ""))
        G_fatal_error(_("Raster map <%s> not found"),
                      inputRaster.nrestOpt->answer);
    if (!G_find_raster2(inputRaster.trestOpt->answer, ""))
        G_fatal_error(_("Raster map <%s> not found"),
                      inputRaster.trestOpt->answer);

    /************************ */
    /*    parameters          */
    /************************ */

    int ang_stoch_range = atoi(params.angStochRangeOpt->answer);
    int vrest_stoch_range = atoi(params.vrestStochRangeOpt->answer);
    int hrest_stoch_range = atoi(params.hrestStochRangeOpt->answer);
    int frict_stoch_range = atoi(params.frictStochRangeOpt->answer);
    int stocasticFunctionAng = atoi(params.stocasticFunctionAngOpt->answer);
    int stocasticFunctionVrest = atoi(params.stocasticFunctionVrestOpt->answer);
    double stop_vel = atof(params.stopvelOpt->answer);
    double start_vel = atof(params.startvelOpt->answer);

    typeParams stoneRunParams = {0};
    strncpy(stoneRunParams.elev_f, inputRaster.demOpt->answer,
            MAX_LEN_STRING - 1);
    strncpy(stoneRunParams.stst_f, inputRaster.sourcesOpt->answer,
            MAX_LEN_STRING - 1);
    strncpy(stoneRunParams.v_elas_f, inputRaster.nrestOpt->answer,
            MAX_LEN_STRING - 1);
    strncpy(stoneRunParams.h_elas_f, inputRaster.trestOpt->answer,
            MAX_LEN_STRING - 1);
    strncpy(stoneRunParams.frict_f, inputRaster.frictionOpt->answer,
            MAX_LEN_STRING - 1);
    strncpy(stoneRunParams.OUT_COUNTERS_FILE, outputRaster.countersOpt->answer,
            MAX_LEN_STRING - 1);
    if (outputRaster.maxvelOpt->answer)
        strncpy(stoneRunParams.OUT_MAX_VEL_FILE, outputRaster.maxvelOpt->answer,
                MAX_LEN_STRING - 1);
    if (outputRaster.maxdzOpt->answer)
        strncpy(stoneRunParams.OUT_MAX_DZ_FILE, outputRaster.maxdzOpt->answer,
                MAX_LEN_STRING - 1);

    stoneRunParams.stoc_angle = ang_stoch_range;
    stoneRunParams.stoc_vel = vrest_stoch_range;
    stoneRunParams.stoc_hel = hrest_stoch_range;
    stoneRunParams.stoc_frict = frict_stoch_range;
    stoneRunParams.min_v = stop_vel;
    stoneRunParams.min_v2 = stoneRunParams.min_v * stoneRunParams.min_v;

    stoneRunParams.max_path = PATH_ARRAY_SIZE;

    /*
     * Fixed parameters that might be elevated to user input at some point.
     */
    stoneRunParams.short_bounce2 = DIST_FLY_ROLL * DIST_FLY_ROLL;
    stoneRunParams.fly_roll_thresh2 = VEL_FLY_ROLL * VEL_FLY_ROLL;
    stoneRunParams.fly_step = FLY_INT_TAB;
    stoneRunParams.roll_step = ROLL_INT_TAB;
    stoneRunParams.tab = OUTPUT_TAB;
    stoneRunParams.gdQuotaUMFactor = OUTPUT_QUOTA_UM_FACTOR;
    stoneRunParams.gdVeloUMFactor = OUTPUT_VELO_UM_FACTOR;
    stoneRunParams.gdTab2 = stoneRunParams.tab * stoneRunParams.tab;

    stoneRunParams.SwitchVelType = SWITCH_VEL_TYPE;
    stoneRunParams.v0 = start_vel;

    stoneRunParams.stoc_flag = STOCH_FLAG;
    stoneRunParams.mANG_STOCH_FUNC = stocasticFunctionAng;
    stoneRunParams.mVREST_STOCH_FUNC = stocasticFunctionVrest;

    // flags to disable future parameters stuff unused at the moment
    stoneRunParams.gen_3d_vect = VECT_3D_FILES_FLAG;
    stoneRunParams.gFlagInfoStat = 0.; // FLAG_CREATE_INPUT_STAT;
    stoneRunParams.giRockType = BOULDER_SHAPE;

    globalParams stoneGlobalParams = {0};
    stoneGlobalParams.gGeometry = malloc(sizeof(typeGeometry));
    stoneGlobalParams.gdInvMaxRandPlusOne = 1. / (RAND_MAX + 1.);

    runStone(&stoneRunParams, &stoneGlobalParams);

    // /* add command line incantation to history file */
    // Rast_short_history(result, "raster", &history);
    // Rast_command_history(&history);
    // Rast_write_history(result, &history);

    exit(EXIT_SUCCESS);
}
