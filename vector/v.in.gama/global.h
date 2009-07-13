#ifndef MAIN
# define EXT extern
#else 
# define EXT
#endif

#ifndef GLOBAL___H
#define GLOBAL___H

#include <grass/gis.h>
#include <grass/Vect.h>
#include <grass/dbmi.h>
#include <grass/glocale.h>

#include <libxml/parser.h>
#include <libxml/tree.h>

#define FIX 0
#define ADJ 1
#define APP 2

#define FIELD_POINT 1
#define FIELD_OBS   2

#define DIM   3                   /* coordinates */

#define ID_LENGTH 128             /* varchar (ID_LENGTH) */

#define OPTIONS struct _options_
EXT OPTIONS
{
    char* input;
    char* output;
    int   dotable;
} options;

struct coor
{
  double val [3];        /* x_fix, x_adj, x_app */
  short  is_null [3];
  short  is_constrained;
};

typedef struct _point_
{
  int         cat; /* -1 -> not writen to the map due missing x|y */
  dbString    id;
  struct coor xyz [3];
} Point;

struct list_points
{
  Point* point;
  struct list_points* next;
};

struct list_nodes
{
  xmlNode* node;
  struct list_nodes* next;
};

/* head.c */
int write_head (struct Map_info*, xmlDoc*);
int find_substring (dbString*, const char*, dbString*);

/* parser.c */
int parse_command_line(int, char**);

/* vect.c */
int create_map (struct Map_info*, xmlDoc*, int);
int create_points (struct Map_info*, xmlDoc*, int, struct list_points**);
void point_init (Point*);
void point_set (Point*, xmlNode*, int, xmlNode*, xmlNode*, xmlNode*);
void write_points (struct Map_info*, xmlNode*, struct list_points*, int);
void list_points_free (struct list_points**);
int list_points_push_back (struct list_points**, Point*);
Point* find_point (struct list_points*, dbString* id);
void point_update (Point*, int, xmlNode*, xmlNode*, xmlNode*);
int point_get_xyz (Point*, char*, double*);
int point_exists (struct list_points*, dbString*);
int create_obs (struct Map_info*, xmlDoc*, int, struct list_points*);
int write_line (struct Map_info*, int, int, int, int);

/* table.c */
int create_tables (struct Map_info*, xmlDoc*);
void insert_point (struct field_info*, dbDriver*, dbTable*, Point*, int);
void insert_obs   (struct field_info*, dbDriver*, dbTable*, xmlNode*, int);

/* tree.c */
int find_node (xmlNode*, const char*, xmlNode**);
int find_nodes (xmlNode*, const char*, struct list_nodes**);
void find__nodes (xmlNode*, xmlNode*, const char*, struct list_nodes**, int*, int*);
void list_init (void**);
void list_nodes_free (struct list_nodes**);
void list_nodes_push_back (struct list_nodes** lnodes, xmlNode* node);
int is_3d_map (xmlDoc*);
int node_get_value_int (xmlNode*, int*);
int node_get_value_double (xmlNode*, double*);
int node_get_value_string (xmlNode*, char*, dbString*);
int axes_xy_str2type (char *);

#endif
