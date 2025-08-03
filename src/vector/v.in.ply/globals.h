#ifndef __GLOBALS_H__
#define __GLOBALS_H__

#define PLY_ASCII        1 /* ascii PLY file */
#define PLY_BINARY_BE    2 /* binary PLY file, big endian */
#define PLY_BINARY_LE    3 /* binary PLY file, little endian */

/* known PLY elements */
#define PLY_VERTEX       1
#define PLY_FACE         2
#define PLY_EDGE         3
#define PLY_OTHER        4

/* PLY data types */
#define PLY_INVALID      0
#define PLY_CHAR         1
#define PLY_UCHAR        2
#define PLY_SHORT        3
#define PLY_USHORT       4
#define PLY_INT          5
#define PLY_UINT         6
#define PLY_FLOAT        7
#define PLY_DOUBLE       8

#define PLY_IS_INT(type) ((type) >= PLY_CHAR && (type) <= PLY_UINT)

extern int ply_type_size[];

struct ply_list {
    int n_values;
    int n_alloc;
    int *index;
};

struct prop_data {
    int int_val;
    double dbl_val;
};

struct ply_property { /* description of a property */
    char *name;       /* property name */
    int type;         /* property's data type */

    int is_list;      /* 0 = scalar, 1 = list */
    int list_type;    /* list index type, must be integer */
    int count_offset; /* offset byte for list count */
};

struct ply_element {  /* description of an element */
    char *name;       /* element name */
    int type;         /* element type (vertex, face, edge, other) */
    int n;            /* number of elements in this object */
    int size;         /* size of element (bytes) or -1 if variable */
    int n_properties; /* number of properties for this element */
    struct ply_property **property; /* list of properties in the file */
};

struct ply_file {                     /* description of PLY file */
    FILE *fp;                         /* file pointer */
    int file_type;                    /* ascii or binary */
    char *version;                    /* version number, should be 1.0 */
    int n_elements;                   /* number of element types of object */
    struct ply_element **element;     /* list of elements */
    struct ply_element *curr_element; /* currently processed element */
    struct ply_list list;             /* list of vertices */
    int n_comments;                   /* number of comments */
    char **comment;                   /* list of comments */
    int header_size;                  /* header_size (offset to body) */
    int x; /* vertex property index for x coordinate */
    int y; /* vertex property index for y coordinate */
    int z; /* vertex property index for z coordinate */
};

#endif
