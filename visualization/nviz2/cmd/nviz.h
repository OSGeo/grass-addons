#ifndef __NVIZ_H__
#define __NVIZ_H__

#include <grass/gsurf.h>

#define MAP_OBJ_UNDEFINED 0
#define MAP_OBJ_SURF 1
#define MAP_OBJ_VOL 2
#define MAP_OBJ_VECT 3

#define RANGE (5 * GS_UNIT_SIZE)
#define RANGE_OFFSET (2 * GS_UNIT_SIZE)
#define ZRANGE (3 * GS_UNIT_SIZE)
#define ZRANGE_OFFSET (1 * GS_UNIT_SIZE)

#define DEFAULT_SURF_COLOR 0x33BBFF

#define RED_MASK 0x000000FF
#define GRN_MASK 0x0000FF00
#define BLU_MASK 0x00FF0000

/* data structures */
typedef struct{
    int id;
    float brt;
    float r, g, b;
    float ar, ag, ab;  /* ambient rgb */
    float x, y, z, w; /* position */
} light_data;

typedef struct {
    /* ranges */
    float zrange, xyrange;
    
    /* cplanes */
    int num_cplanes;
    int cur_cplane, cp_on[MAX_CPLANES];
    float cp_trans[MAX_CPLANES][3];
    float cp_rot[MAX_CPLANES][3];
    
    /* light */
    light_data light[MAX_LIGHTS];
    
    /* background color */
    int bgcolor;
} nv_data;

/* The following structure is used to associate client data with surfaces.
 * We do this so that we don't have to rely on the surface ID (which is libal to change
 * between subsequent executions of nviz) when saving set-up info to files.
 */

typedef struct {
    /* We use logical names to assign textual names to map objects.
       When Nviz needs to refer to a map object it uses the logical name
       rather than the map ID.  By setting appropriate logical names, we
       can reuse names inbetween executions of Nviz.  The Nviz library
       also provides a mechanism for aliasing between logical names.
       Thus several logical names may refer to the same map object.
       Aliases are meant to support the case in which two logical names
       happen to be the same.  The Nviz library automatically assigns
       logical names uniquely if they are not specified in the creation
       of a map object.  When loading a saved file containing several map
       objects, it is expected that the map 0bjects will be aliased to
       their previous names.  This ensures that old scripts will work.
    */
    
    char *logical_name;
    
} nv_clientdata;

#endif /* __NVIZ_H__ */
