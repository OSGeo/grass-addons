/* **************************************************************
 *
 *  MODULE:       v.in.dwg
 *
 *  AUTHOR(S):    Rodrigo Rodrigues da Silva
 *                based on original code by Radim Blazek
 *
 *  PURPOSE:      Import of DWG/DXF files
 *
 *  COPYRIGHT:    (C) 2001, 2010 by the GRASS Development Team
 *
 *                This program is free software under the
 *                GNU General Public License (>=v2).
 *                Read the file COPYING that comes with GRASS
 *                for details.
 *
 * **************************************************************/

/* transformation, first level is 0 ( called from main ) and transformation
 *  for this level is 0,0,0, 1,1,1, 0 so that no transformation is done on first
 * level (not efective but better readable?) */
typedef struct {
    double dx, dy, dz;
    double xscale, yscale, zscale;
    double rotang;
} TRANS;

extern int cat;
extern int
    n_elements; /* number of processed elements (only low level elements) */
extern int
    n_skipped; /* number of skipped low level elements (different layer name) */
extern struct Map_info Map;
extern dbDriver *driver;
extern dbString sql;
extern dbString str;
extern struct line_pnts *Points;
extern struct line_cats *Cats;
extern char *Txt;
extern char *Block;
extern struct field_info *Fi;
extern TRANS *Trans; /* transformation */
extern int atrans;   /* number of allocated levels */
extern struct Option *layers_opt;
extern struct Flag *invert_flag, *circle_flag;

void write_entity(Dwg_Object *obj, Dwg_Object **objects,
                  long unsigned int *ent_counter, int level);

int is_low_level(Dwg_Object *obj);
