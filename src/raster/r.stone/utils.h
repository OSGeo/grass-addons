#include "random2.h"
#include "stone.h"

void print_typeGeometry(typeGeometry *geometry);
void print_typeParams(typeParams *params);
void print_globalParams(globalParams *params);
void print_runtimeParams(runtimeParams *params);
void print_uniData(UniSave *uniData);
void print_long_matrix(long *matrix, globalParams *gParams);
void print_double_array(const char *label, double *darray, int size);
int pivIsValid(long piv, globalParams *gParams);

long QUOTA(runtimeParams *params, int piv);
int DEC_X(globalParams *params, int piv);
int DEC_Y(globalParams *params, int piv);
double POS_X(globalParams *params, int piv);
double POS_Y(globalParams *params, int piv);
long START_STOP(runtimeParams *params, int piv);
long START_VEL(runtimeParams *params, int piv);
long VELO(runtimeParams *params, int piv);
void setVELO(runtimeParams *params, long piv, long value);
long COUNT(runtimeParams *params, long piv);
void setCOUNT(runtimeParams *params, long piv, long value);
long MAX_QUOTA(runtimeParams *params, long piv);
void setMAX_QUOTA(runtimeParams *params, long piv, long value);
long V_ELAS(runtimeParams *params, long piv);
long H_ELAS(runtimeParams *params, long piv);
long FRICT(runtimeParams *params, long piv);
