
extern double OUTPUT_QUOTA_UM_FACTOR;
extern double OUTPUT_VELO_UM_FACTOR;
extern int VECT_3D_FILES_FLAG;
extern int FLAG_CREATE_INPUT_STAT;
extern int VECT_2D_FILES_FLAG;
extern int HREST_STOCH_FUNC;
extern int FRICT_STOCH_FUNC;
// coefficient to account for air drag and boulder shape.
// For a sphere the value range from 0.07 to 0.5.
// See also:
// https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/shape-effects-on-drag/
extern double DRAG_COEFFICIENT;
// when SWITCH_VEL_TYPE = 0, a single starting velocity given by
// START_VEL is used. When SWITCH_VEL_TYPE = 1, velocity values will be read
// from the file specified by ACCELERATION_MTRX_FILE and FROM_ACC_TO_VEL
extern int SWITCH_VEL_TYPE;

// Flying/rolling transition parameters.
// Two parameters are used to decide if a boulder is flying or rolling.
// DIST_FLY_ROLL is a distance, in meters.
// If two successive impact points are at a distance shorter that
// DIST_FLY_ROLL the boulder is assumed to be rolling.
// Unit is meters.
extern double DIST_FLY_ROLL;

// VEL_FLY_ROLL is a velocity, in m/sec.
// If the boulder velocity falls below VEL_FLY_ROLL
// the boulder is assumed to be rolling.
// Unit is m/sec.
extern double VEL_FLY_ROLL;

// Fly and roll internal tabulation steps, in meters
// Used to compute the rock fall trajectories where boulder is flying
// and where boulders are rolling, respectively
//! IMPORTANT: This value should be less or equal than the DEM grid cell.
extern double FLY_INT_TAB;
extern double ROLL_INT_TAB;

// Output tabulation, in meters.
// The minimum distance between two successive points along a r.f. trajectory.
extern double OUTPUT_TAB;

// Path array size. Used to compute the rock fall trajectory.
// Suggested value is 10000. Increase for very long or very complex trajectories
extern int PATH_ARRAY_SIZE;

// Stochastic flag.
// Used to decide if deterministic (single) or stochastic (multiple)
// simulation is performed
//
// Accepted values are 0 (zero) and 1 (one)
//
// STOCH_FLAG = 0, do not perform stochastic simulation (single run)
// STOCH_FLAG = 1, perform stochastic simulation
extern int STOCH_FLAG;
