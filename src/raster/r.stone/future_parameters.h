// PARAMETERS FOR FUTURE ENHANCEMENTS

/**
 * Accepted values are: 0, 1, 2, 3.
 *
 * BOULDER_SHAPE = 0, point, standard kinematic modelling
 * BOULDER_SHAPE = 1, sphere, pseudo-dynamic modelling
 * BOULDER_SHAPE = 2, cylinder, pseudo-dynamic modelling with ratio > 0.5 (ratio
 * is r/h) BOULDER_SHAPE = 3, disk, pseudo-dynamic modelling with ratio <= 0.5
 * (ratio is r/h)
 */
extern int BOULDER_SHAPE;

// The minimum boulder volume (for all: sphere, cylinder and disk) [meters^3]
extern double BOULDER_VOL_MIN;
// The maximum boulder volume (for all: sphere, cylinder and disk) [meters^3]
extern double BOULDER_VOL_MAX;
// The R/H (Radius / Height) (for cylinder and disk)
extern double BOULDER_SHAPE_RATIO;
// the density of the rock in Kg/mc (ex. 2700 Kg/mc for granite)
extern double BOULDER_DENSITY;

// See SWITCH_VEL_TYPE, the 2 below are currently unused.
extern char ACCELERATION_MTRX_FILE[];
extern double FROM_ACC_TO_VEL;

// ! Output files STONESTAT and uStation related. Currently unused.
//
// OUT_STONES_FILE, 3D uStation file obsolete (e.g., stones.ust)
// OUT_DTM_FILE, 3D uStation file for only DTM with stones (e.g., dtm.ust)
// OUT_DTM_ALL_FILE, 3D uStation file for all DTM (e.g., dtm_all.ust)
// OUT_POINT_2D_FILE, 2D point file (e.g., points-2d); contain id, x, y, z
// OUT_ATTRIBUTES_2D_FILE, 2D attributes point file (e.g., attributes-2d);
// contain id, quota, velocita',
//              delta dal terreno, energia (1/2*m*v*v), traiettoria, parabola
// FILE_INPUT_STAT Used to decide if Stone outputs binary file needed by
// STONESTAT
extern char OUT_STONES_FILE[];
extern char OUT_DTM_FILE[];
extern char OUT_DTM_ALL_FILE[];
extern char OUT_POINT_2D_FILE[];
extern char OUT_ATTRIBUTES_2D_FILE[];
extern char FILE_INPUT_STAT[];
extern int STAT_NUM_COLS;
extern int STAT_NUM_ROWS;
extern int STAT_CELL_SIZE;
extern int FLAG_MIN_DZ;
extern int FLAG_MAX_DZ;
extern int FLAG_AVERAGE_DZ;
extern int FLAG_REFUSE_DZ;
extern int FLAG_MIN_VEL;
extern int FLAG_MAX_VEL;
extern int FLAG_AVERAGE_VEL;
extern int FLAG_REFUSE_VEL;
extern int FLAG_COUNTER;
extern int FLAG_COUNT_POINTS;
extern int FLAG_COUNT_END_CELL;
extern char FILE_MIN_DZ[];
extern char FILE_MAX_DZ[];
extern char FILE_AVERAGE_DZ[];
extern char FILE_REFUSE_DZ[];
extern char FILE_MIN_VEL[];
extern char FILE_MAX_VEL[];
extern char FILE_AVERAGE_VEL[];
extern char FILE_REFUSE_VEL[];
extern char FILE_COUNTER[];
extern char FILE_COUNT_POINTS[];
extern char FILE_COUNT_END_CELL[];
extern char DIR_VEL_FREQ[];
extern char DIR_DZ_FREQ[];
extern int NUM_VEL_FREQUENCIES;
extern int NUM_DZ_FREQUENCIES;
extern int VEL_FREQ_01_VALUE;
extern int VEL_FREQ_02_VALUE;
extern int VEL_FREQ_03_VALUE;
extern int VEL_FREQ_04_VALUE;
extern int VEL_FREQ_05_VALUE;
extern int VEL_FREQ_06_VALUE;
extern int DZ_FREQ_01_VALUE;
extern int DZ_FREQ_02_VALUE;
extern int DZ_FREQ_03_VALUE;
extern int DZ_FREQ_04_VALUE;
extern int DZ_FREQ_05_VALUE;
extern double COORD_SW_X;
extern double COORD_SW_Y;
