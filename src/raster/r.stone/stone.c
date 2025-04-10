#include <grass/config.h>
#include <grass/gis.h>
#include <grass/glocale.h>
#include <grass/raster.h>

#include "random2.h"
#include "stone.h"
#include "utils.h"

static void GetMemory(typeParams *rParams, runtimeParams *rtParams,
                      globalParams *gParams);
static void free_memory(typeParams *rParams, runtimeParams *rtParams,
                        globalParams *gParams);
static void WriteInfoStatFile();
static void DumpMatrixToRaster(char *fname, long *mat, int nodata);
static void InitRangeRandValues(typeParams *runParams,
                                runtimeParams *runTimeParams, UniSave *uniData);
static void ReadInputRasters(typeParams *stoneRunParams,
                             globalParams *stoneGlobalParams,
                             runtimeParams *stoneRunTimeParams);
static void ReadRasterToLongMatrix(char *rasterName, long **pmat, double factor,
                                   long nodata, int countRuns);
static void ReadRasterToShortMatrix(char *fname, short **pmat, double factor,
                                    short nodata);

void runStone(typeParams *rParams, globalParams *gParams)
{
    runtimeParams rtParams;
    UniSave uniData = {0};

    // set initial values
    rtParams.glIdMasso = -1;

    G_verbose_message(_("Initialize random data generator."));
    InitRangeRandValues(rParams, &rtParams, &uniData);
    G_verbose_message(_("Done."));

    G_verbose_message(_("Initialize mmath context."));
    MathContext *ctx = init_mmath_system();
    G_verbose_message(_("Done."));

    ReadInputRasters(rParams, gParams, &rtParams);

    G_verbose_message(_(
        "Allocate memory for the runtime parameters and processing matrixes."));
    GetMemory(rParams, &rtParams, gParams);
    G_verbose_message(_("Done."));

    switch (rParams->giRockType) {
    case 0: /* points */
        G_message(_("Processing trajectories using the point shape approach."));
        TrackPoints(rParams, gParams, &rtParams, &uniData, ctx);
        break;
    case 1: /* sphere */
    case 2: /* cylinder */
    case 3: /* disco */
        G_fatal_error(_("At the moment only the point shaped approach "
                        "(BOULDER_SHAPE=0) is supported. Aborting."));
        // TrackNoPoints();
        break;
    default:
        G_fatal_error(_("Inserted BOULDER_SHAPE is not valid. Aborting."));
    }

    DumpMatrixToRaster(rParams->OUT_COUNTERS_FILE, rtParams.gplCountStones, -1);
    if (rParams->OUT_MAX_VEL_FILE != NULL &&
        rParams->OUT_MAX_VEL_FILE[0] != '\0')
        DumpMatrixToRaster(rParams->OUT_MAX_VEL_FILE, rtParams.gplVelo, -1);
    if (rParams->OUT_MAX_DZ_FILE != NULL && rParams->OUT_MAX_DZ_FILE[0] != '\0')
        DumpMatrixToRaster(rParams->OUT_MAX_DZ_FILE, rtParams.gplMaxQuota, -1);

    free_memory(rParams, &rtParams, gParams);

    return;
}

static void InitRangeRandValues(typeParams *runParams,
                                runtimeParams *runTimeParams, UniSave *uniData)
{
    if (!runParams->stoc_flag) {
        runTimeParams->gdStocAngleR = 0.;
        runTimeParams->gdStocVelR = 0.;
        runTimeParams->gdStocHelR = 0.;
        runTimeParams->gdStocFrictR = 0.;

        runTimeParams->gdStocAngle2R = 0.;
        runTimeParams->gdStocVel2R = 0.;
        runTimeParams->gdStocHel2R = 0.;
        runTimeParams->gdStocFrict2R = 0.;
    }
    else {
        runTimeParams->gdStocAngleR = runParams->stoc_angle * 0.01 * PI4;
        runTimeParams->gdStocVelR = runParams->stoc_vel * 0.01;
        runTimeParams->gdStocHelR = runParams->stoc_hel * 0.01;
        runTimeParams->gdStocFrictR = runParams->stoc_frict * 0.01;

        runTimeParams->gdStocAngle2R = runTimeParams->gdStocAngleR * 2.;
        runTimeParams->gdStocVel2R = runTimeParams->gdStocVelR * 2.;
        runTimeParams->gdStocHel2R = runTimeParams->gdStocHelR * 2.;
        runTimeParams->gdStocFrict2R = runTimeParams->gdStocFrictR * 2.;
    }

    Init_RNG(uniData, (unsigned int)runParams->stoc_flag);
}

static void ReadInputRasters(typeParams *rParams, globalParams *gParams,
                             runtimeParams *rtParams)
{
    struct Cell_head window, cellhd;

    G_get_window(&window);

    /* set the window from the header for the elevation file */
    Rast_get_cellhd(rParams->elev_f, "", &cellhd);
    Rast_align_window(&window, &cellhd);
    Rast_set_window(&window);
    /* probably not needed, just to make sure
     * G_get_window() and Rast_get_window()
     * return the same */
    G_set_window(&window);

    // set geometry of the global params from the window
    gParams->gGeometry->cols = window.cols;
    gParams->gGeometry->rows = window.rows;
    gParams->gGeometry->cell = window.ns_res;
    if (window.ns_res != window.ew_res)
        G_warning(
            _("Resolution in north-south direction (%f) is different from "
              "east-west direction (%f). Using north-south resolution."),
            window.ns_res, window.ew_res);
    gParams->gGeometry->sw_x = window.west;
    gParams->gGeometry->sw_y = window.south;
    gParams->gGeometry->ne_x = window.east;
    gParams->gGeometry->ne_y = window.north;

    ReadRasterToLongMatrix(rParams->elev_f, &rtParams->gplQuota, 1000.,
                           9999999L, 0);

    ReadRasterToLongMatrix(rParams->stst_f, &rtParams->gplStartStop, 1., -9999L,
                           1);

    ReadRasterToLongMatrix(rParams->frict_f, &rtParams->gplFrict, 1000.,
                           999999L, 0);

    ReadRasterToShortMatrix(rParams->v_elas_f, &rtParams->gpcVElas, 1., 0);

    ReadRasterToShortMatrix(rParams->h_elas_f, &rtParams->gpcHElas, 1., 0);

    if (rParams->SwitchVelType == 1)
        ReadRasterToLongMatrix(rParams->AccMtrxFile, &rtParams->gplStartVel,
                               rParams->FromAccToVel * 1000, 0, 0);

    /*
      Set globals
    */
    // remember that we need to add an external border of novalues, hence the +
    // 2
    gParams->giCols = gParams->gGeometry->cols + 2;
    gParams->giRows = gParams->gGeometry->rows + 2;
    gParams->glRowsxCols = gParams->giRows * gParams->giCols;
    gParams->gdCell = (double)gParams->gGeometry->cell;
    double gdInvCell = 1 / gParams->gdCell;
    gParams->gdInvCell = 1 / gParams->gdCell;
    gParams->gdInvCell0001 = 0.001 / gParams->gdCell;
    gParams->gdInvCellSq20001 = 0.001 / (gParams->gdCell * SQ2);
    gParams->gdOffset = gParams->gdCell * 0.5;
}

static void ReadRasterToLongMatrix(char *rasterName, long **pmat, double factor,
                                   long nodata, int countRuns)
{
    int r, c;
    double data;
    long piv;
    long *mat;
    char *mapset;
    RASTER_MAP_TYPE map_type;
    struct Cell_head cellhd;
    void *inrast;
    int inFileDescriptor;

    G_verbose_message(_("Reading raster: %s"), rasterName);

    mapset = (char *)G_find_raster2(rasterName, "");
    if (mapset == NULL)
        G_fatal_error(_("Raster map <%s> not found"), rasterName);
    if (strcmp(mapset, G_mapset()) != 0)
        G_fatal_error(_("Raster map <%s> not found in current mapset"),
                      rasterName);

    map_type = Rast_map_type(rasterName, mapset);

    int wRows = Rast_window_rows();
    int wCols = Rast_window_cols();
    // WARNING: the author here decides to create a matrix with an external
    // border of novalues, so the matrix is bigger than the raster and we need
    // to read the raster with an offset of 1 later in the loop
    int irows = wRows + 2;
    int icols = wCols + 2;

    inFileDescriptor = Rast_open_old(rasterName, mapset);
    inrast = Rast_allocate_buf(map_type);

    /*
      Allocate memory for the raster plus an external border of novalues
    */
    *pmat = (long *)malloc(irows * icols * sizeof(long));
    mat = *pmat;

    /*
      Read data
    */
    for (r = 0; r < irows; ++r) {
        G_percent(r, irows, 2);
        if (r == 0 || r == irows - 1) {
            for (c = 0; c < icols; ++c) {
                piv = r * icols + c;
                *(mat + piv) = nodata;
            }
            continue;
        }

        Rast_get_row(inFileDescriptor, inrast, r - 1, map_type);
        for (c = 0; c < icols; ++c) {
            if (c == 0 || c == icols - 1) {
                piv = r * icols + c;
                *(mat + piv) = nodata;
                continue;
            }
            double value;
            switch (map_type) {
            case CELL_TYPE:
                value = ((CELL *)inrast)[c - 1];
                break;
            case FCELL_TYPE:
                value = ((FCELL *)inrast)[c - 1];
                break;
            case DCELL_TYPE:
                value = ((DCELL *)inrast)[c - 1];
                break;
            }

            piv = r * icols + c;
            if (Rast_is_null_value(&value, map_type)) {
                *(mat + piv) = nodata;
            }
            else {
                *(mat + piv) = (long)(value * factor);
                // if (countRuns)
                //     giCountRuns += *(mat + piv);
            }
        }
    }

    G_free(inrast);
    Rast_close(inFileDescriptor);

    G_verbose_message(_("Done."));
}

static void ReadRasterToShortMatrix(char *rasterName, short **pmat,
                                    double factor, short nodata)
{
    int r, c;
    double data;
    long piv;
    short *mat;
    char *mapset;
    RASTER_MAP_TYPE map_type;
    struct Cell_head cellhd;
    void *inrast;
    int inFileDescriptor;

    G_verbose_message(_("Reading raster: %s"), rasterName);

    mapset = (char *)G_find_raster2(rasterName, "");
    if (mapset == NULL)
        G_fatal_error(_("Raster map <%s> not found"), rasterName);
    if (strcmp(mapset, G_mapset()) != 0)
        G_fatal_error(_("Raster map <%s> not found in current mapset"),
                      rasterName);

    map_type = Rast_map_type(rasterName, mapset);

    // ! TODO should I read the current window or the cellhead?
    // I think the current window ?
    int wRows = Rast_window_rows();
    int wCols = Rast_window_cols();
    // Rast_get_cellhd(rasterName, mapset, &cellhd);
    // int irows = cellhd.rows;
    // int icols = cellhd.cols;

    // WARNING: the author here decides to create a matrix with an external
    // border of novalues, so the matrix is bigger than the raster and we need
    // to read the raster with an offset of 1 later in the loop
    int irows = wRows + 2;
    int icols = wCols + 2;

    inFileDescriptor = Rast_open_old(rasterName, mapset);
    inrast = Rast_allocate_buf(map_type);

    /*
      Allocate memory
    */
    *pmat = (short *)malloc(irows * icols * sizeof(short));
    mat = *pmat;

    /*
      Read data
    */
    for (r = 0; r < irows; ++r) {
        G_percent(r, irows, 2);
        if (r == 0 || r == irows - 1) {
            for (c = 0; c < icols; ++c) {
                piv = r * icols + c;
                *(mat + piv) = nodata;
            }
            continue;
        }

        Rast_get_row(inFileDescriptor, inrast, r - 1, map_type);
        for (c = 0; c < icols; ++c) {
            if (c == 0 || c == icols - 1) {
                piv = r * icols + c;
                *(mat + piv) = nodata;
                continue;
            }
            short value;
            switch (map_type) {
            case CELL_TYPE:
                value = (short)((CELL *)inrast)[c - 1];
                break;
            case FCELL_TYPE:
                value = (short)((FCELL *)inrast)[c - 1];
                break;
            case DCELL_TYPE:
                value = (short)((DCELL *)inrast)[c - 1];
                break;
            }

            piv = r * icols + c;
            if (Rast_is_null_value(&value, map_type)) {
                *(mat + piv) = nodata;
            }
            else {
                *(mat + piv) = (short)(value * factor);
                // if (countRuns)
                //     rtParams->giCountRuns += *(mat + piv);
            }
        }
    }

    G_free(inrast);
    Rast_close(inFileDescriptor);

    G_verbose_message(_("Done."));
}

static void DumpMatrixToRaster(char *rasterName, long *mat, int nodata)
{
    int r, c, matrixRow, matrixCol;
    long piv;
    int out_type = CELL_TYPE;

    G_verbose_message(_("Writing raster: %s"), rasterName);

    int wRows = Rast_window_rows();
    int wCols = Rast_window_cols();
    int matricCols = wCols + 2;

    int outfd = Rast_open_new(rasterName, out_type);

    unsigned char *rowBuffer = Rast_allocate_buf(out_type);
    for (r = 0; r < wRows; r++) {
        G_percent(r, wRows, 2);

        matrixRow = r + 1;
        Rast_set_null_value(rowBuffer, wCols, out_type);
        for (c = 0; c < wCols; c++) {
            matrixCol = c + 1;
            piv = matrixRow * matricCols + matrixCol;
            long value = *(mat + piv);
            if (value != nodata) {
                ((CELL *)rowBuffer)[c] = value;
            }
        }

        Rast_put_row(outfd, rowBuffer, out_type);
    }

    G_free(rowBuffer);
    Rast_close(outfd);

    G_verbose_message(_("Raster writing done"));
}

static void GetMemory(typeParams *rParams, runtimeParams *rtParams,
                      globalParams *gParams)
{
    long mem, i;
    char msg[MAX_LEN_STRING];

    strcpy(msg, "Not enough memory");

    long glRowsxCols = gParams->glRowsxCols;

    /*
      Calcola memoria necessaria per elaborazioni
    */
    mem = 6 * glRowsxCols * sizeof(long) + 2 * glRowsxCols * sizeof(char) +
          (sizeof(P3d) + sizeof(typePath) + sizeof(double)) * rParams->max_path;

    if (rParams->SwitchVelType == 1)
        mem += glRowsxCols * sizeof(long);

    G_message("Estimate of memory used for the run: %ldMB", mem / 1024 / 1024);

    rtParams->gplCountStones = (long *)malloc(glRowsxCols * sizeof(long));
    if (rtParams->gplCountStones == NULL)
        G_fatal_error("%s", msg);

    rtParams->gplVelo = (long *)malloc(glRowsxCols * sizeof(long));
    if (rtParams->gplVelo == NULL)
        G_fatal_error("%s", msg);

    rtParams->gplMaxQuota = (long *)malloc(glRowsxCols * sizeof(long));
    if (rtParams->gplMaxQuota == NULL)
        G_fatal_error("%s", msg);

    rtParams->gpPathRoot =
        (typePath *)malloc(sizeof(typePath) * rParams->max_path);
    if (rtParams->gpPathRoot == NULL)
        G_fatal_error("%s", msg);

    rtParams->gP3dZero = (P3d *)malloc(sizeof(P3d));
    if (rtParams->gP3dZero == NULL)
        G_fatal_error("%s", msg);

    for (i = 0; i < glRowsxCols; ++i) {
        // VELO(i) = -1;
        *(rtParams->gplVelo + i) = -1;
        // COUNT(i) = -1;
        *(rtParams->gplCountStones + i) = -1;
        // MAX_QUOTA(i) = -1;
        *(rtParams->gplMaxQuota + i) = -1;
    }

    /*
      offset celle attigue nelle matrici
    */
    int giCols = gParams->giCols;
    rtParams->gsKernel9[0] = (short)-giCols;
    rtParams->gsKernel9[1] = (short)(-giCols + 1);
    rtParams->gsKernel9[2] = 1;
    rtParams->gsKernel9[3] = (short)(giCols + 1);
    rtParams->gsKernel9[4] = (short)giCols;
    rtParams->gsKernel9[5] = (short)(giCols - 1);
    rtParams->gsKernel9[6] = -1;
    rtParams->gsKernel9[7] = (short)(-giCols - 1);
    rtParams->gsKernel9[8] = 0;

    rtParams->gP3dZero->X = 0.;
    rtParams->gP3dZero->Y = 0.;
    rtParams->gP3dZero->Z = 0.;
}

static void free_memory(typeParams *rParams, runtimeParams *rtParams,
                        globalParams *gParams)
{
    // free(rtParams->gplCountStones);
    // free(rtParams->gplVelo);
    // free(rtParams->gplMaxQuota);
    // free(rtParams->gpPathRoot);
    // free(rtParams->gP3dZero);
    // free(rtParams->gpPathCur);
    // free(rtParams->gplQuota);
    // free(rtParams->gplStartStop);
    // free(rtParams->gplFrict);
    // free(rtParams->gplStartVel);
    // free(rtParams->gplStartVel);
    // free(rtParams->gpcVElas);
    // free(rtParams->gpcHElas);
    // free(rtParams);

    // free(gParams->gGeometry);
    // free(gParams);

    // free(rParams);
}

int NewPlane(typeParams *rParams, runtimeParams *rtParams,
             globalParams *gParams, P3d *cp, MathContext *ctx)
{
    int r, c;
    long piv;
    double x0, y0, x1, y1, ym;
    P3d p3d;
    const char *debug_msg = "NewPlane: Moving out of bounds, force stop.";

    double gdOffset = gParams->gdOffset;
    double gdInvCell = gParams->gdInvCell;
    double gdCell = gParams->gdCell;

    typePlane *gPlane = &(rtParams->gPlane);

    c = (int)((cp->X - gdOffset) * gdInvCell);
    r = (int)((cp->Y - gdOffset) * gdInvCell);

    x0 = c * gdCell + gdOffset;
    y0 = r * gdCell + gdOffset;

    piv = Pivot(gParams, x0, y0);
    if (!pivIsValid(piv, gParams)) {
        G_debug(3, "%s", debug_msg);
        return 1;
    }

    x1 = cp->X - x0;
    y1 = cp->Y - y0;

    ym = gdCell - x1;

    if (y1 <= ym) /* Type 1: origin SW */
    {
        if (!pivIsValid(piv, gParams) ||
            !pivIsValid(piv + rtParams->gsKernel9[2], gParams) ||
            !pivIsValid(piv + rtParams->gsKernel9[0], gParams)) {
            G_debug(3, "%s", debug_msg);
            return 1;
        }

        gPlane->type = 1;
        gPlane->p0.X = x0;
        gPlane->p0.Y = y0;
        gPlane->p0.Z = QUOTA(rtParams, piv) * 0.001;
        gPlane->p1.X = x0 + gdCell;
        gPlane->p1.Y = y0;
        gPlane->p1.Z = QUOTA(rtParams, piv + rtParams->gsKernel9[2]) * 0.001;
        gPlane->p2.X = x0;
        gPlane->p2.Y = y0 + gdCell;
        gPlane->p2.Z = QUOTA(rtParams, piv + rtParams->gsKernel9[0]) * 0.001;

        gPlane->Rz = 0.;
    }
    else /* Type 2: origin NE */
    {
        gPlane->type = 2;

        piv += rtParams->gsKernel9[1];
        if (!pivIsValid(piv, gParams) ||
            !pivIsValid(piv + rtParams->gsKernel9[6], gParams) ||
            !pivIsValid(piv + rtParams->gsKernel9[4], gParams)) {
            G_debug(3, "%s", debug_msg);
            return 1;
        }
        gPlane->p0.X = x0 + gdCell;
        gPlane->p0.Y = y0 + gdCell;
        gPlane->p0.Z = QUOTA(rtParams, piv) * 0.001;
        gPlane->p1.X = x0;
        gPlane->p1.Y = y0 + gdCell;
        gPlane->p1.Z = QUOTA(rtParams, piv + rtParams->gsKernel9[6]) * 0.001;
        gPlane->p2.X = x0 + gdCell;
        gPlane->p2.Y = y0;
        gPlane->p2.Z = QUOTA(rtParams, piv + rtParams->gsKernel9[4]) * 0.001;

        gPlane->Rz = PI;
    }

    /*
      Check matrix boundary
    */
    if (gPlane->p0.Z > 9999. || gPlane->p1.Z > 9999. || gPlane->p2.Z > 9999.) {
        // if (gParams.EnabledLogFile)
        //     fprintf(gFileLog, "NewPlane: Matrix boundary\n");
        G_debug(5, "NewPlane: Matrix boundary touched");
        G_debug(5, "NewPlane1: p0: %lf %lf %lf", gPlane->p0.X, gPlane->p0.Y,
                gPlane->p0.Z);
        G_debug(5, "           p1: %lf %lf %lf", gPlane->p1.X, gPlane->p1.Y,
                gPlane->p1.Z);
        G_debug(5, "           p2: %lf %lf %lf", gPlane->p2.X, gPlane->p2.Y,
                gPlane->p2.Z);
        return 1;
    }

    /*
      Origin translations
    */
    gPlane->Tx = -gPlane->p0.X;
    gPlane->Ty = -gPlane->p0.Y;
    gPlane->Tz = -gPlane->p0.Z;

    /*
      Axes rotations
    */
    gPlane->Ry = atan((gPlane->p1.Z - gPlane->p0.Z) * gdInvCell);

    minit(ctx);
    translate(ctx, gPlane->Tx, gPlane->Ty, gPlane->Tz);
    z_rotate(ctx, gPlane->Rz);
    y_rotate(ctx, gPlane->Ry);
    rt(ctx, &(gPlane->p2), &p3d);

    gPlane->Rx = -atan(p3d.Z * gdInvCell);

    G_debug(5, "NewPlane1:  Rx: %lf Ry: %lf Rz: %lf", gPlane->Rx, gPlane->Ry,
            gPlane->Rz);

    /*
      Store transformation matrices
    */
    minit(ctx);
    z_rotate(ctx, gPlane->Rz);
    y_rotate(ctx, gPlane->Ry);
    x_rotate(ctx, gPlane->Rx);
    mget(ctx, gPlane->rToPlane);
    print_double_array("rToPlane", rtParams->gPlane.rToPlane, 16);
    // G_debug(5, "NewPlane1: rToPlane: [%lf,%lf,%lf,%lf,%lf,...]", \
    //         gPlane.rToPlane[0],gPlane.rToPlane[1],gPlane.rToPlane[2],gPlane.rToPlane[3],gPlane.rToPlane[4]);

    minit(ctx);
    translate(ctx, gPlane->Tx, gPlane->Ty, gPlane->Tz);
    z_rotate(ctx, gPlane->Rz);
    y_rotate(ctx, gPlane->Ry);
    x_rotate(ctx, gPlane->Rx);
    mget(ctx, gPlane->toPlane);
    print_double_array("toPlane", rtParams->gPlane.toPlane, 16);
    // G_debug(5, "NewPlane1: toPlane: [%lf,%lf,%lf,%lf,%lf,...]", \
    //         gPlane.toPlane[0],gPlane.toPlane[1],gPlane.toPlane[2],gPlane.toPlane[3],gPlane.toPlane[4]);

    minit(ctx);
    x_rotate(ctx, -gPlane->Rx);
    y_rotate(ctx, -gPlane->Ry);
    z_rotate(ctx, -gPlane->Rz);
    mget(ctx, gPlane->rFromPlane);

    translate(ctx, -gPlane->Tx, -gPlane->Ty, -gPlane->Tz);
    mget(ctx, gPlane->fromPlane);
    print_double_array("fromPlane", rtParams->gPlane.fromPlane, 16);
    // G_debug(5, "NewPlane1: fromPlane: [%lf,%lf,%lf,%lf,%lf,...]", \
    //         gPlane->fromPlane[0],gPlane->fromPlane[1],gPlane->fromPlane[2],gPlane->fromPlane[3],gPlane->fromPlane[4]);

    G_debug(5, "NewPlane2: p0: %lf %lf %lf", gPlane->p0.X, gPlane->p0.Y,
            gPlane->p0.Z);
    G_debug(5, "           p1: %lf %lf %lf", gPlane->p1.X, gPlane->p1.Y,
            gPlane->p1.Z);
    G_debug(5, "           p2: %lf %lf %lf", gPlane->p2.X, gPlane->p2.Y,
            gPlane->p2.Z);
    G_debug(5, "           Rx: %lf Ry: %lf Rz: %lf", gPlane->Rx, gPlane->Ry,
            gPlane->Rz);

#ifdef TRACE
    if (rParams.EnabledLogFile)
        fprintf(gFileLog, "NewPlane: p1: ");
    WriteP3dInLogFile(&gPlane.p0);
    if (rParams.EnabledLogFile)
        fprintf(gFileLog, "NewPlane: p2: ");
    WriteP3dInLogFile(&gPlane.p1);
    if (rParams.EnabledLogFile)
        fprintf(gFileLog, "NewPlane: p3: ");
    WriteP3dInLogFile(&gPlane.p2);
#endif

    /*
      uStation triangles
    */
    // if (rParams.gen_3d_vect)
    //     fprintf(
    //         gFileUst2,
    //         "%.2lf, %.2lf, %.2lf, %.2lf, %.2lf, %.2lf, %.2lf, %.2lf,
    //         %.2lf\n", gGeometry.sw_x + gPlane.p0.X, gGeometry.sw_y +
    //         gPlane.p0.Y, gPlane.p0.Z, gGeometry.sw_x + gPlane.p1.X,
    //         gGeometry.sw_y + gPlane.p1.Y, gPlane.p1.Z,
    //         gGeometry.sw_x + gPlane.p2.X, gGeometry.sw_y + gPlane.p2.Y,
    //         gPlane.p2.Z);

    return 0;
}

void RoundP3d(P3d *p)
{
    p->X = (long)(p->X * 10000. + .5) * 0.0001;
    p->Y = (long)(p->Y * 10000. + .5) * 0.0001;
    p->Z = (long)(p->Z * 10000. + .5) * 0.0001;
}

double P3dDist2(P3d *p1, P3d *p2)
{
    double sum, mul;

    mul = (p1->X - p2->X);
    sum = (mul * mul);

    mul = (p1->Y - p2->Y);
    sum += (mul * mul);

    mul = (p1->Z - p2->Z);
    sum += (mul * mul);

    return sum;
}

void Filter(runtimeParams *rtParams, typeParams *tParams)
{
    P3d *pos1, *pos2;
    typePath *p1, *p2;

    for (p1 = rtParams->gpPathRoot, p2 = rtParams->gpPathRoot + 1;
         p2 < rtParams->gpPathCur; ++p2) {
        pos1 = &p1->pos;
        pos2 = &p2->pos;

        if (P3dDist2(pos1, pos2) < tParams->gdTab2)
            p2->deleted = 1;
        else
            p1 = p2;
    }

    if ((rtParams->gpPathCur - 1)->deleted)
        (rtParams->gpPathCur - 1)->deleted = 0;
}

void WritePath(runtimeParams *rtParams, typeParams *tParams,
               globalParams *gParams, StoneStatus status)
{
    Filter(rtParams, tParams);

    MarkVelo(rtParams, tParams, gParams);

    MarkPath(rtParams, tParams, gParams);

    MarkQuota(rtParams, tParams, gParams);

    if (tParams->gen_3d_vect)
        WriteFile3d(status);

    if (tParams->gen_2d_vect)
        WriteFiles2d();

    if (tParams->gFlagInfoStat)
        WriteInfoStatFile();
}

void MarkVelo(runtimeParams *rtParams, typeParams *tParams,
              globalParams *gParams)
{
    typePath *p;
    P3d *pp, *pv;
    long piv, v;

    /* Warning!
       glLastPiv is global and it is initialized in Track() at start time.
    */
    for (p = rtParams->gpPathRoot; p < rtParams->gpPathCur; ++p) {
        if (p->deleted)
            continue;

        pp = &p->pos;
        pv = &p->v;

        piv = Pivot(gParams, pp->X, pp->Y);
        if (!pivIsValid(piv, gParams))
            continue;

        v = (long)(sqrt(pv->X * pv->X + pv->Y * pv->Y + pv->Z * pv->Z) * 1000. *
                   tParams->gdVeloUMFactor);

        if (v > VELO(rtParams, piv))
            setVELO(rtParams, piv, v);
        // VELO(rtParams, piv) = v;
    }
}

void MarkPath(runtimeParams *rtParams, typeParams *tParams,
              globalParams *gParams)
{
    typePath *p;
    P3d *pp;
    long piv;

    /* Warning!
       glLastPiv is global and it is initialized in Track() at start time.
    */
    for (p = rtParams->gpPathRoot; p < rtParams->gpPathCur; ++p) {
        if (p->deleted)
            continue;

        pp = &p->pos;

        piv = Pivot(gParams, pp->X, pp->Y);

        if (piv != rtParams->glLastPiv && pivIsValid(piv, gParams)) {
            if (COUNT(rtParams, piv) == -1)
                setCOUNT(rtParams, piv, 1);
            // COUNT(piv) = 1;
            else
                setCOUNT(rtParams, piv, COUNT(rtParams, piv) + 1);
            // ++(COUNT(piv));

            rtParams->glLastPiv = piv;
        }
    }
}

void MarkQuota(runtimeParams *rtParams, typeParams *tParams,
               globalParams *gParams)
{
    typePath *p;
    P3d *pp;
    long piv;
    long ldz;

    for (p = rtParams->gpPathRoot; p < rtParams->gpPathCur; ++p) {
        if (p->deleted)
            continue;

        pp = &p->pos;

        piv = Pivot(gParams, pp->X, pp->Y);
        if (!pivIsValid(piv, gParams))
            continue;

        ldz = (long)(p->dz * 1000 * tParams->gdQuotaUMFactor);

        if (MAX_QUOTA(rtParams, piv) < ldz)
            setMAX_QUOTA(rtParams, piv, ldz);
    }
}

void WriteP3dToLog(const char *label, P3d *p)
{
    G_debug(4, "%s X:%11.5lf Y:%11.5lf Z:%11.5lf", label, p->X, p->Y, p->Z);
}

void WriteFile3d(StoneStatus status)
{
    // CURRENTLY NOT SUPPORTED

    // typePath *p;
    // P3d *pp, *pv;
    // double v;

    // if (status == FLY)
    //     fprintf(gFileUst1, "P\t%d\n", ++giUstSlice);
    // else
    //     fprintf(gFileUst1, "R\t%d\n", ++giUstSlice);

    // for (p = gpPathRoot; p < gpPathCur; ++p) {
    //     if (p->deleted)
    //         continue;

    //     pp = &p->pos;
    //     pv = &p->v;

    //     v = sqrt(pv->X * pv->X + pv->Y * pv->Y + pv->Z * pv->Z);

    //     fprintf(gFileUst1, "%.3lf, %.3lf, %.3lf, %.2lf, %.2lf\n",
    //             RoundDouble(gGeometry.sw_x + pp->X),
    //             RoundDouble(gGeometry.sw_y + pp->Y), RoundDouble(pp->Z),
    //             RoundDouble(v), RoundDouble(p->dz));
    // }

    // fflush(gFileUst1);
}

void WriteInfoStatFile()
{
    // CURRENTLY NOT SUPPORTED

    // typeInfoStat info;
    // typePath *p;
    // double vx, vy, vz;

    // info.id = glIdMasso;

    // for (p = gpPathRoot; p < gpPathCur; ++p) {
    //     if (p->deleted)
    //         continue;

    //     info.x = gGeometry.sw_x + p->pos.X;
    //     info.y = gGeometry.sw_y + p->pos.Y;

    //     info.dz = p->dz * 1000 * gdQuotaUMFactor;

    //     vx = p->v.X;
    //     vy = p->v.Y;
    //     vz = p->v.Z;

    //     info.v = sqrt(vx * vx + vy * vy + vz * vz) * 1000 * gdVeloUMFactor;

    //     fwrite(&info, sizeof(info), 1, gFileInfoStat);
    // }

    // fflush(gFileInfoStat);
}

void WriteFiles2d()
{
    // CURRENTLY NOT SUPPORTED

    // typePath *p;
    // P3d *pp, *pv;
    // double v;

    // /*
    //   Last point of path discarted to avoid to have two points
    //   laying on the same place -- last point of this path and
    //   the first of the next
    // */
    // for (p = gpPathRoot; p < gpPathCur - 1; ++p) {
    //     if (p->deleted)
    //         continue;

    //     pp = &p->pos;
    //     pv = &p->v;

    //     v = sqrt(pv->X * pv->X + pv->Y * pv->Y + pv->Z * pv->Z);

    //     ++glConter2d;

    //     fprintf(gFilePoints, "%ld,%.3lf,%.3lf\n", glConter2d,
    //             RoundDouble(gGeometry.sw_x + pp->X),
    //             RoundDouble(gGeometry.sw_y + pp->Y));

    //     fprintf(gFileAttrib, "%ld,%.3lf,%.3lf,%.3lf\n", glConter2d,
    //             RoundDouble(pp->Z), RoundDouble(v), RoundDouble(p->dz));
    // }

    // fflush(gFilePoints);
    // fflush(gFileAttrib);
}

double RoundDouble(double d)
{
    if (d > -0.0009 && d < 0.)
        return 0.;

    return (d * 10000. + 0.5) * 0.0001;
}

double GetRandAngle(typeParams *rParams, runtimeParams *rtParams,
                    globalParams *gParams, UniSave *uniData, int dir)
{
    int cc;
    double alfa, st_alfa;

    cc = (2 - dir + 8) % 8;

    alfa = cc * PI4;

    if (rParams->stoc_flag) {
        switch (rParams->mANG_STOCH_FUNC) {
        case 0: /*gauss*/
            st_alfa = Gaussian(uniData, alfa, rtParams->gdStocAngle2R);
            break;
        case 1: /*cauchy*/
            st_alfa = Cauchy(uniData, alfa, rtParams->gdStocAngleR);
            break;
        case 2: /*uniform*/
            st_alfa = Uniform(uniData, alfa, rtParams->gdStocAngle2R);
            break;
        default:
            st_alfa = alfa - rtParams->gdStocAngleR +
                      rtParams->gdStocAngle2R *
                          (rand() * gParams->gdInvMaxRandPlusOne);
            break;
        }

#ifdef TRACE
        if (rParams.EnabledLogFile)
            fprintf(gFileLog, "Stochastics: Dir=%d Angle: plain=%lf stoc=%lf\n",
                    dir, alfa * RAD_TO_GRAD, st_alfa * RAD_TO_GRAD);
#endif

        return st_alfa;
    }
    else {

#ifdef TRACE
        if (rParams.EnabledLogFile)
            fprintf(gFileLog, "Stochastics: Dir=%d Angle: plain=%lf stoc=OFF\n",
                    dir, alfa * RAD_TO_GRAD);
#endif

        return alfa;
    }
}

double GetRandVElas(typeParams *rParams, runtimeParams *rtParams,
                    globalParams *gParams, UniSave *uniData, long piv)
{
    double v_el, st_v_el;

    v_el = V_ELAS(rtParams, piv) * 0.01;

    if (rParams->stoc_flag) {
        switch (rParams->mVREST_STOCH_FUNC) {
        case 0: /*gauss*/
            st_v_el = Gaussian(uniData, v_el, rtParams->gdStocVel2R);
            break;
        // TODO case 1: /*cauchy*/
        //     st_v_el = Cauchy(uniData, v_el, rtParams->gdStocVelR);
        //     break;
        // case 2: /*uniform*/
        //     st_v_el = Uniform(uniData, v_el, rtParams->gdStocVel2R);
        //     break;
        default:
            st_v_el =
                v_el - rtParams->gdStocVelR +
                rtParams->gdStocVel2R * (rand() * gParams->gdInvMaxRandPlusOne);
            break;
        }

        if (st_v_el < 0.)
            st_v_el = 0.;

        if (st_v_el > 1.)
            st_v_el = 1.;

#ifdef TRACE
        if (rParams.EnabledLogFile)
            fprintf(gFileLog, "Stochastics: Vrest: plain=%lf stoc=%lf\n", v_el,
                    st_v_el);
#endif

        return st_v_el;
    }
    else {

#ifdef TRACE
        if (rParams.EnabledLogFile)
            fprintf(gFileLog, "Stochastics: Vrest: plain=%lf stoc=OFF\n", v_el);
#endif

        return v_el;
    }
}

double GetRandHElas(typeParams *rParams, runtimeParams *rtParams,
                    globalParams *gParams, UniSave *uniData, long piv)
{
    double h_el, st_h_el;

    h_el = H_ELAS(rtParams, piv) * 0.01;

    if (rParams->stoc_flag) {
        switch (rParams->mVREST_STOCH_FUNC) {
        case 0: /*gauss*/
            st_h_el = Gaussian(uniData, h_el, rtParams->gdStocHel2R);
            break;
        // TODO case 1: /*cauchy*/
        //     st_h_el = Cauchy(uniData, h_el, rtParams->gdStocHelR);
        //     break;
        // case 2: /*uniform*/
        //     st_h_el = Uniform(uniData, h_el, rtParams->gdStocHel2R);
        //     break;
        default:
            st_h_el =
                h_el - rtParams->gdStocHelR +
                rtParams->gdStocHel2R * (rand() * gParams->gdInvMaxRandPlusOne);
            break;
        }

        if (st_h_el < 0.)
            st_h_el = 0.;

        if (st_h_el > 1.)
            st_h_el = 1.;

#ifdef TRACE
        if (rParams.EnabledLogFile)
            fprintf(gFileLog, "Stochastics: Hrest: plain=%lf stoc=%lf\n", h_el,
                    st_h_el);
#endif

        return st_h_el;
    }
    else {

#ifdef TRACE
        if (rParams.EnabledLogFile)
            fprintf(gFileLog, "Stochastics: Hrest: plain=%lf stoc=OFF\n", h_el);
#endif

        return h_el;
    }
}

double GetRandFrict(typeParams *rParams, runtimeParams *rtParams,
                    globalParams *gParams, UniSave *uniData, long piv)
{
    double frct, st_frct;

    frct = FRICT(rtParams, piv) * 0.001;

    if (rParams->stoc_flag) {
        switch (rParams->mVREST_STOCH_FUNC) {
        case 0: /*gauss*/
            st_frct = Gaussian(uniData, frct, rtParams->gdStocFrict2R);
            break;
        // TODO case 1: /*cauchy*/
        //     st_frct = Cauchy(uniData, frct, rtParams->gdStocFrictR);
        //     break;
        // case 2: /*uniform*/
        //     st_frct = Uniform(uniData, frct, rtParams->gdStocFrict2R);
        //     break;
        default:
            st_frct = frct - rtParams->gdStocFrictR +
                      rtParams->gdStocFrict2R *
                          (rand() * gParams->gdInvMaxRandPlusOne);
            break;
        }

        if (st_frct < 0.)
            st_frct = 0.;

        if (st_frct > 1.)
            st_frct = 1.;

#ifdef TRACE
        if (rParams.EnabledLogFile)
            fprintf(gFileLog, "Stochastics: Frict: plain=%lf stoc=%lf\n", frct,
                    st_frct);
#endif

        return st_frct;
    }
    else {

#ifdef TRACE
        if (rParams.EnabledLogFile)
            fprintf(gFileLog, "Stochastics: Frict: plain=%lf stoc=OFF\n", frct);
#endif

        return frct;
    }
}

long Pivot(globalParams *gParams, double X, double Y)
{
    long r, c;

    c = 1 + (int)(X * gParams->gdInvCell);

    r = gParams->giRows - 2 - (int)(Y * gParams->gdInvCell);

    long piv = r * gParams->giCols + c;
    return piv;
}
