
#include <grass/gis.h>

#include "random2.h"
#include "stone.h"

long QUOTA(runtimeParams *params, long piv)
{
    return *(params->gplQuota + piv);
}

int DEC_X(globalParams *params, long piv)
{
    return (int)(piv % params->gGeometry->cols);
}

int DEC_Y(globalParams *params, long piv)
{
    return (int)(piv / params->gGeometry->cols);
}

double POS_X(globalParams *params, long piv)
{
    return (double)(params->gdOffset +
                    ((piv % params->giCols) - 1) * params->gdCell);
}

double POS_Y(globalParams *params, long piv)
{
    return (double)(params->gdOffset +
                    (params->giRows - 2 - (piv / params->giCols)) *
                        params->gdCell);
}

long START_STOP(runtimeParams *params, long piv)
{
    return *(params->gplStartStop + piv);
}

long START_VEL(runtimeParams *params, long piv)
{
    return *(params->gplStartVel + piv);
}

long VELO(runtimeParams *params, long piv)
{
    return *(params->gplVelo + piv);
}

void setVELO(runtimeParams *params, long piv, long value)
{
    *(params->gplVelo + piv) = value;
}

long COUNT(runtimeParams *params, long piv)
{
    return *(params->gplCountStones + piv);
}

// and setter
void setCOUNT(runtimeParams *params, long piv, long value)
{
    *(params->gplCountStones + piv) = value;
}

long MAX_QUOTA(runtimeParams *params, long piv)
{
    return *(params->gplMaxQuota + piv);
}

// and setter
void setMAX_QUOTA(runtimeParams *params, long piv, long value)
{
    *(params->gplMaxQuota + piv) = value;
}

long V_ELAS(runtimeParams *params, long piv)
{
    return *(params->gpcVElas + piv);
}

long H_ELAS(runtimeParams *params, long piv)
{
    return *(params->gpcHElas + piv);
}

long FRICT(runtimeParams *params, long piv)
{
    return *(params->gplFrict + piv);
}

/**
 * Check if the pivot is valid.
 *
 * Returns 0 if it is NOT valid, else 1.
 */
int pivIsValid(long piv, globalParams *gParams)
{
    if (piv >= 0 && piv < gParams->glRowsxCols)
        return 1;
    return 0;
}

void print_double_array(const char *label, double *darray, int size)
{
    char buffer[1024]; // A buffer to hold the complete string
    int offset = 0;    // Tracks the position in the buffer

    // Add the label to the buffer
    offset += snprintf(buffer + offset, sizeof(buffer) - offset, "%s: ", label);
    for (int i = 0; i < size; i++) {
        offset += snprintf(buffer + offset, sizeof(buffer) - offset, "%f ",
                           darray[i]);

        // Check for buffer overflow
        if (offset >= sizeof(buffer)) {
            G_debug(4, "Error: Debug string too long");
            return;
        }
    }

    G_debug(4, "%s", buffer); // Send the complete string to G_debug
}

void print_long_matrix(long *matrix, globalParams *gParams)
{
    printf("** Long matrix:");
    long piv = 0;
    int cols = gParams->giCols;
    for (piv = 0; piv < gParams->glRowsxCols; ++piv) {
        if (piv % cols == 0)
            printf("\n");
        long value = *(matrix + piv);
        if (value == -9999) {
            value = 0;
        }
        printf("%ld ", value);
    }
}

void print_typeGeometry(typeGeometry *geometry)
{
    G_message("********************************");
    G_message("** typeGeometry:");
    G_message("\t-> sw_x: %f", geometry->sw_x);
    G_message("\t-> sw_y: %f", geometry->sw_y);
    G_message("\t-> ne_x: %f", geometry->ne_x);
    G_message("\t-> ne_y: %f", geometry->ne_y);
    G_message("\t-> cell: %d", geometry->cell);
    G_message("\t-> rows: %d", geometry->rows);
    G_message("\t-> cols: %d", geometry->cols);
}

void print_typeParams(typeParams *params)
{
    G_message("********************************");
    G_message("** typeParams: ");
    G_message("\t-> v0: %f", params->v0);
    G_message("\t-> min_v: %f", params->min_v);
    G_message("\t-> min_v2: %f", params->min_v2);
    G_message("\t-> tab: %f", params->tab);
    G_message("\t-> fly_step: %f", params->fly_step);
    G_message("\t-> roll_step: %f", params->roll_step);
    G_message("\t-> short_bounce2: %f", params->short_bounce2);
    G_message("\t-> fly_roll_thresh2: %f", params->fly_roll_thresh2);
    G_message("\t-> max_path: %d", params->max_path);
    G_message("\t-> gen_3d_vect: %d", params->gen_3d_vect);
    G_message("\t-> gen_2d_vect: %d", params->gen_2d_vect);
    G_message("\t-> elev_f: %s", params->elev_f);
    G_message("\t-> stst_f: %s", params->stst_f);
    G_message("\t-> v_elas_f: %s", params->v_elas_f);
    G_message("\t-> h_elas_f: %s", params->h_elas_f);
    G_message("\t-> frict_f: %s", params->frict_f);
    if (params->OUT_STONES_FILE[0] != '\0')
        G_message("\t-> OUT_STONES_FILE: %s", params->OUT_STONES_FILE);
    if (params->OUT_DTM_FILE[0] != '\0')
        G_message("\t-> OUT_DTM_FILE: %s", params->OUT_DTM_FILE);
    if (params->OUT_POINT_2D_FILE[0] != '\0')
        G_message("\t-> OUT_POINT_2D_FILE: %s", params->OUT_POINT_2D_FILE);
    if (params->OUT_ATTRIBUTES_2D_FILE[0] != '\0')
        G_message("\t-> OUT_ATTRIBUTES_2D_FILE: %s",
                  params->OUT_ATTRIBUTES_2D_FILE);
    if (params->OUT_COUNTERS_FILE[0] != '\0')
        G_message("\t-> OUT_COUNTERS_FILE: %s", params->OUT_COUNTERS_FILE);
    if (params->OUT_MAX_VEL_FILE[0] != '\0')
        G_message("\t-> OUT_MAX_VEL_FILE: %s", params->OUT_MAX_VEL_FILE);
    if (params->OUT_MAX_DZ_FILE[0] != '\0')
        G_message("\t-> OUT_MAX_DZ_FILE: %s", params->OUT_MAX_DZ_FILE);
    if (params->STAT_INPUT_FILE[0] != '\0')
        G_message("\t-> STAT_INPUT_FILE: %s", params->STAT_INPUT_FILE);
    G_message("\t-> stoc_flag: %d", params->stoc_flag);
    G_message("\t-> stoc_angle: %d", params->stoc_angle);
    G_message("\t-> stoc_vel: %d", params->stoc_vel);
    G_message("\t-> stoc_hel: %d", params->stoc_hel);
    G_message("\t-> stoc_frict: %d", params->stoc_frict);
    G_message("\t-> EnabledVideoOutput: %d", params->EnabledVideoOutput);
    G_message("\t-> EnabledLogFile: %d", params->EnabledLogFile);
    G_message("\t-> SwitchVelType: %d", params->SwitchVelType);
    if (params->AccMtrxFile[0] != '\0')
        G_message("AccMtrxFile: %s", params->AccMtrxFile);
    G_message("\t-> FromAccToVel: %f", params->FromAccToVel);
    G_message("\t-> gdQuotaUMFactor: %f", params->gdQuotaUMFactor);
    G_message("\t-> gdVeloUMFactor: %f", params->gdVeloUMFactor);
    G_message("\t-> gdTab2: %f", params->gdTab2);
    G_message("\t-> gFlagInfoStat: %f", params->gFlagInfoStat);
    G_message("\t-> giRockType: %d", params->giRockType);
    G_message("\t-> randomGenerator: %d", params->randomGenerator);
}

void print_globalParams(globalParams *params)
{
    G_message("********************************");
    G_message("** globalParams:");
    print_typeGeometry(params->gGeometry);
    G_message("\t-> glRowsxCols: %ld", params->glRowsxCols);
    G_message("\t-> gdInvCell: %f", params->gdInvCell);
    G_message("\t-> gdInvCell0001: %f", params->gdInvCell0001);
    G_message("\t-> gdInvCellSq20001: %f", params->gdInvCellSq20001);
    G_message("\t-> gdOffset: %f", params->gdOffset);
}

void print_runtimeParams(runtimeParams *params)
{
    G_message("********************************");
    G_message("** runtimeParams:");
    G_message("\t-> gdStocAngleR: %f", params->gdStocAngleR);
    G_message("\t-> gdStocVelR: %f", params->gdStocVelR);
    G_message("\t-> gdStocHelR: %f", params->gdStocHelR);
    G_message("\t-> gdStocFrictR: %f", params->gdStocFrictR);
    G_message("\t-> gdStocAngle2R: %f", params->gdStocAngle2R);
    G_message("\t-> gdStocVel2R: %f", params->gdStocVel2R);
    G_message("\t-> gdStocHel2R: %f", params->gdStocHel2R);
    G_message("\t-> gdStocFrict2R: %f", params->gdStocFrict2R);

    G_message("\t-> gplQuota: %p", params->gplQuota);
    G_message("\t-> gplStartStop: %p", params->gplStartStop);
    G_message("\t-> gplFrict: %p", params->gplFrict);
    G_message("\t-> gplCountStones: %p", params->gplCountStones);
    G_message("\t-> gplVelo: %p", params->gplVelo);
    G_message("\t-> gplMaxQuota: %p", params->gplMaxQuota);
    G_message("\t-> gplStartVel: %p", params->gplStartVel);
    G_message("\t-> gpcVElas: %p", params->gpcVElas);
    G_message("\t-> gpcHElas: %p", params->gpcHElas);
}

void print_uniData(UniSave *uniData)
{
    G_message("********************************");
    G_message("** UniSave:");
    G_message("\t-> u[0]: %f", uniData->u[0]);
    G_message("\t-> c: %f", uniData->c);
    G_message("\t-> cd: %f", uniData->cd);
    G_message("\t-> cm: %f", uniData->cm);
    G_message("\t-> ui: %d", uniData->ui);
    G_message("\t-> uj: %d", uniData->uj);
    G_message("\t-> randMax: %ld", uniData->randMax);
}
