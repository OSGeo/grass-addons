/*
   This code is described in "Computational Geometry in C" (Second Edition),
   Chapter 4.  It is not written to be comprehensible without the
   explanation in that book.

   Input: 3n integer coordinates for the points.
   Output: the 3D convex hull, in postscript with embedded comments
   showing the vertices and faces.

   Compile: gcc -o chull chull.c

   Written by Joseph O'Rourke, with contributions by
   Kristy Anderson, John Kutcher, Catherine Schevon, Susan Weller.
   Last modified: March 1998
   Questions to orourke@cs.smith.edu.
   --------------------------------------------------------------------
   This code is Copyright 1998 by Joseph O'Rourke.  It may be freely
   redistributed in its entirety provided that this copyright notice is
   not removed.
   --------------------------------------------------------------------
 */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#include <grass/gis.h>

#include "globals.h"

#ifndef __bool_true_false_are_defined
/* Define Boolean type for pre-7.8.6 compatibility */
typedef enum { false = FALSE, true = TRUE } bool;
#endif

/* Define vertex indices. */
#define X 0
#define Y 1
#define Z 2

/* Define structures for vertices, edges and faces */
typedef struct tVertexStructure tsVertex;
typedef tsVertex *tVertex;

typedef struct tEdgeStructure tsEdge;
typedef tsEdge *tEdge;

typedef struct tFaceStructure tsFace;
typedef tsFace *tFace;

struct tVertexStructure {
    long int v[3];
    int vnum;
    tEdge duplicate; /* pointer to incident cone edge (or NULL) */
    bool onhull;     /* T iff point on hull. */
    bool mark;       /* T iff point already processed. */
    tVertex next, prev;
};

struct tEdgeStructure {
    tFace adjface[2];
    tVertex endpts[2];
    tFace newface; /* pointer to incident cone face. */
    bool delete;   /* T iff edge should be delete. */
    tEdge next, prev;
};

struct tFaceStructure {
    tEdge edge[3];
    tVertex vertex[3];
    bool visible; /* T iff face visible from new point. */
    tFace next, prev;
};

/* Define flags */
#define ONHULL    true
#define REMOVED   true
#define VISIBLE   true
#define PROCESSED true
#define SAFE      2000000000 /* Range of safe coord values. */

/* Global variable definitions */
tVertex vertices = NULL;
tEdge edges = NULL;
tFace faces = NULL;
bool debug = false;
bool check = false;

/* Function declarations */
tVertex MakeNullVertex(void);
void ReadVertices(long int *px, long int *py, long int *pz, int num_points);
void Print(void);
void Dump(FILE *tmpfile);
void SubVec(long int a[3], long int b[3], long int c[3]);
int DoubleTriangle(void);
void ConstructHull(void);
bool AddOne(tVertex p);
int VolumeSign(tFace f, tVertex p);
int Volumei(tFace f, tVertex p);
tFace MakeConeFace(tEdge e, tVertex p);
void MakeCcw(tFace f, tEdge e, tVertex p);
tEdge MakeNullEdge(void);
tFace MakeNullFace(void);
tFace MakeFace(tVertex v0, tVertex v1, tVertex v2, tFace f);
void CleanUp(void);
void CleanEdges(void);
void CleanFaces(void);
void CleanVertices(void);
bool Collinear(tVertex a, tVertex b, tVertex c);
void CheckEuler(long int V, long int E, long int F);
void PrintPoint(tVertex p);
void Checks(void);
void Consistency(void);
void Convexity(void);
void PrintOut(tVertex v);
void PrintVertices(void);
void PrintEdges(void);
void PrintFaces(void);

#include "macros.h"

/*

   Release all memory allocated for edges, faces and vertices

 */
void freeMem(void)
{
    tEdge e; /* Primary index into edge list. */
    tFace f; /* Primary pointer into face list. */
    tVertex v;
    tEdge te;   /* Temporary edge pointer. */
    tFace tf;   /* Temporary face pointer. */
    tVertex tv; /* Temporary vertex pointer. */

    if (DEBUG) {
        fprintf(stdout, "FREE MEM:\n");
        fflush(stdout);
    }

    if (DEBUG) {
        fprintf(stdout, "  EDGES:\n");
        fflush(stdout);
    }
    e = edges;
    do {
        te = e;
        e = e->next;
        DELETE(edges, te);
    } while (e != edges);

    if (DEBUG) {
        fprintf(stdout, "  FACES:\n");
        fflush(stdout);
    }
    f = faces;
    do {
        tf = f;
        f = f->next;
        DELETE(faces, tf);
    } while (f != faces);

    if (DEBUG) {
        fprintf(stdout, "  VERTICES:\n");
        fflush(stdout);
    }
    v = vertices;
    do {
        tv = v;
        v = v->next;
        DELETE(vertices, tv);
    } while (v != vertices);

    FREE(te);
    FREE(tf);
    FREE(tv);

    DELETE(edges, e);
    DELETE(faces, f);
    DELETE(vertices, v);

    FREE(edges);
    FREE(faces);
    FREE(vertices);

    if (DEBUG) {
        fprintf(stdout, "MEM FREE'D!\n");
        fflush(stdout);
    }
}

/*-------------------------------------------------------------------*/
int make3DHull(long int *px, long int *py, long int *pz, int num_points,
               FILE *tmpfile)
{
    int error;

    check = false;
    debug = false;

    if (DEBUG > 1)
        check = true;
    if (DEBUG > 2)
        debug = true;

    ReadVertices(px, py, pz, num_points);

    error = DoubleTriangle();
    if (error < 0) {
        G_warning("All points of this layer are in the same voxel plane.\n");
        freeMem();
        return (error);
    }

    ConstructHull();

    Dump(tmpfile);

    freeMem();

    return (0);
}

/*---------------------------------------------------------------------
MakeNullVertex: Makes a vertex, nulls out fields.
---------------------------------------------------------------------*/
tVertex MakeNullVertex(void)
{
    tVertex v;

    NEW(v, tsVertex);
    v->duplicate = NULL;
    v->onhull = !ONHULL;
    v->mark = !PROCESSED;
    ADD(vertices, v);

    return v;
}

/*---------------------------------------------------------------------
ReadVertices: Reads in the vertices, and links them into a circular
list with MakeNullVertex.  There is no need for the # of vertices to be
the first line: the function looks for EOF instead.  Sets the global
variable vertices via the ADD macro.
---------------------------------------------------------------------*/
void ReadVertices(long int *px, long int *py, long int *pz, int num_points)
{
    tVertex v;
    int vnum = 0;
    int i;

    for (i = 0; i < num_points; i++) {
        v = MakeNullVertex();
        v->v[X] = px[i];
        v->v[Y] = py[i];
        v->v[Z] = pz[i];
        v->vnum = vnum++;
        if ((abs(px[i]) > SAFE) || (abs(py[i]) > SAFE) || (abs(pz[i]) > SAFE)) {
            printf("Coordinate of vertex below might be too large: run with -c "
                   "flag\n");
            PrintPoint(v);
        }
    }
}

/*---------------------------------------------------------------------
Dump: Dumps out the vertices and the faces to a file.
Uses the vnum indices  corresponding to the order in which the vertices
were input.
Output is in GRASS ASCII file format.
---------------------------------------------------------------------*/
void Dump(FILE *tmpfile)
{
    /* Pointers to vertices, edges, faces. */
    tVertex v;
    tEdge e;
    tFace f;
    double dx, dy, dz;
    long int a[3], b[3]; /* used to compute normal vector */

    /* Counters for Euler's formula. */
    long int V = 0, E = 0, F = 0;

    /* Note: lowercase==pointer, uppercase==counter. */
    long int cat;

    f = faces;
    do {
        ++F;
        f = f->next;
    } while (f != faces);

    /* GRASS 6 map header */
    fprintf(tmpfile, "ORGANIZATION: \n");
    fprintf(tmpfile, "DIGIT DATE: \n");
    fprintf(tmpfile, "DIGIT NAME: \n");
    fprintf(tmpfile, "MAP NAME: \n");
    fprintf(tmpfile, "MAP DATE: \n");
    fprintf(tmpfile, "MAP SCALE: 10000\n");
    fprintf(tmpfile, "OTHER INFO: %li faces.\n", F);
    fprintf(tmpfile, "ZONE: 0\n");
    fprintf(tmpfile, "MAP THRESH: 0.5\n");
    fprintf(tmpfile, "VERTI:\n");

    cat = 1;

    /* putting all faces into one object does not produce nice output in NVIZ !
       If we decided to dump all layers into a single file, we would also need
       a cat for each object to be passed from the main program.
     */

    /*
       printf("F  %li 1\n", F*4);
       do {
       dx = ((double) ( f->vertex[0]->v[X] ) / (1000));
       dy = ((double) ( f->vertex[0]->v[Y] ) / (1000));
       dz = ((double) ( f->vertex[0]->v[Z] ) / (1000));
       printf(" %.3f %.3f %.3f\n", dx, dy, dz);
       dx = ((double) ( f->vertex[1]->v[X] ) / (1000));
       dy = ((double) ( f->vertex[1]->v[Y] ) / (1000));
       dz = ((double) ( f->vertex[1]->v[Z] ) / (1000));
       printf(" %.3f %.3f %.3f\n", dx, dy, dz);
       dx = ((double) ( f->vertex[2]->v[X] ) / (1000));
       dy = ((double) ( f->vertex[2]->v[Y] ) / (1000));
       dz = ((double) ( f->vertex[2]->v[Z] ) / (1000));
       printf(" %.3f %.3f %.3f\n", dx, dy, dz);
       dx = ((double) ( f->vertex[0]->v[X] ) / (1000));
       dy = ((double) ( f->vertex[0]->v[Y] ) / (1000));
       dz = ((double) ( f->vertex[0]->v[Z] ) / (1000));
       printf(" %.3f %.3f %.3f\n", dx, dy, dz);
       f = f->next;
       } while ( f != faces );
       printf(" %li 1\n", cat);
     */

    do {
        fprintf(tmpfile, "F  4 1\n");
        dx = ((double)(f->vertex[0]->v[X]) / (PRECISION));
        dy = ((double)(f->vertex[0]->v[Y]) / (PRECISION));
        dz = ((double)(f->vertex[0]->v[Z]) / (PRECISION));
        fprintf(tmpfile, " %.3f %.3f %.3f\n", dx, dy, dz);
        dx = ((double)(f->vertex[1]->v[X]) / (PRECISION));
        dy = ((double)(f->vertex[1]->v[Y]) / (PRECISION));
        dz = ((double)(f->vertex[1]->v[Z]) / (PRECISION));
        fprintf(tmpfile, " %.3f %.3f %.3f\n", dx, dy, dz);
        dx = ((double)(f->vertex[2]->v[X]) / (PRECISION));
        dy = ((double)(f->vertex[2]->v[Y]) / (PRECISION));
        dz = ((double)(f->vertex[2]->v[Z]) / (PRECISION));
        fprintf(tmpfile, " %.3f %.3f %.3f\n", dx, dy, dz);
        dx = ((double)(f->vertex[0]->v[X]) / (PRECISION));
        dy = ((double)(f->vertex[0]->v[Y]) / (PRECISION));
        dz = ((double)(f->vertex[0]->v[Z]) / (PRECISION));
        fprintf(tmpfile, " %.3f %.3f %.3f\n", dx, dy, dz);
        fprintf(tmpfile, " %li 1\n", cat);
        cat++;
        f = f->next;
    } while (f != faces);

    if (DEBUG > 0) {
        fprintf(stdout, "3D Convex hull check (Euler):\n");
        check = true;
        CheckEuler(V, E, F);
    }
}

/*---------------------------------------------------------------------
Print: Prints out the vertices and the faces.  Uses the vnum indices
corresponding to the order in which the vertices were input.
Output is in PostScript format.
---------------------------------------------------------------------*/
void Print(void)
{
    /* Pointers to vertices, edges, faces. */
    tVertex v;
    tEdge e;
    tFace f;
    long int xmin, ymin, xmax, ymax;
    long int a[3], b[3]; /* used to compute normal vector */

    /* Counters for Euler's formula. */
    long int V = 0, E = 0, F = 0;

    /* Note: lowercase==pointer, uppercase==counter. */

    /*-- find X min & max --*/
    v = vertices;
    xmin = xmax = v->v[X];
    do {
        if (v->v[X] > xmax)
            xmax = v->v[X];
        else if (v->v[X] < xmin)
            xmin = v->v[X];
        v = v->next;
    } while (v != vertices);

    /*-- find Y min & max --*/
    v = vertices;
    ymin = ymax = v->v[Y];
    do {
        if (v->v[Y] > ymax)
            ymax = v->v[Y];
        else if (v->v[Y] < ymin)
            ymin = v->v[Y];
        v = v->next;
    } while (v != vertices);

    /* PostScript header */
    printf("%%!PS\n");
    printf("%%%%BoundingBox: %li %li %li %li\n", xmin, ymin, xmax, ymax);
    printf(".00 .00 setlinewidth\n");
    printf("%li %li translate\n", -xmin + 72, -ymin + 72);
    /* The +72 shifts the figure one inch from the lower left corner */

    /* Vertices. */
    v = vertices;
    do {
        if (v->mark)
            V++;
        v = v->next;
    } while (v != vertices);
    printf("\n%%%% Vertices:\tV = %li\n", V);
    printf("%%%% index:\tx\ty\tz\n");
    do {
        printf("%%%% %5d:\t%li\t%li\t%li\n", v->vnum, v->v[X], v->v[Y],
               v->v[Z]);
        v = v->next;
    } while (v != vertices);

    /* Faces. */
    /* visible faces are printed as PS output */
    f = faces;
    do {
        ++F;
        f = f->next;
    } while (f != faces);
    printf("\n%%%% Faces:\tF = %li\n", F);
    printf("%%%% Visible faces only: \n");
    do {
        /* Print face only if it is visible: if normal vector >= 0 */
        SubVec(f->vertex[1]->v, f->vertex[0]->v, a);
        SubVec(f->vertex[2]->v, f->vertex[1]->v, b);
        if ((a[0] * b[1] - a[1] * b[0]) >= 0) {
            printf("%%%% vnums:  %d  %d  %d\n", f->vertex[0]->vnum,
                   f->vertex[1]->vnum, f->vertex[2]->vnum);
            printf("newpath\n");
            printf("%li\t%li\tmoveto\n", f->vertex[0]->v[X],
                   f->vertex[0]->v[Y]);
            printf("%li\t%li\tlineto\n", f->vertex[1]->v[X],
                   f->vertex[1]->v[Y]);
            printf("%li\t%li\tlineto\n", f->vertex[2]->v[X],
                   f->vertex[2]->v[Y]);
            printf("closepath stroke\n\n");
        }
        f = f->next;
    } while (f != faces);

    /* prints a list of all faces */
    printf("%%%% List of all faces: \n");
    printf("%%%%\tv0\tv1\tv2\t(vertex indices)\n");
    do {
        printf("%%%%\t%d\t%d\t%d\n", f->vertex[0]->vnum, f->vertex[1]->vnum,
               f->vertex[2]->vnum);
        f = f->next;
    } while (f != faces);

    /* Edges. */
    e = edges;
    do {
        E++;
        e = e->next;
    } while (e != edges);
    printf("\n%%%% Edges:\tE = %li\n", E);
    /* Edges not printed out (but easily added). */

    printf("\nshowpage\n\n");

    if (DEBUG > 0) {
        fprintf(stdout, "3D Convex hull check (Euler):\n");
        check = true;
        CheckEuler(V, E, F);
    }
}

/*---------------------------------------------------------------------
SubVec:  Computes a - b and puts it into c.
---------------------------------------------------------------------*/
void SubVec(long int a[3], long int b[3], long int c[3])
{
    long int i;

    for (i = 0; i < 2; i++)
        c[i] = a[i] - b[i];
}

/*---------------------------------------------------------------------
 DoubleTriangle builds the initial double triangle.  It first finds 3
 noncollinear points and makes two faces out of them, in opposite order.
 It then finds a fourth point that is not coplanar with that face.  The
 vertices are stored in the face structure in counterclockwise order so
 that the volume between the face and the point is negative. Lastly, the
 3 newfaces to the fourth point are constructed and the data structures
 are cleaned up.
---------------------------------------------------------------------*/

/* RETURN:      0 if OK */
/*              -1 if all points collinear */
/*              -2 if all points coplanar */

int DoubleTriangle(void)
{
    tVertex v0, v1, v2, v3, t;
    tFace f0, f1 = NULL;
    tEdge e0, e1, e2, s;
    long int vol;

    /* Find 3 noncollinear points. */
    v0 = vertices;
    while (Collinear(v0, v0->next, v0->next->next)) {
        if ((v0 = v0->next) == vertices) {
            if (debug) {
                printf("DoubleTriangle:  All points are collinear!\n");
            }
            return (-1);
        }
    }
    v1 = v0->next;
    v2 = v1->next;

    /* Mark the vertices as processed. */
    v0->mark = PROCESSED;
    v1->mark = PROCESSED;
    v2->mark = PROCESSED;

    /* Create the two "twin" faces. */
    f0 = MakeFace(v0, v1, v2, f1);
    f1 = MakeFace(v2, v1, v0, f0);

    /* Link adjacent face fields. */
    f0->edge[0]->adjface[1] = f1;
    f0->edge[1]->adjface[1] = f1;
    f0->edge[2]->adjface[1] = f1;
    f1->edge[0]->adjface[1] = f0;
    f1->edge[1]->adjface[1] = f0;
    f1->edge[2]->adjface[1] = f0;

    /* Find a fourth, noncoplanar point to form tetrahedron. */
    v3 = v2->next;
    vol = VolumeSign(f0, v3);
    while (!vol) {
        if ((v3 = v3->next) == v0) {
            if (debug) {
                printf("DoubleTriangle:  All points are coplanar!\n");
            }
            return (-2);
        }
        vol = VolumeSign(f0, v3);
    }

    /* Insure that v3 will be the first added. */
    vertices = v3;
    if (debug) {
        fprintf(stderr, "DoubleTriangle: finished. Head repositioned at v3.\n");
        PrintOut(vertices);
    }

    return (0);
}

/*---------------------------------------------------------------------
ConstructHull adds the vertices to the hull one at a time.  The hull
vertices are those in the list marked as onhull.
---------------------------------------------------------------------*/
void ConstructHull(void)
{
    tVertex v, vnext;
    long int vol;
    bool changed; /* T if addition changes hull; not used. */
    int i;
    int numVertices;

    if (VERBOSE) {
        fprintf(stdout, "  Constructing 3D hull: \n");
    }

    v = vertices;
    i = 0;
    do {
        vnext = v->next;
        v = vnext;
        i++;
    } while (v != vertices);
    numVertices = i;

    v = vertices;
    i = 0;
    do {
        vnext = v->next;
        if (!v->mark) {
            v->mark = PROCESSED;
            changed = AddOne(v);
            CleanUp();

            if (check) {
                fprintf(stderr, "ConstructHull: After Add of %d & Cleanup:\n",
                        v->vnum);
                Checks();
            }
            if (debug)
                PrintOut(v);
        }
        v = vnext;
        i++;
        if (VERBOSE) {
            G_percent(i, numVertices, 1);
        }
    } while (v != vertices);

    fflush(stdout);
}

/*---------------------------------------------------------------------
AddOne is passed a vertex.  It first determines all faces visible from
that point.  If none are visible then the point is marked as not
onhull.  Next is a loop over edges.  If both faces adjacent to an edge
are visible, then the edge is marked for deletion.  If just one of the
adjacent faces is visible then a new face is constructed.
---------------------------------------------------------------------*/
bool AddOne(tVertex p)
{
    tFace f;
    tEdge e, temp;
    long int vol;
    bool vis = false;

    if (debug) {
        fprintf(stderr, "AddOne: starting to add v%d.\n", p->vnum);
        PrintOut(vertices);
    }

    /* Mark faces visible from p. */
    f = faces;
    do {
        vol = VolumeSign(f, p);
        if (debug)
            fprintf(stderr, "faddr: %6x   paddr: %6x   Vol = %li\n",
                    (unsigned int)f, (unsigned int)p, vol);
        if (vol < 0) {
            f->visible = VISIBLE;
            vis = true;
        }
        f = f->next;
    } while (f != faces);

    /* If no faces are visible from p, then p is inside the hull. */
    if (!vis) {
        p->onhull = !ONHULL;
        return false;
    }

    /* Mark edges in interior of visible region for deletion.
       Erect a newface based on each border edge. */
    e = edges;
    do {
        temp = e->next;
        if (e->adjface[0]->visible && e->adjface[1]->visible)
            /* e interior: mark for deletion. */
            e->delete = REMOVED;
        else if (e->adjface[0]->visible || e->adjface[1]->visible)
            /* e border: make a new face. */
            e->newface = MakeConeFace(e, p);
        e = temp;
    } while (e != edges);
    return true;
}

/*---------------------------------------------------------------------
VolumeSign returns the sign of the volume of the tetrahedron determined by f
and p.  VolumeSign is +1 iff p is on the negative side of f,
where the positive side is determined by the rh-rule.  So the volume
is positive if the ccw normal to f points outside the tetrahedron.
The final fewer-multiplications form is due to Bob Williamson.
---------------------------------------------------------------------*/
int VolumeSign(tFace f, tVertex p)
{
    double vol;
    long int voli;
    double ax, ay, az, bx, by, bz, cx, cy, cz;

    ax = f->vertex[0]->v[X] - p->v[X];
    ay = f->vertex[0]->v[Y] - p->v[Y];
    az = f->vertex[0]->v[Z] - p->v[Z];
    bx = f->vertex[1]->v[X] - p->v[X];
    by = f->vertex[1]->v[Y] - p->v[Y];
    bz = f->vertex[1]->v[Z] - p->v[Z];
    cx = f->vertex[2]->v[X] - p->v[X];
    cy = f->vertex[2]->v[Y] - p->v[Y];
    cz = f->vertex[2]->v[Z] - p->v[Z];

    vol = ax * (by * cz - bz * cy) + ay * (bz * cx - bx * cz) +
          az * (bx * cy - by * cx);

    if (debug)
        fprintf(stderr,
                "Face=%6x; Vertex=%d: vol(int) = %li, vol(double) = %.f\n",
                (unsigned int)f, p->vnum, voli, vol);

    /* The volume should be an integer. */
    if (vol > 0.5)
        return 1;
    else if (vol < -0.5)
        return -1;
    else
        return 0;
}

/*---------------------------------------------------------------------*/
int Volumei(tFace f, tVertex p)
{
    double vol;
    long int voli;
    double ax, ay, az, bx, by, bz, cx, cy, cz, dx, dy, dz;

    ax = f->vertex[0]->v[X] - p->v[X];
    ay = f->vertex[0]->v[Y] - p->v[Y];
    az = f->vertex[0]->v[Z] - p->v[Z];
    bx = f->vertex[1]->v[X] - p->v[X];
    by = f->vertex[1]->v[Y] - p->v[Y];
    bz = f->vertex[1]->v[Z] - p->v[Z];
    cx = f->vertex[2]->v[X] - p->v[X];
    cy = f->vertex[2]->v[Y] - p->v[Y];
    cz = f->vertex[2]->v[Z] - p->v[Z];

    vol = (ax * (by * cz - bz * cy) + ay * (bz * cx - bx * cz) +
           az * (bx * cy - by * cx));

    if (debug)
        fprintf(stderr,
                "Face=%6x; Vertex=%d: vol(int) = %li, vol(double) = %.f\n",
                (unsigned int)f, p->vnum, voli, vol);

    /* The volume should be an integer. */
    if (vol > 0.5)
        return 1;
    else if (vol < -0.5)
        return -1;
    else
        return 0;
}

/*-------------------------------------------------------------------*/
void PrintPoint(tVertex p)
{
    int i;

    for (i = 0; i < 3; i++)
        printf("\t%li", p->v[i]);
    putchar('\n');
}

/*---------------------------------------------------------------------
MakeConeFace makes a new face and two new edges between the
edge and the point that are passed to it. It returns a pointer to
the new face.
---------------------------------------------------------------------*/
tFace MakeConeFace(tEdge e, tVertex p)
{
    tEdge new_edge[2];
    tFace new_face;
    int i, j;

    /* Make two new edges (if don't already exist). */
    for (i = 0; i < 2; ++i)
        /* If the edge exists, copy it into new_edge. */
        if (!(new_edge[i] = e->endpts[i]->duplicate)) {
            /* Otherwise (duplicate is NULL), MakeNullEdge. */
            new_edge[i] = MakeNullEdge();
            new_edge[i]->endpts[0] = e->endpts[i];
            new_edge[i]->endpts[1] = p;
            e->endpts[i]->duplicate = new_edge[i];
        }

    /* Make the new face. */
    new_face = MakeNullFace();
    new_face->edge[0] = e;
    new_face->edge[1] = new_edge[0];
    new_face->edge[2] = new_edge[1];
    MakeCcw(new_face, e, p);

    /* Set the adjacent face pointers. */
    for (i = 0; i < 2; ++i)
        for (j = 0; j < 2; ++j)
            /* Only one NULL link should be set to new_face. */
            if (!new_edge[i]->adjface[j]) {
                new_edge[i]->adjface[j] = new_face;
                break;
            }

    return new_face;
}

/*---------------------------------------------------------------------
MakeCcw puts the vertices in the face structure in counterclock wise
order.  We want to store the vertices in the same
order as in the visible face.  The third vertex is always p.
---------------------------------------------------------------------*/
void MakeCcw(tFace f, tEdge e, tVertex p)
{
    tFace fv; /* The visible face adjacent to e */
    int i;    /* Index of e->endpoint[0] in fv. */
    tEdge s;  /* Temporary, for swapping */

    if (e->adjface[0]->visible)
        fv = e->adjface[0];
    else
        fv = e->adjface[1];

    /* Set vertex[0] & [1] of f to have the same orientation
       as do the corresponding vertices of fv. */
    for (i = 0; fv->vertex[i] != e->endpts[0]; ++i)
        ;
    /* Orient f the same as fv. */
    if (fv->vertex[(i + 1) % 3] != e->endpts[1]) {
        f->vertex[0] = e->endpts[1];
        f->vertex[1] = e->endpts[0];
    }
    else {
        f->vertex[0] = e->endpts[0];
        f->vertex[1] = e->endpts[1];
        SWAP(s, f->edge[1], f->edge[2]);
    }
    /* This swap is tricky. e is edge[0]. edge[1] is based on endpt[0],
       edge[2] on endpt[1].  So if e is oriented "forwards," we
       need to move edge[1] to follow [0], because it precedes. */

    f->vertex[2] = p;
}

/*---------------------------------------------------------------------
MakeNullEdge creates a new cell and initializes all pointers to NULL
and sets all flags to off.  It returns a pointer to the empty cell.
---------------------------------------------------------------------*/
tEdge MakeNullEdge(void)
{
    tEdge e;

    NEW(e, tsEdge);
    e->adjface[0] = e->adjface[1] = e->newface = NULL;
    e->endpts[0] = e->endpts[1] = NULL;
    e->delete = !REMOVED;
    ADD(edges, e);
    return e;
}

/*--------------------------------------------------------------------
MakeNullFace creates a new face structure and initializes all of its
flags to NULL and sets all the flags to off.  It returns a pointer
to the empty cell.
---------------------------------------------------------------------*/
tFace MakeNullFace(void)
{
    tFace f;
    int i;

    NEW(f, tsFace);
    for (i = 0; i < 3; ++i) {
        f->edge[i] = NULL;
        f->vertex[i] = NULL;
    }
    f->visible = !VISIBLE;
    ADD(faces, f);
    return f;
}

/*---------------------------------------------------------------------
MakeFace creates a new face structure from three vertices (in ccw
order).  It returns a pointer to the face.
---------------------------------------------------------------------*/
tFace MakeFace(tVertex v0, tVertex v1, tVertex v2, tFace fold)
{
    tFace f;
    tEdge e0, e1, e2;

    /* Create edges of the initial triangle. */
    if (!fold) {
        e0 = MakeNullEdge();
        e1 = MakeNullEdge();
        e2 = MakeNullEdge();
    }
    else { /* Copy from fold, in reverse order. */
        e0 = fold->edge[2];
        e1 = fold->edge[1];
        e2 = fold->edge[0];
    }
    e0->endpts[0] = v0;
    e0->endpts[1] = v1;
    e1->endpts[0] = v1;
    e1->endpts[1] = v2;
    e2->endpts[0] = v2;
    e2->endpts[1] = v0;

    /* Create face for triangle. */
    f = MakeNullFace();
    f->edge[0] = e0;
    f->edge[1] = e1;
    f->edge[2] = e2;
    f->vertex[0] = v0;
    f->vertex[1] = v1;
    f->vertex[2] = v2;

    /* Link edges to face. */
    e0->adjface[0] = e1->adjface[0] = e2->adjface[0] = f;

    return f;
}

/*---------------------------------------------------------------------
CleanUp goes through each data structure list and clears all
flags and NULLs out some pointers.  The order of processing
(edges, faces, vertices) is important.
---------------------------------------------------------------------*/
void CleanUp(void)
{
    CleanEdges();
    CleanFaces();
    CleanVertices();
}

/*---------------------------------------------------------------------
CleanEdges runs through the edge list and cleans up the structure.
If there is a newface then it will put that face in place of the
visible face and NULL out newface. It also deletes so marked edges.
---------------------------------------------------------------------*/
void CleanEdges(void)
{
    tEdge e; /* Primary index into edge list. */
    tEdge t; /* Temporary edge pointer. */

    /* Integrate the newface's into the data structure. */
    /* Check every edge. */
    e = edges;
    do {
        if (e->newface) {
            if (e->adjface[0]->visible)
                e->adjface[0] = e->newface;
            else
                e->adjface[1] = e->newface;
            e->newface = NULL;
        }
        e = e->next;
    } while (e != edges);

    /* Delete any edges marked for deletion. */
    while (edges && edges->delete) {
        e = edges;
        DELETE(edges, e);
    }
    e = edges->next;
    do {
        if (e->delete) {
            t = e;
            e = e->next;
            DELETE(edges, t);
        }
        else
            e = e->next;
    } while (e != edges);
}

/*---------------------------------------------------------------------
CleanFaces runs through the face list and deletes any face marked visible.
---------------------------------------------------------------------*/
void CleanFaces(void)
{
    tFace f; /* Primary pointer into face list. */
    tFace t; /* Temporary pointer, for deleting. */

    while (faces && faces->visible) {
        f = faces;
        DELETE(faces, f);
    }
    f = faces->next;
    do {
        if (f->visible) {
            t = f;
            f = f->next;
            DELETE(faces, t);
        }
        else
            f = f->next;
    } while (f != faces);
}

/*---------------------------------------------------------------------
CleanVertices runs through the vertex list and deletes the
vertices that are marked as processed but are not incident to any
undeleted edges.
---------------------------------------------------------------------*/
void CleanVertices(void)
{
    tEdge e;
    tVertex v, t;

    /* Mark all vertices incident to some undeleted edge as on the hull. */
    e = edges;
    do {
        e->endpts[0]->onhull = e->endpts[1]->onhull = ONHULL;
        e = e->next;
    } while (e != edges);

    /* Delete all vertices that have been processed but
       are not on the hull. */
    while (vertices && vertices->mark && !vertices->onhull) {
        v = vertices;
        DELETE(vertices, v);
    }
    v = vertices->next;
    do {
        if (v->mark && !v->onhull) {
            t = v;
            v = v->next;
            DELETE(vertices, t)
        }
        else
            v = v->next;
    } while (v != vertices);

    /* Reset flags. */
    v = vertices;
    do {
        v->duplicate = NULL;
        v->onhull = !ONHULL;
        v = v->next;
    } while (v != vertices);
}

/*---------------------------------------------------------------------
Collinear checks to see if the three points given are collinear,
by checking to see if each element of the cross product is zero.
---------------------------------------------------------------------*/
bool Collinear(tVertex a, tVertex b, tVertex c)
{
    return (c->v[Z] - a->v[Z]) * (b->v[Y] - a->v[Y]) -
                   (b->v[Z] - a->v[Z]) * (c->v[Y] - a->v[Y]) ==
               0 &&
           (b->v[Z] - a->v[Z]) * (c->v[X] - a->v[X]) -
                   (b->v[X] - a->v[X]) * (c->v[Z] - a->v[Z]) ==
               0 &&
           (b->v[X] - a->v[X]) * (c->v[Y] - a->v[Y]) -
                   (b->v[Y] - a->v[Y]) * (c->v[X] - a->v[X]) ==
               0;
}

/*---------------------------------------------------------------------
Consistency runs through the edge list and checks that all
adjacent faces have their endpoints in opposite order.  This verifies
that the vertices are in counterclockwise order.
---------------------------------------------------------------------*/
void Consistency(void)
{
    register tEdge e;
    register int i, j;

    e = edges;

    do {
        /* find index of endpoint[0] in adjacent face[0] */
        for (i = 0; e->adjface[0]->vertex[i] != e->endpts[0]; ++i)
            ;

        /* find index of endpoint[0] in adjacent face[1] */
        for (j = 0; e->adjface[1]->vertex[j] != e->endpts[0]; ++j)
            ;

        /* check if the endpoints occur in opposite order */
        if (!(e->adjface[0]->vertex[(i + 1) % 3] ==
                  e->adjface[1]->vertex[(j + 2) % 3] ||
              e->adjface[0]->vertex[(i + 2) % 3] ==
                  e->adjface[1]->vertex[(j + 1) % 3]))
            break;
        e = e->next;

    } while (e != edges);

    if (e != edges)
        fprintf(stderr, "Checks: edges are NOT consistent.\n");
    else
        fprintf(stderr, "Checks: edges consistent.\n");
}

/*---------------------------------------------------------------------
Convexity checks that the volume between every face and every
point is negative.  This shows that each point is inside every face
and therefore the hull is convex.
---------------------------------------------------------------------*/
void Convexity(void)
{
    register tFace f;
    register tVertex v;
    long int vol;

    f = faces;

    do {
        v = vertices;
        do {
            if (v->mark) {
                vol = VolumeSign(f, v);
                if (vol < 0)
                    break;
            }
            v = v->next;
        } while (v != vertices);

        f = f->next;

    } while (f != faces);

    if (f != faces)
        fprintf(stderr, "Checks: NOT convex.\n");
    else if (check)
        fprintf(stderr, "Checks: convex.\n");
}

/*---------------------------------------------------------------------
CheckEuler checks Euler's relation, as well as its implications when
all faces are known to be triangles.  Only prints positive information
when debug is true, but always prints negative information.
---------------------------------------------------------------------*/
void CheckEuler(long int V, long int E, long int F)
{
    if (check)
        fprintf(stderr, "Checks: V, E, F = %li %li %li:\t", V, E, F);

    if ((V - E + F) != 2)
        fprintf(stderr, "Checks: V-E+F != 2\n");
    else if (check)
        fprintf(stderr, "V-E+F = 2\t");

    if (F != (2 * V - 4))
        fprintf(stderr, "Checks: F=%li != 2V-4=%li; V=%li\n", F, 2 * V - 4, V);
    else if (check)
        fprintf(stderr, "F = 2V-4\t");

    if ((2 * E) != (3 * F))
        fprintf(stderr, "Checks: 2E=%li != 3F=%li; E=%li, F=%li\n", 2 * E,
                3 * F, E, F);
    else if (check)
        fprintf(stderr, "2E = 3F\n");
}

/*-------------------------------------------------------------------*/
void Checks(void)
{
    tVertex v;
    tEdge e;
    tFace f;
    long int V = 0, E = 0, F = 0;

    Consistency();
    Convexity();
    if (v = vertices)
        do {
            if (v->mark)
                V++;
            v = v->next;
        } while (v != vertices);
    if (e = edges)
        do {
            E++;
            e = e->next;
        } while (e != edges);
    if (f = faces)
        do {
            F++;
            f = f->next;
        } while (f != faces);
    CheckEuler(V, E, F);
}

/*===================================================================
These functions are used whenever the debug flag is set.
They print out the entire contents of each data structure.
Printing is to standard error.  To grab the output in a file in the csh,
use this:
        chull < i.file >&! o.file
=====================================================================*/

/*-------------------------------------------------------------------*/
void PrintOut(tVertex v)
{
    fprintf(stderr, "\nHead vertex %d = %6x :\n", v->vnum, (unsigned int)v);
    PrintVertices();
    PrintEdges();
    PrintFaces();
}

/*-------------------------------------------------------------------*/
void PrintVertices(void)
{
    tVertex temp;

    temp = vertices;
    fprintf(stderr, "Vertex List\n");
    if (vertices)
        do {
            fprintf(stderr, "  addr %6x\t", (unsigned int)vertices);
            fprintf(stderr, "  vnum %4d", vertices->vnum);
            fprintf(stderr, "   (%6li,%6li,%6li)", vertices->v[X],
                    vertices->v[Y], vertices->v[Z]);
            fprintf(stderr, "   active:%3d", vertices->onhull);
            fprintf(stderr, "   dup:%5x", (unsigned int)vertices->duplicate);
            fprintf(stderr, "   mark:%2d\n", vertices->mark);
            vertices = vertices->next;
        } while (vertices != temp);
}

/*-------------------------------------------------------------------*/
void PrintEdges(void)
{
    tEdge temp;
    int i;

    temp = edges;
    fprintf(stderr, "Edge List\n");
    if (edges)
        do {
            fprintf(stderr, "  addr: %6x\t", (unsigned int)edges);
            fprintf(stderr, "adj: ");
            for (i = 0; i < 2; ++i)
                fprintf(stderr, "%6x", (unsigned int)edges->adjface[i]);
            fprintf(stderr, "  endpts:");
            for (i = 0; i < 2; ++i)
                fprintf(stderr, "%4d", edges->endpts[i]->vnum);
            fprintf(stderr, "  del:%3d\n", edges->delete);
            edges = edges->next;
        } while (edges != temp);
}

/*-------------------------------------------------------------------*/
void PrintFaces(void)
{
    int i;
    tFace temp;

    temp = faces;
    fprintf(stderr, "Face List\n");
    if (faces)
        do {
            fprintf(stderr, "  addr: %6x\t", (unsigned int)faces);
            fprintf(stderr, "  edges:");
            for (i = 0; i < 3; ++i)
                fprintf(stderr, "%6x", (unsigned int)faces->edge[i]);
            fprintf(stderr, "  vert:");
            for (i = 0; i < 3; ++i)
                fprintf(stderr, "%4d", faces->vertex[i]->vnum);
            fprintf(stderr, "  vis: %d\n", faces->visible);
            faces = faces->next;
        } while (faces != temp);
}
